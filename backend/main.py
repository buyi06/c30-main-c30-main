"""FastAPI入口 - C30管理面板后端"""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import load_config
from .core.state import AppState
from .core.log_buffer import LogBuffer
from .core.scheduler import SchedulerService
from .api.routes import router as api_router
from .api.ws import router as ws_router

# 前端dist路径
FRONTEND_DIST = os.environ.get(
    "C30_FRONTEND_DIST",
    str(Path(__file__).parent.parent / "frontend" / "dist")
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 加载配置
    config = load_config()
    app.state.config = config

    # 初始化状态
    app.state.app_state = AppState()

    # 初始化日志缓冲区
    log_buffer = LogBuffer(max_lines=config.get("log_max_lines", 500))
    app.state.log_buffer = log_buffer
    log_buffer.info("C30管理面板启动", "system")

    # 初始化调度器
    scheduler = SchedulerService(config, app.state.app_state, log_buffer)
    app.state.scheduler_service = scheduler
    scheduler.start()

    yield

    # 关闭调度器
    scheduler.stop()
    log_buffer.info("C30管理面板关闭", "system")


app = FastAPI(title="C30管理面板", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router)
app.include_router(ws_router)

# 挂载前端静态文件（生产模式）
dist_path = Path(FRONTEND_DIST)
if dist_path.exists() and dist_path.is_dir():
    # SPA fallback - 先尝试API路由，再尝试静态文件，最后fallback到index.html
    app.mount("/", StaticFiles(directory=str(dist_path), html=True), name="frontend")