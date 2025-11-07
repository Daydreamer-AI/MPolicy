import pandas as pd
from typing import Sequence

from common.logging_manager import get_logger
logger = get_logger(__name__)

policy_filter_ma5_diff = 0.02
policy_filter_ma10_diff = 0.02
policy_filter_ma20_diff = 0.02
policy_filter_ma24_diff = 0.03
policy_filter_ma30_diff = 0.03
policy_filter_ma52_diff = 0.03
policy_filter_ma60_diff = 0.03

policy_filter_turn = 3.0
policy_filter_lb = 1.0
b_weekly_condition = True
s_filter_date = ""

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

def set_policy_filter_turn(turn=3.0):
    global policy_filter_turn
    # logger.info("设置前换手率：", policy_filter_turn, ", 目标值：", turn)
    policy_filter_turn = turn
    # logger.info("设置后换手率：", policy_filter_turn)

def set_policy_filter_lb(lb=1.0):
    global policy_filter_lb
    # logger.info("设置前量比：", policy_filter_lb, ", 目标值：", lb)
    policy_filter_lb = lb
    # logger.info("设置后量比：", policy_filter_lb)

def set_weekly_condition(b_weekly):
    global b_weekly_condition
    b_weekly_condition = b_weekly

def set_filter_date(date):
    global s_filter_date
    s_filter_date = date

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

def get_policy_filter_turn():
    return policy_filter_turn

def get_policy_filter_lb():
    return policy_filter_lb

def get_weekly_condition():
    return b_weekly_condition

def get_filter_date():
    return s_filter_date

def columns_check(df_data, col_names: Sequence[str]) -> bool:
    # logger.info("df_data.columns:")
    # logger.info(df_data.columns)
    # logger.info(col_names)
    for arg in col_names:
        if arg in df_data.columns:
            continue
        else:
            logger.info(f"错误，列不存在：{arg}")
            return False
    return True

def daily_data_check(df_daily_data):
    pass

# 未验证暂不考虑 ，暂无用 
def daily_ma52_filter(df_daily_data):
    '''
        筛选逻辑：最新收盘价无限接近MA52。缺点：未分辨零轴上方还是下方，暂不考虑。
    '''
    if df_daily_data.empty:
        return False

    day_close = 0.0
    day_ma52 = 0.0
    day_turn = 0.0
    day_lb = 0.0

    # 检查列是否存在
    if columns_check(df_daily_data, ('日期', '收盘', 'MA52', '换手率', '量比5日')):
    # if '收盘' in df_daily_data.columns and 'MA52' in df_daily_data.columns and '换手率' in df_daily_data.columns and '量比5日' in df_daily_data.columns:
        last_day_row = df_daily_data.tail(1)
        day_close = last_day_row['收盘'].item()
        day_ma52 = last_day_row['MA52'].item()
        day_turn = last_day_row['换手率'].item()
        day_lb = last_day_row['量比5日'].item()
    else:
        logger.info("错误：日线数据必要的列不存在")
        logger.info("可用列：", df_daily_data.columns.tolist())
        return False  # 或者处理错误情况
    
    day_diff = day_ma52 * policy_filter_ma52_diff
    # logger.info(f"day_close: {day_close}, day_ma52: {day_ma52}, diff: {day_diff}, day_turn>: {day_turn}, day_lb: {day_lb}")

    # 修改后条件判断
    if (abs(day_close - day_ma52) < day_diff) and (day_turn > policy_filter_turn) and (day_lb > policy_filter_lb):
    # 执行逻辑
    # if (week_stock_data.tail(1)['收盘'] > week_stock_data.tail(1)['MA52']) and (abs(day_stock_data.tail(1)['收盘'] - day_stock_data.tail(1)['MA52']) < day_stock_data.tail(1)['MA52'] * 1.1):
        # logger.info("符合日线MA52筛选")
        return True
    else:
        # logger.info("不符合多空逻辑")
        return False

# 策略待优化 ，暂无用 
def daily_and_weekly_ma52_filter(df_daily_data, df_weekly_data):
    '''
        筛选逻辑：周线在零轴上方保证中期趋势，日线最新收盘价无限接近零轴。缺点同上，未区分零轴上方下方，存在零轴纠缠情况。
    '''
    if df_daily_data.empty or df_weekly_data.empty:
        return False
    
    day_close = 0.0
    day_ma52 = 0.0
    day_turn = 0.0
    day_lb = 0.0

    if columns_check(df_daily_data, ('日期', '收盘', 'MA52', '换手率', '量比5日')):
        last_day_row = df_daily_data.tail(1)
        day_close = last_day_row['收盘'].item()
        day_ma52 = last_day_row['MA52'].item()
        day_turn = last_day_row['换手率'].item()
        day_lb = last_day_row['量比5日'].item()
    else:
        logger.info("错误：【日线】数据必要的列不存在")
        return False

    week_close = 0.0
    week_ma52 = 0.0
    if columns_check(df_weekly_data, ('日期', '收盘', 'MA52')):
        last_week_row = df_weekly_data.tail(1)
        week_close = last_week_row['收盘'].item()
        week_ma52 = last_week_row['MA52'].item()
    else:
        logger.info("错误：【周线】数据必要的列不存在")
        return False

    day_diff = day_ma52 * policy_filter_ma52_diff
    # logger.info(f"day_close: {day_close}, day_ma52: {day_ma52}, diff: {day_diff}, day_turn>: {day_turn}, day_lb: {day_lb}")
    # logger.info(f"week_close: {week_close}, week_ma52: {week_ma52}")
    if week_close > week_ma52 and (abs(day_close - day_ma52) < day_diff) and (day_turn > policy_filter_turn) and (day_lb > policy_filter_lb):
        # logger.info("符合日线&周线MA52筛选")
        return True
    else:
        return False
    
