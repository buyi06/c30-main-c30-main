#!/usr/bin/env python3
"""
C30在线 全功能自动化脚本 v4
- 签到/签退：普通/手势/扫码全部自动（sign/get泄露答案）
- 讨论：自动回复
- 头脑风暴：自动提交观点
- 投票：自动投票
- 课表驱动智能轮询
用法:
  python3 iclass30_autosign.py              # 全功能自动化
  python3 iclass30_autosign.py --dry-run     # 仅查看状态
  python3 iclass30_autosign.py --only-sign   # 只处理签到/签退
  python3 iclass30_autosign.py --daemon      # 守护进程模式
"""

import requests
import json
import sys
import time
import os
from datetime import datetime, timedelta
from collections import defaultdict

# ============ 配置 ============
GATEWAY = "https://pxservice.iclass30.com/gatewayApi"
USERNAME = "2504140523"
PASSWORD = "114114Aa@"

# 活动类型（从逆向确认的完整枚举）
ACT_SIGN_IN = 1      # 签到
ACT_DISCUSS = 2      # 讨论
ACT_VOTE = 3         # 投票（原activityType=2在旧版，新版=3）
ACT_BRAINSTORM = 4   # 头脑风暴
ACT_SIGN_OUT = 9     # 签退

# 签到模式
PATTERN_NORMAL = 1   # 普通
PATTERN_QRCODE = 2   # 扫码/手势（sign/get返回答案）
PATTERN_GESTURE = 3  # 手势

# 课堂/活动状态
STATE_ONGOING = 2
STATE_ENDED = 3

# 自动回复配置
AUTO_DISCUSS_CONTENT = "老师讲得很好，受益匪浅"  # 讨论自动回复内容
AUTO_BRAINSTORM_CONTENT = "我认为应该从多个角度思考这个问题，结合实践进行深入分析"  # 头脑风暴自动内容

# 轮询间隔
POLL_PRE_CLASS = 60
POLL_IN_CLASS = 120
POLL_BETWEEN = 1800
POLL_WEEKEND = 7200

SCHEDULE_CACHE_HOURS = 6
SCHEDULE_FILE = "/root/.hermes/scripts/c30_schedule.json"


class ScheduleManager:
    def __init__(self):
        self.schedule = {}
        self.today_classes = []
        self.loaded_date = None

    def load_from_api(self, session):
        today = datetime.now()
        start = today.strftime("%Y-%m-%d")
        end = (today + timedelta(days=7)).strftime("%Y-%m-%d")
        resp = session.get(f"{GATEWAY}/faceteach/stu/getListByAll", params={
            "startDate": start, "endDate": end, "page": 1, "pageSize": 200,
        }, timeout=10)
        data = resp.json()
        if data.get("code") != 200:
            return False
        classes = data.get("result", [])
        if isinstance(classes, dict):
            classes = classes.get("list", classes.get("records", []))
        self.schedule = defaultdict(list)
        for cls in classes:
            ts = cls.get("teachDate", 0)
            if isinstance(ts, (int, float)) and ts > 0:
                date_str = datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d")
            else:
                continue
            self.schedule[date_str].append({
                "courseName": cls.get("courseName", ""),
                "faceTeachId": cls.get("id", cls.get("faceTeachId", "")),
                "startTime": cls.get("startTime", ""),
                "endTime": cls.get("endTime", ""),
            })
        today_str = today.strftime("%Y-%m-%d")
        self.today_classes = [c["faceTeachId"] for c in self.schedule.get(today_str, [])]
        self.loaded_date = today_str
        self._save_cache()
        return True

    def load_from_cache(self):
        if not os.path.exists(SCHEDULE_FILE):
            return False
        try:
            with open(SCHEDULE_FILE, "r") as f:
                cache = json.load(f)
            cache_time = datetime.fromisoformat(cache.get("timestamp", "2000-01-01"))
            if datetime.now() - cache_time > timedelta(hours=SCHEDULE_CACHE_HOURS):
                return False
            self.schedule = cache.get("schedule", {})
            today_str = datetime.now().strftime("%Y-%m-%d")
            self.today_classes = [c["faceTeachId"] for c in self.schedule.get(today_str, [])]
            self.loaded_date = today_str
            return True
        except Exception:
            return False

    def _save_cache(self):
        try:
            with open(SCHEDULE_FILE, "w") as f:
                json.dump({"timestamp": datetime.now().isoformat(), "schedule": dict(self.schedule)}, f, ensure_ascii=False)
        except Exception:
            pass

    def get_today_courses(self):
        return self.schedule.get(datetime.now().strftime("%Y-%m-%d"), [])

    def has_class_today(self):
        return len(self.get_today_courses()) > 0

    def get_current_status(self):
        now = datetime.now()
        if now.weekday() >= 5:
            return "weekend"
        if not self.has_class_today():
            return "no_class_today"
        h, m = now.hour, now.minute
        now_min = h * 60 + m
        for course in self.get_today_courses():
            st, et = course.get("startTime", ""), course.get("endTime", "")
            if not st or not et:
                continue
            try:
                sh, sm = map(int, st.split(":"))
                eh, em = map(int, et.split(":"))
                start_min, end_min = sh * 60 + sm, eh * 60 + em
                if start_min - 5 <= now_min < start_min:
                    return "pre_class"
                if start_min <= now_min <= end_min:
                    return "in_class"
            except (ValueError, AttributeError):
                pass
        for sh, sm, eh, em in [(8,10,12,0),(14,20,18,0),(19,0,20,50)]:
            if sh*60+sm-5 <= now_min <= eh*60+em:
                return "pre_class" if now_min < sh*60+sm else "in_class"
        return "between"

    def get_poll_interval(self):
        status = self.get_current_status()
        intervals = {"pre_class": POLL_PRE_CLASS, "in_class": POLL_IN_CLASS,
                     "between": POLL_BETWEEN, "weekend": POLL_WEEKEND, "no_class_today": POLL_WEEKEND}
        return intervals.get(status, POLL_BETWEEN), status


