from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def read_root():
    return """
    <html>
        <head>
            <title>AlphaHunter API</title>
        </head>
        <body>
            <h1>AlphaHunter API v3.0</h1>
            <p>服务正在运行。请使用WebSocket客户端连接到 <code>/ws/dashboard</code> 以接收实时数据。</p>
        </body>
    </html>
    """

@router.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket, request: Request):
    manager = request.app.state.manager
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"客户端 {websocket.client.host} 已断开。") 