# 策略待优化 ，暂无用 
def daily_ma52_ma24_filter(df_daily_data, df_weekly_data, isUp=False):
    if df_daily_data.empty or df_weekly_data.empty:
        return False
    
    day_close = 0.0
    day_dea = 0.0
    day_ma24 = 0.0
    day_ma52 = 0.0
    day_turn = 0.0
    day_lb = 0.0
    if columns_check(df_daily_data, ('日期', '收盘', 'DEA', 'MA24', 'MA52', '换手率', '量比5日')):
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
    if columns_check(df_weekly_data, ('日期', '收盘', 'MA52')):
        last_week_row = df_weekly_data.tail(1)
        week_close = last_week_row['收盘'].item()
        week_ma52 = last_week_row['MA52'].item()
    else:
        return False

    day_diff = day_ma52 * policy_filter_ma52_diff
    # logger.info(f"day_close: {day_close}, day_dea: {day_dea}, day_ma24: {day_ma24}, day_ma52: {day_ma52}, diff: {day_diff}, day_turn>: {day_turn}, day_lb: {day_lb}")
    # logger.info(f"week_close: {week_close}, week_ma52: {week_ma52}")

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
        # logger.info("符合日线MA24&MA52筛选")
        return True
    
    return False


# -------------------------------------------------------------日线零轴上方策略-------------------------------------------------------------------

# 零轴上方MA52选股法
def daily_up_ma52_filter(df_daily_data, df_weekly_data):
    '''
        筛选逻辑：零轴上方回踩MA52筛选法，最好是第一次回踩MA24(回踩MA60也可考虑)。
        进场逻辑：最新收盘价位于MA24、MA60之间，即收盘价小于MA24，大于MA52或MA60，且下面30（或15）分钟级别零轴下方出现底背离或下跌动能不足形态，或者站上突破15分钟MA52压力，亦或者等15分钟DEA突破零轴，回踩15分钟MA5或MA10，才满足进场条件
        止盈位：有效反弹看前高
        止损位：有效跌破日线MA52或MA60清仓离场，等待日线零轴下方或大级别的零轴上方机会。
    '''
    if df_daily_data.empty or df_weekly_data.empty:
        logger.info("日线或周线数据为空！")
        return False

    if not columns_check(df_daily_data, ('日期', '收盘', 'DIF', 'DEA', 'MA5', 'MA10', 'MA24', 'MA30',  'MA52', 'MA60', '换手率', '量比5日')):
        logger.info("日线列名不存在！")
        return False

    last_day_row = df_daily_data.tail(1)
    day_close = last_day_row['收盘'].item()
    day_dif = last_day_row['DIF'].item()
    day_dea = last_day_row['DEA'].item()
    day_ma5 = last_day_row['MA5'].item()
    day_ma10 = last_day_row['MA10'].item()
    # day_ma20 = last_day_row['MA20'].item()
    day_ma24 = last_day_row['MA24'].item()
    day_ma30 = last_day_row['MA30'].item()
    day_ma52 = last_day_row['MA52'].item()
    day_ma60 = last_day_row['MA60'].item()
    day_turn = last_day_row['换手率'].item()
    day_lb = last_day_row['量比5日'].item()


    if not columns_check(df_weekly_data, ('日期', '收盘', 'DEA', 'MA52')):
        logger.info("周线列名不存在！")
        return False
    
    last_week_row = df_weekly_data.tail(1)
    week_close = last_week_row['收盘'].item()
    week_dea = last_week_row['DEA'].item()
    week_ma52 = last_week_row['MA52'].item()


    # day_diff = day_ma52 * policy_filter_ma52_diff
    # logger.info(f"day_close: {day_close}, day_dea: {day_dea}, day_ma24: {day_ma24}, day_ma52: {day_ma52}, diff: {day_diff}, day_turn>: {day_turn}, day_lb: {day_lb}")
    # logger.info(f"week_close: {week_close}, week_ma52: {week_ma52}")

    b_ret = (day_turn > policy_filter_turn) and (day_lb > policy_filter_lb)
    b_ret_2 = (week_close > week_ma52 and week_dea > 0) if b_weekly_condition else True

    b_ret_3 = day_dea > 0 and day_dif > 0
    b_ret_4 = (day_close >= day_ma52) and (day_close <= day_ma24) and day_close <= day_ma5
    b_ret_5 = day_ma5 <= day_ma10 and day_ma5 <= day_ma24 and day_ma5 >= day_ma52 and day_ma24 >= day_ma52

    # 优化判断：MA5大于MA52；近2根k线收盘价均大于MA52，小于MA24；

    if b_ret and b_ret_2 and b_ret_3 and b_ret_4 and b_ret_5:
        # logger.info("符合【日线零轴上方MA52】筛选")
        return True
    
    # logger.info("不符合【日线零轴上方MA52】筛选")
    # logger.info(f"b_ret: {b_ret}, b_ret_2: {b_ret_2}, b_ret_3: {b_ret_3}, b_ret_4: {b_ret_4}, b_ret_5: {b_ret_5}")
    # logger.info(f"day_turn: {day_turn}, day_lb: {day_lb}")
    # logger.info(f"day_dea: {day_dea}, day_close: {day_close}, day_ma52: {day_ma52}, day_ma60: {day_ma60}, day_ma30: {day_ma30}")
    # logger.info(f"day_ma5: {day_ma5}, day_ma24: {day_ma24}, day_ma52: {day_ma52}, day_ma60: {day_ma60}")
    return False

