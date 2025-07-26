import pandas as pd
from .base_strategy import BaseStrategy
from src.app.logger_config import log

class BoxBreakoutStrategy(BaseStrategy):
    """
    V5.0模块化：箱体突破策略。
    
    该策略旨在寻找经过一段时间盘整（形成箱体）后，
    股价放量突破箱体上沿的股票。
    """

    def __init__(self, consolidation_days=60, breakout_strength=1.5):
        self.consolidation_days = consolidation_days
        self.breakout_strength = breakout_strength

    @property
    def name(self) -> str:
        return "经典箱体突破"

    def scan(self, historical_data: dict) -> list:
        opportunities = []
        log.info(f"--- 开始执行 [{self.name}] 策略扫描 ---")

        for ticker, df in historical_data.items():
            if len(df) < self.consolidation_days + 1:
                # log.debug(f"[{ticker}] 数据不足，跳过。")
                continue

            try:
                # 使用最近N天的数据进行计算
                recent_df = df.iloc[-(self.consolidation_days + 1):]
                
                # 定义盘整区间（不包括今天）
                consolidation_period = recent_df.iloc[:-1]
                
                # 定义突破日（今天）
                breakout_day = recent_df.iloc[-1]
                
                # 计算箱体
                box_high = consolidation_period['high'].max()
                box_low = consolidation_period['low'].min()
                
                # 计算盘整期平均成交量
                consolidation_avg_volume = consolidation_period['volume'].mean()

                # 判断突破条件
                # 1. 盘整期间振幅不能过大（例如，超过30%），过滤掉趋势股
                if (box_high - box_low) / box_low > 0.5:
                    continue

                # 2. 突破日收盘价 > 箱体上沿
                # 3. 突破日最高价 > 箱体上沿 (允许影线突破)
                # 4. 突破日成交量 > 盘整期平均成交量 * 倍数
                if (breakout_day['close'] > box_high and
                    breakout_day['high'] > box_high and
                    breakout_day['volume'] > consolidation_avg_volume * self.breakout_strength):
                    
                    opportunity = {
                        'ticker': ticker,
                        'strategy_name': self.name,
                        'breakout_date': breakout_day['date'],
                        'breakout_price': breakout_day['close'],
                        'box_high': box_high,
                        'box_low': box_low,
                        'consolidation_period_days': self.consolidation_days,
                        'breakout_volume': breakout_day['volume'],
                        'consolidation_avg_volume': consolidation_avg_volume,
                        'full_historical_data': df,
                        'description': f"在经历{self.consolidation_days}天盘整后, 于{breakout_day['date']}放量突破箱体。"
                    }
                    opportunities.append(opportunity)
                    log.success(f"发现机会！[{ticker}] 符合 [{self.name}] 策略。")

            except Exception as e:
                log.error(f"[{ticker}] 在执行 [{self.name}] 策略时发生错误: {e}", exc_info=True)
                
        log.info(f"--- [{self.name}] 策略扫描完成，共发现 {len(opportunities)} 个机会 ---")
        return opportunities 