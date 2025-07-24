import akshare as ak
from typing import Dict, Any
from src.app.logger_config import log

def enhance_opportunity_with_akshare(ticker: str) -> Dict[str, Any]:
    """
    使用AkShare为单个股票代码提供多维度数据增强。

    Args:
        ticker: 标准股票代码，例如 "sh.600519"

    Returns:
        一个包含多个维度增强数据的字典。
    """
    log.info(f"开始为股票 {ticker} 进行AkShare数据增强...")
    enhanced_data = {}
    
    # AkShare需要不带 'sh.' 或 'sz.' 前缀的代码
    symbol = ticker.split('.')[-1]

    # 1. 获取公司概况 (基本面)
    try:
        info_df = ak.stock_individual_info_em(symbol=symbol)
        info_dict = dict(zip(info_df['item'], info_df['value']))
        enhanced_data['company_profile'] = {
            'industry': info_dict.get('行业'),
            'total_market_cap': info_dict.get('总市值'),
            'circulating_market_cap': info_dict.get('流通市值')
        }
        log.info(f"[{ticker}] 成功获取公司概况。")
    except Exception as e:
        log.warning(f"[{ticker}] 获取公司概况失败: {e}")
        enhanced_data['company_profile'] = {}

    # 2. 获取财务指标 (基本面)
    try:
        financial_df = ak.stock_financial_analysis_indicator(symbol=symbol)
        # 获取最新一期（最后一行）的财务数据
        latest_financials = financial_df.iloc[-1]
        enhanced_data['financial_indicators'] = {
            'pe_ratio': latest_financials.get('市盈率(PE-TTM)', 'N/A'),
            'pb_ratio': latest_financials.get('市净率(PB)', 'N/A'),
            'roe': latest_financials.get('净资产收益率(ROE-TTM)', 'N/A')
        }
        log.info(f"[{ticker}] 成功获取财务指标。")
    except Exception as e:
        log.warning(f"[{ticker}] 获取财务指标失败: {e}")
        enhanced_data['financial_indicators'] = {}

    # 3. 获取近期新闻 (消息面)
    try:
        news_df = ak.stock_news_em(stock=symbol)
        # 提取最近3条新闻标题
        enhanced_data['recent_news'] = news_df['新闻标题'].head(3).tolist()
        log.info(f"[{ticker}] 成功获取近期新闻。")
    except Exception as e:
        log.warning(f"[{ticker}] 获取近期新闻失败: {e}")
        enhanced_data['recent_news'] = []

    # 4. 获取资金流向 (资金面)
    try:
        fund_flow_df = ak.stock_individual_fund_flow(stock=symbol, market="北向")
        latest_fund_flow = fund_flow_df.iloc[-1]
        enhanced_data['fund_flow'] = {
            'main_net_inflow': latest_fund_flow.get('主力净流入-净额'),
            'super_large_net_inflow': latest_fund_flow.get('超大单净流入-净额')
        }
        log.info(f"[{ticker}] 成功获取资金流向。")
    except Exception as e:
        log.warning(f"[{ticker}] 获取资金流向失败: {e}")
        enhanced_data['fund_flow'] = {}
        
    log.success(f"完成对股票 {ticker} 的数据增强。")
    return enhanced_data

# --- 本地测试代码 ---
if __name__ == '__main__':
    # 测试一个常见的股票代码
    test_ticker = "sh.600519"  # 贵州茅台
    log.info(f"--- 正在测试 {test_ticker} 的数据增强功能... ---")
    
    data = enhance_opportunity_with_akshare(test_ticker)
    
    import json
    print(json.dumps(data, indent=4, ensure_ascii=False)) 