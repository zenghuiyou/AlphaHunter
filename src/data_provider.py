import pandas as pd
import baostock as bs
from datetime import datetime, timedelta

def get_realtime_market_data() -> pd.DataFrame:
    """
    从BaoStock API获取A股市场的最新交易日行情快照数据。
    返回一个经过清洗和重命名的DataFrame，列包括：
    'ticker', 'price', 'volume', 'change_pct'
    """
    # 1. 登录系统
    lg = bs.login()
    if lg.error_code != '0':
        print(f"错误: 登录BaoStock失败: {lg.error_msg}")
        return pd.DataFrame()

    try:
        # 2. 获取A股所有股票列表
        rs = bs.query_all_stock(day=datetime.today().strftime("%Y-%m-%d"))
        if rs.error_code != '0':
            print(f"错误: 查询所有A股列表失败: {rs.error_msg}")
            return pd.DataFrame()
        
        all_stocks = rs.get_data()
        # 筛选出沪深A股（sh或sz开头）
        a_stocks = all_stocks[
            all_stocks['code'].str.match(r'^(sh|sz)\.60|^(sh|sz)\.00|^(sh|sz)\.30')
        ]
        all_tickers = a_stocks['code'].to_list()

        # 3. 获取最新交易日的行情数据
        # BaoStock的实时行情接口有使用限制，我们用日线行情接口获取最新数据作为替代
        today_str = datetime.today().strftime('%Y-%m-%d')
        rs_daily = bs.query_history_k_data_plus(
            ",".join(all_tickers),
            "code,close,volume,pctChg,tradeStatus", # 增加请求 tradeStatus 字段
            start_date=today_str, 
            end_date=today_str,
            frequency="d", 
            adjustflag="3" # 不复权
        )
        if rs_daily.error_code != '0':
            print(f"错误: 查询最新日线行情失败: {rs_daily.error_msg}")
            return pd.DataFrame()

        market_data = rs_daily.get_data()
        
        # 4. 数据清洗和重命名
        # 将空值（通常是停牌）的行填充为0，并将类型转换为数值
        market_data.replace('', '0', inplace=True)
        # 增加对 tradeStatus 的处理
        market_data = market_data.astype({
            'close': 'float',
            'volume': 'float',
            'pctChg': 'float',
            'tradeStatus': 'int'
        })
        
        # 关键修复：在获取到日线数据后再根据交易状态过滤
        market_data = market_data[market_data['tradeStatus'] == 1]
        
        # 为了与项目其他部分的代码兼容，我们重命名列
        market_data.rename(columns={
            'code': 'ticker',
            'close': 'price',
            'volume': 'volume',
            'pctChg': 'change_pct'
        }, inplace=True)
        
        return market_data[['ticker', 'price', 'volume', 'change_pct']]

    finally:
        # 5. 登出系统
        bs.logout()


# --- 本地测试代码 ---
if __name__ == '__main__':
    print("--- 正在从 BaoStock 获取真实市场数据... ---")
    real_data = get_realtime_market_data()
    
    if not real_data.empty:
        print("--- 成功获取市场数据 ---")
        # 筛选出非零交易量和价格的数据进行展示
        active_data = real_data[(real_data['price'] > 0) & (real_data['volume'] > 0)]
        print(active_data.head())
    else:
        print("--- 获取市场数据失败或数据为空 ---")
