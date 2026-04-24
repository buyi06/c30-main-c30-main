"""日志缓冲区 - 环形缓冲 + WebSocket广播"""

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class LogEntry:
    timestamp: str
    level: str    # info / success / error
    message: str
    category: str  # sign / discuss / brainstorm / vote / system / error

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "level": self.level,
            "message": self.message,
            "category": self.category,
        }


class LogBuffer:
    """环形日志缓冲区，支持WebSocket广播"""

    def __init__(self, max_lines: int = 500):
        self.max_lines = max_lines
        self.buffer: deque[LogEntry] = deque(maxlen=max_lines)
        self._callbacks: list[Callable] = []

    def add(self, level: str, message: str, category: str = "system"):
        """添加日志并通知广播回调"""
        from datetime import datetime
        entry = LogEntry(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            level=level,
            message=message,
            category=category,
        )
        self.buffer.append(entry)
        # 通知所有WebSocket广播回调
        for cb in self._callbacks:
            try:
                cb(entry.to_dict())
            except Exception:
                pass

    def info(self, message: str, category: str = "system"):
        self.add("info", message, category)

    def success(self, message: str, category: str = "system"):
        self.add("success", message, category)

    def error(self, message: str, category: str = "error"):
        self.add("error", message, category)

    def register_callback(self, cb: Callable):
        """注册广播回调（WebSocket端点使用）"""
        self._callbacks.append(cb)

    def unregister_callback(self, cb: Callable):
        """注销广播回调"""
        if cb in self._callbacks:
            self._callbacks.remove(cb)

    def get_recent(self, n: int = 100, category: str = None) -> list[dict]:
        """获取最近n条日志，可按分类筛选"""
        entries = list(self.buffer)
        if category and category != "all":
            entries = [e for e in entries if e.category == category or e.level == "error"]
        return [e.to_dict() for e in entries[-n:]]

    def get_all(self, category: str = None) -> list[dict]:
        """获取全部日志"""
        return self.get_recent(self.max_lines, category)

    def clear(self):
        self.buffer.clear()
