import pandas as pd
import numpy as np


def get_market_data() -> pd.DataFrame:
    """
    生成模拟的中国A股市场数据。
    返回一个包含股票代码、价格、成交量和涨跌幅的DataFrame。
    """
    # 使用典型的A股股票代码（.SH代表上海, .SZ代表深圳）
    tickers = [
        '600519.SH', '000858.SZ', '601318.SH', '002415.SZ', 
        '600036.SH', '300750.SZ', '000001.SZ'
    ]
    
    data = {
        'ticker': np.random.choice(tickers, 5),
        # A股股价范围更广
        'price': np.random.uniform(10, 300, 5),
        'volume': np.random.randint(1_000_000, 50_000_000, 5),
        # A股涨跌停为10%（创业板/科创板20%），这里我们模拟一个更常见的波动范围
        'change_pct': np.random.uniform(-5, 5, 5)
    }
    
    return pd.DataFrame(data)


# --- 本地测试代码 ---
if __name__ == '__main__':
    market_data = get_market_data()
    print("--- 模拟获取的市场数据 ---")
    print(market_data)
