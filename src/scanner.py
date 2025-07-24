import pandas as pd
from src.app.logger_config import log
from src.data_provider import get_realtime_market_data # 修正：导入正确的函数名
from src.config import settings  # 导入配置


def scan_opportunities(market_data: pd.DataFrame, threshold=3.0) -> pd.DataFrame:
    """
    扫描市场数据以寻找交易机会。

    基于预设的规则对输入的市场数据DataFrame进行分析。
    当前规则：寻找 'change_pct' 大于 2.0 的股票。

    Args:
        market_data: 包含市场数据的Pandas DataFrame。

    Returns:
        一个新的Pandas DataFrame，仅包含符合条件的交易机会。
        如果没有找到机会，则返回一个空的DataFrame。
    """
    # 使用配置中的阈值，而不是硬编码的值
    threshold = settings.SCANNER_CHANGE_PCT_THRESHOLD
    opportunities = market_data[market_data['change_pct'] > threshold]
    return opportunities


def scan_strategic_breakouts(historical_data: dict, consolidation_period=60, breakout_threshold=1.03) -> list:
    """
    (V4.5 新增)
    扫描识别经典的“箱体突破”战略形态。

    逻辑:
    1. 定义一个“盘整期”（例如过去60个交易日）。
    2. 在此期间，计算出价格的“箱体”上轨（最高价）和下轨（最低价）。
    3. 检查箱体的“振幅”是否在一个合理的范围（太宽不是盘整，太窄可能是死股）。
    4. 检查最近一个交易日是否满足“突破”条件：
       a. 收盘价 > 箱体上轨 * (1 + 突破阈值%)
       b. 当天的成交量 > 盘整期平均成交量的 1.5 倍以上 (放量突破)
    
    :param historical_data: 包含多支股票历史数据的字典。
    :param consolidation_period: 盘整期窗口大小（单位：交易日）。
    :param breakout_threshold: 向上突破箱体上轨的最小百分比。
    :return: 一个列表，包含所有识别出的突破机会的详细信息。
    """
    log.info(f"--- [V4.5] 开始扫描 {len(historical_data)} 支股票的“箱体突破”战略形态 ---")
    breakout_opportunities = []

    for ticker, df in historical_data.items():
        if len(df) < consolidation_period + 1:
            continue  # 数据不足，无法判断

        # 定义盘整期和突破日
        recent_data = df.tail(consolidation_period + 1)
        consolidation_df = recent_data.head(consolidation_period)
        breakout_day = recent_data.tail(1).iloc[0]

        # 计算箱体指标
        box_high = consolidation_df['high'].max()
        box_low = consolidation_df['low'].min()
        box_amplitude = (box_high - box_low) / box_low

        # 过滤掉振幅过大或过小的情况
        if not (0.1 < box_amplitude < 0.5):
            continue

        # 计算成交量指标
        consolidation_avg_volume = consolidation_df['volume'].mean()
        
        # 判断突破条件
        is_price_breakout = breakout_day['close'] > box_high * breakout_threshold
        is_volume_breakout = breakout_day['volume'] > consolidation_avg_volume * 1.5

        if is_price_breakout and is_volume_breakout:
            opportunity = {
                "ticker": ticker,
                "breakout_date": breakout_day['date'],
                "breakout_price": breakout_day['close'],
                "box_high": box_high,
                "box_low": box_low,
                "consolidation_period_days": consolidation_period,
                "consolidation_avg_volume": consolidation_avg_volume,
                "breakout_volume": breakout_day['volume'],
                "full_historical_data": df # 将全部历史数据传入，供AI分析上下文
            }
            breakout_opportunities.append(opportunity)
            log.success(f"发现战略机会！股票 {ticker} 在 {breakout_day['date']} 成功突破箱体！")

    log.info(f"--- [V4.5] 箱体突破扫描完成，共发现 {len(breakout_opportunities)} 个机会 ---")
    return breakout_opportunities


# --- 本地测试代码 ---
if __name__ == '__main__':
    print("--- 启动机会扫描引擎 ---")
    # 1. 获取原始市场数据
    current_market_data = get_realtime_market_data() # 修正：调用正确的函数名
    print("\n[1] 原始市场数据:")
    print(current_market_data.head()) # 打印部分数据即可

    # 2. 扫描机会
    found_opportunities = scan_opportunities(current_market_data)
    print(f"\n[2] 扫描发现的机会 (change_pct > {settings.SCANNER_CHANGE_PCT_THRESHOLD}%):")

    if not found_opportunities.empty:
        print(found_opportunities)
    else:
        print("未发现符合条件的机会。")
