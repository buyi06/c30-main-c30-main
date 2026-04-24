"""REST API路由"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ..config import load_config, save_config, create_jwt, verify_jwt
from ..core.state import AppState
from ..core.log_buffer import LogBuffer
from ..core.scheduler import SchedulerService
from ..core.iclass30_api import (
    C30AutoSign, ACT_TYPE_MAP, PATTERN_MAP,
    ACT_SIGN_IN, ACT_SIGN_OUT, ACT_DISCUSS, ACT_BRAINSTORM, ACT_VOTE,
    STATE_ONGOING, STATE_ENDED,
)

router = APIRouter(prefix="/api")


# ===== JWT验证依赖 =====
async def get_current_user(request: Request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=401, detail="未登录")
    config = request.app.state.config
    if not verify_jwt(config, token):
        raise HTTPException(status_code=401, detail="登录已过期")
    return token


# ===== 请求模型 =====
class LoginRequest(BaseModel):
    password: str

class ConfigUpdate(BaseModel):
    auto_discuss_content: str | None = None
    auto_brainstorm_content: str | None = None
    poll_intervals: dict | None = None

class CredentialsUpdate(BaseModel):
    c30_username: str
    c30_password: str

class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str

class DiscussAction(BaseModel):
    content: str | None = None

class BrainstormAction(BaseModel):
    content: str | None = None

class VoteAction(BaseModel):
    options: str | None = None  # sortOrder逗号分隔


# ===== 认证 =====
@router.post("/auth/login")
async def auth_login(req: LoginRequest, request: Request):
    config = request.app.state.config
    token = create_jwt(config, req.password)
    if not token:
        raise HTTPException(status_code=401, detail="密码错误")
    return {"code": 200, "token": token}


# ===== 状态查询 =====
@router.get("/status")
async def get_status(request: Request, _=Depends(get_current_user)):
    state: AppState = request.app.state.app_state
    return {"code": 200, "result": state.get_status()}


@router.get("/courses/today")
async def get_courses_today(request: Request, _=Depends(get_current_user)):
    scheduler: SchedulerService = request.app.state.scheduler_service
    api = scheduler.api
    if not api:
        raise HTTPException(status_code=500, detail="API未初始化")
    courses = api.get_today_classes()
    return {"code": 200, "result": courses}


@router.get("/courses/{face_teach_id}/activities")
async def get_course_activities(face_teach_id: str, request: Request, _=Depends(get_current_user)):
    scheduler: SchedulerService = request.app.state.scheduler_service
    api = scheduler.api
    if not api:
        raise HTTPException(status_code=500, detail="API未初始化")
    # 获取进行中和已结束的活动
    activities_ongoing = api.get_activity_list(face_teach_id, STATE_ONGOING)
    activities_ended = api.get_activity_list(face_teach_id, STATE_ENDED)
    return {"code": 200, "result": activities_ongoing + activities_ended}


@router.get("/activities/{activity_id}/detail")
async def get_activity_detail(activity_id: str, request: Request, _=Depends(get_current_user)):
    scheduler: SchedulerService = request.app.state.scheduler_service
    api = scheduler.api
    if not api:
        raise HTTPException(status_code=500, detail="API未初始化")
    # 先获取活动列表来判断类型
    # 需要知道活动类型才能调用对应详情API
    # 从今日课程获取
    for cls in api.get_today_classes():
        fid = cls.get("id", cls.get("faceTeachId", ""))
        for cs in [STATE_ONGOING, STATE_ENDED]:
            acts = api.get_activity_list(fid, cs)
            for act in acts:
                if act.get("id") == activity_id:
                    act_type = act.get("activityType", 0)
                    return _get_detail_by_type(api, activity_id, act_type, fid)
    raise HTTPException(status_code=404, detail="活动未找到")


def _get_detail_by_type(api: C30AutoSign, activity_id: str, act_type: int, face_teach_id: str) -> dict:
    """根据活动类型获取详情"""
    if act_type in [ACT_SIGN_IN, ACT_SIGN_OUT]:
        detail = api.get_sign_detail(activity_id)
        sign_status = api.check_sign_status(activity_id)
        return {
            "code": 200,
            "result": {
                "type": ACT_TYPE_MAP.get(act_type, ""),
                "typeId": act_type,
                "activityId": activity_id,
                "signDetail": detail,
                "signStatus": sign_status,  # 1=已签, 0=未签
                "pattern": PATTERN_MAP.get(detail.get("signPatternType", 0) if detail else 0, "未知"),
            }
        }
    elif act_type == ACT_DISCUSS:
        detail = api.get_discuss_detail(activity_id)
        return {
            "code": 200,
            "result": {
                "type": "讨论",
                "typeId": act_type,
                "activityId": activity_id,
                "discussDetail": detail,
            }
        }
    elif act_type == ACT_BRAINSTORM:
        detail = api.get_brainstorm_detail(activity_id)
        return {
            "code": 200,
            "result": {
                "type": "头脑风暴",
                "typeId": act_type,
                "activityId": activity_id,
                "brainstormDetail": detail,
            }
        }
    elif act_type == ACT_VOTE:
        detail = api.get_vote_detail(activity_id)
        return {
            "code": 200,
            "result": {
                "type": "投票",
                "typeId": act_type,
                "activityId": activity_id,
                "voteDetail": detail,
            }
        }
    return {"code": 200, "result": {"type": ACT_TYPE_MAP.get(act_type, "未知"), "activityId": activity_id}}


# ===== 手动操作 =====
@router.post("/actions/sign/{activity_id}")
async def manual_sign(activity_id: str, request: Request, _=Depends(get_current_user)):
    scheduler: SchedulerService = request.app.state.scheduler_service
    log: LogBuffer = request.app.state.log_buffer
    api = scheduler.api
    if not api:
        raise HTTPException(status_code=500, detail="API未初始化")

    # 获取签到详情
    detail = api.get_sign_detail(activity_id)
    if not detail:
        raise HTTPException(status_code=500, detail="无法获取签到详情")
    sign_pattern_data = detail.get("signPatternData", "")
    center_point = detail.get("centerPoint", "{}")

    ok, msg = api.do_sign(activity_id, sign_pattern_data, center_point)
    if ok:
        log.success(f"[手动签到] {msg}", "sign")
        return {"code": 200, "message": msg}
    else:
        log.error(f"[手动签到] 失败: {msg}", "sign")
        return {"code": 500, "message": msg}


@router.post("/actions/discuss/{activity_id}")
async def manual_discuss(activity_id: str, req: DiscussAction, request: Request, _=Depends(get_current_user)):
    scheduler: SchedulerService = request.app.state.scheduler_service
    log: LogBuffer = request.app.state.log_buffer
    api = scheduler.api
    if not api:
        raise HTTPException(status_code=500, detail="API未初始化")

    content = req.content or request.app.state.config.get("auto_discuss_content", "老师讲得很好，受益匪浅")
    ok, msg = api.do_discuss_reply(activity_id, content)
    if ok:
        log.success(f"[手动讨论] {msg}", "discuss")
        return {"code": 200, "message": msg}
    else:
        log.error(f"[手动讨论] 失败: {msg}", "discuss")
        return {"code": 500, "message": msg}


@router.post("/actions/brainstorm/{activity_id}")
async def manual_brainstorm(activity_id: str, req: BrainstormAction, request: Request, _=Depends(get_current_user)):
    scheduler: SchedulerService = request.app.state.scheduler_service
    log: LogBuffer = request.app.state.log_buffer
    api = scheduler.api
    if not api:
        raise HTTPException(status_code=500, detail="API未初始化")

    # 需要知道faceTeachId
    content = req.content or request.app.state.config.get("auto_brainstorm_content", "我认为应该从多个角度思考这个问题")
    # 从课程列表获取faceTeachId
    face_teach_id = ""
    for cls in api.get_today_classes():
        fid = cls.get("id", cls.get("faceTeachId", ""))
        for cs in [STATE_ONGOING, STATE_ENDED]:
            acts = api.get_activity_list(fid, cs)
            for act in acts:
                if act.get("id") == activity_id:
                    face_teach_id = fid
                    break

    if not face_teach_id:
        raise HTTPException(status_code=404, detail="无法确定课程ID")

    ok, msg = api.do_brainstorm_submit(activity_id, face_teach_id, content)
    if ok:
        log.success(f"[手动头脑风暴] {msg}", "brainstorm")
        return {"code": 200, "message": msg}
    else:
        log.error(f"[手动头脑风暴] 失败: {msg}", "brainstorm")
        return {"code": 500, "message": msg}


@router.post("/actions/vote/{activity_id}")
async def manual_vote(activity_id: str, req: VoteAction, request: Request, _=Depends(get_current_user)):
    scheduler: SchedulerService = request.app.state.scheduler_service
    log: LogBuffer = request.app.state.log_buffer
    api = scheduler.api
    if not api:
        raise HTTPException(status_code=500, detail="API未初始化")

    if req.options:
        content = req.options
    else:
        # 自动选第一个选项
        detail = api.get_vote_detail(activity_id)
        if not detail:
            raise HTTPException(status_code=500, detail="无法获取投票详情")
        import json
        options = detail.get("optionData", [])
        if isinstance(options, str):
            try:
                options = json.loads(options)
            except Exception:
                options = []
        if not options:
            raise HTTPException(status_code=500, detail="无选项数据")
        content = str(options[0].get("sortOrder", "1"))

    ok, msg = api.do_vote(activity_id, content)
    if ok:
        log.success(f"[手动投票] {msg}", "vote")
        return {"code": 200, "message": msg}
    else:
        log.error(f"[手动投票] 失败: {msg}", "vote")
        return {"code": 500, "message": msg}


@router.post("/actions/refresh")
async def manual_refresh(request: Request, _=Depends(get_current_user)):
    scheduler: SchedulerService = request.app.state.scheduler_service
    await scheduler.refresh_now()
    return {"code": 200, "message": "刷新完成"}


# ===== 配置 =====
@router.get("/config")
async def get_config(request: Request, _=Depends(get_current_user)):
    config = request.app.state.config
    # 不返回敏感信息
    safe_config = {
        "c30_username": config.get("c30_username", ""),
        "auto_discuss_content": config.get("auto_discuss_content", ""),
        "auto_brainstorm_content": config.get("auto_brainstorm_content", ""),
        "poll_intervals": config.get("poll_intervals", {}),
        "log_max_lines": config.get("log_max_lines", 500),
    }
    return {"code": 200, "result": safe_config}


@router.put("/config")
async def update_config(req: ConfigUpdate, request: Request, _=Depends(get_current_user)):
    config = request.app.state.config
    if req.auto_discuss_content is not None:
        config["auto_discuss_content"] = req.auto_discuss_content
    if req.auto_brainstorm_content is not None:
        config["auto_brainstorm_content"] = req.auto_brainstorm_content
    if req.poll_intervals is not None:
        config["poll_intervals"] = req.poll_intervals
    save_config(config)
    return {"code": 200, "message": "配置已更新"}


@router.put("/config/credentials")
async def update_credentials(req: CredentialsUpdate, request: Request, _=Depends(get_current_user)):
    config = request.app.state.config
    config["c30_username"] = req.c30_username
    config["c30_password"] = req.c30_password
    save_config(config)
    # 重建API实例
    scheduler: SchedulerService = request.app.state.scheduler_service
    scheduler.api = scheduler._create_api()
    scheduler._schedule_loaded_day = None  # 强制重新加载课表
    return {"code": 200, "message": "账号已更新"}


@router.put("/config/password")
async def update_password(req: PasswordUpdate, request: Request, _=Depends(get_current_user)):
    config = request.app.state.config
    if req.old_password != config.get("admin_password", "admin123"):
        raise HTTPException(status_code=401, detail="旧密码错误")
    config["admin_password"] = req.new_password
    save_config(config)
    return {"code": 200, "message": "密码已更新"}


# ===== 调度控制 =====
@router.post("/scheduler/pause")
async def scheduler_pause(request: Request, _=Depends(get_current_user)):
    scheduler: SchedulerService = request.app.state.scheduler_service
    scheduler.pause()
    return {"code": 200, "message": "调度已暂停"}


@router.post("/scheduler/resume")
async def scheduler_resume(request: Request, _=Depends(get_current_user)):
    scheduler: SchedulerService = request.app.state.scheduler_service
    scheduler.resume()
    return {"code": 200, "message": "调度已恢复"}


@router.get("/scheduler/jobs")
async def scheduler_jobs(request: Request, _=Depends(get_current_user)):
    scheduler: SchedulerService = request.app.state.scheduler_service
    return {"code": 200, "result": scheduler.get_jobs_info()}