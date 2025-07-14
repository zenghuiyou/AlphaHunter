import pandas as pd
from typing import Dict, Any


def analyze_opportunity(opportunity: Dict[str, Any]) -> str:
    """
    接收一个交易机会（字典），为其生成一个模拟的AI分析报告。
    报告内容将更贴合A股市场的分析语境。

    Args:
        opportunity: 一个包含单支股票机会数据的字典。

    Returns:
        一个模拟的、结构化的AI分析报告字符串。
    """
    ticker = opportunity.get('ticker', '未知代码')
    price = opportunity.get('price', 0)

    # 模拟基于A股特点的分析逻辑
    if '600' in ticker or '000' in ticker: # 简单判断为主板
        analysis_focus = "主力资金动向和板块轮动效应"
    elif '300' in ticker: # 简单判断为创业板
        analysis_focus = "成长性、赛道前景和技术突破可能性"
    else:
        analysis_focus = "市场情绪和短期技术形态"

    # 生成更符合A股语境的分析报告
    report = f"""
    - **股票代码**: {ticker}
    - **当前价格**: {price:.2f}
    - **AI分析摘要**: 
      - **核心逻辑**: 基于 {analysis_focus} 的综合评估，该股表现出潜在的交易机会。
      - **技术面**: K线图呈现多头排列趋势，下方均线形成有力支撑。
      - **基本面**: 公司近期发布利好公告，市场预期较高。
      - **建议**: 建议密切关注未来几个交易日的量价关系变化，寻找合适的入场点。
    - **风险提示**: 市场波动风险，请注意控制仓位。
    """
    return report.strip()


# --- 本地测试代码 ---
if __name__ == '__main__':
    print("--- 启动AI分析模块测试 ---")
    # 创建一个模拟的单一机会数据 (Pandas Series)
    mock_opportunity = pd.Series({
        'ticker': 'TEST',
        'price': 999.99,
        'volume': 10000000,
        'change_pct': 5.0
    })

    print("\n[1] 模拟的输入机会:")
    print(mock_opportunity)

    # 2. 进行AI分析
    report = analyze_opportunity(mock_opportunity)
    print("\n[2] 生成的AI分析报告:")
    print(report)
