import pandas as pd
from typing import Dict, Any
from src.app.logger_config import log
from src.config import settings
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from zhipuai import ZhipuAI

@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
    retry=retry_if_exception_type(Exception),
    before_sleep=lambda retry_state: log.warning(
        f"调用智谱AI API失败，正在进行第 {retry_state.attempt_number} 次重试..."
    )
)
def get_analysis_from_glm4(opportunity: Dict[str, Any]) -> str:
    """
    接收一个经过增强的交易机会（字典），调用智谱AI GLM-4为其生成四维一体的深度分析报告。
    增加了tenacity重试机制和loguru日志记录。

    Args:
        opportunity: 一个包含单支股票多维度数据的字典。

    Returns:
        一个由AI生成的、结构化的深度分析报告字符串。如果失败则返回错误信息。
    """
    try:
        # 1. 初始化ZhipuAI客户端
        client = ZhipuAI(api_key=settings.ZHIPUAI_API_KEY)
        
        # 2. 从富数据中提取信息并构造新的Prompt
        # 技术面
        ticker = opportunity.get('ticker', 'N/A')
        price = opportunity.get('price', 0)
        change_pct = opportunity.get('change_pct', 0)
        
        # 基本面
        profile = opportunity.get('company_profile', {})
        financials = opportunity.get('financial_indicators', {})
        industry = profile.get('industry', 'N/A')
        pe_ratio = financials.get('pe_ratio', 'N/A')
        pb_ratio = financials.get('pb_ratio', 'N/A')
        
        # 消息面
        news = opportunity.get('recent_news', [])
        news_str = "\n".join(f"- {n}" for n in news) if news else "无"
        
        # 资金面
        fund_flow = opportunity.get('fund_flow', {})
        main_inflow = fund_flow.get('main_net_inflow', 'N/A')

        prompt = f"""
        请扮演一位顶级的中国A股市场首席分析师。
        你现在需要对一只通过了技术面初步筛选的股票进行全面的“四维”深度分析。
        请基于以下所有信息，给出一份专业、深度、结构化的投资分析报告。

        ---
        ### 1. 技术面数据 (由BaoStock初筛触发)
        - **股票代码**: {ticker}
        - **当前价格**: {price:.2f}
        - **今日涨跌幅**: {change_pct:.2f}%
        - **核心发现**: 该股今日出现显著的价量异动，符合预设的扫描规则，因此进入我们的视野。

        ### 2. 基本面数据 (由AkShare增强)
        - **所属行业**: {industry}
        - **市盈率 (PE TTM)**: {pe_ratio}
        - **市净率 (PB)**: {pb_ratio}

        ### 3. 消息面数据 (由AkShare增强)
        - **近期相关新闻**:
        {news_str}

        ### 4. 资金面数据 (由AkShare增强)
        - **主力资金净流入**: {main_inflow}

        ---
        ### 分析任务
        请根据以上全部信息，以Markdown格式输出一份包含以下部分的分析报告：

        #### 一、技术形态分析
        点评当前的技术走势，是突破、反弹还是回调？量价关系是否健康？

        #### 二、基本面健康度评估
        基于其行业地位和核心财务指标（PE/PB），评估其估值水平和基本面质量。

        #### 三、消息面催化剂解读
        分析近期新闻中是否存在潜在的股价催化剂（利好或利空）。

        #### 四、资金面共识度判断
        解读主力资金的动向，是在流入还是流出？这反映了什么市场情绪？

        #### 五、综合投资评级与核心逻辑
        **评级**: (例如：强烈推荐, 积极关注, 中性观察, 建议规避)
        **核心逻辑**: 用2-3句话，凝练地总结出当前关注或规避这只股票的核心原因。

        请直接输出分析报告，不要包含任何额外的前言或结语。
        """
        log.info(f"为股票 {ticker} 生成四维分析Prompt，准备调用AI分析...")

        # 3. 调用智谱AI GLM-4 API
        response = client.chat.completions.create(
            model="glm-4-plus",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )

        # 4. 解析并返回结果
        if response and response.choices:
            analysis_content = response.choices[0].message.content
            log.success(f"成功获取股票 {ticker} 的AI分析报告。")
            return analysis_content.strip()
        else:
            log.error("AI模型未返回有效分析结果。")
            return "AI模型未返回有效分析结果。"

    except Exception as e:
        log.error(f"调用智谱AI API时发生严重错误: {e}")
        # 抛出异常以触发tenacity重试
        raise e


