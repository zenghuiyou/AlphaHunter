from pathlib import Path
import importlib
import pkgutil
import pandas as pd
from typing import List, Dict, Any
from .strategies.base_strategy import BaseStrategy
from src.app.logger_config import log
from src.data_provider import get_realtime_market_data # 修正：导入正确的函数名
from src.config import settings  # 导入配置


def load_strategies(strategies_path='src/strategies') -> List[BaseStrategy]:
    """
    动态加载指定路径下的所有策略模块。
    """
    strategies = []
    path = Path(strategies_path)
    if not path.is_dir():
        log.error(f"策略目录不存在: {strategies_path}")
        return []
    
    log.info(f"--- 开始从 '{strategies_path}' 动态加载策略 ---")
    
    # 确保__init__.py存在，使其成为一个包
    if not (path / "__init__.py").exists():
        log.warning(f"策略目录 {strategies_path}缺少__init__.py文件，将自动创建。")
        (path / "__init__.py").touch()

    for _, name, _ in pkgutil.iter_modules([str(path)]):
        if name == 'base_strategy':
            continue  # 不加载基类
        try:
            module_name = f'src.strategies.{name}'
            module = importlib.import_module(module_name)
            for item in dir(module):
                obj = getattr(module, item)
                # 确保是BaseStrategy的子类，但不是BaseStrategy本身
                if isinstance(obj, type) and issubclass(obj, BaseStrategy) and obj is not BaseStrategy:
                    strategy_instance = obj()
                    strategies.append(strategy_instance)
                    log.success(f"成功加载策略: {strategy_instance.name}")
        except Exception as e:
            log.error(f"加载策略模块 '{name}' 失败: {e}", exc_info=True)
            
    log.info(f"--- 共加载了 {len(strategies)} 个策略 ---")
    return strategies

def scan_opportunities(strategies: List[BaseStrategy], historical_data: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
    """
    使用所有已加载的策略，对提供的历史数据进行扫描。
    """
    all_opportunities = []
    log.info(f"--- 开始使用 {len(strategies)} 个策略进行全面扫描 ---")

    for strategy in strategies:
        try:
            # 每个策略独立扫描，并将结果合并
            opportunities = strategy.scan(historical_data)
            if opportunities:
                all_opportunities.extend(opportunities)
        except Exception as e:
            log.error(f"策略 [{strategy.name}] 在扫描过程中发生错误: {e}", exc_info=True)
            
    return all_opportunities


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
    # 首先加载策略
    strategies = load_strategies()
    # 然后使用策略扫描市场数据
    found_opportunities = scan_opportunities(strategies, {"test_ticker": current_market_data})
    print(f"\n[2] 扫描发现的机会 (change_pct > {settings.SCANNER_CHANGE_PCT_THRESHOLD}%):")

    if not found_opportunities:
        print("未发现符合条件的机会。")
    else:
        for opp in found_opportunities:
            print(opp)
