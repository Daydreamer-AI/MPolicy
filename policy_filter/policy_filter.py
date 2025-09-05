import pandas as pd
from typing import Sequence

policy_filter_ma5_diff = 0.02
policy_filter_ma10_diff = 0.02
policy_filter_ma20_diff = 0.02
policy_filter_ma24_diff = 0.03
policy_filter_ma30_diff = 0.03
policy_filter_ma52_diff = 0.03
policy_filter_ma60_diff = 0.03

policy_filter_turn = 3
policy_filter_lb = 1

def set_ma5_diff(ma5_diff):
    policy_filter_ma5_diff = ma5_diff

def set_ma10_diff(ma10_diff):
    policy_filter_ma10_diff = ma10_diff

def set_ma20_diff(ma20_diff):
    policy_filter_ma20_diff = ma20_diff

def set_ma24_diff(ma24_diff):
    policy_filter_ma24_diff = ma24_diff

def set_ma30_diff(ma30_diff):
    policy_filter_ma30_diff = ma30_diff

def set_ma52_diff(ma52_diff):
    policy_filter_ma52_diff = ma52_diff

def set_ma60_diff(ma60_diff):
    policy_filter_ma60_diff = ma60_diff

def get_ma5_diff():
    return policy_filter_ma5_diff

def get_ma10_diff():
    return policy_filter_ma10_diff

def get_ma20_diff():
    return policy_filter_ma20_diff

def get_ma24_diff():
    return policy_filter_ma24_diff

def get_ma30_diff():
    return policy_filter_ma30_diff

def get_ma52_diff():
    return policy_filter_ma52_diff

def get_ma60_diff():
    return policy_filter_ma60_diff

def columns_check(df_data, col_names: Sequence[str]) -> bool:
    # print("df_data.columns:")
    # print(df_data.columns)
    # print(col_names)
    for arg in col_names:
        if arg in df_data.columns:
            continue
        else:
            print("错误，列不存在：", arg)
            return False
    return True

def daily_data_check(df_daily_data):
    pass

def daily_ma52_filter(df_daily_data):
    if df_daily_data.empty:
        return False

    day_close = 0.0
    day_ma52 = 0.0
    day_turn = 0.0
    day_lb = 0.0

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
    
    day_diff = day_ma52 * policy_filter_ma52_diff
    # print(f"day_close: {day_close}, day_ma52: {day_ma52}, diff: {day_diff}, day_turn>: {day_turn}, day_lb: {day_lb}")

    # 修改后条件判断
    if (abs(day_close - day_ma52) < day_diff) and (day_turn > policy_filter_turn) and (day_lb > policy_filter_lb):
    # 执行逻辑
    # if (week_stock_data.tail(1)['收盘'] > week_stock_data.tail(1)['MA52']) and (abs(day_stock_data.tail(1)['收盘'] - day_stock_data.tail(1)['MA52']) < day_stock_data.tail(1)['MA52'] * 1.1):
        # print("符合日线MA52筛选")
        return True
    else:
        # print("不符合多空逻辑")
        return False
    
def daily_and_weekly_ma52_filter(df_daily_data, df_weekly_data):
    if df_daily_data.empty or df_weekly_data.empty:
        return False
    
    day_close = 0.0
    day_ma52 = 0.0
    day_turn = 0.0
    day_lb = 0.0

    if columns_check(df_daily_data, ('收盘', 'MA52', '换手率', '量比5日')):
        last_day_row = df_daily_data.tail(1)
        day_close = last_day_row['收盘'].item()
        day_ma52 = last_day_row['MA52'].item()
        day_turn = last_day_row['换手率'].item()
        day_lb = last_day_row['量比5日'].item()
    else:
        print("错误：【日线】数据必要的列不存在")
        return False

    week_close = 0.0
    week_ma52 = 0.0
    if columns_check(df_weekly_data, ('收盘', 'MA52')):
        last_week_row = df_weekly_data.tail(1)
        week_close = last_week_row['收盘'].item()
        week_ma52 = last_week_row['MA52'].item()
    else:
        print("错误：【周线】数据必要的列不存在")
        return False

    day_diff = day_ma52 * policy_filter_ma52_diff
    # print(f"day_close: {day_close}, day_ma52: {day_ma52}, diff: {day_diff}, day_turn>: {day_turn}, day_lb: {day_lb}")
    # print(f"week_close: {week_close}, week_ma52: {week_ma52}")
    if week_close > week_ma52 and (abs(day_close - day_ma52) < day_diff) and (day_turn > policy_filter_turn) and (day_lb > policy_filter_lb):
        # print("符合日线&周线MA52筛选")
        return True
    else:
        return False
    

