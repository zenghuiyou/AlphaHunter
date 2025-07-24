# -*- coding: utf-8 -*-
import argparse
import json
from datetime import datetime, timedelta
from src.app.logger_config import log
from src.data_provider import get_historical_daily_data
from src.scanner import scan_strategic_breakouts
from src.ai_analyzer import get_strategic_analysis_from_glm4

def run_strategic_analysis(tickers: list):
    """
    运行离线战略分析的核心函数。
    """
    log.info(f"--- [V4.5 离线战略分析器] 开始为 {len(tickers)} 支股票执行分析 ---")
    
    # 1. 获取大量的历史日线数据
    end_date = datetime.today()
    start_date = end_date - timedelta(days=730)
    historical_data = get_historical_daily_data(
        tickers=tickers,
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d')
    )
    
    if not historical_data:
        log.error("未能获取到任何历史数据，分析中止。")
        return

    # 2. 使用战略扫描器发现潜在机会
    breakout_opportunities = scan_strategic_breakouts(historical_data)
    
    if not breakout_opportunities:
        log.info("在指定的股票池中，未发现符合“箱体突破”条件的战略机会。")
        # 即使没有机会，也生成一个空的JSON文件
        output_data = {"strategic_opportunities": []}
        with open("strategic_recommendations.json", "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=4)
        log.info("已生成空的 strategic_recommendations.json 文件。")
        return

    # 3. 对每个机会调用AI进行深度分析
    analyzed_reports = []
    for opp in breakout_opportunities:
        report = get_strategic_analysis_from_glm4(opp)
        analyzed_reports.append({
            "ticker": opp['ticker'],
            "opportunity_details": {k: v for k, v in opp.items() if k != 'full_historical_data'},
            "ai_strategic_report": report
        })

    # 4. 将最终结果写入JSON文件
    final_output = {"strategic_opportunities": analyzed_reports}
    with open("strategic_recommendations.json", "w", encoding="utf-8") as f:
        json.dump(final_output, f, ensure_ascii=False, indent=4, default=str)
    
    log.success(f"--- [V4.5] 分析完成！已将 {len(analyzed_reports)} 份战略报告写入 strategic_recommendations.json ---")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AlphaHunter V4.5 - Offline Strategic Analyzer")
    parser.add_argument(
        '--tickers',
        type=str,
        default="sz.002475,sh.600519", # 默认分析立讯精密和贵州茅台
        help='要分析的股票代码列表，以逗号分隔。例如: "sh.600036,sz.000001"'
    )
    args = parser.parse_args()
    
    ticker_list = [t.strip() for t in args.tickers.split(',')]
    run_strategic_analysis(tickers=ticker_list) 