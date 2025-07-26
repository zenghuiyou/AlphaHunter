import baostock as bs
import pandas as pd
import time
from datetime import datetime, date, timedelta
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func
import sys
import os

# 将项目根目录添加到Python的模块搜索路径中
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app.database import engine
from src.app.models import StockDailyData

# --- 配置 ---
# 对于新股票，一次性回补多少天的历史数据
HISTORY_LOOKBACK_DAYS = 365

def get_latest_trading_day():
    """
    获取最近的一个交易日。
    """
    print("正在查询最近一个交易日...")
    today = date.today()
    for i in range(10): # 最多向前查找10天
        day_to_check = today - timedelta(days=i)
        date_str = day_to_check.strftime('%Y-%m-%d')
        rs = bs.query_trade_dates(start_date=date_str, end_date=date_str)
        if rs.error_code == '0' and rs.next():
            is_trading_day = rs.get_row_data()[1]
            if is_trading_day == '1':
                print(f"找到最近一个交易日: {date_str}")
                return date_str
    print("错误：在过去10天内未找到交易日。")
    return None

def get_all_a_share_codes(target_date):
    """
    获取指定日期的所有A股代码列表, 并进行筛选。
    """
    print(f"正在获取 {target_date} 的所有A股代码...")
    stock_rs = bs.query_all_stock(day=target_date)
    if stock_rs.error_code != '0':
        print(f"获取全市场股票列表失败: {stock_rs.error_msg}")
        return []

    stock_list = []
    while (stock_rs.error_code == '0') & stock_rs.next():
        stock_info = stock_rs.get_row_data()
        code_numeric = stock_info[0].split('.')[1]
        
        # 精确筛选沪深A股
        if code_numeric.startswith('60') or code_numeric.startswith('688'):
            code_full = f"sh.{code_numeric}"
        elif code_numeric.startswith('00') or code_numeric.startswith('300'):
            code_full = f"sz.{code_numeric}"
        else:
            continue

        # 过滤ST, *ST, 退市等
        if 'ST' in stock_info[2] or '*' in stock_info[2] or '退' in stock_info[2]:
            continue
        
        stock_list.append(code_full)
    
    print(f"获取到 {len(stock_list)} 只符合条件的A股代码。")
    return stock_list

def get_start_date_for_code(session, code):
    """
    查询数据库中特定股票的最新日期，来决定本次同步的开始日期。
    """
    latest_date_record = session.query(func.max(StockDailyData.date)).filter(StockDailyData.code == code).scalar()
    
    if latest_date_record:
        # 如果数据库中已有数据，则从最新日期的下一天开始同步
        return latest_date_record + timedelta(days=1)
    else:
        # 如果是新股票，则回补过去一年的数据
        print(f"发现新股票: {code}，将为其回补过去 {HISTORY_LOOKBACK_DAYS} 天的数据。")
        return date.today() - timedelta(days=HISTORY_LOOKBACK_DAYS)

def sync_daily_data():
    """
    核心数据同步函数：
    1. 获取全市场A股列表。
    2. 对每只股票，智能判断需要同步的起始日期。
    3. 从BaoStock下载数据。
    4. 高效批量存入SQLite数据库。
    """
    print("--- AlphaHunter开始执行日线数据同步任务 ---")
    start_time = time.time()

    # 创建数据库会话
    Session = sessionmaker(bind=engine)
    session = Session()

    lg = bs.login()
    if lg.error_code != '0':
        print(f"BaoStock登录失败: {lg.error_msg}")
        session.close()
        return

    print("BaoStock登录成功。")

    try:
        latest_trading_day = get_latest_trading_day()
        if not latest_trading_day:
            return # 如果找不到交易日，则直接退出

        all_codes = get_all_a_share_codes(latest_trading_day)
        total_codes = len(all_codes)
        
        for i, code in enumerate(all_codes):
            print(f"\n--- 正在处理: {code} ({i+1}/{total_codes}) ---")
            
            start_date = get_start_date_for_code(session, code)
            end_date = date.today()

            # 如果开始日期在结束日期之后，说明数据已经是最新，无需同步
            if start_date > end_date:
                print(f"{code} 的数据已是最新，无需同步。")
                continue

            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')

            print(f"准备下载 {code} 从 {start_date_str} 到 {end_date_str} 的数据...")
            
            rs = bs.query_history_k_data_plus(code,
                "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST",
                start_date=start_date_str, end_date=end_date_str,
                frequency="d", adjustflag="2") # qfq-前复权
            
            df = rs.get_data()

            if not df.empty and not df.iloc[0]['date'] == '':
                # 数据清洗和类型转换
                df.replace('', pd.NA, inplace=True)
                numeric_cols = ['open', 'high', 'low', 'close', 'preclose', 'volume', 'amount', 'turn', 'pctChg', 'peTTM', 'pbMRQ', 'psTTM', 'pcfNcfTTM']
                for col in numeric_cols:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # 转换日期格式，并移除任何可能因为API错误产生的空日期行
                df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
                df.dropna(subset=['date'], inplace=True)

                if df.empty:
                    print(f"数据清洗后，{code} 没有有效数据可同步。")
                    continue
                
                try:
                    data_to_insert = df.to_dict('records')
                    session.bulk_insert_mappings(StockDailyData, data_to_insert)
                    session.commit()
                    print(f"成功将 {len(data_to_insert)} 条 {code} 的数据存入数据库。")
                except Exception as e:
                    print(f"存入 {code} 数据时发生严重错误: {e}")
                    session.rollback()
            else:
                 print(f"未获取到 {code} 在指定时间段内的新数据。")

            time.sleep(0.1) # 礼貌性延迟

    finally:
        bs.logout()
        print("\nBaoStock已登出。")
        session.close()
        print("数据库会话已关闭。")

    end_time = time.time()
    print(f"\n--- 数据同步任务全部完成 ---")
    print(f"总耗时: {(end_time - start_time) / 60:.2f} 分钟")

if __name__ == '__main__':
    sync_daily_data() 