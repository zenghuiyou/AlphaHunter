import pandas as pd
import baostock as bs
import json
from datetime import datetime, timedelta
from src.app.logger_config import log
import time

# 注意：在此次重构中，我们将tenacity的重试逻辑移至上层调用方 (run_scanner.py)
# 因此移除函数装饰器，让函数本身只负责单次的数据获取逻辑

def get_realtime_market_data() -> pd.DataFrame:
    """
    (V4.2 同步重构版)
    获取A股市场的近实时行情快照数据，并将结果写入JSON文件。
    这是一个同步阻塞函数，应该在一个独立的进程中运行。
    """
    log.info("正在登录BaoStock...")
    lg = bs.login()
    if lg.error_code != '0':
        log.error(f"登录BaoStock失败: {lg.error_msg}")
        raise IOError(f"BaoStock login failed: {lg.error_msg}")

    final_df = pd.DataFrame()
    try:
        # 1. 获取交易日
        log.info("正在获取最新交易日...")
        rs_dates = bs.query_trade_dates(start_date=(datetime.today() - timedelta(days=10)).strftime('%Y-%m-%d'))
        if rs_dates.error_code != '0':
            log.error(f"查询交易日历失败: {rs_dates.error_msg}")
            return pd.DataFrame()
        
        # 修正：直接使用返回的交易日历，不再按错误的列名筛选
        trade_dates_df = rs_dates.get_data()
        if trade_dates_df.empty:
            log.warning("无法获取到交易日历信息，跳过扫描。")
            return pd.DataFrame()
        
        trade_dates = trade_dates_df['calendar_date'].tolist()
        if len(trade_dates) < 2:
            log.warning("无法获取到足够的交易日信息（今天和昨天），跳过扫描。")
            return pd.DataFrame()
            
        today_str = trade_dates[-1]
        prev_trade_day_str = trade_dates[-2]
        log.info(f"判定当前交易日: {today_str}, 上一交易日: {prev_trade_day_str}")

        # 2. 获取所有A股列表
        rs_stocks = bs.query_all_stock(day=today_str)
        if rs_stocks.error_code != '0':
            log.error(f"查询所有A股列表失败: {rs_stocks.error_msg}")
            return pd.DataFrame()
        
        all_stocks = rs_stocks.get_data()
        
        # --- 最终修复：处理盘中返回完全为空的情况 ---
        if all_stocks.empty:
            log.warning("获取到的股票列表为空，可能是盘中时段BaoStock尚未生成完整列表。跳过本轮扫描。")
            return pd.DataFrame()

        # 移除调试代码
        # log.debug(f"BaoStock query_all_stock 返回的列名: {all_stocks.columns.tolist()}")
        
        a_stocks = all_stocks[all_stocks['code'].str.match(r'^(sh|sz)\.60|^(sh|sz)\.00|^(sh|sz)\.30')]
        all_tickers = a_stocks['code'].to_list()
        
        # --- !! 测试模式：仅获取前10只股票 !! ---
        all_tickers = all_tickers[:10]
        log.warning(f"--- !!! 测试模式已激活，仅处理 {len(all_tickers)} 支股票 !!! ---")

        # 3. 逐个获取上日收盘价
        prev_close_list = []
        log.info(f"开始逐个获取 {len(all_tickers)} 支股票的上日收盘价...")
        for t in all_tickers:
            rs_prev_close = bs.query_history_k_data_plus(
                t, "code,close", prev_trade_day_str, prev_trade_day_str, "d", "3"
            )
            if rs_prev_close.error_code == '0':
                prev_close_list.append(rs_prev_close.get_data())
            else:
                log.warning(f"未能获取到 {t} 的上日收盘价，跳过。")
        
        # 过滤掉失败的结果并合并
        valid_prev_close_dfs = [df for df in prev_close_list if df is not None and not df.empty]
        if not valid_prev_close_dfs:
            log.error("未能获取到任何股票的上一交易日收盘价。")
            return pd.DataFrame()
        prev_close_df = pd.concat(valid_prev_close_dfs).rename(columns={'close': 'prev_close'})
        prev_close_df['prev_close'] = pd.to_numeric(prev_close_df['prev_close'])

        # 4. 逐个获取当天的5分钟K线数据
        minute_data_list = []
        log.info(f"开始逐个获取当天的5分钟线行情...")
        for t in all_tickers:
            rs_minute_data = bs.query_history_k_data_plus(
                t, "code,time,close,volume,tradeStatus", today_str, today_str, "5", "3"
            )
            if rs_minute_data.error_code == '0':
                minute_data_list.append(rs_minute_data.get_data())
            else:
                log.warning(f"未能获取到 {t} 的5分钟线行情，跳过。")
        
        # 过滤掉失败的结果并合并
        valid_minute_dfs = [df for df in minute_data_list if df is not None and not df.empty]
        if not valid_minute_dfs:
            log.warning("未能获取到任何股票的5分钟线行情 (可能是休市期)。")
            return pd.DataFrame()
        minute_data = pd.concat(valid_minute_dfs)

        # 5. 数据清洗与处理
        minute_data.replace('', '0', inplace=True)
        for col in ['close', 'volume', 'tradeStatus']:
            minute_data[col] = pd.to_numeric(minute_data[col])
        
        # 6. 提取最新行情并与前收盘价合并
        latest_data = minute_data[minute_data['tradeStatus'] == 1].sort_values('time').drop_duplicates('code', keep='last')
        log.info(f"提取到 {len(latest_data)} 支正在交易股票的最新行情。")

        merged_df = pd.merge(latest_data, prev_close_df, on='code')
        if merged_df.empty:
            log.warning("最新行情与前收盘价合并后数据为空。")
            return pd.DataFrame()
            
        # 7. 计算实时涨跌幅
        merged_df['change_pct'] = ((merged_df['close'] / merged_df['prev_close']) - 1) * 100
        
        # 8. 格式化输出
        merged_df.rename(columns={'code': 'ticker', 'close': 'price'}, inplace=True)
        log.success("成功获取并处理完市场近实时数据。")
        final_df = merged_df[['ticker', 'price', 'volume', 'change_pct']]

    finally:
        bs.logout()
        log.info("已登出BaoStock。")
        return final_df