def daily_ma52_ma24_filter(df_daily_data, df_weekly_data, isUp=False):
    if df_daily_data.empty or df_weekly_data.empty:
        return False
    
    day_close = 0.0
    day_dea = 0.0
    day_ma24 = 0.0
    day_ma52 = 0.0
    day_turn = 0.0
    day_lb = 0.0
    if columns_check(df_daily_data, ('收盘', 'DEA', 'MA24', 'MA52', '换手率', '量比5日')):
        last_day_row = df_daily_data.tail(1)
        day_close = last_day_row['收盘'].item()
        day_dea = last_day_row['DEA'].item()
        day_ma24 = last_day_row['MA24'].item()
        day_ma52 = last_day_row['MA52'].item()
        day_turn = last_day_row['换手率'].item()
        day_lb = last_day_row['量比5日'].item()
    else:
        return False

    week_close = 0.0
    week_ma52 = 0.0
    if columns_check(df_weekly_data, ('收盘', 'MA52')):
        last_week_row = df_weekly_data.tail(1)
        week_close = last_week_row['收盘'].item()
        week_ma52 = last_week_row['MA52'].item()
    else:
        return False

    day_diff = day_ma52 * policy_filter_ma52_diff
    # print(f"day_close: {day_close}, day_dea: {day_dea}, day_ma24: {day_ma24}, day_ma52: {day_ma52}, diff: {day_diff}, day_turn>: {day_turn}, day_lb: {day_lb}")
    # print(f"week_close: {week_close}, week_ma52: {week_ma52}")

    b_ret = (day_turn > policy_filter_turn) and (day_lb > policy_filter_lb)
    b_ret_2 = week_close > week_ma52
    if isUp:
        # 零轴上方
        b_ret_3 = day_close < day_ma24 and (abs(day_close - day_ma52) < day_ma52 * policy_filter_ma52_diff)
        b_ret_4 = day_dea > 0
    else:
        # 零轴下方
        b_ret_3 = day_close > day_ma24 and day_close < day_ma52 and day_ma24 < day_ma52# (abs(day_close - day_ma24) < day_ma24 * policy_filter_ma24_diff)
        b_ret_4 = day_dea < 0

    if b_ret and b_ret_2 and b_ret_3 and b_ret_4:
        # print("符合日线MA24&MA52筛选")
        return True
    
    return False

def daily_ma24_filter(df_daily_data, df_weekly_data):
    '''
        筛选逻辑：零轴上方回踩MA24筛选法，最好是第一次回踩MA24。和daily_ma52_ma24_filter稍有重复。
        进场逻辑：最新收盘价无限接近MA24，且收盘价小于MA5或小于MA10，且下面15(或7.5)分钟级别零轴下方出现底背离或下跌动能不足形态，或者站上突破15分钟MA52压力，亦或者等15分钟DEA突破零轴，回踩15分钟MA5或MA10，才满足进场条件
        止盈位：有效反弹看前高
        止损位：有效跌破日线MA24或MA30清仓离场，等待日线MA52机会。
    '''
    if df_daily_data.empty or df_weekly_data.empty:
        return False
    
    day_close = 0.0
    day_dea = 0.0
    day_ma24 = 0.0
    day_ma52 = 0.0
    day_turn = 0.0
    day_lb = 0.0
    week_close = 0.0
    week_ma52 = 0.0
    if columns_check(df_daily_data, ('收盘', 'DEA', 'MA5', 'MA10', 'MA24', 'MA30', 'MA52', '换手率', '量比5日')):
        last_day_row = df_daily_data.tail(1)
        day_close = last_day_row['收盘'].item()
        day_dea = last_day_row['DEA'].item()
        day_ma5 = last_day_row['MA5'].item()
        day_ma10 = last_day_row['MA10'].item()
        day_ma24 = last_day_row['MA24'].item()
        day_ma30 = last_day_row['MA30'].item()
        day_ma52 = last_day_row['MA52'].item()
        day_turn = last_day_row['换手率'].item()
        day_lb = last_day_row['量比5日'].item()
    else:
        return False


    if columns_check(df_weekly_data, ('收盘', 'MA52')):
        last_week_row = df_weekly_data.tail(1)
        week_close = last_week_row['收盘'].item()
        week_ma52 = last_week_row['MA52'].item()
    else:
        return False

    day_diff = day_ma52 * policy_filter_ma52_diff
    # print(f"day_close: {day_close}, day_dea: {day_dea}, day_ma24: {day_ma24}, day_ma52: {day_ma52}, diff: {day_diff}, day_turn>: {day_turn}, day_lb: {day_lb}")
    # print(f"week_close: {week_close}, week_ma52: {week_ma52}")

    b_ret = (day_turn > policy_filter_turn) and (day_lb > policy_filter_lb)
    b_ret_2 = week_close > week_ma52

    b_ret_3 = day_dea > 0
    b_ret_4 = (day_close > day_ma24 or day_close > day_ma30) and (day_close < day_ma5 and day_close < day_ma10)# abs(day_close - day_ma24) < day_ma24 * policy_filter_ma24_diff
    b_ret_5 = day_ma5 <= day_ma10 and day_ma10 > day_ma24 and day_ma5 > day_ma24 and day_ma24 > day_ma52

    if b_ret and b_ret_2 and b_ret_3 and b_ret_4 and b_ret_5:
        # print("符合日线MA24筛选")
        return True
    
    return False