# 零轴上方MA24选股法
def daily_up_ma24_filter(df_daily_data, df_weekly_data):
    '''
        筛选逻辑：零轴上方回踩MA24筛选法，最好是第一次回踩MA24(回踩MA20、30均可考虑)。和daily_ma52_ma24_filter稍有重复。
        进场逻辑：最新收盘价无限接近MA24，且收盘价小于MA5或小于MA10，且下面15(或7.5)分钟级别零轴下方出现底背离或下跌动能不足形态，或者站上突破15分钟MA52压力，亦或者等15分钟DEA突破零轴，回踩15分钟MA5或MA10，才满足进场条件
        止盈位：有效反弹看前高
        止损位：有效跌破日线MA24或MA30清仓离场，等待日线MA52机会。
    '''
    if df_daily_data.empty or df_weekly_data.empty:
        return False
    
    
    if not columns_check(df_daily_data, ('日期', '收盘', 'DIF', 'DEA', 'MA5', 'MA10', 'MA20', 'MA24', 'MA30', 'MA52', '换手率', '量比5日')):
        return False
    
    last_day_row = df_daily_data.tail(1)
    day_close = last_day_row['收盘'].item()
    day_dif = last_day_row['DIF'].item()
    day_dea = last_day_row['DEA'].item()
    day_ma5 = last_day_row['MA5'].item()
    day_ma10 = last_day_row['MA10'].item()
    day_ma20 = last_day_row['MA20'].item()
    day_ma24 = last_day_row['MA24'].item()
    day_ma30 = last_day_row['MA30'].item()
    day_ma52 = last_day_row['MA52'].item()
    day_turn = last_day_row['换手率'].item()
    day_lb = last_day_row['量比5日'].item()


    if not columns_check(df_weekly_data, ('日期', '收盘', 'MA52')):
        return False
    
    last_week_row = df_weekly_data.tail(1)
    week_close = last_week_row['收盘'].item()
    week_ma52 = last_week_row['MA52'].item()

    # day_diff = day_ma52 * policy_filter_ma52_diff
    # logger.info(f"day_close: {day_close}, day_dea: {day_dea}, day_ma24: {day_ma24}, day_ma52: {day_ma52}, diff: {day_diff}, day_turn>: {day_turn}, day_lb: {day_lb}")
    # logger.info(f"week_close: {week_close}, week_ma52: {week_ma52}")

    b_ret = (day_turn > policy_filter_turn) and (day_lb > policy_filter_lb)
    b_ret_2 = (week_close > week_ma52) if b_weekly_condition else True

    b_ret_3 = day_dea > 0 and day_dif > 0
    b_ret_4 = (day_close >= day_ma20 or day_close >= day_ma24) and (day_close <= day_ma5 or day_close <= day_ma10)# abs(day_close - day_ma24) < day_ma24 * policy_filter_ma24_diff
    b_ret_5 = day_ma5 <= day_ma10 and day_ma10 >= day_ma24 and day_ma5 >= day_ma24 and day_ma24 > day_ma52

    if b_ret and b_ret_2 and b_ret_3 and b_ret_4 and b_ret_5:
        # logger.info("符合【日线零轴上方MA24】筛选")
        return True
    
    return False

# 零轴上方MA5选股法
def daily_up_ma5_filter(df_daily_data):
    pass

# 零轴上方MA10选股法
def daily_up_ma10_filter(df_daily_data):
    '''
        筛选逻辑：零轴上方，回踩MA10
        进场逻辑：最新收盘价位于MA5、MA10之间，次日必须低开，且接近30或60分钟MA52，且30或60分钟DEA大于0，且下面5分钟出现底背离或下跌动能不足，才满足进场条件。
        止盈：指数看到30或60分钟背离或上涨动能不足离场止盈
        止损：有效跌破30或60分钟MA52，且对应的DEA下穿零轴清仓止损
    '''
    if df_daily_data.empty:
        return False

    if not columns_check(df_daily_data, ('日期', '收盘', 'DEA', 'MA5', 'MA10', 'MA24', 'MA52', '换手率', '量比5日')):
        return False
    
    last_day_row = df_daily_data.tail(1)
    day_close = last_day_row['收盘'].item()
    day_dea = last_day_row['DEA'].item()
    day_ma5 = last_day_row['MA5'].item()
    day_ma10 = last_day_row['MA10'].item()
    day_ma24 = last_day_row['MA24'].item()
    day_ma52 = last_day_row['MA52'].item()
    day_turn = last_day_row['换手率'].item()
    day_lb = last_day_row['量比5日'].item()

    b_ret = (day_turn > policy_filter_turn) and (day_lb > policy_filter_lb)
    b_ret_2 = day_dea > 0
    b_ret_3 = day_ma24 > day_ma52 and day_ma10 > day_ma24 and day_ma5 > day_ma10
    b_ret_4 = day_close > day_ma10 and day_close < day_ma5# abs(day_close - day_ma10) < day_ma10 * policy_filter_ma10_diff

    day_ma10_diff = day_ma10 * policy_filter_ma10_diff
    # logger.info(f"day_close: {day_close}, day_dea: {day_dea}, day_ma10: {day_ma10}, day_ma24: {day_ma24}, day_ma52: {day_ma52}, day_ma10_diff: {day_ma10_diff}, day_turn>: {day_turn}, day_lb: {day_lb}")

    if b_ret and b_ret_2 and b_ret_3 and b_ret_4:
        # logger.info("符合【日线零轴上方MA10】筛选")
        return True
    
    return False