def run_data_pipeline():
    """
    完整的数据处理流水线：获取->扫描->增强->分析->检查持仓->写入文件
    """
    log.info("--- 开始执行完整数据流水线 ---")
    
    # 导入必要的模块
    from src.data_provider import get_realtime_market_data
    from src.scanner import scan_opportunities
    from src.data_enhancer import enhance_opportunity_with_akshare
    from src.ai_analyzer import get_analysis_from_glm4
    import src.portfolio_manager as portfolio
    import src.selling_strategy as strategy
    from src.app.models import PositionStatus

    # 1. 获取市场数据
    market_data = get_realtime_market_data()
    if market_data.empty:
        log.warning("获取市场数据为空，流水线终止。")
        # 即使没有数据，也要确保JSON文件存在，以便API服务器读取
        with open("latest_opportunities.json", "w", encoding="utf-8") as f:
            json.dump({"new_opportunities": [], "sell_alerts": []}, f, ensure_ascii=False, indent=4)
        return

    # 2. 扫描新机会
    opportunities_df = scan_opportunities(market_data)
    
    # 3. 增强 & 分析新机会
    analyzed_opportunities = []
    if not opportunities_df.empty:
        log.info(f"发现 {len(opportunities_df)} 个新机会，开始进行增强和分析...")
        for _, series in opportunities_df.iterrows():
            opportunity_dict = series.to_dict()
            enhanced_data = enhance_opportunity_with_akshare(opportunity_dict['ticker'])
            full_data = {**opportunity_dict, **enhanced_data}
            ai_report = get_analysis_from_glm4(full_data)
            full_data['ai_analysis'] = ai_report
            analyzed_opportunities.append(full_data)
    else:
        log.info("未发现符合条件的新机会。")

    # 4. (V4.2 功能补全) 检查现有持仓并应用卖出策略
    open_positions = portfolio.get_open_positions()
    sell_alerts = []
    if open_positions:
        log.info(f"开始检查 {len(open_positions)} 个现有持仓的卖出策略...")
        ticker_price_map = pd.Series(market_data.price.values, index=market_data.ticker).to_dict()
        
        for pos in open_positions:
            current_price = ticker_price_map.get(pos.ticker)
            if current_price is None:
                log.warning(f"无法获取持仓 {pos.ticker} 的当前价格，跳过此持仓的策略检查。")
                continue

            sell_signal = strategy.check_all_strategies(pos, current_price)
            if sell_signal["triggered"]:
                portfolio.update_position_status(pos.id, PositionStatus.CLOSED)
                alert = {
                    "type": "SELL_ALERT",
                    "ticker": pos.ticker,
                    "reason": sell_signal["reason"],
                    "buy_price": pos.buy_price,
                    "sell_price": current_price,
                    "profit_pct": (current_price - pos.buy_price) / pos.buy_price
                }
                sell_alerts.append(alert)
                log.critical(f"卖出信号触发！平仓: {pos.ticker}, 原因: {sell_signal['reason']}")
    else:
        log.info("当前无持仓，跳过卖出策略检查。")

    # 5. 整合所有信息并写入JSON文件
    output_data = {
        "new_opportunities": analyzed_opportunities,
        "sell_alerts": sell_alerts
    }
    
    with open("latest_opportunities.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4, default=str)
    
    log.success(f"--- 数据流水线执行完毕，结果已写入 latest_opportunities.json ---")

def get_historical_daily_data(tickers: list, start_date: str, end_date: str) -> dict:
    """
    (V4.5 新增)
    为离线战略分析模块获取指定股票池的完整历史日线数据。

    :param tickers: 股票代码列表，例如 ["sh.600036", "sz.000001"]
    :param start_date: 开始日期，格式 'YYYY-MM-DD'
    :param end_date: 结束日期，格式 'YYYY-MM-DD'
    :return: 一个字典，键为股票代码，值为包含该股票所有历史数据的DataFrame。
    """
    log.info(f"--- [V4.5] 开始为 {len(tickers)} 支股票获取从 {start_date} 到 {end_date} 的历史日线数据 ---")
    
    historical_data = {}
    
    lg = bs.login()
    if lg.error_code != '0':
        log.error(f"BaoStock登录失败: {lg.error_msg}")
        return historical_data
        
    try:
        for i, ticker in enumerate(tickers):
            log.info(f"正在获取 {ticker} ({i+1}/{len(tickers)})...")
            # a. 详细的日线数据
            rs = bs.query_history_k_data_plus(
                ticker,
                "date,code,open,high,low,close,preclose,volume,amount,turn,tradestatus,pctChg,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST",
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                adjustflag="2"  # 后复权
            )
            
            result_df = rs.get_data() # 只调用一次 get_data()，并将结果存起来

            if rs.error_code == '0' and not result_df.empty:
                df = result_df # 使用存储的结果

                # 数据类型转换，方便后续计算
                data_types = {
                    'open': float, 'high': float, 'low': float, 'close': float,
                    'preclose': float, 'volume': int, 'amount': float, 'turn': float,
                    'pctChg': float, 'peTTM': float, 'pbMRQ': float, 'psTTM': float,
                    'pcfNcfTTM': float
                }
                for col, dtype in data_types.items():
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                historical_data[ticker] = df
            else:
                log.warning(f"未能获取到 {ticker} 的历史数据。错误信息: {rs.error_msg}")
            
            # 防止请求过于频繁
            time.sleep(0.1)

    finally:
        bs.logout()
        log.info("已登出BaoStock。")

    log.success(f"--- [V4.5] 成功获取了 {len(historical_data)} 支股票的历史数据 ---")
    return historical_data

if __name__ == '__main__':
    run_data_pipeline()
