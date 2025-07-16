import asyncio
from fastapi import FastAPI
from typing import List

from src.app.websocket_manager import ConnectionManager
from src.app.background_task import core_task

def create_app() -> FastAPI:
    """
    应用工厂函数，负责创建和配置FastAPI实例。
    """
    
    app = FastAPI(
        title="AlphaHunter API",
        description="实时A股机会发现与AI分析引擎",
        version="3.0.0"
    )
    
    # 挂载WebSocket管理器
    app.state.manager = ConnectionManager()

    @app.on_event("startup")
    async def startup_event():
        # 将管理器实例传递给后台任务
        task = core_task(app.state.manager)
        asyncio.create_task(task)

    # 在这里可以包含路由的注册
    from . import routes
    app.include_router(routes.router)

    return app 