# 情况被上面MA24选股法包括，不再使用
def daily_up_ma20_filter(df_daily_data):
    '''
        筛选逻辑：零轴上方，回踩MA20
        进场逻辑：最新收盘价位于MMA10、MA20之间，次日必须低开，且接近30或60分钟MA52，且30或60分钟DEA大于0，且下面5、10分钟出现底背离或下跌动能不足，才满足进场条件。
        止盈：指数看到30或60分钟背离或上涨动能不足离场止盈
        止损：有效跌破30或60分钟MA52，且对应的DEA下穿零轴清仓止损
    '''
    if df_daily_data.empty:
        return False
    
    day_close = 0.0
    day_dea = 0.0
    day_ma20 = 0.0
    day_ma24 = 0.0
    day_ma52 = 0.0
    day_turn = 0.0
    day_lb = 0.0
    if not columns_check(df_daily_data, ('日期', '收盘', 'DEA', 'MA5', 'MA10', 'MA20', 'MA24', 'MA52', '换手率', '量比5日')):
        return False
    
    last_day_row = df_daily_data.tail(1)
    day_close = last_day_row['收盘'].item()
    day_dea = last_day_row['DEA'].item()
    day_ma5 = last_day_row['MA5'].item()
    day_ma10 = last_day_row['MA10'].item()
    day_ma20 = last_day_row['MA20'].item()
    day_ma24 = last_day_row['MA24'].item()
    day_ma52 = last_day_row['MA52'].item()
    day_turn = last_day_row['换手率'].item()
    day_lb = last_day_row['量比5日'].item()

    b_ret = (day_turn > policy_filter_turn) and (day_lb > policy_filter_lb)
    b_ret_2 = day_dea > 0
    b_ret_3 = day_close >= day_ma20 and (day_close <= day_ma5 and day_close <= day_ma10)# abs(day_close - day_ma24) < day_ma24 * policy_filter_ma24_diff
    b_ret_4 = day_ma5 <= day_ma10 and day_ma10 > day_ma24 and day_ma5 > day_ma24 and day_ma24 > day_ma52


    # day_ma20_diff = day_ma20 * policy_filter_ma20_diff
    # logger.info(f"day_close: {day_close}, day_dea: {day_dea}, day_ma20: {day_ma20}, day_ma24: {day_ma24}, day_ma52: {day_ma52}, day_ma20_diff: {day_ma20_diff}, day_turn>: {day_turn}, day_lb: {day_lb}")

    if b_ret and b_ret_2 and b_ret_3 and b_ret_4:
        # logger.info("符合【日线零轴上方MA20】筛选")
        return True
    
    return False


# -------------------------------------------------------------日线零轴下方策略-------------------------------------------------------------------
def daily_down_between_ma24_ma52_filter(df_daily_data, df_weekly_data):
    '''
        筛选逻辑：周线在零轴上方确保中期趋势；日线零轴下方，MA24 < MA52 or MA24 < MA60, MA52 <= MA60，且最新收盘价位于MA24、MA60之间，即日线最新收盘价大于MA24，小于MA52或MA60
        进场逻辑：回踩MA24进场。最好是前面已经过多个120分钟级别的单位调整周期调整，做上穿日线零轴趋势行情。可参考下面15分钟底背离或下跌动能不足进场。
        止盈：趋势行情，有效站上日线零轴上方后参考前高止盈。
        止损：跌破日线MA24清仓离场。也可参考下面60分钟MA52,跌破60分钟MA52离场。
    '''
    if df_daily_data.empty or df_weekly_data.empty:
        return False
    
    if not columns_check(df_daily_data, ('日期', '收盘', 'DEA', 'MA24', 'MA52', 'MA60', '换手率', '量比5日')):
        return False
    
    if s_filter_date == '':
        last_day_row = df_daily_data.tail(1)
    else:
        # 直接筛选出指定日期的数据并取最后一行
        filtered_data = df_daily_data[df_daily_data['日期'] == s_filter_date]
        if not filtered_data.empty:
            last_day_row = filtered_data.tail(1)
            # 然后可以安全地访问具体值
            # day_close = last_day_row['收盘'].item()
        else:
            # 处理找不到指定日期的情况
            logger.info(f"未找到日期 {s_filter_date} 的数据")
            return False  # 或其他适当的处理
    
    day_close = last_day_row['收盘'].item()
    day_dea = last_day_row['DEA'].item()
    # day_ma5 = last_day_row['MA5'].item()
    # day_ma10 = last_day_row['MA10'].item()
    # day_ma20 = last_day_row['MA20'].item()
    day_ma24 = last_day_row['MA24'].item()
    # day_ma30 = last_day_row['MA30'].item()
    day_ma52 = last_day_row['MA52'].item()
    day_ma60 = last_day_row['MA60'].item()
    day_turn = last_day_row['换手率'].item()
    day_lb = last_day_row['量比5日'].item()


    if not columns_check(df_weekly_data, ('日期', '收盘', 'DEA', 'MA52')):
        return False
    
    if s_filter_date == '':
        last_week_row = df_weekly_data.tail(1)
    else:
        # 筛选出日期小于等于s_filter_date的所有行，然后取最后一行（因为日期是升序排列）
        filtered_data = df_weekly_data[df_weekly_data['日期'] <= s_filter_date]
        if not filtered_data.empty:
            last_week_row = filtered_data.iloc[-1]  # 获取最后一行，即最接近s_filter_date的那一行
            # logger.info(f"last_week_row的日期: {last_week_row['日期']}")
        else:
            # 处理没有找到符合条件的行的情况
            last_week_row = None
            logger.info(f"未找到日期 {s_filter_date} 前的周线数据")
            return False

    week_close = last_week_row['收盘'].item()
    week_dea = last_week_row['DEA'].item()
    week_ma52 = last_week_row['MA52'].item()
        
    # day_diff = day_ma52 * policy_filter_ma52_diff
    # logger.info(f"day_close: {day_close}, day_dea: {day_dea}, day_ma24: {day_ma24}, day_ma52: {day_ma52}, diff: {day_diff}, day_turn>: {day_turn}, day_lb: {day_lb}")
    # logger.info(f"week_close: {week_close}, week_ma52: {week_ma52}")

    b_ret = (day_turn > policy_filter_turn) and (day_lb > policy_filter_lb)
    b_ret_2 = (week_close > week_ma52 and week_dea > 0) if b_weekly_condition else True

    b_ret_3 = day_dea < 0
    b_ret_4 = (day_close <= day_ma52 or day_close <= day_ma60) and (day_close >= day_ma24)
    b_ret_5 = (day_ma24 < day_ma52 or day_ma24 < day_ma60) and day_ma52 <= day_ma60

    if b_ret and b_ret_2 and b_ret_3 and b_ret_4 and b_ret_5:
        # logger.info("符合【日线零轴下方MA52】筛选")
        return True
    
    return False

