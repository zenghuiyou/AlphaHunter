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
    log.warning("--- !!! 注意：当前处于AI分析模块的模拟测试模式 !!! ---")

    # a. 先获取一份真实的历史数据作为AI分析的上下文
    # 我们只使用列表中的第一支股票作为模拟的蓝本
    first_ticker = tickers[0] if tickers else "sz.002475"
    log.info(f"正在获取'{first_ticker}'的历史数据作为模拟机会的上下文...")

    historical_data = get_historical_daily_data(
        tickers=[first_ticker],
        start_date=(datetime.today() - timedelta(days=730)).strftime('%Y-%m-%d'),
        end_date=datetime.today().strftime('%Y-%m-%d')
    )

    if not historical_data or first_ticker not in historical_data:
        log.error("无法获取用于模拟的上下文历史数据，测试中止。")
        return

    # b. 基于真实数据，手工构造一个“完美”的虚拟机会
    last_day = historical_data[first_ticker].iloc[-1]
    
    mock_opportunity = {
        "ticker": f"{first_ticker} (模拟演示)",
        "breakout_date": last_day['date'],
        "breakout_price": last_day['close'] * 1.05,
        "box_high": last_day['close'],
        "box_low": last_day['close'] * 0.8,
        "consolidation_period_days": 60,
        "consolidation_avg_volume": last_day['volume'] / 2,
        "breakout_volume": last_day['volume'] * 2,
        "full_historical_data": historical_data[first_ticker]
    }
    breakout_opportunities = [mock_opportunity]
    log.success("已成功构建一个用于测试的虚拟“箱体突破”机会。")

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
        default="sz.002475", # 默认只分析一支股票作为演示蓝本
        help='要分析的股票代码列表，以逗号分隔。例如: "sh.600036,sz.000001"'
    )
    args = parser.parse_args()
    
    ticker_list = [t.strip() for t in args.tickers.split(',')]
    run_strategic_analysis(tickers=ticker_list) 