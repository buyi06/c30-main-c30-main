"""C30平台API调用层 - 从iclass30_autosign.py抽取复用"""

import os
import requests
import json
import time
from datetime import datetime, timedelta
from collections import defaultdict

# API网关
GATEWAY = "https://pxservice.iclass30.com/gatewayApi"

# 活动类型枚举
ACT_SIGN_IN = 1      # 签到
ACT_DISCUSS = 2      # 讨论
ACT_VOTE = 3         # 投票
ACT_BRAINSTORM = 4   # 头脑风暴
ACT_SIGN_OUT = 9     # 签退

# 签到模式枚举
PATTERN_NORMAL = 1   # 普通
PATTERN_QRCODE = 2   # 扫码
PATTERN_GESTURE = 3  # 手势

# 课堂/活动状态枚举
STATE_ONGOING = 2
STATE_ENDED = 3

# 活动类型中文映射
ACT_TYPE_MAP = {
    1: "签到", 2: "讨论", 3: "投票", 4: "头脑风暴",
    5: "抢答", 6: "课件", 7: "PK", 8: "评价",
    9: "签退", 10: "测验", 11: "问卷", 12: "弹幕", 13: "PK"
}

# 签到模式中文映射
PATTERN_MAP = {1: "普通", 2: "扫码", 3: "手势"}

# 课表缓存
SCHEDULE_CACHE_HOURS = 6
SCHEDULE_CACHE_FILE = os.environ.get(
    "C30_SCHEDULE_CACHE",
    os.path.join(os.path.dirname(__file__), "..", "..", "schedule_cache.json")
)

# API重试
MAX_RETRIES = 3
RETRY_DELAY = 2


def _retry_request(fn, *args, **kwargs):
    """带重试的请求执行，最多3次，间隔2秒"""
    last_exc = None
    for attempt in range(MAX_RETRIES):
        try:
            return fn(*args, **kwargs)
        except (requests.RequestException, requests.Timeout) as e:
            last_exc = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
    raise last_exc