def daily_down_between_ma5_ma52_filter(df_daily_data, df_weekly_data):
    '''
        筛选逻辑：周线在零轴上方确保中期趋势；日线零轴下方，MA5 < MA52 or MA6 < MA60, MA52 <= MA60，且最新收盘价位于MA5、MA60之间，即日线最新收盘价大于MA5，小于MA52或MA60
        进场逻辑：回踩MA5进场。最好是前面已经过多个30、60分钟级别的单位调整周期调整，且处于日线下跌线段第一个单位调整周期中，做日线零轴下方归零轴的超跌反弹行情。可参考下面15分钟底背离或下跌动能不足进场。
        止盈：参考日线MA52或MA60附近止盈。
        止损：跌破日线MA5或底部区间低点清仓离场。也可参考下面30分钟MA52,跌破30分钟MA52离场。
    '''
    if df_daily_data.empty or df_weekly_data.empty:
        return False
    
    if not columns_check(df_daily_data, ('日期', '收盘', 'DEA', 'MA5', 'MA10', 'MA52', 'MA60', '换手率', '量比5日')):
        return False

    last_day_row = df_daily_data.tail(1)
    day_close = last_day_row['收盘'].item()
    day_dea = last_day_row['DEA'].item()
    day_ma5 = last_day_row['MA5'].item()
    day_ma10 = last_day_row['MA10'].item()
    # day_ma20 = last_day_row['MA20'].item()
    # day_ma24 = last_day_row['MA24'].item()
    # day_ma30 = last_day_row['MA30'].item()
    day_ma52 = last_day_row['MA52'].item()
    day_ma60 = last_day_row['MA60'].item()
    day_turn = last_day_row['换手率'].item()
    day_lb = last_day_row['量比5日'].item()


    if not columns_check(df_weekly_data, ('日期', '收盘', 'DEA', 'MA52')):
        return False

    last_week_row = df_weekly_data.tail(1)
    week_close = last_week_row['收盘'].item()
    week_dea = last_week_row['DEA'].item()
    week_ma52 = last_week_row['MA52'].item()
        
    # day_diff = day_ma52 * policy_filter_ma52_diff
    # logger.info(f"day_close: {day_close}, day_dea: {day_dea}, day_ma24: {day_ma24}, day_ma52: {day_ma52}, diff: {day_diff}, day_turn>: {day_turn}, day_lb: {day_lb}")
    # logger.info(f"week_close: {week_close}, week_ma52: {week_ma52}")

    b_ret = (day_turn > policy_filter_turn) and (day_lb > policy_filter_lb)
    b_ret_2 = (week_close > week_ma52 and week_dea > 0) if b_weekly_condition else True

    b_ret_3 = day_dea < 0
    b_ret_4 = (day_close <= day_ma52 or day_close <= day_ma60) and (day_close >= day_ma5 or day_close >= day_ma10)
    b_ret_5 = (day_ma5 < day_ma52 or day_ma5 < day_ma60) and day_ma52 <= day_ma60

    if b_ret and b_ret_2 and b_ret_3 and b_ret_4 and b_ret_5:
        # logger.info("符合【日线零轴下方MA5】筛选")
        return True
    
    return False