class C30AutoSign:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
            "Referer": "https://px.iclass30.com/onlineC30/",
            "Origin": "https://px.iclass30.com",
        })
        self.token = ""
        self.done_ids = set()  # 已处理的活动ID（签到/签退/讨论/头脑风暴/投票）
        self.schedule_mgr = ScheduleManager()

    def login(self):
        resp = self.session.get(f"{GATEWAY}/user/portal/newLoginApp", params={
            "userName": USERNAME, "password": PASSWORD,
            "clientId": "4", "sourceType": "4", "terminalType": "h5", "userId": "",
        }, timeout=10)
        data = resp.json()
        if data.get("code") == 200 and data.get("result"):
            result = data["result"]
            self.token = result["token"] if isinstance(result, dict) else str(result)
            self.session.headers["token"] = self.token
            return True, "登录成功"
        return False, f"登录失败: {json.dumps(data, ensure_ascii=False)}"

    def get_today_classes(self):
        today = datetime.now().strftime("%Y-%m-%d")
        resp = self.session.get(f"{GATEWAY}/faceteach/stu/getListByAll", params={
            "startDate": today, "endDate": today, "page": 1, "pageSize": 50,
        }, timeout=10)
        data = resp.json()
        if data.get("code") == 200:
            classes = data.get("result", [])
            if isinstance(classes, dict):
                classes = classes.get("list", classes.get("records", []))
            return classes
        return []

    def get_activity_list(self, face_teach_id, class_state=STATE_ONGOING):
        resp = self.session.get(f"{GATEWAY}/faceteach/activity/stu/list", params={
            "classState": class_state, "faceTeachId": face_teach_id,
        }, timeout=10)
        data = resp.json()
        if data.get("code") == 200:
            return data.get("result", [])
        return []

    def check_sign_status(self, sign_id):
        resp = self.session.get(f"{GATEWAY}/faceteach/sign/study/getStudyData",
                                params={"signId": sign_id}, timeout=10)
        data = resp.json()
        if data.get("code") == 200:
            return data.get("result", {}).get("studySignState", -1)
        elif data.get("code") == -200:
            return 0
        return -1

    def get_sign_detail(self, sign_id):
        resp = self.session.get(f"{GATEWAY}/faceteach/sign/get",
                                params={"signId": sign_id}, timeout=10)
        data = resp.json()
        if data.get("code") == 200:
            return data.get("result", {})
        return None

    def do_sign(self, sign_id, sign_pattern_data="", center_point="{}"):
        resp = self.session.post(f"{GATEWAY}/faceteach/sign/study/participate", data={
            "signPatternData": sign_pattern_data,
            "signId": sign_id,
            "centerPoint": center_point,
        }, timeout=10)
        data = resp.json()
        if data.get("code") == -200:
            self.done_ids.add(sign_id)
            return True, "已签到(重复)"
        return data.get("code") == 200, data

    # ===== 讨论 =====
    def get_discuss_detail(self, discuss_id):
        resp = self.session.get(f"{GATEWAY}/faceteach/discuss/view",
                                params={"discussId": discuss_id}, timeout=10)
        data = resp.json()
        if data.get("code") == 200:
            return data.get("result", {})
        return None

    def do_discuss_reply(self, discuss_id, content, parent_id="0"):
        resp = self.session.post(f"{GATEWAY}/faceteach/discuss/reply/add", json={
            "discussId": discuss_id,
            "parentId": parent_id,
            "sourceType": 1,
            "url": "",
            "content": content,
            "file": "[]",
        }, timeout=10)
        data = resp.json()
        if data.get("code") == 200:
            self.done_ids.add(discuss_id)
            return True, "讨论回复成功"
        elif data.get("msg", "") == "请勿重复签到或签退" or data.get("code") == -200:
            self.done_ids.add(discuss_id)
            return True, "已回复(重复)"
        return data.get("code") == 200, data

    # ===== 头脑风暴 =====
    def get_brainstorm_detail(self, brainstorm_id):
        resp = self.session.get(f"{GATEWAY}/faceteach/brainstorm/getBrainStorm",
                                params={"brainstormId": brainstorm_id}, timeout=10)
        data = resp.json()
        if data.get("code") == 200:
            return data.get("result", {})
        return None

    def do_brainstorm_submit(self, brainstorm_id, face_teach_id, answer):
        resp = self.session.post(f"{GATEWAY}/faceteach/brainstormstu/addBrainStormStu", json={
            "brainstormId": brainstorm_id,
            "answer": answer,
            "faceTeachId": face_teach_id,
            "file": "[]",
        }, timeout=10)
        data = resp.json()
        if data.get("code") == 200:
            self.done_ids.add(brainstorm_id)
            return True, "头脑风暴提交成功"
        elif data.get("code") == -200:
            self.done_ids.add(brainstorm_id)
            return True, "已提交(重复)"
        return data.get("code") == 200, data

    # ===== 投票 =====
    def get_vote_detail(self, vote_id):
        resp = self.session.get(f"{GATEWAY}/faceteach/vote/get",
                                params={"voteId": vote_id}, timeout=10)
        data = resp.json()
        if data.get("code") == 200:
            return data.get("result", {})
        return None

    def do_vote(self, vote_id, content):
        """content = 选项sortOrder逗号分隔"""
        resp = self.session.post(f"{GATEWAY}/faceteach/vote/study/participate", data={
            "voteId": vote_id,
            "content": content,
        }, timeout=10)
        data = resp.json()
        if data.get("code") == 200:
            self.done_ids.add(vote_id)
            return True, "投票成功"
        elif data.get("code") == -200:
            self.done_ids.add(vote_id)
            return True, "已投票(重复)"
        return data.get("code") == 200, data

    def run_once(self, dry_run=False, only_sign=False):
        log = []
        alerts = []
        stats = {"total": 0, "success": 0}

        ok, msg = self.login()
        log.append(msg)
        if not ok:
            return log, alerts

        classes = self.get_today_classes()
        weekday = datetime.now().strftime("%A")
        log.append(f"今日({weekday}): {len(classes)}个课堂")

        if not classes:
            log.append("没有课堂，跳过")
            return log, alerts

        for cls in classes:
            course_name = cls.get("courseName", "未知课程")
            face_teach_id = cls.get("id", cls.get("faceTeachId", ""))
            state = cls.get("state", 0)
            state_str = "进行中" if state == STATE_ONGOING else "已结束"
            log.append(f"📚 {course_name} ({state_str})")

            for cs in [STATE_ONGOING, STATE_ENDED]:
                activities = self.get_activity_list(face_teach_id, cs)
                for act in activities:
                    act_type = act.get("activityType", 0)
                    act_pattern = act.get("activityPattern", 0)
                    act_state = act.get("state", 0)
                    act_title = act.get("title", "")
                    act_id = act.get("id", "")

                    if act_id in self.done_ids:
                        continue

                    type_map = {1: "签到", 2: "讨论", 3: "投票", 4: "头脑风暴",
                                5: "抢答", 6: "课件", 7: "PK", 8: "评价", 9: "签退",
                                10: "测验", 11: "问卷", 12: "弹幕", 13: "PK"}
                    type_str = type_map.get(act_type, f"类型{act_type}")
                    pattern_map = {1: "普通", 2: "扫码", 3: "手势"}
                    pattern_str = pattern_map.get(act_pattern, "")
                    act_state_str = "进行中" if act_state == STATE_ONGOING else "已结束"

                    # ===== 签到/签退 =====
                    if act_type in [ACT_SIGN_IN, ACT_SIGN_OUT]:
                        sign_status = self.check_sign_status(act_id)
                        if sign_status == 1:
                            self.done_ids.add(act_id)
                            log.append(f"  ✅ [{type_str}] {act_title} - 已完成")
                            continue
                        if act_state != STATE_ONGOING:
                            log.append(f"  ⏳ [{type_str}] {act_title} - 已结束未签")
                            alerts.append({"type": "ended_not_signed", "typeId": act_id,
                                           "courseName": course_name, "title": act_title})
                            continue

                        if act_pattern == PATTERN_NORMAL:
                            if dry_run:
                                log.append(f"  🔍 [{type_str}] {act_title} - 模拟普通签到")
                                stats["total"] += 1
                                continue
                            stats["total"] += 1
                            detail = self.get_sign_detail(act_id)
                            cp = detail.get("centerPoint", "{}") if detail else "{}"
                            log.append(f"  🚀 [{type_str}] {act_title} - 普通签到...")
                            ok, resp = self.do_sign(act_id, "", cp)
                            if ok:
                                stats["success"] += 1
                                self.done_ids.add(act_id)
                                log.append(f"  ✅ [{type_str}] {act_title} - 成功！")
                            else:
                                log.append(f"  ✗ [{type_str}] {act_title} - 失败: {resp}")

                        elif act_pattern in [PATTERN_QRCODE, PATTERN_GESTURE]:
                            detail = self.get_sign_detail(act_id)
                            answer = detail.get("signPatternData", "") if detail else ""
                            atype = detail.get("signPatternType", 0) if detail else 0
                            cp = detail.get("centerPoint", "{}") if detail else "{}"
                            if answer:
                                log.append(f"  📋 [{type_str}] 答案: {answer} (type={atype})")
                            if dry_run:
                                log.append(f"  🔍 [{type_str}] {act_title} - 模拟{pattern_str}签到")
                                stats["total"] += 1
                                continue
                            stats["total"] += 1
                            log.append(f"  🚀 [{type_str}] {act_title} - {pattern_str}签到...")
                            ok, resp = self.do_sign(act_id, answer, cp)
                            if ok:
                                stats["success"] += 1
                                self.done_ids.add(act_id)
                                log.append(f"  ✅ [{type_str}] {act_title} - 成功！")
                            else:
                                log.append(f"  ✗ [{type_str}] {act_title} - 失败: {resp}")

                    # ===== 讨论（只处理进行中的） =====
                    elif act_type == ACT_DISCUSS and not only_sign:
                        if act_state != STATE_ONGOING:
                            continue  # 已结束的讨论不处理
                        discuss_id = act_id
                        if dry_run:
                            log.append(f"  🔍 [讨论] {act_title} - 模拟回复")
                            stats["total"] += 1
                            continue
                        stats["total"] += 1
                        log.append(f"  🚀 [讨论] {act_title} - 自动回复...")
                        ok, resp = self.do_discuss_reply(discuss_id, AUTO_DISCUSS_CONTENT)
                        if ok:
                            stats["success"] += 1
                            log.append(f"  ✅ [讨论] {act_title} - {resp}")
                        else:
                            log.append(f"  ✗ [讨论] {act_title} - 失败: {resp}")

                    # ===== 头脑风暴 =====
                    elif act_type == ACT_BRAINSTORM and not only_sign:
                        if act_state != STATE_ONGOING:
                            continue
                        if dry_run:
                            log.append(f"  🔍 [头脑风暴] {act_title} - 模拟提交")
                            stats["total"] += 1
                            continue
                        stats["total"] += 1
                        log.append(f"  🚀 [头脑风暴] {act_title} - 自动提交...")
                        ok, resp = self.do_brainstorm_submit(act_id, face_teach_id, AUTO_BRAINSTORM_CONTENT)
                        if ok:
                            stats["success"] += 1
                            log.append(f"  ✅ [头脑风暴] {act_title} - {resp}")
                        else:
                            log.append(f"  ✗ [头脑风暴] {act_title} - 失败: {resp}")

                    # ===== 投票 =====
                    elif act_type == ACT_VOTE and not only_sign:
                        if act_state != STATE_ONGOING:
                            continue
                        vote_id = act_id
                        detail = self.get_vote_detail(vote_id)
                        if not detail:
                            log.append(f"  ⚠️ [投票] {act_title} - 无法获取详情")
                            continue
                        vote_type = detail.get("voteType", 0)
                        options = detail.get("optionData", [])
                        # 解析选项，选择第一个
                        if isinstance(options, str):
                            try:
                                options = json.loads(options)
                            except:
                                options = []
                        if not options:
                            log.append(f"  ⚠️ [投票] {act_title} - 无选项数据")
                            continue
                        # 选第一个选项的sortOrder
                        first_sort = options[0].get("sortOrder", "1")
                        content = str(first_sort)
                        if vote_type == 4:  # 多选，选全部
                            content = ",".join(str(o.get("sortOrder", i+1)) for i, o in enumerate(options[:3]))

                        if dry_run:
                            log.append(f"  🔍 [投票] {act_title} - 模拟投票(选项:{content})")
                            stats["total"] += 1
                            continue
                        stats["total"] += 1
                        log.append(f"  🚀 [投票] {act_title} - 投票(选项:{content})...")
                        ok, resp = self.do_vote(vote_id, content)
                        if ok:
                            stats["success"] += 1
                            log.append(f"  ✅ [投票] {act_title} - {resp}")
                        else:
                            log.append(f"  ✗ [投票] {act_title} - 失败: {resp}")

                    # 其他类型暂不自动处理
                    elif act_type in [5, 6, 7, 8, 10, 11, 12, 13]:
                        pass  # 抢答/课件/PK/评价/测验/问卷/弹幕/PK - 暂不处理

        if stats["total"] > 0:
            log.append(f"结果: 成功 {stats['success']}/{stats['total']}")

        if alerts:
            alert_file = "/root/.hermes/scripts/c30_alerts.json"
            with open(alert_file, "w") as f:
                json.dump({"timestamp": datetime.now().isoformat(), "alerts": alerts}, f, ensure_ascii=False)
            log.append(f"⚠️ 写入 {len(alerts)} 个alert")

        return log, alerts

    def daemon_loop(self):
        print("[daemon] C30全功能自动化 v4 启动", flush=True)
        print("[daemon] 签退/讨论/头脑风暴/投票全自动", flush=True)

        schedule_load_day = None

        while True:
            now = datetime.now()
            today_str = now.strftime("%Y-%m-%d")

            if schedule_load_day != today_str:
                if not self.schedule_mgr.load_from_cache():
                    ok, _ = self.login()
                    if ok:
                        self.schedule_mgr.load_from_api(self.session)
                schedule_load_day = today_str
                courses = self.schedule_mgr.get_today_courses()
                if courses:
                    print(f"\n[课表] 今日 {len(courses)} 门课:", flush=True)
                    for c in courses:
                        print(f"  {c['courseName']} {c.get('startTime','')}-{c.get('endTime','')}", flush=True)
                else:
                    print(f"\n[课表] 今日无课", flush=True)

            interval, status = self.schedule_mgr.get_poll_interval()
            status_cn = {"pre_class":"课前","in_class":"课中","between":"课间","weekend":"周末","no_class_today":"无课"}.get(status, status)
            print(f"\n[{now.strftime('%H:%M:%S')}] {now.strftime('%A')} | {status_cn} | {interval}s", flush=True)

            try:
                log, alerts = self.run_once()
                for line in log:
                    print(f"  {line}", flush=True)
            except Exception as e:
                print(f"  [ERROR] {e}", flush=True)

            print(f"  下次: {interval}s后", flush=True)
            time.sleep(interval)


def main():
    dry_run = "--dry-run" in sys.argv
    only_sign = "--only-sign" in sys.argv
    daemon = "--daemon" in sys.argv

    bot = C30AutoSign()

    if daemon:
        bot.daemon_loop()
    else:
        log, alerts = bot.run_once(dry_run=dry_run, only_sign=only_sign)
        for line in log:
            print(line)
        if alerts:
            print(f"\n⚠️ 有 {len(alerts)} 个异常需要介入！")
            for a in alerts:
                print(f"  - {a['type']}: {a.get('courseName','')} {a.get('title','')}")


if __name__ == "__main__":
    main()