class ScheduleManager:
    """课表管理 - 拉取/缓存课表，判断当前时段"""

    def __init__(self):
        self.schedule = {}
        self.today_classes = []
        self.loaded_date = None
        self.poll_intervals = {
            "pre_class": 60, "in_class": 120,
            "between": 1800, "weekend": 7200
        }

    def load_from_api(self, session):
        today = datetime.now()
        start = today.strftime("%Y-%m-%d")
        end = (today + timedelta(days=7)).strftime("%Y-%m-%d")
        resp = _retry_request(session.get, f"{GATEWAY}/faceteach/stu/getListByAll", params={
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

    def load_from_cache(self) -> bool:
        """从本地缓存加载课表（6小时内有效）"""
        if not os.path.exists(SCHEDULE_CACHE_FILE):
            return False
        try:
            with open(SCHEDULE_CACHE_FILE, "r", encoding="utf-8") as f:
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
        """保存课表到本地缓存"""
        try:
            with open(SCHEDULE_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "schedule": dict(self.schedule),
                }, f, ensure_ascii=False)
        except Exception:
            pass

    def get_today_courses(self):
        return self.schedule.get(datetime.now().strftime("%Y-%m-%d"), [])

    def has_class_today(self):
        return len(self.get_today_courses()) > 0

    def get_current_status(self):
        """返回当前时段: pre_class/in_class/between/weekend/no_class_today"""
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
        return "between"

    def get_poll_interval(self):
        status = self.get_current_status()
        interval = self.poll_intervals.get(status, self.poll_intervals["between"])
        return interval, status


class C30AutoSign:
    """C30平台API调用封装"""

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
            "Referer": "https://px.iclass30.com/onlineC30/",
            "Origin": "https://px.iclass30.com",
        })
        self.token = ""
        self.schedule_mgr = ScheduleManager()

    def login(self) -> tuple[bool, str]:
        """登录获取token"""
        resp = _retry_request(self.session.get, f"{GATEWAY}/user/portal/newLoginApp", params={
            "userName": self.username, "password": self.password,
            "clientId": "4", "sourceType": "4", "terminalType": "h5", "userId": "",
        }, timeout=10)
        data = resp.json()
        if data.get("code") == 200 and data.get("result"):
            result = data["result"]
            self.token = result["token"] if isinstance(result, dict) else str(result)
            self.session.headers["token"] = self.token
            return True, "登录成功"
        return False, f"登录失败: {json.dumps(data, ensure_ascii=False)}"

    def _is_token_expired(self, resp_data: dict) -> bool:
        """检测C30 token是否过期（响应码特征）"""
        code = resp_data.get("code")
        msg = str(resp_data.get("msg", "")).lower()
        if code == 401 or code == 403:
            return True
        if "token" in msg and ("过期" in msg or "失效" in msg or "expired" in msg or "invalid" in msg):
            return True
        return False

    def _request_with_relogin(self, method: str, url: str, **kwargs) -> requests.Response:
        """带自动重新登录的请求：若token过期则重新login后重试一次"""
        timeout = kwargs.pop("timeout", 10)
        if method == "get":
            resp = _retry_request(self.session.get, url, timeout=timeout, **kwargs)
        else:
            resp = _retry_request(self.session.post, url, timeout=timeout, **kwargs)
        try:
            data = resp.json()
            if self._is_token_expired(data):
                ok, _ = self.login()
                if ok:
                    if method == "get":
                        resp = _retry_request(self.session.get, url, timeout=timeout, **kwargs)
                    else:
                        resp = _retry_request(self.session.post, url, timeout=timeout, **kwargs)
        except Exception:
            pass
        return resp

    def get_today_classes(self) -> list:
        """获取今日课堂列表"""
        today = datetime.now().strftime("%Y-%m-%d")
        resp = self._request_with_relogin("get", f"{GATEWAY}/faceteach/stu/getListByAll", params={
            "startDate": today, "endDate": today, "page": 1, "pageSize": 50,
        })
        data = resp.json()
        if data.get("code") == 200:
            classes = data.get("result", [])
            if isinstance(classes, dict):
                classes = classes.get("list", classes.get("records", []))
            return classes
        return []

    def get_activity_list(self, face_teach_id: str, class_state: int = STATE_ONGOING) -> list:
        """获取活动列表"""
        resp = self._request_with_relogin("get", f"{GATEWAY}/faceteach/activity/stu/list", params={
            "classState": class_state, "faceTeachId": face_teach_id,
        })
        data = resp.json()
        if data.get("code") == 200:
            return data.get("result", [])
        return []

    def check_sign_status(self, sign_id: str) -> int:
        """查询签到状态: 1=已签, 0=未签, -1=查询失败"""
        resp = self._request_with_relogin("get", f"{GATEWAY}/faceteach/sign/study/getStudyData",
                                          params={"signId": sign_id})
        data = resp.json()
        if data.get("code") == 200:
            return data.get("result", {}).get("studySignState", -1)
        elif data.get("code") == -200:
            return 0
        return -1

    def get_sign_detail(self, sign_id: str) -> dict | None:
        """获取签到详情（含签到答案）"""
        resp = self._request_with_relogin("get", f"{GATEWAY}/faceteach/sign/get",
                                          params={"signId": sign_id})
        data = resp.json()
        if data.get("code") == 200:
            return data.get("result", {})
        return None

    def do_sign(self, sign_id: str, sign_pattern_data: str = "", center_point: str = "{}") -> tuple[bool, str]:
        """执行签到/签退 - 必须用form-urlencoded(data=)"""
        resp = self._request_with_relogin("post", f"{GATEWAY}/faceteach/sign/study/participate", data={
            "signPatternData": sign_pattern_data,
            "signId": sign_id,
            "centerPoint": center_point,
        })
        data = resp.json()
        if data.get("code") == -200:
            return True, "已签到(重复)"
        if data.get("code") == 200:
            return True, "签到成功"
        return False, data.get("msg", str(data))

    # ===== 讨论 =====
    def get_discuss_detail(self, discuss_id: str) -> dict | None:
        resp = self._request_with_relogin("get", f"{GATEWAY}/faceteach/discuss/view",
                                          params={"discussId": discuss_id})
        data = resp.json()
        if data.get("code") == 200:
            return data.get("result", {})
        return None

    def do_discuss_reply(self, discuss_id: str, content: str, parent_id: str = "0") -> tuple[bool, str]:
        """讨论回复 - 用json="""
        resp = self._request_with_relogin("post", f"{GATEWAY}/faceteach/discuss/reply/add", json={
            "discussId": discuss_id,
            "parentId": parent_id,
            "sourceType": 1,
            "url": "",
            "content": content,
            "file": "[]",
        })
        data = resp.json()
        if data.get("code") == 200:
            return True, "讨论回复成功"
        elif data.get("code") == -200:
            return True, "已回复(重复)"
        return False, data.get("msg", str(data))

    # ===== 头脑风暴 =====
    def get_brainstorm_detail(self, brainstorm_id: str) -> dict | None:
        resp = self._request_with_relogin("get", f"{GATEWAY}/faceteach/brainstorm/getBrainStorm",
                                          params={"brainstormId": brainstorm_id})
        data = resp.json()
        if data.get("code") == 200:
            return data.get("result", {})
        return None

    def do_brainstorm_submit(self, brainstorm_id: str, face_teach_id: str, answer: str) -> tuple[bool, str]:
        """头脑风暴提交 - 用json="""
        resp = self._request_with_relogin("post", f"{GATEWAY}/faceteach/brainstormstu/addBrainStormStu", json={
            "brainstormId": brainstorm_id,
            "answer": answer,
            "faceTeachId": face_teach_id,
            "file": "[]",
        })
        data = resp.json()
        if data.get("code") == 200:
            return True, "头脑风暴提交成功"
        elif data.get("code") == -200:
            return True, "已提交(重复)"
        return False, data.get("msg", str(data))

    # ===== 投票 =====
    def get_vote_detail(self, vote_id: str) -> dict | None:
        resp = self._request_with_relogin("get", f"{GATEWAY}/faceteach/vote/get",
                                          params={"voteId": vote_id})
        data = resp.json()
        if data.get("code") == 200:
            return data.get("result", {})
        return None

    def do_vote(self, vote_id: str, content: str) -> tuple[bool, str]:
        """投票 - 用data=(form-urlencoded)"""
        resp = self._request_with_relogin("post", f"{GATEWAY}/faceteach/vote/study/participate", data={
            "voteId": vote_id,
            "content": content,
        })
        data = resp.json()
        if data.get("code") == 200:
            return True, "投票成功"
        elif data.get("code") == -200:
            return True, "已投票(重复)"
        return False, data.get("msg", str(data))