def daily_down_breakthrough_ma24_filter(df_daily_data):
    '''
        日线零轴下方MA24突破筛选
        筛选逻辑：日线MACD的diff、dea均小于0；最新k线收盘价大于MA24，小于MA52；MA5必须要金叉MA10，MA24小于MA52
        进场逻辑：回踩MA24进场。
        止盈：短期看日线MA52压力止盈；若120分钟经过多个单位调整周期调整，且单位调整周期间已明显背离或下跌动能不足，则可做突破日线MA52的趋势行情。
        止损：跌破MA24清仓离场。
    '''
    if df_daily_data.empty:
        return False
    
    if not columns_check(df_daily_data, ('日期', '收盘', 'DIF', 'DEA', 'MA5', 'MA10', 'MA24', 'MA52', 'MA60', '换手率', '量比5日')):
        return False
    
    last_day_row = df_daily_data.tail(1)
    day_close = last_day_row['收盘'].item()
    day_diff = last_day_row['DIF'].item()
    day_dea = last_day_row['DEA'].item()
    day_ma5 = last_day_row['MA5'].item()
    day_ma10 = last_day_row['MA10'].item()
    # day_ma20 = last_day_row['MA20'].item()
    day_ma24 = last_day_row['MA24'].item()
    # day_ma30 = last_day_row['MA30'].item()
    day_ma52 = last_day_row['MA52'].item()
    day_ma60 = last_day_row['MA60'].item()
    day_turn = last_day_row['换手率'].item()
    day_lb = last_day_row['量比5日'].item()

    b_ret = day_diff < 0 and day_dea < 0
    b_ret_2 = day_close >= day_ma24 and day_close <= day_ma60
    b_ret_3 = day_ma5 >= day_ma10 and day_ma24 < day_ma52
    if b_ret and b_ret_2 and b_ret_3:
        # logger.info("符合【日线零轴下方MA24突破】筛选")
        return True
    
    return False


def daily_down_breakthrough_ma52_filter(df_daily_data):
    '''
        日线零轴下方MA52突破筛选
        筛选逻辑：日线MACD的dea小于0；最新k线收盘价大于MA52且与MA52的差值小于MA52*0.1；MA5必须要金叉MA10，MA24小于MA52
        进场逻辑：回踩MA52进场。
        止盈：短期看上面级别（2日、3日、周线）压力止盈；若成功突破上面级别压力，则可做有效反弹的趋势行情。
        止损：跌破MA52或MA24清仓离场。
    '''
    if df_daily_data.empty:
        return False
    
    if not columns_check(df_daily_data, ('日期', '收盘', 'DIF', 'DEA', 'MA5', 'MA10', 'MA24', 'MA52', 'MA60', '换手率', '量比5日')):
        return False
    
    last_day_row = df_daily_data.tail(1)
    day_close = last_day_row['收盘'].item()
    day_diff = last_day_row['DIF'].item()
    day_dea = last_day_row['DEA'].item()
    day_ma5 = last_day_row['MA5'].item()
    day_ma10 = last_day_row['MA10'].item()
    # day_ma20 = last_day_row['MA20'].item()
    day_ma24 = last_day_row['MA24'].item()
    # day_ma30 = last_day_row['MA30'].item()
    day_ma52 = last_day_row['MA52'].item()
    day_ma60 = last_day_row['MA60'].item()
    day_turn = last_day_row['换手率'].item()
    day_lb = last_day_row['量比5日'].item()

    b_ret = day_dea <= 0
    b_ret_2 = day_close >= day_ma52 and (day_close - day_ma52) <= day_ma52 * 0.1
    b_ret_3 = day_ma5 >= day_ma10 and day_ma5 <= day_ma52 and day_ma24 < day_ma52
    if b_ret and b_ret_2 and b_ret_3:
        # logger.info("符合【日线零轴下方MA52突破】筛选")
        return True
    
    return False

