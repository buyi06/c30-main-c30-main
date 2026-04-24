"""全局状态管理 - 内存维护"""

import time
from datetime import datetime
from dataclasses import dataclass, field
from typing import Any

from .iclass30_api import (
    ACT_SIGN_IN, ACT_SIGN_OUT, ACT_DISCUSS, ACT_BRAINSTORM, ACT_VOTE,
    ACT_TYPE_MAP, STATE_ONGOING, STATE_ENDED
)


@dataclass
class AppState:
    """全局应用状态（内存中）"""
    # 服务状态
    service: dict = field(default_factory=lambda: {
        "status": "running",       # running / paused / error
        "start_time": time.time(),
        "last_poll": None,         # 上次轮询时间
        "next_poll": None,         # 下次轮询时间
        "current_period": "no_class_today",  # 当前时段
    })
    # 账号状态
    account: dict = field(default_factory=lambda: {
        "logged_in": False,
        "username": "",
        "last_login": None,
    })
    # 今日课程
    today_courses: list = field(default_factory=list)
    # 活动统计 {type: {done, pending, failed}}
    activities: dict = field(default_factory=lambda: {
        "sign_in": {"done": 0, "pending": 0, "failed": 0},
        "sign_out": {"done": 0, "pending": 0, "failed": 0},
        "discuss": {"done": 0, "pending": 0, "failed": 0},
        "brainstorm": {"done": 0, "pending": 0, "failed": 0},
        "vote": {"done": 0, "pending": 0, "failed": 0},
    })
    # 已处理的活动ID
    done_ids: set = field(default_factory=set)

    def get_status(self) -> dict:
        """获取完整状态快照"""
        uptime = int(time.time() - self.service["start_time"])
        return {
            "service": {
                **self.service,
                "uptime": uptime,
            },
            "account": self.account,
            "today_courses": self.today_courses,
            "activities": self.activities,
        }

    def update_login(self, logged_in: bool, username: str = ""):
        self.account["logged_in"] = logged_in
        self.account["username"] = username
        self.account["last_login"] = datetime.now().isoformat()

    def update_poll_time(self, next_interval: int = 0):
        self.service["last_poll"] = datetime.now().isoformat()
        if next_interval > 0:
            from datetime import timedelta
            next_time = datetime.now() + timedelta(seconds=next_interval)
            self.service["next_poll"] = next_time.isoformat()

    def update_period(self, period: str):
        self.service["current_period"] = period

    def update_courses(self, courses: list):
        self.today_courses = courses

    def reset_activity_stats(self):
        """重置活动统计（每次轮询时重新计算）"""
        for key in self.activities:
            self.activities[key] = {"done": 0, "pending": 0, "failed": 0}

    def count_activity(self, act_type: int, status: str):
        """统计活动: status=done/pending/failed"""
        type_key_map = {
            ACT_SIGN_IN: "sign_in",
            ACT_SIGN_OUT: "sign_out",
            ACT_DISCUSS: "discuss",
            ACT_BRAINSTORM: "brainstorm",
            ACT_VOTE: "vote",
        }
        key = type_key_map.get(act_type)
        if key and status in self.activities.get(key, {}):
            self.activities[key][status] += 1

    def set_paused(self, paused: bool):
        self.service["status"] = "paused" if paused else "running"