def get_strategic_analysis_from_glm4(opportunity: dict) -> str:
    """
    (V4.5 新增)
    调用ZhipuAI的glm-4-plus模型，对识别出的“箱体突破”战略机会进行深度、专业的复盘和前景分析。

    :param opportunity: 一个包含突破机会详细信息的字典。
    :return: 由AI生成的Markdown格式的深度分析报告。
    """
    log.info(f"--- [V4.5] 开始为股票 {opportunity['ticker']} 生成战略分析报告 ---")
    
    # 为了防止prompt过长，我们只取最近250个交易日的数据给AI
    recent_history_df = opportunity['full_historical_data'].tail(250)
    history_summary = recent_history_df[['date', 'open', 'high', 'low', 'close', 'volume', 'pctChg']].to_string()

    prompt = f"""
请扮演一位顶级的中国A股市场首席策略分析师。

你的任务是对一个刚刚出现经典“箱体突破”技术形态的股票进行全面、深度的战略评估。

---
### **核心事件：技术形态突破**
- **股票代码**: {opportunity['ticker']}
- **突破日期**: {opportunity['breakout_date']}
- **突破日收盘价**: {opportunity['breakout_price']:.2f}
- **事件描述**: 该股票在经历了长达 **{opportunity['consolidation_period_days']}** 个交易日的箱体盘整后，于今日以放量形式成功向上突破了箱体上轨 **{opportunity['box_high']:.2f}**。

---
### **盘整期关键数据**
- **盘整区间**: {opportunity['box_low']:.2f} - {opportunity['box_high']:.2f}
- **盘整期日均成交量**: {opportunity['consolidation_avg_volume']:.0f}
- **突破日成交量**: {opportunity['breakout_volume']:.0f} (为盘整期均量的 **{opportunity['breakout_volume']/opportunity['consolidation_avg_volume']:.2f}** 倍)

---
### **近一年历史日线数据摘要**
```
{history_summary}
```

---
### **你的分析任务 (请以Markdown格式输出)**

1.  **突破形态质量评估**:
    *   **复盘**: 这次长达 {opportunity['consolidation_period_days']} 天的盘整期，其形态是否标准？成交量在盘整后期是否有萎缩迹象？
    *   **定性**: 本次突破是“真突破”还是“假突破”的可能性有多大？成交量的放大程度是否足够支撑后续行情？请结合历史数据给出你的判断依据。

2.  **上涨潜力与目标价位预估**:
    *   **量度涨幅**: 根据经典的箱体理论，本次突破的“最小理论上涨目标价位”是多少？(目标价 = 箱体上轨 + (箱体上轨 - 箱体下轨))
    *   **关键阻力**: 从历史数据看，上方有哪些关键的历史高点或成交密集区会形成阻力？

3.  **主要风险点提示**:
    *   如果突破失败，可能会回踩到哪些关键支撑位？
    *   当前市场整体环境（大盘走势）对这次突破是助力还是阻力？
    *   有没有其他潜在的风险需要注意？

4.  **综合投资建议**:
    *   **一句话总结**: 对这次投资机会给出一个清晰、明确的定性结论。
    *   **操作策略**: 如果你是基金经理，你会如何操作？是立即买入，还是等待回踩确认？仓位如何控制？
"""

    try:
        client = ZhipuAI(api_key=settings.ZHIPUAI_API_KEY)
        response = client.chat.completions.create(
            model="glm-4-plus",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            top_p=0.8,
            stream=False,
        )
        final_report = response.choices[0].message.content
        
        log.success(f"--- [V4.5] 成功为 {opportunity['ticker']} 生成战略分析报告 ---")
        return final_report.strip()

    except Exception as e:
        log.error(f"调用智谱AI时发生严重错误: {e}")
        return f"无法为 {opportunity['ticker']} 生成分析报告，错误: {e}"


# --- 本地测试代码 ---
if __name__ == '__main__':
    log.info("--- 启动AI分析模块测试 ---")
    
    if not settings.ZHIPUAI_API_KEY or settings.ZHIPUAI_API_KEY == "Ycbc6048999334838bd99235c3d83d105.obCizMjN6pVPUeor":
        log.error("错误: 请在 src/config.py 或环境变量中设置您的 ZHIPUAI_API_KEY。")
    else:
        # 模拟一个经过增强的数据包
        mock_opportunity = {
            'ticker': 'sh.600519',
            'price': 1688.88,
            'change_pct': 3.1,
            'company_profile': {
                'industry': '酿酒行业',
                'total_market_cap': '2.12万亿',
                'circulating_market_cap': '2.12万亿'
            },
            'financial_indicators': {
                'pe_ratio': 32.5,
                'pb_ratio': 9.8,
                'roe': 35.1
            },
            'recent_news': [
                '贵州茅台发布年度业绩预告，净利润超预期增长',
                '高端白酒行业景气度持续提升',
                '公司宣布新的分红方案'
            ],
            'fund_flow': {
                'main_net_inflow': '5.2亿元',
                'super_large_net_inflow': '3.1亿元'
            }
        }

        log.info(f"\n[1] 模拟的输入机会:\n{mock_opportunity}")
        log.info("\n--- 正在调用智谱AI进行分析... ---")
        
        try:
            report = get_analysis_from_glm4(mock_opportunity)
            log.info(f"\n[2] 生成的AI分析报告:\n{report}")
        except Exception as e:
            log.critical(f"经过多次重试后，AI分析最终失败: {e}")