def daily_down_double_bottom_filter(df_daily_data, df_weekly_data, b_weekly_filter=True):
    '''
        日线零轴下方双底筛选
        筛选逻辑：
            日线MACD的dea小于0；
            往回找dea第一次下穿零轴k线、diff第一次下穿零轴k线，得到dea第一次下穿零轴到当前位置区间；
            遍历区间，用收盘价更新最低值及其对应k线、MACD值；
            判断：
                当前收盘价大于等于最低值
                当前收盘价小于MA10
                MA5小于等于MA24，MA24小于MA52

        进场逻辑：回踩MA24或前低进场。
        止盈：短期看日线MA52压力止盈；若成功突破日线MA52压力，则可做有效反弹的趋势行情。
        止损：跌破前低清仓离场。
    '''
    if df_daily_data.empty or df_weekly_data.empty:
        return False
    
    # logger.info(df_daily_data.tail(10))
    
    if not columns_check(df_daily_data, ('日期', '收盘', 'DIF', 'DEA', 'MA5', 'MA10', 'MA24', 'MA52', 'MA60', '换手率', '量比5日')):
        return False
    
    last_day_row = df_daily_data.tail(1)
    day_close = last_day_row['收盘'].item()
    day_diff = last_day_row['DIF'].item()
    day_dea = last_day_row['DEA'].item()
    day_ma5 = last_day_row['MA5'].item()
    day_ma10 = last_day_row['MA10'].item()
    # day_ma20 = last_day_row['MA20'].item()
    day_ma24 = last_day_row['MA24'].item()
    # day_ma30 = last_day_row['MA30'].item()
    day_ma52 = last_day_row['MA52'].item()
    day_ma60 = last_day_row['MA60'].item()
    day_turn = last_day_row['换手率'].item()
    day_lb = last_day_row['量比5日'].item()

    if day_diff >= 0 or day_dea >= 0 and day_ma24 >= day_ma52:
        return False
    
    if not columns_check(df_weekly_data, ('日期', '收盘', 'DEA', 'MA52')):
        return False
    
    last_week_row = df_weekly_data.tail(1)
    week_close = last_week_row['收盘'].item()
    week_dea = last_week_row['DEA'].item()
    week_ma52 = last_week_row['MA52'].item()
    # week_ma60 = last_week_row['MA52'].item()  # 周线没有维护MA60
        

    # logger.info("find_lowest_after_dea_cross_below_zero")
    lowest_result = find_lowest_after_dea_cross_below_zero(df_daily_data)
    lowest_value = lowest_result['lowest_value']
    lowest_date = lowest_result['lowest_date']
    neck_line = lowest_result['neckline']

    b_ret = day_diff <= 0 and day_dea < 0 and day_turn > policy_filter_turn and day_lb > policy_filter_lb
    b_ret_2 = day_close >= lowest_value and day_close <= day_ma10 and day_close < day_ma24 and day_close < day_ma52
    b_ret_3 = day_ma5 <= day_ma24 and day_ma24 < day_ma52
    b_ret_4 = neck_line >= day_ma10
    
    b_ret_5 = (week_dea >= 0) if b_weekly_condition else True

    if b_ret and b_ret_2 and b_ret_3 and b_ret_4 and b_ret_5:
        code = last_day_row['股票代码'].item()
        logger.info(f"股票代码【{code}】符合【日线零轴下方双底】筛选, 最低点：{lowest_value}, 最低点日期：{lowest_date}, 局部高点：{neck_line}")
        return True
    
    return False

def find_lowest_after_dea_cross_below_zero(df_daily_data):
    '''
    从最后的日期k线开始往前遍历，找到dea最近一次下穿零轴（小于0）的位置，
    然后从该位置往后遍历，判断该位置到最后这段区间内的日k的最低值
    
    Args:
        df_daily_data (pandas.DataFrame): 日线股票数据
        
    Returns:
        dict: 包含以下键值的字典：
            - found (bool): 是否找到DEA下穿零轴的情况
            - cross_index (int): DEA下穿零轴的位置索引
            - lowest_value (float): 区间内的最低值
            - lowest_index (int): 最低值的位置索引
            - lowest_date (str): 最低值对应的日期
    '''
    # 初始化返回结果
    result = {
        'found': False,
        'cross_index': -1,
        'lowest_value': float('inf'),
        'lowest_index': -1,
        'lowest_date': None,
        'neckline': float('inf')
    }
    
    # 检查数据是否为空
    if df_daily_data.empty:
        logger.info("日线数据为空")
        return result
    
    # 检查是否包含必要的列
    if not columns_check(df_daily_data, ('股票代码', 'DEA', '最低')):
        logger.info("缺少必要的列：股票代码 或 DEA 或 最低")
        return result
    
    # 因为数据已按日期排序（最后一行是最新的日期），所以直接使用原数据
    df_data = df_daily_data
    
    # 从最后的日期开始往前遍历，找到DEA最近一次下穿零轴的位置
    cross_index = -1
    for i in range(len(df_data) - 1, 0, -1):  # 从倒数第二个开始，避免索引越界
        current_dea = df_data.iloc[i]['DEA']
        previous_dea = df_data.iloc[i-1]['DEA']
        
        # 判断是否为下穿零轴：当前DEA<=0 且 前一个DEA>0
        if current_dea <= 0 and previous_dea > 0:
            cross_index = i
            break
    
    # 如果没有找到下穿零轴的情况
    if cross_index == -1:
        # logger.info("未找到DEA下穿零轴的情况")
        return result
    
    # 从下穿零轴的位置到最后一个位置，查找最低值
    lowest_value = float('inf')
    lowest_index = -1
    
    for i in range(cross_index, len(df_data)):
        low_price = df_data.iloc[i]['最低']
        if low_price < lowest_value:
            lowest_value = low_price
            lowest_index = i

    # 寻找两个底部之间的高点(颈线)
    intermediate_high = max(df_data['收盘'][lowest_index:len(df_data)])
            
    # 检查颈线是否明显高于底部
    if (intermediate_high - lowest_value) / lowest_value < 0.03:  # 至少3%的颈线高度
        return result
        
    
    # 设置返回结果
    result['found'] = True
    result['cross_index'] = cross_index
    result['lowest_value'] = lowest_value
    result['lowest_index'] = lowest_index
    result['lowest_date'] = df_data.index[lowest_index] if lowest_index >= 0 else None
    result['neckline'] = intermediate_high
    
    # code = df_data.iloc[-1]['股票代码']
    # logger.info(f"找到 {code} DEA下穿零轴位置: {cross_index}, 区间最低值: {lowest_value}, 最低值位置: {lowest_index}")
    
    return result


