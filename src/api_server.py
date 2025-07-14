# -*- coding: utf-8 -*-
import asyncio
import json
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import Response

# 导入我们第一阶段的核心逻辑函数
from src.ai_analyzer import analyze_opportunity
from src.data_provider import get_market_data
from src.scanner import scan_opportunities


# --- 1. 创建一个WebSocket连接管理器 ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        # 在移除前，先检查客户端是否仍在活动连接列表中，防止重复移除导致错误
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"客户端 {websocket.client} 已成功从列表中移除。")

    async def broadcast(self, message: str):
        # 创建一个连接列表的副本进行迭代，以防在广播期间列表被修改
        for connection in self.active_connections[:]:
            try:
                await connection.send_text(message)
            except WebSocketDisconnect:
                # 如果客户端在广播时断开连接，就将其从列表中移除
                print(f"广播时发现客户端 {connection.client} 已断开，将其移除。")
                self.disconnect(connection)
            except Exception as e:
                print(f"向客户端 {connection.client} 广播时发生错误: {e}")
                self.disconnect(connection)

manager = ConnectionManager()


# --- 2. 创建一个后台扫描任务 ---
async def background_scanner(manager: ConnectionManager):
    """每10秒扫描一次机会并广播"""
    while True:
        print(">>> [后台任务] 开始新一轮扫描...")
        market_data = get_market_data()
        opportunities_df = scan_opportunities(market_data)
        
        if not opportunities_df.empty:
            print(f">>> [后台任务] 发现 {len(opportunities_df)} 个机会, 准备进行AI分析...")
            
            # 1. 将DataFrame转换为字典列表，方便处理
            opportunities_list = opportunities_df.to_dict(orient='records')
            
            # 2. 为每个机会添加AI分析
            for opp in opportunities_list:
                opp['ai_analysis'] = analyze_opportunity(opp)

            # 3. 将处理后的列表转换为JSON并广播
            opportunities_json = json.dumps(opportunities_list, ensure_ascii=False)
            
            await manager.broadcast(opportunities_json)
            print(f">>> [后台任务] 广播完成。")
        else:
            print(">>> [后台任务] 未发现新机会。")

        await asyncio.sleep(10)


# --- 3. 定义FastAPI应用的生命周期事件 ---
async def lifespan(app: FastAPI):
    # 在应用启动时，创建一个后台任务来运行扫描器
    print("应用启动...")
    asyncio.create_task(background_scanner(manager))
    yield
    # 在应用关闭时执行清理（如果需要）
    print("应用关闭。")


# --- 4. 更新FastAPI实例和WebSocket端点 ---
app = FastAPI(
    title="AlphaHunter API",
    description="为Alpha狩猎系统提供实时数据和分析的后端服务。",
    version="1.0.0",
    lifespan=lifespan  # 注册生命周期函数
)


@app.get("/")
def read_root():
    """
    根端点，用于检查API服务的健康状态。
    """
    content = {"status": "ok", "message": "欢迎使用 AlphaHunter API"}

    # --- 编码问题修复 ---
    # 直接返回字典或使用JSONResponse在某些环境下可能出现中文乱码。
    # 为了保证兼容性，我们手动将字典转为UTF-8编码的JSON字符串，
    # 并通过底层的Response对象强制指定HTTP头部的Content-Type，
    # 确保浏览器能以正确的UTF-8编码解析响应。
    json_str = json.dumps(content, ensure_ascii=False)
    return Response(content=json_str, media_type="application/json; charset=utf-8")


@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    """
    处理仪表盘的WebSocket连接。
    将新的连接交给ConnectionManager管理。
    """
    await manager.connect(websocket)
    print(f"WebSocket客户端 {websocket.client} 已连接。当前连接数: {len(manager.active_connections)}")
    try:
        # 保持连接开放，等待客户端断开
        while True:
            # 等待客户端消息（但我们目前不处理任何收到的消息）
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"WebSocket客户端 {websocket.client} 已断开。剩余连接数: {len(manager.active_connections)}")
    except Exception as e:
        manager.disconnect(websocket)
        print(f"WebSocket 出现错误: {e}, 连接已关闭。")
