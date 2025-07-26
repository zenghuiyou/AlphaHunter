import baostock as bs
import pandas as pd
import time

def minimal_api_test():
    """
    最小化API调用测试：
    1. 登录BaoStock。
    2. 对单个、硬编码的正确股票代码进行查询。
    3. 打印详细的返回结果。
    """
    print("--- AlphaHunter最小化API调用测试 ---")

    # 1. 登录系统
    lg = bs.login()
    if lg.error_code != '0':
        print(f"BaoStock登录失败: {lg.error_msg}")
        return
    print("BaoStock登录成功。")

    try:
        # 2. 核心：对单个、硬编码的股票进行查询
        target_code = "sz.000001"
        target_date = "2025-07-25"
        print(f"\n准备查询单个股票...")
        print(f"  - 股票代码: {target_code}")
        print(f"  - 查询日期: {target_date}")

        rs = bs.query_history_k_data_plus(
            target_code,
            "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST",
            start_date=target_date,
            end_date=target_date,
            frequency="d",
            adjustflag="3" # 不复权
        )

        # 3. 打印完整的返回结果
        print("\n--- API返回结果 ---")
        print(f"Error Code: {rs.error_code}")
        print(f"Error Msg:  {rs.error_msg}")

        if rs.error_code == '0':
            print("\n查询成功！数据如下：")
            data_list = []
            while rs.next():
                data_list.append(rs.get_row_data())
            result_df = pd.DataFrame(data_list, columns=rs.fields)
            print(result_df)
        else:
            print("\n查询失败。")

    finally:
        # 4. 登出系统
        bs.logout()
        print("\nBaoStock已登出。")

if __name__ == '__main__':
    minimal_api_test() 