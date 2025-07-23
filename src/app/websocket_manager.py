from fastapi import WebSocket
from typing import List

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"新客户端连接: {websocket.client.host}:{websocket.client.port}。当前共 {len(self.active_connections)} 个连接。")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"客户端断开连接。当前共 {len(self.active_connections)} 个连接。")

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message) 