import pandas as pd

def columns_check(df_data, *args):
    for arg in args:
        if arg in df_data.columns:
            continue
        else:
            return False
    return True

def daily_data_check(df_daily_data):
    pass

def daily_ma52_filter(df_daily_data):
    if df_daily_data.empty:
        return False

    
    # 检查列是否存在
    if columns_check(df_daily_data, ('收盘', 'MA52', '换手率', '量比5日')):
    # if '收盘' in df_daily_data.columns and 'MA52' in df_daily_data.columns and '换手率' in df_daily_data.columns and '量比5日' in df_daily_data.columns:
        last_day_row = df_daily_data.tail(1)
        day_close = last_day_row['收盘'].item()
        day_ma52 = last_day_row['MA52'].item()
        day_turn = last_day_row['换手率'].item()
        day_lb = last_day_row['量比5日'].item()
    else:
        print("错误：日线数据必要的列不存在")
        print("可用列：", df_daily_data.columns.tolist())
        return False  # 或者处理错误情况

    # 修改后条件判断
    if (abs(day_close - day_ma52) < day_ma52 * 0.1) and (day_turn > 3) and (day_lb > 1):
    # 执行逻辑
    # if (week_stock_data.tail(1)['收盘'] > week_stock_data.tail(1)['MA52']) and (abs(day_stock_data.tail(1)['收盘'] - day_stock_data.tail(1)['MA52']) < day_stock_data.tail(1)['MA52'] * 1.1):
        print("符合日线MA52筛选")
        return True
    else:
        # print("不符合多空逻辑")
        return False
    
def daily_and_weekly_ma52_filter(df_daily_data, df_weekly_data):
    if df_daily_data.empty or df_weekly_data.empty:
        return False
    
    if columns_check(df_daily_data, ('收盘', 'MA52', '换手率', '量比5日')):
        last_day_row = df_daily_data.tail(1)
        day_close = last_day_row['收盘'].item()
        day_ma52 = last_day_row['MA52'].item()
        day_turn = last_day_row['换手率'].item()
        day_lb = last_day_row['量比5日'].item()


    if columns_check(df_weekly_data, ('收盘', 'MA52')):
        last_week_row = df_weekly_data.tail(1)
        week_close = last_week_row['收盘'].item()
        week_ma52 = last_week_row['MA52'].item()

    if week_close > week_ma52 and (abs(day_close - day_ma52) < day_ma52 * 0.1) and (day_turn > 3) and (day_lb > 1):
        print("符合日线&周线MA52筛选")
        return True
    else:
        return False
    

def daily_ma52_ma24_filter(df_daily_data, df_weekly_data, isUp=False):
    if df_daily_data.empty or df_weekly_data.empty:
        return False
    
    if columns_check(df_daily_data, ('收盘', 'DEA', 'MA24', 'MA52', '换手率', '量比5日')):
        last_day_row = df_daily_data.tail(1)
        day_close = last_day_row['收盘'].item()
        day_dea = last_day_row['DEA'].item()
        day_ma24 = last_day_row['MA24'].item()
        day_ma52 = last_day_row['MA52'].item()
        day_turn = last_day_row['换手率'].item()
        day_lb = last_day_row['量比5日'].item()


    if columns_check(df_weekly_data, ('收盘', 'MA52')):
        last_week_row = df_weekly_data.tail(1)
        week_close = last_week_row['收盘'].item()
        week_ma52 = last_week_row['MA52'].item()

    b_ret = (day_turn > 3) and (day_lb > 1)
    b_ret_2 = week_close > week_ma52
    if isUp:
        # 零轴上方
        b_ret_3 = day_close < day_ma24 and (abs(day_close - day_ma52) < day_ma52 * 0.1)
        b_ret_4 = day_dea > 0
    else:
        # 零轴下方
        b_ret_3 = day_close > day_ma24 and (abs(day_close - day_ma52) < day_ma52 * 0.1)
        b_ret_4 = day_dea > 0

    if b_ret and b_ret_2 and b_ret_3 and b_ret_4:
        print("符合日线MA24&MA52筛选")
        return True
    
    return False

def daily_ma24_filter(df_daily_data, df_weekly_data):
    if df_daily_data.empty or df_weekly_data.empty:
        return False
    
    if columns_check(df_daily_data, ('收盘', 'DEA', 'MA24', 'MA52', '换手率', '量比5日')):
        last_day_row = df_daily_data.tail(1)
        day_close = last_day_row['收盘'].item()
        day_dea = last_day_row['DEA'].item()
        day_ma24 = last_day_row['MA24'].item()
        day_ma52 = last_day_row['MA52'].item()
        day_turn = last_day_row['换手率'].item()
        day_lb = last_day_row['量比5日'].item()


    if columns_check(df_weekly_data, ('收盘', 'MA52')):
        last_week_row = df_weekly_data.tail(1)
        week_close = last_week_row['收盘'].item()
        week_ma52 = last_week_row['MA52'].item()

    b_ret = (day_turn > 3) and (day_lb > 1)
    b_ret_2 = week_close > week_ma52

    b_ret_3 = day_dea > 0
    b_ret_4 = abs(day_close - day_ma24) < day_ma24 * 0.1

    if b_ret and b_ret_2 and b_ret_3 and b_ret_4:
        print("符合日线MA24筛选")
        return True
    
    return False