def daily_down_double_bottom_filter_old(df_daily_data):
    '''
        日线零轴下方双底筛选
        筛选逻辑：
            1. 日线MACD的dea小于0；
            2. 存在双底形态：
               - 两个明显的低点
               - 两个低点之间的反弹高点（颈线）
               - 第二个低点不跌破第一个低点
               - 当前价格突破颈线
            3. 技术指标满足：
               - MA5小于等于MA24，MA24小于MA52

        进场逻辑：突破颈线进场。
        止盈：短期看日线MA52压力止盈；若成功突破日线MA52压力，则可做有效反弹的趋势行情。
        止损：跌破第二个底部清仓离场。
    '''
    if df_daily_data.empty:
        return False
    
    if not columns_check(df_daily_data, ('日期', '收盘', 'DIF', 'DEA', 'MA5', 'MA10', 'MA24', 'MA52', 'MA60', '换手率', '量比5日')):
        return False
    
    last_day_row = df_daily_data.tail(1)
    day_close = last_day_row['收盘'].item()
    day_diff = last_day_row['DIF'].item()
    day_dea = last_day_row['DEA'].item()
    day_ma5 = last_day_row['MA5'].item()
    day_ma10 = last_day_row['MA10'].item()
    day_ma24 = last_day_row['MA24'].item()
    day_ma52 = last_day_row['MA52'].item()
    day_ma60 = last_day_row['MA60'].item()
    day_turn = last_day_row['换手率'].item()
    day_lb = last_day_row['量比5日'].item()

    # 基本条件检查
    if day_dea >= 0 or day_ma24 >= day_ma52:
        return False

    # 检测双底形态
    double_bottom_result = detect_double_bottom(df_daily_data)
    
    if not double_bottom_result['found']:
        return False
    
    neckline = double_bottom_result['neckline']
    first_low = double_bottom_result['first_low']
    second_low = double_bottom_result['second_low']
    first_idx = double_bottom_result['first_low_idx']
    second_idx = double_bottom_result['second_low_idx']
    
    # 判断当前价格是否突破颈线且未突破MA52
    b_ret_1 = day_close < neckline and day_close < day_ma24 and day_close < day_ma52
    # 第二个底部不跌破第一个底部
    b_ret_2 = second_low >= first_low * 0.99  # 允许1%的误差
    # 均线排列正确
    b_ret_3 = day_ma5 <= day_ma24 and day_ma24 < day_ma52
    # 成交量条件
    # b_ret_4 = day_turn > policy_filter_turn and day_lb > policy_filter_lb
    
    if b_ret_1 and b_ret_2 and b_ret_3:
        code = df_daily_data.iloc[-1]['股票代码']
        logger.info(f"日线零轴下方双底筛选通过：{code}, 第一个低点：{first_low}， 索引：{first_idx}, 第二个低点：{second_low}，索引：{second_idx}")
        return True
    
    return False

def detect_double_bottom(df_data, min_distance=10, max_distance=120):
    '''
    检测双底形态
    
    Args:
        df_data: 股票数据
        min_distance: 两个底部之间的最小距离(周期)
        max_distance: 两个底部之间的最大距离(周期)
        
    Returns:
        dict: 双底检测结果
    '''
    result = {
        'found': False,
        'first_low': None,
        'second_low': None,
        'first_low_idx': None,
        'second_low_idx': None,
        'neckline': None
    }
    
    if len(df_data) < 30:  # 数据太少无法判断形态
        return result
    
    # 从最后的日期开始往前遍历，找到DEA最近一次下穿零轴的位置
    cross_index = -1
    for i in range(len(df_data) - 1, 0, -1):  # 从倒数第二个开始，避免索引越界
        current_dea = df_data.iloc[i]['DEA']
        previous_dea = df_data.iloc[i-1]['DEA']
        
        # 判断是否为下穿零轴：当前DEA<=0 且 前一个DEA>0
        if current_dea <= 0 and previous_dea > 0:
            cross_index = i
            break
    
    # 如果没有找到下穿零轴的情况
    if cross_index == -1:
        # logger.info("未找到DEA下穿零轴的情况")
        return result
    
    close_prices = df_data['收盘'].values
    low_prices = df_data['最低'].values
    
    # 寻找局部低点
    local_lows = []
    for i in range(cross_index, len(close_prices) - 1):
        if low_prices[i] < low_prices[i-1] and low_prices[i] < low_prices[i+1]:
            local_lows.append((i, low_prices[i]))
    
    if len(local_lows) < 2:
        return result
    
    # 寻找符合条件的双底组合
    for i in range(len(local_lows)):
        for j in range(i+1, len(local_lows)):
            first_idx, first_low = local_lows[i]
            second_idx, second_low = local_lows[j]
            
            distance = second_idx - first_idx
            
            # 检查两个底部之间的距离是否符合要求
            if distance < min_distance or distance > max_distance:
                continue
            
            # 检查两个底部的价格是否相近(允许一定误差)
            if abs(first_low - second_low) / first_low > 0.05:  # 5%以内差异
                continue
            
            # 寻找两个底部之间的高点(颈线)
            intermediate_high = max(close_prices[first_idx:second_idx+1])
            
            # 检查颈线是否明显高于底部
            if (intermediate_high - first_low) / first_low < 0.03:  # 至少3%的颈线高度
                continue
            
            # 检查第二底部之后是否有突破颈线的趋势
            # if second_idx + 5 < len(close_prices):
            #     post_breakout = any(price > intermediate_high for price in close_prices[second_idx:second_idx+5])
            #     if not post_breakout:
            #         continue
            
            result['found'] = True
            result['first_low'] = first_low
            result['second_low'] = second_low
            result['first_low_idx'] = first_idx
            result['second_low_idx'] = second_idx
            result['neckline'] = intermediate_high
            
            return result
    
    return result