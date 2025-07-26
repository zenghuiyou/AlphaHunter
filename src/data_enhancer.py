import akshare as ak
from typing import Dict, Any
from tenacity import retry, stop_after_attempt, wait_fixed
from src.app.logger_config import log

# Helper functions with retry decorators can be defined here if needed

def enhance_opportunity_with_akshare(ticker: str) -> dict:
    """
    使用AkShare为单个股票机会进行多维度数据增强。
    V5.0 修正版：
    - 对每个API调用增加独立的try-except块，提高健壮性。
    - 修正了错误的API参数。
    - 增加了更详细的日志。
    """
    log.info(f"开始为股票 {ticker} 进行AkShare数据增强...")
    # AkShare通常需要不带交易所前缀的纯数字代码
    symbol = ticker.split(".")[1]

    enhanced_data = {
        'company_profile': {},
        'financial_indicators': {},
        'recent_news': [],
        'fund_flow': {}
    }

    # 1. 公司概况
    try:
        profile_df = ak.stock_individual_info_em(symbol=symbol)
        info_dict = dict(zip(profile_df['item'], profile_df['value']))
        enhanced_data['company_profile'] = {
            'industry': info_dict.get('行业'),
            'total_market_cap': info_dict.get('总市值'),
            'circulating_market_cap': info_dict.get('流通市值')
        }
        log.info(f"[{ticker}] 成功获取公司概况。")
    except Exception as e:
        log.warning(f"[{ticker}] 获取公司概况失败: {e}")

    # 2. 核心财务指标 (修正了参数名)
    try:
        indicators_df = ak.stock_financial_analysis_indicator(symbol=symbol)
        if not indicators_df.empty:
            latest_financials = indicators_df.iloc[-1]
            enhanced_data['financial_indicators'] = {
                'pe_ratio': latest_financials.get('市盈率TTM', 'N/A'),
                'pb_ratio': latest_financials.get('市净率', 'N/A'),
                'roe': latest_financials.get('净资产收益率TTM', 'N/A'),
            }
            log.info(f"[{ticker}] 成功获取财务指标。")
        else:
            log.warning(f"[{ticker}] 获取财务指标数据为空。")
    except Exception as e:
        log.warning(f"[{ticker}] 获取财务指标失败: {e}")

    # 3. 近期新闻 (修正了参数名 stock -> symbol)
    try:
        news_df = ak.stock_news_em(symbol=symbol)
        enhanced_data['recent_news'] = news_df['新闻标题'].head(3).tolist()
        log.info(f"[{ticker}] 成功获取近期新闻。")
    except Exception as e:
        log.warning(f"[{ticker}] 获取近期新闻失败: {e}")

    # 4. 资金流向 (修正了API和market参数)
    try:
        fund_flow_df = ak.stock_individual_fund_flow(stock=symbol, market="全部")
        if not fund_flow_df.empty:
            latest_flow = fund_flow_df.iloc[-1]
            enhanced_data['fund_flow'] = {
                '主力净流入': latest_flow.get('主力净流入-净额'),
                '超大单净流入': latest_flow.get('超大单净流入-净额'),
                '大单净流入': latest_flow.get('大单净流入-净额'),
                '中单净流入': latest_flow.get('中单净流入-净额'),
                '小单净流入': latest_flow.get('小单净流入-净额'),
            }
            log.info(f"[{ticker}] 成功获取资金流向。")
        else:
            log.warning(f"[{ticker}] 获取资金流向数据为空。")
    except Exception as e:
        log.warning(f"[{ticker}] 获取资金流向失败: {e}")

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