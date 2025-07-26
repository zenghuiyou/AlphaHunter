# -*- coding: utf-8 -*-
import asyncio
import json
import os
from pathlib import Path
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from loguru import logger as log

from src.app.database import init_db

# V5.0 最终修复版
# 1. 增加了 last_known_timestamps 用于可靠地检测文件更新。
# 2. 修改了 ConnectionManager，使其在客户端连接时能主动推送一次最新数据。

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        log.info(f"新的WebSocket连接: {websocket.client.host}:{websocket.client.port}")
        # [核心修复A] 新客户端连接时，立即发送一次当前最新的战略和实时机会
        await self.send_latest_data(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        log.warning(f"WebSocket连接断开: {websocket.client.host}:{websocket.client.port}")

    async def broadcast(self, message: str):
        log.info(f"广播消息给 {len(self.active_connections)} 个客户端")
        for connection in self.active_connections:
            await connection.send_text(message)

    async def send_latest_data(self, websocket: WebSocket):
        """立即向单个客户端发送最新的数据"""
        log.info(f"正在向新客户端 {websocket.client.host}:{websocket.client.port} 推送最新数据...")
        # 推送战略机遇
        try:
            with open("strategic_recommendations.json", "r", encoding="utf-8") as f:
                strategic_data = json.load(f)
            await websocket.send_text(json.dumps({"type": "STRATEGIC_UPDATE", "data": strategic_data}))
            log.success(f"已成功向新客户端推送战略报告。")
        except (FileNotFoundError, json.JSONDecodeError):
            log.warning("strategic_recommendations.json 不存在或为空，跳过推送。")

        # 推送实时机会 (如果存在)
        try:
            with open("latest_opportunities.json", "r", encoding="utf-8") as f:
                realtime_data = json.load(f)
            await websocket.send_text(json.dumps({"type": "REALTIME_UPDATE", "data": realtime_data}))
            log.success(f"已成功向新客户端推送实时机会。")
        except (FileNotFoundError, json.JSONDecodeError):
            log.warning("latest_opportunities.json 不存在或为空，跳过推送。")


manager = ConnectionManager()
app = FastAPI()

# 使用 last_known_timestamps 替代 last_known_contents，更可靠
last_known_timestamps = {
    "latest_opportunities.json": 0.0,
    "strategic_recommendations.json": 0.0,
}

async def file_watcher_task():
    """监视文件更新并广播给所有客户端"""
    log.info("文件监视任务启动...")
    files_to_watch = {
        "latest_opportunities.json": "REALTIME_UPDATE",
        "strategic_recommendations.json": "STRATEGIC_UPDATE",
    }

    while True:
        for file_path_str, event_type in files_to_watch.items():
            file_path = Path(file_path_str)
            if not file_path.exists():
                continue

            try:
                current_timestamp = file_path.stat().st_mtime
                # [核心修复B] 使用文件修改时间戳进行比较
                if current_timestamp > last_known_timestamps[file_path_str]:
                    log.info(f"检测到 {file_path_str} 文件内容更新 (时间戳: {current_timestamp})，正在广播...")
                    with file_path.open("r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    broadcast_payload = {"type": event_type, "data": data}
                    await manager.broadcast(json.dumps(broadcast_payload, ensure_ascii=False, default=str))
                    last_known_timestamps[file_path_str] = current_timestamp

            except json.JSONDecodeError:
                log.error(f"读取 {file_path_str} 文件失败，可能是JSON格式错误或文件正在写入中。")
            except Exception as e:
                log.error(f"监视 {file_path_str} 的任务发生未知错误: {e}", exc_info=True)

        await asyncio.sleep(2) # 缩短轮询间隔，提高响应速度


@app.on_event("startup")
async def startup_event():
    log.info("服务器启动...")
    init_db()
    # 启动文件监视后台任务
    asyncio.create_task(file_watcher_task())


@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # 保持连接开放以接收（尽管我们目前不处理客户端消息）
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# 挂载静态文件目录，指向 frontend/dist
# 注意：这应该在生产环境中指向构建好的文件
# 在开发环境中，我们通常通过 npm run dev 的服务来访问前端
static_path = Path(__file__).parent.parent.parent / "frontend" / "dist"
if static_path.exists():
    app.mount("/", StaticFiles(directory=static_path, html=True), name="static")
    log.info(f"已成功挂载静态文件目录: {static_path}")
else:
    log.warning(f"未找到生产环境静态文件目录: {static_path}，请运行 `npm run build`。")
        
