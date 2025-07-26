# -*- coding: utf-8 -*-
import argparse
import json
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.app.logger_config import log
from src.app.database import SQLALCHEMY_DATABASE_URL
from src.app.models import StockDailyData
from src.scanner import load_strategies, scan_opportunities
from src.data_enhancer import enhance_opportunity_with_akshare
from src.ai_analyzer import get_strategic_analysis_from_glm4
import os

# --- 数据库交互层 ---
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_all_tickers_from_db(session):
    """从数据库获取所有不重复的股票代码列表"""
    log.info("正在从数据库获取所有股票代码...")
    tickers = session.query(StockDailyData.code).distinct().all()
    ticker_list = [item[0] for item in tickers]
    log.info(f"获取到 {len(ticker_list)} 只股票代码。")
    return ticker_list

def get_data_from_db(session, tickers, start_date, end_date):
    """从数据库中为指定的股票列表获取指定日期范围的数据"""
    log.info(f"正在从数据库查询 {len(tickers)} 只股票从 {start_date} 到 {end_date} 的数据...")
    query = session.query(StockDailyData).filter(
        StockDailyData.code.in_(tickers),
        StockDailyData.date >= start_date,
        StockDailyData.date <= end_date
    )
    df = pd.read_sql(query.statement, session.bind)
    
    # 将数据按股票代码分组，转换为字典
    if not df.empty:
        log.success(f"成功从数据库查询到 {len(df)} 条数据。")
        return {ticker: group_df for ticker, group_df in df.groupby('code')}
    else:
        log.warning("在指定日期范围内未查询到任何数据。")
        return {}

def run_strategic_analysis(args):
    """
    [V4.5] 离线战略分析器 (数据库驱动版)
    1. 从数据库获取全市场股票列表
    2. 分块从数据库获取历史数据并进行扫描
    3. (可选) 对扫描到的机会进行数据增强和AI分析
    4. 将结果写入JSON文件
    """
    log.info("--- [V4.5] 开始执行“离线战略分析” (数据库驱动) ---")
    
    session = SessionLocal()
    all_opportunities = []
    
    try:
        strategies = load_strategies()
        if not strategies:
            log.error("没有加载到任何策略，分析中止。")
            return

        all_tickers = get_all_tickers_from_db(session)
        if not all_tickers:
            log.error("数据库中没有任何股票，分析中止。")
            return

        log.info(f"准备分析全市场 {len(all_tickers)} 只股票...")
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=365)
        
        # 定义批处理大小
        BATCH_SIZE = 100
        for i in range(0, len(all_tickers), BATCH_SIZE):
            batch_tickers = all_tickers[i:i + BATCH_SIZE]
            log.info(f"--- 正在处理批次 {i//BATCH_SIZE + 1}，包含 {len(batch_tickers)} 只股票 ---")
            
            historical_data = get_data_from_db(
                session=session,
                tickers=batch_tickers,
                start_date=start_date,
                end_date=end_date
            )
            
            if not historical_data:
                log.warning(f"批次 {i//BATCH_SIZE + 1}未能从数据库获取任何历史数据，跳过。")
                continue

            batch_opportunities = scan_opportunities(strategies, historical_data)
            if batch_opportunities:
                log.info(f"批次 {i//BATCH_SIZE + 1} 发现 {len(batch_opportunities)} 个机会。")
                all_opportunities.extend(batch_opportunities)

        if not all_opportunities:
            log.warning("所有策略扫描完毕，未发现任何机会。")
            with open("strategic_recommendations.json", "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=4)
            return

        log.success(f"--- 所有策略扫描完毕，共发现 {len(all_opportunities)} 个潜在机会 ---")

        # 如果是仅扫描模式，则直接保存机会列表并退出
        if args.scan_only:
            log.info("检测到 --scan-only 模式，正在保存扫描结果...")
            with open("strategic_recommendations.json", "w", encoding="utf-8") as f:
                json.dump(all_opportunities, f, ensure_ascii=False, indent=4, default=str)
            log.success(f"--- 扫描完成！已将 {len(all_opportunities)} 个潜在机会写入 strategic_recommendations.json (未进行AI分析) ---")
            return

        final_reports = []
        for opportunity in all_opportunities:
            log.info(f"--- 开始处理由【{opportunity['strategy_name']}】发现的机会: {opportunity['ticker']} ---")
            
            enhanced_data = enhance_opportunity_with_akshare(opportunity['ticker'])
            full_opportunity_data = {**opportunity, **enhanced_data}

            ai_report = get_strategic_analysis_from_glm4(full_opportunity_data)
            full_opportunity_data['ai_analysis'] = ai_report
            
            final_reports.append(full_opportunity_data)

        with open("strategic_recommendations.json", "w", encoding="utf-8") as f:
            json.dump(final_reports, f, ensure_ascii=False, indent=4, default=str)
        
        log.success(f"--- 分析全部完成！已将 {len(final_reports)} 份战略报告写入 strategic_recommendations.json ---")
    
    finally:
        session.close()
        log.info("数据库会话已关闭。")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AlphaHunter V4.5 - Offline Strategic Analyzer")
    parser.add_argument(
        "--tickers",
        type=str,
        default=None,
        help="要分析的股票代码列表，以逗号分隔 (可选, 若提供则只分析指定股票)"
    )
    parser.add_argument(
        "--zhipu_api_key",
        type=str,
        default=None,
        help="智谱AI的API Key"
    )
    parser.add_argument(
        "--scan-only",
        action="store_true",
        help="仅执行策略扫描，不调用AI进行分析"
    )
    args = parser.parse_args()

    # 仅在非 scan-only 模式下才检查API Key
    if not args.scan_only:
        if args.zhipu_api_key:
            os.environ['ZHIPUAI_API_KEY'] = args.zhipu_api_key
        elif not os.getenv('ZHIPUAI_API_KEY'):
            log.error("错误：ZHIPUAI_API_KEY 未设置。请通过环境变量或--zhipu_api_key参数提供。")
            exit(1)

    run_strategic_analysis(args) 