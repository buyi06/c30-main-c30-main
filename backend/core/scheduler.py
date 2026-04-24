"""APScheduler定时任务管理 - 嵌入FastAPI进程"""

import asyncio
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .iclass30_api import (
    C30AutoSign, ScheduleManager,
    ACT_SIGN_IN, ACT_SIGN_OUT, ACT_DISCUSS, ACT_BRAINSTORM, ACT_VOTE,
    PATTERN_NORMAL, PATTERN_QRCODE, PATTERN_GESTURE,
    STATE_ONGOING, STATE_ENDED, ACT_TYPE_MAP, PATTERN_MAP,
)
from .state import AppState
from .log_buffer import LogBuffer


class SchedulerService:
    """定时任务服务 - 轮询C30平台并自动处理活动"""

    def __init__(self, config: dict, state: AppState, log_buffer: LogBuffer):
        self.config = config
        self.state = state
        self.log = log_buffer
        self.scheduler = AsyncIOScheduler()
        self.api: C30AutoSign | None = None
        self._schedule_loaded_day = None
        self._job = None
        self._running = False
        # 活动→faceTeachId 缓存（避免O(n²)遍历）
        self._activity_course_map: dict[str, str] = {}

    def _create_api(self) -> C30AutoSign:
        """创建C30API实例"""
        return C30AutoSign(
            username=self.config.get("c30_username", ""),
            password=self.config.get("c30_password", ""),
        )

    def start(self):
        """启动定时任务"""
        self.api = self._create_api()
        # 尝试从缓存加载课表
        if self.api.schedule_mgr.load_from_cache():
            self.log.info("课表已从缓存加载", "system")
            self._schedule_loaded_day = datetime.now().strftime("%Y-%m-%d")
        # 更新课表轮询间隔
        self.api.schedule_mgr.poll_intervals = self.config.get("poll_intervals", {
            "pre_class": 60, "in_class": 120, "between": 1800, "weekend": 7200
        })
        self._running = True
        # 根据当前时段设置初始轮询间隔，避免启动时多余轮询
        interval, _ = self.api.schedule_mgr.get_poll_interval()
        self._job = self.scheduler.add_job(
            self._tick, "interval", seconds=interval, id="c30_poll",
            next_run_time=datetime.now()
        )
        self.scheduler.start()
        self.log.info("调度器已启动")

    def stop(self):
        """停止定时任务"""
        self._running = False
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
        self.log.info("调度器已停止")

    def pause(self):
        """暂停调度"""
        if self._job:
            self._job.pause()
        self.state.set_paused(True)
        self.log.info("自动调度已暂停")

    def resume(self):
        """恢复调度"""
        if self._job:
            self._job.resume()
        self.state.set_paused(False)
        self.log.info("自动调度已恢复")

    def is_paused(self) -> bool:
        if self._job:
            return self._job.next_run_time is None
        return not self._running

    def get_jobs_info(self) -> list:
        """获取任务列表"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name or job.id,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "paused": job.next_run_time is None,
            })
        return jobs

    def get_face_teach_id(self, activity_id: str) -> str | None:
        """从缓存获取活动所属课程ID"""
        return self._activity_course_map.get(activity_id)

    async def _tick(self):
        """定时轮询执行"""
        try:
            # 在线程池中运行同步的API调用
            await asyncio.get_event_loop().run_in_executor(None, self._do_poll)
        except Exception as e:
            self.log.error(f"轮询异常: {e}")

    def _do_poll(self):
        """执行一次完整轮询"""
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")

        # 每天重新加载课表
        if self._schedule_loaded_day != today_str:
            ok, msg = self.api.login()
            self.log.info(msg, "system")
            if not ok:
                self.state.update_login(False)
                # 尝试从缓存恢复课表
                if self.api.schedule_mgr.load_from_cache():
                    self.log.info("API登录失败，使用缓存课表", "system")
                return
            self.state.update_login(True, self.config.get("c30_username", ""))
            self.api.schedule_mgr.load_from_api(self.api.session)
            self._schedule_loaded_day = today_str
            courses = self.api.schedule_mgr.get_today_courses()
            if courses:
                self.log.info(f"今日 {len(courses)} 门课", "system")
                for c in courses:
                    self.log.info(f"  {c['courseName']}", "system")
            else:
                self.log.info("今日无课", "system")
        else:
            # 非首次轮询也尝试登录刷新token
            ok, msg = self.api.login()
            if not ok:
                self.log.error(msg, "system")
                self.state.update_login(False)
                return
            self.state.update_login(True, self.config.get("c30_username", ""))

        # 更新课表轮询间隔（可能被配置修改）
        self.api.schedule_mgr.poll_intervals = self.config.get("poll_intervals", {
            "pre_class": 60, "in_class": 120, "between": 1800, "weekend": 7200
        })

        interval, status = self.api.schedule_mgr.get_poll_interval()
        status_cn = {"pre_class": "课前", "in_class": "课中", "between": "课间",
                     "weekend": "周末", "no_class_today": "无课"}.get(status, status)

        self.state.update_period(status)
        self.state.update_poll_time(interval)
        self.log.info(f"{now.strftime('%H:%M:%S')} | {status_cn} | 下次{interval}秒后", "system")

        # 动态调整轮询间隔
        if self._job:
            self._job.modify(trigger="interval", seconds=interval)

        # 获取今日课程
        classes = self.api.get_today_classes()
        self.state.update_courses(classes)

        # 重置统计
        self.state.reset_activity_stats()

        # 处理每个课程的活动
        for cls in classes:
            course_name = cls.get("courseName", "未知课程")
            face_teach_id = cls.get("id", cls.get("faceTeachId", ""))
            state_val = cls.get("state", 0)

            for cs in [STATE_ONGOING, STATE_ENDED]:
                activities = self.api.get_activity_list(face_teach_id, cs)
                for act in activities:
                    # 缓存活动→课程映射
                    act_id = act.get("id", "")
                    if act_id:
                        self._activity_course_map[act_id] = face_teach_id
                    self._process_activity(act, face_teach_id, course_name)

    def _process_activity(self, act: dict, face_teach_id: str, course_name: str):
        """处理单个活动"""
        act_type = act.get("activityType", 0)
        act_pattern = act.get("activityPattern", 0)
        act_state = act.get("state", 0)
        act_title = act.get("title", "")
        act_id = act.get("id", "")

        # 跳过已处理的
        if self.state.is_done(act_id):
            self.state.count_activity(act_type, "done")
            return

        type_str = ACT_TYPE_MAP.get(act_type, f"类型{act_type}")

        # ===== 签到/签退 =====
        if act_type in [ACT_SIGN_IN, ACT_SIGN_OUT]:
            category = "sign"
            sign_status = self.api.check_sign_status(act_id)
            if sign_status == 1:
                self.state.mark_done(act_id)
                self.state.count_activity(act_type, "done")
                self.log.success(f"[{type_str}] {act_title} - 已完成", category)
                return
            if act_state != STATE_ONGOING:
                self.state.count_activity(act_type, "pending")
                self.log.info(f"[{type_str}] {act_title} - 已结束未签", category)
                return

            self.state.count_activity(act_type, "pending")

            if act_pattern == PATTERN_NORMAL:
                detail = self.api.get_sign_detail(act_id)
                cp = detail.get("centerPoint", "{}") if detail else "{}"
                self.log.info(f"[{type_str}] {act_title} - 普通签到...", category)
                ok, resp = self.api.do_sign(act_id, "", cp)
                if ok:
                    self.state.mark_done(act_id)
                    self.state.count_activity(act_type, "done")
                    self.log.success(f"[{type_str}] {act_title} - {resp}", category)
                else:
                    self.log.error(f"[{type_str}] {act_title} - 失败: {resp}", category)

            elif act_pattern in [PATTERN_QRCODE, PATTERN_GESTURE]:
                detail = self.api.get_sign_detail(act_id)
                answer = detail.get("signPatternData", "") if detail else ""
                cp = detail.get("centerPoint", "{}") if detail else "{}"
                pattern_str = PATTERN_MAP.get(act_pattern, "")
                if answer:
                    self.log.info(f"[{type_str}] 答案: {answer}", category)
                self.log.info(f"[{type_str}] {act_title} - {pattern_str}签到...", category)
                ok, resp = self.api.do_sign(act_id, answer, cp)
                if ok:
                    self.state.mark_done(act_id)
                    self.state.count_activity(act_type, "done")
                    self.log.success(f"[{type_str}] {act_title} - {resp}", category)
                else:
                    self.log.error(f"[{type_str}] {act_title} - 失败: {resp}", category)

        # ===== 讨论 =====
        elif act_type == ACT_DISCUSS:
            category = "discuss"
            if act_state != STATE_ONGOING:
                return
            content = self.config.get("auto_discuss_content", "老师讲得很好，受益匪浅")
            self.log.info(f"[讨论] {act_title} - 自动回复...", category)
            ok, resp = self.api.do_discuss_reply(act_id, content)
            if ok:
                self.state.mark_done(act_id)
                self.state.count_activity(act_type, "done")
                self.log.success(f"[讨论] {act_title} - {resp}", category)
            else:
                self.log.error(f"[讨论] {act_title} - 失败: {resp}", category)

        # ===== 头脑风暴 =====
        elif act_type == ACT_BRAINSTORM:
            category = "brainstorm"
            if act_state != STATE_ONGOING:
                return
            content = self.config.get("auto_brainstorm_content", "我认为应该从多个角度思考这个问题")
            self.log.info(f"[头脑风暴] {act_title} - 自动提交...", category)
            ok, resp = self.api.do_brainstorm_submit(act_id, face_teach_id, content)
            if ok:
                self.state.mark_done(act_id)
                self.state.count_activity(act_type, "done")
                self.log.success(f"[头脑风暴] {act_title} - {resp}", category)
            else:
                self.log.error(f"[头脑风暴] {act_title} - 失败: {resp}", category)

        # ===== 投票 =====
        elif act_type == ACT_VOTE:
            category = "vote"
            if act_state != STATE_ONGOING:
                return
            detail = self.api.get_vote_detail(act_id)
            if not detail:
                self.log.error(f"[投票] {act_title} - 无法获取详情", category)
                return
            import json as _json
            options = detail.get("optionData", [])
            if isinstance(options, str):
                try:
                    options = _json.loads(options)
                except Exception:
                    options = []
            if not options:
                self.log.error(f"[投票] {act_title} - 无选项数据", category)
                return
            first_sort = options[0].get("sortOrder", "1")
            content = str(first_sort)
            self.log.info(f"[投票] {act_title} - 投票(选项:{content})...", category)
            ok, resp = self.api.do_vote(act_id, content)
            if ok:
                self.state.mark_done(act_id)
                self.state.count_activity(act_type, "done")
                self.log.success(f"[投票] {act_title} - {resp}", category)
            else:
                self.log.error(f"[投票] {act_title} - 失败: {resp}", category)

    async def refresh_now(self):
        """立即刷新一次"""
        self.log.info("手动触发刷新", "system")
        await self._tick()
