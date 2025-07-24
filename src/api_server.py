# -*- coding: utf-8 -*-
import asyncio
import json
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from src.app.logger_config import log
from src.app.database import init_db

# --- 1. FastAPI应用和CORS配置 ---
app = FastAPI(title="AlphaHunter API - v4.2 Stable")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 为调试方便，暂时允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. WebSocket连接管理器 (不变) ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        log.info(f"新的WebSocket连接: {websocket.client.host}:{websocket.client.port}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        log.warning(f"WebSocket连接断开: {websocket.client.host}:{websocket.client.port}")

    async def broadcast(self, message: str):
        log.info(f"广播消息给 {len(self.active_connections)} 个客户端")
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# --- 3. (V4.2 新架构) 文件监视与广播任务 ---
# 用于存储上一次文件内容的全局变量
last_known_data = None

async def file_watcher_task():
    """
    后台任务，监视latest_opportunities.json文件的变化，
    并在内容更新时，将新数据广播给所有客户端。
    """
    global last_known_data
    while True:
        try:
            with open("latest_opportunities.json", "r", encoding="utf-8") as f:
                current_data = json.load(f)
            
            # 如果是第一次读取，或者文件内容发生了变化
            if current_data != last_known_data:
                log.info("检测到 aatest_opportunities.json 文件内容更新，正在广播...")
                broadcast_json = json.dumps(current_data, ensure_ascii=False, default=str)
                await manager.broadcast(broadcast_json)
                last_known_data = current_data
            
        except FileNotFoundError:
            # 在扫描器第一次运行前，文件可能不存在，这是正常情况
            log.warning("latest_opportunities.json 文件暂未找到，等待扫描器生成...")
        except json.JSONDecodeError:
            log.error("读取 latest_opportunities.json 文件失败，可能是JSON格式错误。")
        except Exception as e:
            log.error(f"文件监视任务发生未知错误: {e}", exc_info=True)
            
        # 每隔3秒检查一次文件
        await asyncio.sleep(3)

@app.on_event("startup")
async def startup_event():
    log.info("服务器启动...")
    init_db()
    log.info("文件监视后台任务已创建。")
    asyncio.create_task(file_watcher_task())

# --- 4. 根端点 (不变) ---
@app.get("/")
def read_root():
    log.info("接收到根路径'/'的GET请求。")
    return {"status": "ok", "message": "欢迎使用 AlphaHunter API"}

# --- 5. WebSocket端点 (不变) ---
@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    log.info("---!!! WebSocket连接请求已到达端点 !!!---")
    
    await manager.connect(websocket)
    try:
        while True:
            # 保持连接开放，等待客户端断开
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        
