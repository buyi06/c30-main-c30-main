"""WebSocket日志推送"""

import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..core.log_buffer import LogBuffer

router = APIRouter(prefix="/ws")


@router.websocket("/logs")
async def ws_logs(websocket: WebSocket):
    await websocket.accept()
    log_buffer: LogBuffer = websocket.app.state.log_buffer

    # 发送历史日志
    recent = log_buffer.get_recent(100)
    for entry in recent:
        try:
            await websocket.send_json(entry)
        except Exception:
            break

    # 注册广播回调
    async_queue = asyncio.Queue()

    def broadcast_callback(entry_dict: dict):
        try:
            async_queue.put_nowait(entry_dict)
        except Exception:
            pass

    log_buffer.register_callback(broadcast_callback)

    try:
        # 双任务：发送日志 + 检测断线
        send_task = asyncio.create_task(_send_loop(websocket, async_queue))
        recv_task = asyncio.create_task(_recv_loop(websocket))
        done, pending = await asyncio.wait(
            [send_task, recv_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for t in pending:
            t.cancel()
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        log_buffer.unregister_callback(broadcast_callback)
        try:
            await websocket.close()
        except Exception:
            pass


async def _send_loop(websocket: WebSocket, queue: asyncio.Queue):
    """持续发送日志到WebSocket"""
    while True:
        entry = await queue.get()
        try:
            await websocket.send_json(entry)
        except Exception:
            break


async def _recv_loop(websocket: WebSocket):
    """检测客户端断线"""
    while True:
        try:
            await websocket.receive_text()
        except Exception:
            break