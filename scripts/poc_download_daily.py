import baostock as bs
import pandas as pd
import time
from datetime import datetime, timedelta

def get_latest_trading_day(bs_instance):
    """
    获取最近的一个交易日。
    使用传入的已登录的BaoStock实例。
    """
    today = datetime.now()
    day_to_check = today if today.hour >= 15 else today - timedelta(days=1)

    for i in range(10):
        date_str = day_to_check.strftime('%Y-%m-%d')
        rs = bs_instance.query_trade_dates(start_date=date_str, end_date=date_str)
        if rs.error_code == '0' and rs.next():
            is_trading_day = rs.get_row_data()[1]
            if is_trading_day == '1':
                return date_str
        day_to_check -= timedelta(days=1)
        
    return None

def proof_of_concept_download():
    """
    概念验证函数：
    1. 登录BaoStock。
    2. 获取最近一个交易日的全市场日线行情数据。
    3. 打印部分结果和性能指标。
    """
    print("--- AlphaHunter数据下载性能验证脚本 (V4 - Date-Fix) ---")
    start_time = time.time()

    # 1. 登录系统
    lg = bs.login()
    if lg.error_code != '0':
        print(f"BaoStock登录失败: {lg.error_msg}")
        return
    
    print("BaoStock登录成功。")
    login_time = time.time()
    print(f"登录耗时: {login_time - start_time:.2f}秒")

    try:
        # 2. 获取股票和交易日信息
        # 硬编码一个真实的、过去的交易日进行最终测试
        target_date = "2024-07-25"
        print(f"目标下载日期 (硬编码): {target_date}")

        stock_rs = bs.query_all_stock(day=target_date)
        if stock_rs.error_code != '0':
            print(f"获取全市场股票列表失败: {stock_rs.error_msg}")
            return
            
        stock_list = []
        while (stock_rs.error_code == '0') & stock_rs.next():
            stock_info = stock_rs.get_row_data()
            code_numeric = stock_info[0].split('.')[1] # 获取纯数字代码
            
            # 根据官方规则手动拼接正确前缀，并过滤
            if code_numeric.startswith('60') or code_numeric.startswith('688'):
                code_full = f"sh.{code_numeric}"
            elif code_numeric.startswith('00') or code_numeric.startswith('300'):
                code_full = f"sz.{code_numeric}"
            else:
                continue # 过滤掉北交所、或其他类型

            # 再次过滤ST、*ST、退市股
            if 'ST' in stock_info[2] or '*' in stock_info[2] or '退' in stock_info[2]:
                continue
            
            stock_list.append(code_full)

        print(f"已获取到 {len(stock_list)} 只符合条件的A股股票。")
        prepare_time = time.time()
        print(f"信息准备耗时: {prepare_time - login_time:.2f}秒")

        # 3. 核心：一次性下载全市场数据
        print("\n开始下载全市场日线数据 (逐个查询模式)，请稍候...")
        all_data = []
        
        total_stocks = len(stock_list)
        for i, code in enumerate(stock_list):
            rs = bs.query_history_k_data_plus(
                code,
                "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST",
                start_date=target_date,
                end_date=target_date,
                frequency="d",
                adjustflag="3" # 不复权
            )
            
            if rs.error_code == '0' and rs.next():
                all_data.append(rs.get_row_data())
            
            # 打印进度
            if (i + 1) % 100 == 0:
                print(f"  > 已处理 {i + 1} / {total_stocks} 只股票...")

        download_time = time.time()
        print(f"\n数据下载完成。下载过程耗时: {download_time - prepare_time:.2f}秒")

        if not all_data:
            print("错误：未能下载到任何数据。")
            return
            
        # 4. 结果展示
        result_df = pd.DataFrame(all_data, columns=rs.fields)
        
        print("\n--- 下载结果预览 ---")
        print(f"成功下载到 {len(result_df)} 条日线数据。")
        print("数据样例 (前5条):")
        print(result_df.head())

    finally:
        # 5. 登出系统
        bs.logout()
        print("\nBaoStock已登出。")
        
    end_time = time.time()
    print("\n--- 性能总结 ---")
    print(f"脚本执行总耗时: {end_time - start_time:.2f}秒")


if __name__ == '__main__':
    proof_of_concept_download() 