def daily_ma10_filter(df_daily_data):
    '''
        筛选逻辑：零轴上方，回踩MA10
        进场逻辑：最新收盘价位于MA5、MA10之间，次日必须低开，且接近30或60分钟MA52，且30或60分钟DEA大于0，且下面5分钟出现底背离或下跌动能不足，才满足进场条件。
        止盈：指数看到30或60分钟背离或上涨动能不足离场止盈
        止损：有效跌破30或60分钟MA52，且对应的DEA下穿零轴清仓止损
    '''
    if df_daily_data.empty:
        return False
    day_close = 0.0
    day_dea = 0.0
    day_ma10 = 0.0
    day_ma24 = 0.0
    day_ma52 = 0.0
    day_turn = 0.0
    day_lb = 0.0
    if columns_check(df_daily_data, ('收盘', 'DEA', 'MA5', 'MA10', 'MA24', 'MA52', '换手率', '量比5日')):
        last_day_row = df_daily_data.tail(1)
        day_close = last_day_row['收盘'].item()
        day_dea = last_day_row['DEA'].item()
        day_ma5 = last_day_row['MA5'].item()
        day_ma10 = last_day_row['MA10'].item()
        day_ma24 = last_day_row['MA24'].item()
        day_ma52 = last_day_row['MA52'].item()
        day_turn = last_day_row['换手率'].item()
        day_lb = last_day_row['量比5日'].item()
    else:
        return False

    b_ret = (day_turn > policy_filter_turn) and (day_lb > policy_filter_lb)
    b_ret_2 = day_dea > 0
    b_ret_3 = day_ma24 > day_ma52 and day_ma10 > day_ma24 and day_ma5 > day_ma10
    b_ret_4 = day_close > day_ma10 and day_close < day_ma5# abs(day_close - day_ma10) < day_ma10 * policy_filter_ma10_diff

    day_ma10_diff = day_ma10 * policy_filter_ma10_diff
    # print(f"day_close: {day_close}, day_dea: {day_dea}, day_ma10: {day_ma10}, day_ma24: {day_ma24}, day_ma52: {day_ma52}, day_ma10_diff: {day_ma10_diff}, day_turn>: {day_turn}, day_lb: {day_lb}")

    if b_ret and b_ret_2 and b_ret_3 and b_ret_4:
        # print("符合日线MA10筛选")
        return True
    
    return False

def daily_ma20_filter(df_daily_data):
    if df_daily_data.empty:
        return False
    
    day_close = 0.0
    day_dea = 0.0
    day_ma20 = 0.0
    day_ma24 = 0.0
    day_ma52 = 0.0
    day_turn = 0.0
    day_lb = 0.0
    if columns_check(df_daily_data, ('收盘', 'DEA', 'MA20', 'MA24', 'MA52', '换手率', '量比5日')):
        last_day_row = df_daily_data.tail(1)
        day_close = last_day_row['收盘'].item()
        day_dea = last_day_row['DEA'].item()
        day_ma20 = last_day_row['MA20'].item()
        day_ma24 = last_day_row['MA24'].item()
        day_ma52 = last_day_row['MA52'].item()
        day_turn = last_day_row['换手率'].item()
        day_lb = last_day_row['量比5日'].item()
    else:
        return False

    b_ret = (day_turn > policy_filter_turn) and (day_lb > policy_filter_lb)
    b_ret_2 = day_dea > 0
    b_ret_3 = day_ma24 > day_ma52
    b_ret_4 = abs(day_close - day_ma20) < day_ma20 * policy_filter_ma20_diff

    day_ma20_diff = day_ma20 * policy_filter_ma20_diff
    # print(f"day_close: {day_close}, day_dea: {day_dea}, day_ma20: {day_ma20}, day_ma24: {day_ma24}, day_ma52: {day_ma52}, day_ma20_diff: {day_ma20_diff}, day_turn>: {day_turn}, day_lb: {day_lb}")

    if b_ret and b_ret_2 and b_ret_3 and b_ret_4:
        # print("符合日线MA20筛选")
        return True
    
    return False