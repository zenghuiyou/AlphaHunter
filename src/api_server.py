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

# --- 3. (V4.5 升级) 通用文件监视与广播任务 ---
# 用于存储不同文件上一次内容的全局字典
last_known_contents = {}

async def watch_and_broadcast(file_path: str, event_type: str):
    """
    通用后台任务，监视指定JSON文件的变化，并在内容更新时，
    将新数据以特定的事件类型广播给所有客户端。
    """
    global last_known_contents
    last_known_contents[file_path] = None # 初始化

    while True:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                current_data = json.load(f)
            
            if current_data != last_known_contents.get(file_path):
                log.info(f"检测到 {file_path} 文件内容更新，正在以 '{event_type}' 类型广播...")
                
                # 包装最终的广播数据
                broadcast_payload = {
                    "type": event_type,
                    "data": current_data
                }
                
                broadcast_json = json.dumps(broadcast_payload, ensure_ascii=False, default=str)
                await manager.broadcast(broadcast_json)
                last_known_contents[file_path] = current_data
            
        except FileNotFoundError:
            log.warning(f"{file_path} 文件暂未找到，等待扫描器生成...")
        except json.JSONDecodeError:
            log.error(f"读取 {file_path} 文件失败，可能是JSON格式错误。")
        except Exception as e:
            log.error(f"监视 {file_path} 的任务发生未知错误: {e}", exc_info=True)
            
        await asyncio.sleep(5) # 统一轮询间隔为5秒

@app.on_event("startup")
async def startup_event():
    log.info("服务器启动...")
    init_db()
    
    # 创建两个并行的后台任务，分别监视不同的文件
    log.info("创建实时机会监视任务 (REALTIME_UPDATE)...")
    asyncio.create_task(watch_and_broadcast(
        file_path="latest_opportunities.json",
        event_type="REALTIME_UPDATE"
    ))
    
    log.info("创建战略报告监视任务 (STRATEGIC_UPDATE)...")
    asyncio.create_task(watch_and_broadcast(
        file_path="strategic_recommendations.json",
        event_type="STRATEGIC_UPDATE"
    ))

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
        
