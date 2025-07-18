# -*- coding: utf-8 -*-
import asyncio
import json
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware

# 导入我们重构后的核心逻辑函数
from src.ai_analyzer import get_analysis_from_glm4
from src.data_provider import get_realtime_market_data
from src.scanner import scan_opportunities

# --- 1. FastAPI应用和CORS配置 ---
app = FastAPI(title="AlphaHunter API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 为调试方便，暂时允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. 极度简化的WebSocket连接管理器 ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# --- 3. 重构后的后台扫描任务 ---
async def background_scanner():
    """
    后台任务，定期从Tushare获取数据，扫描机会，调用AI进行分析，
    然后将结果通过WebSocket广播给所有连接的客户端。
    """
    while True:
        print(">>> [后台任务] 开始新一轮扫描...")
        # 1. 从真实数据源获取数据
        market_data = get_realtime_market_data()
        
        if market_data.empty:
            print(">>> [后台任务] 未获取到市场数据，跳过本轮扫描。")
            await asyncio.sleep(60) # 如果获取数据失败，等待更长时间再重试
            continue

        # 2. 扫描机会
        opportunities_df = scan_opportunities(market_data)
        
        if not opportunities_df.empty:
            print(f">>> [后台任务] 发现 {len(opportunities_df)} 个潜在机会，正在进行AI分析...")
            
            # 3. 对每个机会进行AI分析并准备广播数据
            analyzed_opportunities = []
            for index, opportunity_series in opportunities_df.iterrows():
                # 将Pandas Series转换为字典
                opportunity_dict = opportunity_series.to_dict()
                
                # 调用AI分析
                ai_report = get_analysis_from_glm4(opportunity_dict)
                
                # 将AI分析结果添加到字典中
                opportunity_dict['ai_analysis'] = ai_report
                analyzed_opportunities.append(opportunity_dict)
            
            # 4. 广播包含AI分析的完整数据
            if analyzed_opportunities:
                opportunities_json = json.dumps(analyzed_opportunities, ensure_ascii=False)
            await manager.broadcast(opportunities_json)
                print(f">>> [后台任务] 已广播 {len(analyzed_opportunities)} 条附带AI分析的机会。")

        else:
            print(">>> [后台任务] 本轮未发现符合条件的机会。")
            
        # 每隔一段时间运行，例如60秒。真实场景中可能需要更长间隔。
        await asyncio.sleep(60)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_scanner())

# --- 4. 根端点 (保持不变) ---
@app.get("/")
def read_root():
    return {"status": "ok", "message": "欢迎使用 AlphaHunter API"}

# --- 5. 修正和简化的WebSocket端点 ---
@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    # 这是我们用来判断路由是否被匹配到的关键证据！
    print("---!!! WebSocket连接请求已到达端点 !!!---")
    
    await manager.connect(websocket)
    try:
        while True:
            # 保持连接开放，等待客户端断开
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("---!!! 一个客户端已断开连接 !!!---")
