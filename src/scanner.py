import pandas as pd
from src.data_provider import get_realtime_market_data # 修正：导入正确的函数名
from src.config import settings  # 导入配置


def scan_opportunities(market_data: pd.DataFrame) -> pd.DataFrame:
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
