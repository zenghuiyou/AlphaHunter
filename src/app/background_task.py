import asyncio
import json
from src.data_provider import get_market_data
from src.scanner import scan_opportunities
from src.ai_analyzer import analyze_opportunity
from src.app.websocket_manager import ConnectionManager

async def core_task(manager: ConnectionManager):
    """
    系统核心任务，定期执行数据获取、扫描和分析，并通过WebSocket广播。
    """
    print(">>> [后台核心任务] 启动运行...")
    while True:
        try:
            # 1. 获取数据
            print("[后台任务] 正在获取市场数据...")
            market_data_df = get_market_data()

            # 2. 扫描机会
            print("[后台任务] 正在扫描潜在机会...")
            opportunities_df = scan_opportunities(market_data_df)

            if opportunities_df.empty:
                print("[后台任务] 扫描完成，未发现符合条件的机会。")
                await manager.broadcast(json.dumps({"status": "scanning", "data": [], "message": "未发现机会"}))
            else:
                print(f"[后台任务] 扫描完成！发现 {len(opportunities_df)} 个机会。")
                
                # 3. 分析机会
                reports = []
                for _, opportunity in opportunities_df.iterrows():
                    analysis_result = analyze_opportunity(opportunity) 
                    reports.append(analysis_result)

                # 4. 广播结果
                print("[后台任务] 正在广播分析结果...")
                await manager.broadcast(json.dumps({"status": "data", "data": reports}))

        except Exception as e:
            print(f"!!! [后台核心任务] 发生严重错误: {e}")
            await manager.broadcast(json.dumps({"status": "error", "message": f"后台服务发生错误: {str(e)}"}))
        
        await asyncio.sleep(15) 