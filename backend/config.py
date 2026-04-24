"""配置管理 - config.json读写 + JWT"""

import hashlib
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt

# 配置文件路径（优先环境变量，默认当前目录）
CONFIG_PATH = os.environ.get("C30_CONFIG_PATH", str(Path(__file__).parent.parent.parent / "config.json"))

DEFAULT_CONFIG = {
    "admin_password": "admin123",
    "c30_username": "",
    "c30_password": "",
    "auto_discuss_content": "老师讲得很好，受益匪浅",
    "auto_brainstorm_content": "我认为应该从多个角度思考这个问题，结合实践进行深入分析",
    "poll_intervals": {
        "pre_class": 60,
        "in_class": 120,
        "between": 1800,
        "weekend": 7200
    },
    "log_max_lines": 500,
    "jwt_secret": ""
}


def load_config() -> dict:
    """加载配置文件，不存在则创建默认配置"""
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
            config.update(saved)
        except (json.JSONDecodeError, IOError):
            pass
    # 确保 jwt_secret 存在
    if not config.get("jwt_secret"):
        config["jwt_secret"] = secrets.token_hex(32)
        save_config(config)
    return config


def save_config(config: dict):
    """保存配置到文件"""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def _hash_password(password: str) -> str:
    """SHA256哈希密码"""
    return hashlib.sha256(password.encode()).hexdigest()


def _verify_password(password: str, stored: str) -> bool:
    """验证密码（兼容明文和哈希）"""
    if len(stored) < 64:
        return password == stored
    return _hash_password(password) == stored


def create_jwt(config: dict, password: str) -> str | None:
    """验证管理密码并生成JWT，失败返回None"""
    stored = config.get("admin_password", "admin123")
    if not _verify_password(password, stored):
        return None
    payload = {
        "sub": "admin",
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, config["jwt_secret"], algorithm="HS256")


def verify_jwt(config: dict, token: str) -> bool:
    """验证JWT"""
    try:
        jwt.decode(token, config["jwt_secret"], algorithms=["HS256"])
        return True
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return False
