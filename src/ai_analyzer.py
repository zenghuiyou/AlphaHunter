import pandas as pd
from typing import Dict, Any
from zhipuai import ZhipuAI
from src.config import settings

def get_analysis_from_glm4(opportunity: Dict[str, Any]) -> str:
    """
    接收一个交易机会（字典），调用智谱AI GLM-4为其生成专业的分析报告。

    Args:
        opportunity: 一个包含单支股票机会数据的字典。

    Returns:
        一个由AI生成的、结构化的分析报告字符串。如果失败则返回错误信息。
    """
    try:
        # 1. 初始化ZhipuAI客户端
        # 确保在config.py或环境变量中设置了ZHIPUAI_API_KEY
        client = ZhipuAI(api_key=settings.ZHIPUAI_API_KEY)
        
        # 2. 精心构造高质量的Prompt
        ticker = opportunity.get('ticker', 'N/A')
        price = opportunity.get('price', 0)
        change_pct = opportunity.get('change_pct', 0)

        prompt = f"""
        请扮演一个专业的中国A股市场分析师。
        基于以下股票的实时数据，提供一份简洁、专业、结构化的分析报告。

        **股票代码**: {ticker}
        **当前价格**: {price:.2f}
        **涨跌幅**: {change_pct:.2f}%

        你的分析报告应包含以下几个方面, 并以 Markdown 格式返回:
        1.  **技术面分析**: 根据价格和涨跌幅，简要分析目前的技术形态（例如：放量上涨、突破关键位、技术性回调等）。
        2.  **市场情绪**: 结合涨跌幅，评估当前市场的短期情绪（例如：看涨情绪浓厚、市场存在分歧、恐慌性抛售等）。
        3.  **核心观点**: 综合以上信息，给出一个明确的核心投资观点（例如：建议关注、短期看涨、风险较高、建议观望等）。
        4.  **风险提示**: 提醒潜在的风险点。

        请直接输出分析报告内容，不要包含任何额外的前言或结语。
        """

        # 3. 调用智谱AI GLM-4 API
        response = client.chat.completions.create(
            model="glm-4-plus",  # 已更新为 glm-4-plus
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7, # 保持一定的创造性
        )

        # 4. 解析并返回结果
        if response and response.choices:
            analysis_content = response.choices[0].message.content
            return analysis_content.strip()
        else:
            return "AI模型未返回有效分析结果。"

    except Exception as e:
        print(f"错误: 调用智谱AI API失败: {e}")
        return f"调用AI分析服务时发生错误: {e}"


# --- 本地测试代码 ---
if __name__ == '__main__':
    # 在运行此测试之前，请确保您已经在 config.py 或环境变量中配置了 ZHIPUAI_API_KEY
    if settings.ZHIPUAI_API_KEY == "YOUR_ZHIPUAI_API_KEY_HERE" or settings.ZHIPUAI_API_KEY == "3a15d25fa9e94dceafe0d83b078f7927.yfAKSzDcQk6SBxF4":
        print("--- 启动AI分析模块测试 ---")
        
        # 1. 创建一个模拟的单一机会数据
        mock_opportunity = {
            'ticker': '600519.SH', # 贵州茅台
            'price': 1650.88,
            'change_pct': 2.5
        }

        print("\n[1] 模拟的输入机会:")
        print(mock_opportunity)

        # 2. 进行真实的AI分析
        print("\n--- 正在调用智谱AI进行分析... ---")
        report = get_analysis_from_glm4(mock_opportunity)
        
        print("\n[2] 生成的AI分析报告:")
        print(report)
    else:
        print("错误: 请在 src/config.py 或环境变量中设置您的 ZHIPUAI_API_KEY。")
        print("当前的Key似乎不是一个有效的测试或占位符Key。")
