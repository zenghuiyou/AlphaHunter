from src.data_provider import get_realtime_market_data
from src.scanner import scan_opportunities
from src.ai_analyzer import analyze_opportunity
from src.app.logger_config import log


def main():
    """
    Alpha狩猎系统的主执行函数。
    
    该函数按顺序执行完整的处理流程：
    1. 获取市场数据。
    2. 扫描潜在机会。
    3. 对发现的每个机会进行AI分析。
    4. 打印分析报告到控制台。
    """
    log.info(">>> [Alpha狩猎系统] 启动运行...")
    
    # 1. 获取数据
    log.info("[1/3] 正在获取市场数据...")
    market_data = get_realtime_market_data()
    log.success("      市场数据获取完毕。")
    
    # 2. 扫描机会
    log.info("[2/3] 正在扫描潜在机会...")
    opportunities = scan_opportunities(market_data)
    
    if opportunities.empty:
        log.warning("      扫描完成，未发现符合条件的机会。系统运行结束。")
        return
        
    log.success(f"      扫描完成！发现 {len(opportunities)} 个机会。")
    
    # 3. 分析机会并打印报告
    log.info("[3/3] 正在对机会进行AI分析...")
    
    # iterrows() 用于遍历DataFrame的每一行
    for index, opportunity in opportunities.iterrows():
        report = analyze_opportunity(opportunity)
        # 使用loguru info来打印报告，也可以根据报告内容分级
        log.info(f"分析报告:\n{report}")
        
    log.success("\n>>> [Alpha狩猎系统] 所有任务完成。")


if __name__ == '__main__':
    main()