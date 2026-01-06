import pandas as pd
from typing import Sequence
import copy

from common.common_api import *
from manager.period_manager import TimePeriod
from manager.logging_manager import get_logger
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
s_target_code = ""          # 带前缀，如：sh.600000, sz_000001

b_less_than_ma5 = False
b_filter_log = False

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

def set_target_code(code):
    global s_target_code
    s_target_code = code

def set_b_less_than_ma5(b_less_than):
    global b_less_than_ma5
    b_less_than_ma5 = b_less_than

def set_b_filter_log(b_log):
    global b_filter_log
    b_filter_log = b_log

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

def get_target_code():
    return s_target_code

def get_b_less_than_ma5():
    return b_less_than_ma5

def get_b_filter_log():
    return b_filter_log

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

# -------------------------------------------------------------零轴上方策略-------------------------------------------------------------------

# 零轴上方MA52选股法
def daily_up_ma52_filter(df_filter_data, df_weekly_data, period=TimePeriod.DAY):
    '''
        筛选逻辑：零轴上方回踩MA52筛选法，最好是第一次回踩MA24(回踩MA60也可考虑)。
        进场逻辑：最新收盘价位于MA24、MA60之间，即收盘价小于MA24，大于MA52或MA60，且下面30（或15）分钟级别零轴下方出现底背离或下跌动能不足形态，或者站上突破15分钟MA52压力，亦或者等15分钟DEA突破零轴，回踩15分钟MA5或MA10，才满足进场条件
        止盈位：有效反弹看前高
        止损位：有效跌破日线MA52或MA60清仓离场，等待日线零轴下方或大级别的零轴上方机会。
    '''
    if df_filter_data.empty:
        logger.info("筛选数据数据为空！")
        return False

    if not columns_check(df_filter_data, ('date', 'close', 'diff', 'dea', 'ma5', 'ma10', 'ma24', 'ma30',  'ma52', 'ma60', 'turnover_rate', 'volume_ratio')):
        logger.info("筛选数据列名不存在！")
        return False

    last_day_row = df_filter_data.tail(1)
    day_close = last_day_row['close'].item()
    day_dif = last_day_row['diff'].item()
    day_dea = last_day_row['dea'].item()
    day_ma5 = last_day_row['ma5'].item()
    day_ma10 = last_day_row['ma10'].item()
    # day_ma20 = last_day_row['ma20'].item()
    day_ma24 = last_day_row['ma24'].item()
    day_ma30 = last_day_row['ma30'].item()
    day_ma52 = last_day_row['ma52'].item()
    day_ma60 = last_day_row['ma60'].item()
    day_turn = last_day_row['turnover_rate'].item()
    day_lb = last_day_row['volume_ratio'].item()

    if b_weekly_condition and df_weekly_data is not None and not df_weekly_data.empty:
        if not columns_check(df_weekly_data, ('date', 'close', 'dea', 'ma52')):
            logger.info("周线列名不存在！")
            return False
        
        last_week_row = df_weekly_data.tail(1)
        week_close = last_week_row['close'].item()
        week_dea = last_week_row['dea'].item()
        week_ma52 = last_week_row['ma52'].item()

        b_ret_2 = (week_close > week_ma52 and week_dea > 0) if b_weekly_condition else True
    else:
        b_ret_2 = True

    # day_diff = day_ma52 * policy_filter_ma52_diff
    # logger.info(f"day_close: {day_close}, day_dea: {day_dea}, day_ma24: {day_ma24}, day_ma52: {day_ma52}, diff: {day_diff}, day_turn>: {day_turn}, day_lb: {day_lb}")
    # logger.info(f"week_close: {week_close}, week_ma52: {week_ma52}")

    b_ret = True if TimePeriod.is_minute_level(period) else (day_turn > policy_filter_turn) and (day_lb > policy_filter_lb)
    
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
def daily_up_ma24_filter(df_filter_data, df_weekly_data, period=TimePeriod.DAY):
    '''
        筛选逻辑：零轴上方回踩MA24筛选法，最好是第一次回踩MA24(回踩MA20、30均可考虑)。和daily_ma52_ma24_filter稍有重复。
        进场逻辑：最新收盘价无限接近MA24，且收盘价小于MA5或小于MA10，且下面15(或7.5)分钟级别零轴下方出现底背离或下跌动能不足形态，或者站上突破15分钟MA52压力，亦或者等15分钟DEA突破零轴，回踩15分钟MA5或MA10，才满足进场条件
        止盈位：有效反弹看前高
        止损位：有效跌破日线MA24或MA30清仓离场，等待日线MA52机会。
    '''
    if df_filter_data.empty:
        return False
    
    
    if not columns_check(df_filter_data, ('date', 'close', 'diff', 'dea', 'ma5', 'ma10', 'ma20', 'ma24', 'ma30', 'ma52', 'turnover_rate', 'volume_ratio')):
        return False
    
    last_day_row = df_filter_data.tail(1)
    day_close = last_day_row['close'].item()
    day_dif = last_day_row['diff'].item()
    day_dea = last_day_row['dea'].item()
    day_ma5 = last_day_row['ma5'].item()
    day_ma10 = last_day_row['ma10'].item()
    day_ma20 = last_day_row['ma20'].item()
    day_ma24 = last_day_row['ma24'].item()
    day_ma30 = last_day_row['ma30'].item()
    day_ma52 = last_day_row['ma52'].item()
    day_turn = last_day_row['turnover_rate'].item()
    day_lb = last_day_row['volume_ratio'].item()

    if b_weekly_condition and df_weekly_data is not None and not df_weekly_data.empty:
        if not columns_check(df_weekly_data, ('date', 'close', 'ma52')):
            return False
        
        last_week_row = df_weekly_data.tail(1)
        week_close = last_week_row['close'].item()
        week_ma52 = last_week_row['ma52'].item()
        b_ret_2 = (week_close > week_ma52) if b_weekly_condition else True
    else:
        b_ret_2 = True

    # day_diff = day_ma52 * policy_filter_ma52_diff
    # logger.info(f"day_close: {day_close}, day_dea: {day_dea}, day_ma24: {day_ma24}, day_ma52: {day_ma52}, diff: {day_diff}, day_turn>: {day_turn}, day_lb: {day_lb}")
    # logger.info(f"week_close: {week_close}, week_ma52: {week_ma52}")

    b_ret = True if TimePeriod.is_minute_level(period) else (day_turn > policy_filter_turn) and (day_lb > policy_filter_lb)

    b_ret_3 = day_dea > 0 and day_dif > 0
    b_ret_4 = (day_close >= day_ma20 or day_close >= day_ma24) and (day_close <= day_ma5 or day_close <= day_ma10)# abs(day_close - day_ma24) < day_ma24 * policy_filter_ma24_diff
    b_ret_5 = day_ma5 <= day_ma10 and day_ma10 >= day_ma24 and day_ma5 >= day_ma24 and day_ma24 > day_ma52

    if b_ret and b_ret_2 and b_ret_3 and b_ret_4 and b_ret_5:
        # logger.info("符合【日线零轴上方MA24】筛选")
        return True
    
    return False

# 零轴上方MA5选股法
def daily_up_ma5_filter(df_filter_data):
    pass

# 零轴上方MA10选股法
def daily_up_ma10_filter(df_filter_data, period=TimePeriod.DAY):
    '''
        筛选逻辑：零轴上方，回踩MA10
        进场逻辑：最新收盘价位于MA5、MA10之间，次日必须低开，且接近30或60分钟MA52，且30或60分钟DEA大于0，且下面5分钟出现底背离或下跌动能不足，才满足进场条件。
        止盈：指数看到30或60分钟背离或上涨动能不足离场止盈
        止损：有效跌破30或60分钟MA52，且对应的DEA下穿零轴清仓止损
    '''
    
    if df_filter_data.empty:
        return False

    if not columns_check(df_filter_data, ('date', 'close', 'dea', 'ma5', 'ma10', 'ma24', 'ma52', 'turnover_rate', 'volume_ratio')):
        return False
    
    last_day_row = df_filter_data.tail(1)
    day_close = last_day_row['close'].item()
    day_dea = last_day_row['dea'].item()
    day_ma5 = last_day_row['ma5'].item()
    day_ma10 = last_day_row['ma10'].item()
    day_ma24 = last_day_row['ma24'].item()
    day_ma52 = last_day_row['ma52'].item()
    day_turn = last_day_row['turnover_rate'].item()
    day_lb = last_day_row['volume_ratio'].item()

    b_ret = True if TimePeriod.is_minute_level(period) else (day_turn > policy_filter_turn) and (day_lb > policy_filter_lb)
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
def daily_up_ma20_filter(df_filter_data, period=TimePeriod.DAY):
    '''
        筛选逻辑：零轴上方，回踩MA20
        进场逻辑：最新收盘价位于MMA10、MA20之间，次日必须低开，且接近30或60分钟MA52，且30或60分钟DEA大于0，且下面5、10分钟出现底背离或下跌动能不足，才满足进场条件。
        止盈：指数看到30或60分钟背离或上涨动能不足离场止盈
        止损：有效跌破30或60分钟MA52，且对应的DEA下穿零轴清仓止损
    '''
    if df_filter_data.empty:
        return False
    
    day_close = 0.0
    day_dea = 0.0
    day_ma20 = 0.0
    day_ma24 = 0.0
    day_ma52 = 0.0
    day_turn = 0.0
    day_lb = 0.0
    if not columns_check(df_filter_data, ('date', 'close', 'dea', 'ma5', 'ma10', 'ma20', 'ma24', 'ma52', 'turnover_rate', 'volume_ratio')):
        return False
    
    last_day_row = df_filter_data.tail(1)
    day_close = last_day_row['close'].item()
    day_dea = last_day_row['dea'].item()
    day_ma5 = last_day_row['ma5'].item()
    day_ma10 = last_day_row['ma10'].item()
    day_ma20 = last_day_row['ma20'].item()
    day_ma24 = last_day_row['ma24'].item()
    day_ma52 = last_day_row['ma52'].item()
    day_turn = last_day_row['turnover_rate'].item()
    day_lb = last_day_row['volume_ratio'].item()

    b_ret = True if TimePeriod.is_minute_level(period) else (day_turn > policy_filter_turn) and (day_lb > policy_filter_lb)
    b_ret_2 = day_dea > 0
    b_ret_3 = day_close >= day_ma20 and (day_close <= day_ma5 and day_close <= day_ma10)# abs(day_close - day_ma24) < day_ma24 * policy_filter_ma24_diff
    b_ret_4 = day_ma5 <= day_ma10 and day_ma10 > day_ma24 and day_ma5 > day_ma24 and day_ma24 > day_ma52


    # day_ma20_diff = day_ma20 * policy_filter_ma20_diff
    # logger.info(f"day_close: {day_close}, day_dea: {day_dea}, day_ma20: {day_ma20}, day_ma24: {day_ma24}, day_ma52: {day_ma52}, day_ma20_diff: {day_ma20_diff}, day_turn>: {day_turn}, day_lb: {day_lb}")

    if b_ret and b_ret_2 and b_ret_3 and b_ret_4:
        # logger.info("符合【日线零轴上方MA20】筛选")
        return True
    
    return False


# 涨停复制
def limit_copy_filter(df_filter_data, target_date=None):
    if df_filter_data.empty:
        return False
    
    # 当target_date为None时，使用最后一行数据
    if target_date is None:
        if len(df_filter_data) < 1:
            return False
        
        target_row = df_filter_data.tail(1)
        
        # 获取前一行数据（倒数第二行）
        if len(df_filter_data) >= 2:
            previous_row = df_filter_data.tail(2).head(1)  # 获取倒数第二行
        else:
            previous_row = None  # 只有一行数据时，前一行设为None
    else:
        # 当target_date不为None时，查找指定日期的数据
        target_rows = df_filter_data[df_filter_data['date'] == target_date]
        
        # 检查是否有匹配的日期数据
        if target_rows.empty:
            logger.warning(f"未找到指定日期 {target_date} 的数据")
            return False
        
        # 如果有多个匹配项，使用第一个
        if len(target_rows) > 1:
            # logger.warning(f"找到多个日期为 {target_date} 的数据，将使用第一个")
            target_row = target_rows.iloc[[0]]
        else:
            target_row = target_rows
        
        # 获取指定日期的前一行数据（按日期排序）
        # 按日期排序的DataFrame，查找指定日期之前的行
        df_sorted = df_filter_data.sort_values('date')
        target_date_row = df_sorted[df_sorted['date'] == target_date]
        
        if not target_date_row.empty:
            # 获取目标日期的索引
            target_idx = target_date_row.index[0]
            # 找到目标日期之前的行
            previous_rows = df_sorted[df_sorted['date'] < target_date]
            if not previous_rows.empty:
                # 获取最接近目标日期的前一行数据
                previous_row = previous_rows.tail(1)
            else:
                previous_row = None  # 没有前一行数据
        else:
            previous_row = None  # 没有找到目标日期的索引
    
    # 继续后续的处理逻辑
    try:
        # 获取当前行的日期和收盘价
        date_val = target_row['date'].item()
        current_close = target_row['close'].item()
        
        # 获取前一行数据的收盘价
        previous_close = None
        if previous_row is not None:
            try:
                previous_date_val = previous_row['date'].item()
                previous_close = previous_row['close'].item()
            except (ValueError, KeyError):
                logger.warning("获取前一行收盘价时出错")
                previous_row = None
        
        # 检查是否有股票代码用于判断板块
        stock_code = None
        if 'code' in target_row.columns:
            stock_code = target_row['code'].item()
        
        # 使用涨停判断函数
        if previous_close is not None and stock_code is not None:
            # 使用common_api.py中的is_stock_limit_up函数判断是否涨停
            from common.common_api import is_stock_limit_up
            is_limit_up = is_stock_limit_up(stock_code, current_close, previous_close)
            
            # if is_limit_up:
            #     logger.info(f"股票 {stock_code} 在 {date_val} 涨停，当前价格: {current_close}，前一日收盘价: {previous_close}")
            # else:
            #     logger.info(f"股票 {stock_code} 在 {date_val} 未涨停，当前价格: {current_close}，前一日收盘价: {previous_close}")
        elif previous_close is None:
            logger.warning(f"无法获取前一日收盘价，无法判断涨停情况")
        elif stock_code is None:
            logger.warning(f"无法获取股票代码，无法判断涨停情况")
        
        # 其他处理逻辑...
    except ValueError:
        logger.error("获取数据项时出错")
        return False
    except ImportError:
        logger.error("无法导入is_stock_limit_up函数，请确保common_api模块可用")
        return False

    
    return is_limit_up

def break_through_and_step_back(self, df_filter_data, period=TimePeriod.DAY):
    if df_filter_data.empty:
        return False
    
    if not columns_check(df_filter_data, ('date', 'close', 'diff', 'dea', 'ma5', 'ma10', 'ma20', 'ma24', 'ma30', 'ma52', 'turnover_rate', 'volume_ratio')):
        return False

    last_row = df_filter_data.tail(1)
    close = last_row['close'].item()
    dif = last_row['diff'].item()
    dea = last_row['dea'].item()
    ma5 = last_row['ma5'].item()
    ma10 = last_row['ma10'].item()
    ma20 = last_row['ma20'].item()
    ma24 = last_row['ma24'].item()
    ma30 = last_row['ma30'].item()
    ma52 = last_row['ma52'].item()
    turn = last_row['turnover_rate'].item()
    lb = last_row['volume_ratio'].item()


    b_ret = True if TimePeriod.is_minute_level(period) else (turn > policy_filter_turn) and (lb > policy_filter_lb)
    b_ret_2 = (close >= ma52*0.98)
    b_ret_3 = ma5 <= ma52 and ma5 >= ma24 and ma24 <= ma52

    if b_ret and b_ret_2 and b_ret_3:
        # logger.info("符合【突破回踩】筛选")
        return True
    
    return False
def break_through_and_step_back_2(self, df_filter_data, period=TimePeriod.DAY):
    if df_filter_data.empty:
        return False
    
    if not columns_check(df_filter_data, ('date', 'close', 'diff', 'dea', 'ma5', 'ma10', 'ma20', 'ma24', 'ma30', 'ma52', 'turnover_rate', 'volume_ratio')):
        return False

    last_row = df_filter_data.tail(1)
    close = last_row['close'].item()
    dif = last_row['diff'].item()
    dea = last_row['dea'].item()
    ma5 = last_row['ma5'].item()
    ma10 = last_row['ma10'].item()
    ma20 = last_row['ma20'].item()
    ma24 = last_row['ma24'].item()
    ma30 = last_row['ma30'].item()
    ma52 = last_row['ma52'].item()
    turn = last_row['turnover_rate'].item()
    lb = last_row['volume_ratio'].item()

    b_ret = True if TimePeriod.is_minute_level(period) else (turn > policy_filter_turn) and (lb > policy_filter_lb)
    b_ret_2 = (close >= ma24)
    b_ret_3 = ma5 >= ma52*0.98 and ma10 >= ma24*0.98 and ma10 <= ma52 and ma24 <= ma52

    if b_ret and b_ret_2 and b_ret_3:
        # logger.info("符合【突破回踩2】筛选")
        return True
    
    return False

def break_through_and_step_back_3(self, df_filter_data, period=TimePeriod.DAY):
    if df_filter_data.empty:
        return False
    
    if not columns_check(df_filter_data, ('date', 'close', 'diff', 'dea', 'ma5', 'ma10', 'ma20', 'ma24', 'ma30', 'ma52', 'turnover_rate', 'volume_ratio')):
        return False

    last_row = df_filter_data.tail(1)
    close = last_row['close'].item()
    dif = last_row['diff'].item()
    dea = last_row['dea'].item()
    ma5 = last_row['ma5'].item()
    ma10 = last_row['ma10'].item()
    ma20 = last_row['ma20'].item()
    ma24 = last_row['ma24'].item()
    ma30 = last_row['ma30'].item()
    ma52 = last_row['ma52'].item()
    turn = last_row['turnover_rate'].item()
    lb = last_row['volume_ratio'].item()

    b_ret = True if TimePeriod.is_minute_level(period) else (turn > policy_filter_turn) and (lb > policy_filter_lb)
    b_ret_2 = (close >= ma52*0.96 or close >= ma24) and close <= ma5
    b_ret_3 = ma5 >= ma52 and ma10 >= ma52 and ma10 <= ma52 and ma24 <= ma52
    b_ret_4 = abs(ma52 - ma24) <= ma52*0.02
    b_ret_5 = dea >= 0

    if b_ret and b_ret_2 and b_ret_3 and b_ret_4 and b_ret_5:
        # logger.info("符合【突破回踩3】筛选")
        return True
    
    return False


# -------------------------------------------------------------日线零轴下方策略-------------------------------------------------------------------
def daily_down_between_ma24_ma52_filter(df_filter_data, df_weekly_data, period=TimePeriod.DAY):
    '''
        筛选逻辑：周线在零轴上方确保中期趋势；日线零轴下方，MA24 < MA52 or MA24 < MA60, MA52 <= MA60，且最新收盘价位于MA24、MA60之间，即日线最新收盘价大于MA24，小于MA52或MA60
        进场逻辑：回踩MA24进场。最好是前面已经过多个120分钟级别的单位调整周期调整，做上穿日线零轴趋势行情。可参考下面15分钟底背离或下跌动能不足进场。
        止盈：趋势行情，有效站上日线零轴上方后参考前高止盈。
        止损：跌破日线MA24清仓离场。也可参考下面60分钟MA52,跌破60分钟MA52离场。
    '''
    if df_filter_data.empty:
        return False
    
    if not columns_check(df_filter_data, ('date', 'close', 'dea', 'ma24', 'ma52', 'ma60', 'turnover_rate', 'volume_ratio')):
        return False
    
    last_day_row = df_filter_data.tail(1)
    
    day_close = last_day_row['close'].item()
    day_dea = last_day_row['dea'].item()
    day_ma5 = last_day_row['ma5'].item()
    # day_ma10 = last_day_row['ma10'].item()
    # day_ma20 = last_day_row['ma20'].item()
    day_ma24 = last_day_row['ma24'].item()
    # day_ma30 = last_day_row['ma30'].item()
    day_ma52 = last_day_row['ma52'].item()
    day_ma60 = last_day_row['ma60'].item()
    day_turn = last_day_row['turnover_rate'].item()
    day_lb = last_day_row['volume_ratio'].item()

    if b_weekly_condition and df_weekly_data is not None and not df_weekly_data.empty:
        if not columns_check(df_weekly_data, ('date', 'close', 'dea', 'ma52')):
            return False
    
        last_week_row = df_weekly_data.tail(1)

        week_close = last_week_row['close'].item()
        week_dea = last_week_row['dea'].item()
        week_ma52 = last_week_row['ma52'].item()
        b_ret_2 = (week_close > week_ma52 and week_dea > 0) if b_weekly_condition else True
    else:
        b_ret_2 = True
        week_close = 0.0
        week_dea = 0.0
        week_ma52 = 0.0

    b_ret = True if TimePeriod.is_minute_level(period) else (day_turn > policy_filter_turn) and (day_lb > policy_filter_lb)
    
    b_ret_3 = day_dea <= 0
    b_ret_4 = (day_close <= day_ma52 or day_close <= day_ma60) and (day_close >= day_ma24 * 0.96)
    b_ret_5 = (day_ma24 < day_ma52 or day_ma24 < day_ma60) and day_ma52 <= day_ma60

    b_ret_6 = day_close <= day_ma5 if b_less_than_ma5 else True


    if s_target_code != '':
        logger.info(f"特定筛选--s_target_code: {s_target_code}")

        day_diff = day_ma52 * policy_filter_ma52_diff
        logger.info(f"day_turn: {day_turn}, day_lb: {day_lb}, b_weekly_condition: {b_weekly_condition}")
        logger.info(f"day_close: {day_close}, day_dea: {day_dea}, diff: {day_diff}")
        logger.info(f"day_ma24: {day_ma24}, day_ma52: {day_ma52}, day_ma60: {day_ma60}")
        logger.info(f"week_close: {week_close}, week_ma52: {week_ma52}, week_dea: {week_dea}")
        logger.info(f"b_ret: {b_ret}, b_ret_2: {b_ret_2}, b_ret_3: {b_ret_3}, b_ret_4: {b_ret_4}, b_ret_5: {b_ret_5}")

        logger.info(f"完整日线数据：\n{last_day_row}")    
        logger.info(f"完整周线数据：\n{last_week_row}")


    if b_ret and b_ret_2 and b_ret_3 and b_ret_4 and b_ret_5 and b_ret_6:
        # logger.info("符合【日线零轴下方MA52】筛选")
        return True
    
    return False

def daily_down_between_ma5_ma52_filter(df_filter_data, df_weekly_data, period=TimePeriod.DAY):
    '''
        筛选逻辑：周线在零轴上方确保中期趋势；日线零轴下方，MA5 < MA52 or MA6 < MA60, MA52 <= MA60，且最新收盘价位于MA5、MA60之间，即日线最新收盘价大于MA5，小于MA52或MA60
        进场逻辑：回踩MA5进场。最好是前面已经过多个30、60分钟级别的单位调整周期调整，且处于日线下跌线段第一个单位调整周期中，做日线零轴下方归零轴的超跌反弹行情。可参考下面15分钟底背离或下跌动能不足进场。
        止盈：参考日线MA52或MA60附近止盈。
        止损：跌破日线MA5或底部区间低点清仓离场。也可参考下面30分钟MA52,跌破30分钟MA52离场。
    '''
    if df_filter_data.empty:
        return False
    
    if not columns_check(df_filter_data, ('date', 'close', 'dea', 'ma5', 'ma10', 'ma52', 'ma60', 'turnover_rate', 'volume_ratio')):
        return False

    last_day_row = df_filter_data.tail(1)
    day_close = last_day_row['close'].item()
    day_dea = last_day_row['dea'].item()
    day_ma5 = last_day_row['ma5'].item()
    day_ma10 = last_day_row['ma10'].item()
    # day_ma20 = last_day_row['ma20'].item()
    # day_ma24 = last_day_row['ma24'].item()
    # day_ma30 = last_day_row['ma30'].item()
    day_ma52 = last_day_row['ma52'].item()
    day_ma60 = last_day_row['ma60'].item()
    day_turn = last_day_row['turnover_rate'].item()
    day_lb = last_day_row['volume_ratio'].item()

    if b_weekly_condition and df_weekly_data is not None and not df_weekly_data.empty:
        if not columns_check(df_weekly_data, ('date', 'close', 'dea', 'ma52')):
            return False

        last_week_row = df_weekly_data.tail(1)
        week_close = last_week_row['close'].item()
        week_dea = last_week_row['dea'].item()
        week_ma52 = last_week_row['ma52'].item()

        b_ret_2 = (week_close > week_ma52 and week_dea > 0) if b_weekly_condition else True
    else:
        b_ret_2 = True
        
    # day_diff = day_ma52 * policy_filter_ma52_diff
    # logger.info(f"day_close: {day_close}, day_dea: {day_dea}, day_ma24: {day_ma24}, day_ma52: {day_ma52}, diff: {day_diff}, day_turn>: {day_turn}, day_lb: {day_lb}")
    # logger.info(f"week_close: {week_close}, week_ma52: {week_ma52}")

    b_ret = True if TimePeriod.is_minute_level(period) else (day_turn > policy_filter_turn) and (day_lb > policy_filter_lb)

    b_ret_3 = day_dea < 0
    b_ret_4 = (day_close <= day_ma52 or day_close <= day_ma60) and (day_close >= day_ma5 or day_close >= day_ma10)
    b_ret_5 = (day_ma5 < day_ma52 or day_ma5 < day_ma60) and day_ma52 <= day_ma60

    if b_ret and b_ret_2 and b_ret_3 and b_ret_4 and b_ret_5:
        # logger.info("符合【日线零轴下方MA5】筛选")
        return True
    
    return False

def daily_down_breakthrough_ma24_filter(df_filter_data):
    '''
        日线零轴下方MA24突破筛选
        筛选逻辑：日线MACD的diff、dea均小于0；最新k线收盘价大于MA24，小于MA52；MA5必须要金叉MA10，MA24小于MA52
        进场逻辑：回踩MA24进场。
        止盈：短期看日线MA52压力止盈；若120分钟经过多个单位调整周期调整，且单位调整周期间已明显背离或下跌动能不足，则可做突破日线MA52的趋势行情。
        止损：跌破MA24清仓离场。
    '''
    if df_filter_data.empty:
        return False
    
    if not columns_check(df_filter_data, ('date', 'close', 'diff', 'dea', 'ma5', 'ma10', 'ma24', 'ma52', 'ma60', 'turnover_rate', 'volume_ratio')):
        return False
    
    last_day_row = df_filter_data.tail(1)
    day_close = last_day_row['close'].item()
    day_diff = last_day_row['diff'].item()
    day_dea = last_day_row['dea'].item()
    day_ma5 = last_day_row['ma5'].item()
    day_ma10 = last_day_row['ma10'].item()
    # day_ma20 = last_day_row['ma20'].item()
    day_ma24 = last_day_row['ma24'].item()
    # day_ma30 = last_day_row['ma30'].item()
    day_ma52 = last_day_row['ma52'].item()
    day_ma60 = last_day_row['ma60'].item()
    day_turn = last_day_row['turnover_rate'].item()
    day_lb = last_day_row['volume_ratio'].item()

    b_ret = day_diff < 0 and day_dea < 0
    b_ret_2 = day_close >= day_ma24 and day_close <= day_ma60
    b_ret_3 = day_ma5 >= day_ma10 and day_ma24 < day_ma52
    if b_ret and b_ret_2 and b_ret_3:
        # logger.info("符合【日线零轴下方MA24突破】筛选")
        return True
    
    return False


def daily_down_breakthrough_ma52_filter(df_filter_data):
    '''
        日线零轴下方MA52突破筛选
        筛选逻辑：日线MACD的dea小于0；最新k线收盘价大于MA52且与MA52的差值小于MA52*0.1；MA5必须要金叉MA10，MA24小于MA52
        进场逻辑：回踩MA52进场。
        止盈：短期看上面级别（2日、3日、周线）压力止盈；若成功突破上面级别压力，则可做有效反弹的趋势行情。
        止损：跌破MA52或MA24清仓离场。
    '''
    if df_filter_data.empty:
        return False
    
    if not columns_check(df_filter_data, ('date', 'close', 'diff', 'dea', 'ma5', 'ma10', 'ma24', 'ma52', 'ma60', 'turnover_rate', 'volume_ratio')):
        return False
    
    last_day_row = df_filter_data.tail(1)
    day_close = last_day_row['close'].item()
    day_diff = last_day_row['diff'].item()
    day_dea = last_day_row['dea'].item()
    day_ma5 = last_day_row['ma5'].item()
    day_ma10 = last_day_row['ma10'].item()
    # day_ma20 = last_day_row['ma20'].item()
    day_ma24 = last_day_row['ma24'].item()
    # day_ma30 = last_day_row['ma30'].item()
    day_ma52 = last_day_row['ma52'].item()
    day_ma60 = last_day_row['ma60'].item()
    day_turn = last_day_row['turnover_rate'].item()
    day_lb = last_day_row['volume_ratio'].item()

    b_ret = day_dea <= 0
    b_ret_2 = day_close >= day_ma52 and (day_close - day_ma52) <= day_ma52 * 0.1
    b_ret_3 = day_ma5 >= day_ma10 and day_ma5 <= day_ma52 and day_ma24 < day_ma52
    if b_ret and b_ret_2 and b_ret_3:
        # logger.info("符合【日线零轴下方MA52突破】筛选")
        return True
    
    return False

def daily_down_double_bottom_filter(df_filter_data, df_weekly_data, b_weekly_filter=True):
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
    if df_filter_data.empty:
        return False
    
    # logger.info(df_filter_data.tail(10))
    
    if not columns_check(df_filter_data, ('date', 'code', 'close', 'diff', 'dea', 'ma5', 'ma10', 'ma24', 'ma52', 'ma60', 'turnover_rate', 'volume_ratio')):
        return False
    
    last_day_row = df_filter_data.tail(1)
    day_close = last_day_row['close'].item()
    day_diff = last_day_row['diff'].item()
    day_dea = last_day_row['dea'].item()
    day_ma5 = last_day_row['ma5'].item()
    day_ma10 = last_day_row['ma10'].item()
    # day_ma20 = last_day_row['ma20'].item()
    day_ma24 = last_day_row['ma24'].item()
    # day_ma30 = last_day_row['ma30'].item()
    day_ma52 = last_day_row['ma52'].item()
    day_ma60 = last_day_row['ma60'].item()
    day_turn = last_day_row['turnover_rate'].item()
    day_lb = last_day_row['volume_ratio'].item()

    if day_diff >= 0 or day_dea >= 0 and day_ma24 >= day_ma52:
        return False
    
    if b_weekly_condition and df_weekly_data is not None and not df_weekly_data.empty:
        if not columns_check(df_weekly_data, ('date', 'close', 'dea', 'ma52')):
            return False
        
        last_week_row = df_weekly_data.tail(1)
        week_close = last_week_row['close'].item()
        week_dea = last_week_row['dea'].item()
        week_ma52 = last_week_row['ma52'].item()
        # week_ma60 = last_week_row['ma52'].item()  # 周线没有维护MA60

        b_ret_5 = (week_dea >= 0) if b_weekly_condition else True
    else:
        b_ret_5 = True
        

    # logger.info("find_lowest_after_dea_cross_below_zero")
    lowest_result = find_lowest_after_dea_cross_below_zero(df_filter_data)
    lowest_value = lowest_result['lowest_value']
    lowest_date = lowest_result['lowest_date']
    neck_line = lowest_result['neckline']

    b_ret = day_diff <= 0 and day_dea < 0 and day_turn > policy_filter_turn and day_lb > policy_filter_lb
    b_ret_2 = day_close >= lowest_value and day_close <= day_ma10 and day_close < day_ma24 and day_close < day_ma52
    b_ret_3 = day_ma5 <= day_ma24 and day_ma24 < day_ma52
    b_ret_4 = neck_line >= day_ma10
    
    

    if b_ret and b_ret_2 and b_ret_3 and b_ret_4 and b_ret_5:
        code = last_day_row['code'].item()
        logger.info(f"股票代码【{code}】符合【日线零轴下方双底】筛选, 最低点：{lowest_value}, 最低点日期：{lowest_date}, 局部高点：{neck_line}")
        return True
    
    return False

def find_lowest_after_dea_cross_below_zero(df_filter_data):
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
    if df_filter_data.empty:
        logger.info("日线数据为空")
        return result
    
    # 检查是否包含必要的列
    if not columns_check(df_filter_data, ('code', 'dea', 'low')):
        logger.info("缺少必要的列：股票代码 或 DEA 或 最低")
        return result
    
    # 因为数据已按日期排序（最后一行是最新的日期），所以直接使用原数据
    df_data = df_filter_data
    
    # 从最后的日期开始往前遍历，找到DEA最近一次下穿零轴的位置
    cross_index = -1
    for i in range(len(df_data) - 1, 0, -1):  # 从倒数第二个开始，避免索引越界
        current_dea = df_data.iloc[i]['dea']
        previous_dea = df_data.iloc[i-1]['dea']
        
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
        low_price = df_data.iloc[i]['low']
        if low_price < lowest_value:
            lowest_value = low_price
            lowest_index = i

    # 寻找两个底部之间的高点(颈线)
    intermediate_high = max(df_data['close'][lowest_index:len(df_data)])
            
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
    
    # code = df_data.iloc[-1]['code']
    # logger.info(f"找到 {code} DEA下穿零轴位置: {cross_index}, 区间最低值: {lowest_value}, 最低值位置: {lowest_index}")
    
    return result

def get_cross_index(df_data):
    '''#从最后的日期开始往前遍历，找到价格、diff、dea最近一次下穿零轴的位置'''
    # 检查数据是否为空
    if df_data.empty:
        logger.info("日线数据为空")
        return {}
    
    # 检查是否包含必要的列
    if not columns_check(df_data, ('code', 'close', 'low', 'high', 'diff', 'dea', 'macd', 'ma24', 'ma52')):
        logger.info("缺少必要的列：股票代码 或 DEA 或 最低")
        return {}

    
    dea_cross_zero_index = -1
    diff_cross_zero_index = -1
    close_cross_ma52_index = -1
    for i in range(len(df_data) - 1, 0, -1):  # 从倒数第二个开始，避免索引越界
        current_dea = df_data.iloc[i]['dea']
        previous_dea = df_data.iloc[i-1]['dea']
        
        # 判断是否为dea下穿零轴：当前DEA<=0 且 前一个DEA>0
        if current_dea < 0 and previous_dea >= 0:
            dea_cross_zero_index = i
            # break

        # 判断diff下穿零轴：当前diff<=0 且 前一个diff>0
        current_diff = df_data.iloc[i]['diff']
        previous_diff = df_data.iloc[i-1]['diff']
        if current_diff < 0 and previous_diff >= 0:
            diff_cross_zero_index = i

        # 判断价格下穿MA52：当前价格<=MA52 且 前一个价格>MA52
        current_close = df_data.iloc[i]['close']
        current_ma52 = df_data.iloc[i]['ma52']
        current_dea = df_data.iloc[i]['dea']

        previous_close = df_data.iloc[i-1]['close']
        previous_ma52 = df_data.iloc[i-1]['ma52']
        if current_close < current_ma52 and previous_close >= previous_ma52 and current_dea >= 0:
            close_cross_ma52_index = i

        if dea_cross_zero_index != -1 and diff_cross_zero_index != -1 and close_cross_ma52_index != -1:
            break

    
    # 如果没有找到下穿零轴的情况
    if dea_cross_zero_index == -1 or diff_cross_zero_index == -1 or close_cross_ma52_index == -1:
        logger.info("未找到价格、diff、dea下穿零轴的情况")
        return {}
    
    return {
        'dea_cross_zero_index': dea_cross_zero_index,
        'diff_cross_zero_index': diff_cross_zero_index,
        'close_cross_ma52_index': close_cross_ma52_index
    }
    
def get_last_adjust_period_deviate_status(df_filter_data, period=TimePeriod.DAY):
    if df_filter_data is None or df_filter_data.empty:
        logger.info("数据为空")
        return -1
    
    # 检查是否包含必要的列
    if not columns_check(df_filter_data, ('date', 'code', 'turnover_rate', 'volume_ratio')):
        logger.info("缺少必要的列")
        return -1
    
    last_day_row = df_filter_data.tail(1)
    day_date = last_day_row['date'].item()
    day_code = last_day_row['code'].item()

    day_turn = last_day_row['turnover_rate'].item()
    day_lb = last_day_row['volume_ratio'].item()
    # logger.info(f"最新换手率量比：{day_turn}, {day_lb}，限制：{policy_filter_turn}, {policy_filter_lb}")
    b_turn_ret = False if TimePeriod.is_minute_level(period) else day_turn < policy_filter_turn or day_lb < policy_filter_lb    # 分钟级别筛选不比较换手率和量比
    if b_turn_ret:
        return -1
    
    # 做日期和代码筛选
    df_data = df_filter_data

    if s_target_code != "" and day_code != s_target_code:
        return -1
    
    unit_adjust_period_list = find_unit_adjust_period(df_data, period)
    if not unit_adjust_period_list:
        return -1

    last_unit_adjust_period = unit_adjust_period_list[-1]
    return last_unit_adjust_period.period_deviate_status

def find_unit_adjust_period(df_data, period=TimePeriod.DAY):
    unit_adjust_period_list = []

    s_date_col_name = 'date'
    if TimePeriod.is_minute_level(period):
        s_date_col_name = 'time'

    # 检查数据是否为空
    if df_data.empty:
        logger.info("股票数据为空")
        return unit_adjust_period_list
    
    # 检查是否包含必要的列
    if not columns_check(df_data, ('code', 'close', 'low', 'high', 'diff', 'dea', 'macd', 'ma24', 'ma52')):
        logger.info("缺少必要的列：股票代码 或 DEA 或 最低")
        return unit_adjust_period_list
    
    last_day_row = df_data.tail(1)
    day_close = last_day_row['close'].item()
    day_diff = last_day_row['diff'].item()
    day_dea = last_day_row['dea'].item()
    day_ma5 = last_day_row['ma5'].item()
    day_ma24 = last_day_row['ma24'].item()
    day_ma52 = last_day_row['ma52'].item()
    if b_filter_log:  
        logger.info(f"最新日K线：{day_diff}, {day_dea}, {day_ma24}, {day_ma52}")
    if day_diff >= 0 or day_dea >= 0 or day_ma24 >= day_ma52:
        return unit_adjust_period_list
    
    if day_close > day_ma5 if b_less_than_ma5 else False:
        return unit_adjust_period_list
    

    dict_cross_index = get_cross_index(df_data)
    if not dict_cross_index or dict_cross_index == {}:
        return unit_adjust_period_list
    
    
    close_cross_ma52_index = dict_cross_index['close_cross_ma52_index']
    diff_cross_zero_index = dict_cross_index['diff_cross_zero_index']
    dea_cross_zero_index = dict_cross_index['dea_cross_zero_index']

    if b_filter_log:  
        logger.info(f"DEA下穿零轴位置: {dea_cross_zero_index},  diff下穿零轴位置: {diff_cross_zero_index}, 价格下穿MA52位置: {close_cross_ma52_index}")
        logger.info(f"DEA下穿零轴日期: {df_data.iloc[dea_cross_zero_index][s_date_col_name]},  \
                    diff下穿零轴位置: {df_data.iloc[diff_cross_zero_index][s_date_col_name]}, \
                    价格下穿MA52位置: {df_data.iloc[close_cross_ma52_index][s_date_col_name]}")

    # 手动创建第一个单位调整周期
    unit_adjust_period = UnitAdjustPeriod()
    unit_adjust_period.period_status = 0
    unit_adjust_period.period_start_index = diff_cross_zero_index                        # 可用diff或dea下穿零轴标识开始
    unit_adjust_period.period_start_date = df_data.iloc[diff_cross_zero_index][s_date_col_name]

    unit_adjust_period.close_cross_ma52_index = close_cross_ma52_index
    unit_adjust_period.close_cross_ma52_date = df_data.iloc[close_cross_ma52_index][s_date_col_name]

    unit_adjust_period.diff_cross_zero_index = diff_cross_zero_index
    unit_adjust_period.diff_cross_zero_date = df_data.iloc[diff_cross_zero_index][s_date_col_name]

    unit_adjust_period.dea_cross_zero_index = dea_cross_zero_index
    unit_adjust_period.dea_cross_zero_date = df_data.iloc[dea_cross_zero_index][s_date_col_name]


    period_status = 0
    for i in range(dea_cross_zero_index, len(df_data)):
        low_price = df_data.iloc[i]['low']
        if low_price < unit_adjust_period.lowest_value:
            unit_adjust_period.lowest_value = low_price
            unit_adjust_period.lowest_value_index = i
            unit_adjust_period.lowest_value_date = df_data.iloc[i][s_date_col_name]

        low_diff = df_data.iloc[i]['diff']
        if low_diff < unit_adjust_period.lowest_diff:
            unit_adjust_period.lowest_diff = low_diff
            unit_adjust_period.lowest_diff_index = i
            unit_adjust_period.lowest_diff_date = df_data.iloc[i][s_date_col_name]

        low_dea = df_data.iloc[i]['dea']
        if low_dea < unit_adjust_period.lowest_dea:
            unit_adjust_period.lowest_dea = low_dea
            unit_adjust_period.lowest_dea_index = i
            unit_adjust_period.lowest_dea_date = df_data.iloc[i][s_date_col_name]

        low_macd = df_data.iloc[i]['macd']
        if low_macd < unit_adjust_period.lowest_macd:
            unit_adjust_period.lowest_macd = low_macd
            unit_adjust_period.lowest_macd_index = i
            unit_adjust_period.lowest_macd_date = df_data.iloc[i][s_date_col_name]


        close_price = df_data.iloc[i]['close']
        ma24 = df_data.iloc[i]['ma24']
        if close_price >= ma24:
            if b_filter_log:  
                logger.info(f"更新当前周期记录, index: {i}, date: {df_data.iloc[i][s_date_col_name]}")

            if period_status == 0 and unit_adjust_period not in unit_adjust_period_list:
                # logger.info(f"添加周期：{unit_adjust_period}")
                unit_adjust_period_list.append(unit_adjust_period)

            # 可记录调整确认阶段的关键值：最高值及其索引

            period_status =1


        if period_status == 1 and close_price < ma24:
            if b_filter_log:  
                logger.info(f"开始新一轮周期记录, index: {i}, date: {df_data.iloc[i][s_date_col_name]}")

            period_status = 0

            # 更新上一周期的结束索引和结束日期
            unit_adjust_period.period_status = 1
            unit_adjust_period.period_end_index = i
            unit_adjust_period.period_end_date = df_data.iloc[i][s_date_col_name]

            # log_unit_adjust_period(unit_adjust_period_list)


            # 重置单位调整周期
            unit_adjust_period = UnitAdjustPeriod()


            # 开始新一轮周期记录
            unit_adjust_period.period_status = 0
            unit_adjust_period.period_start_index = i
            unit_adjust_period.period_start_date = df_data.iloc[i][s_date_col_name]

        if i == len(df_data) - 1:
            if b_filter_log:  
                logger.info(f"遍历结束，更新结束周期信息。索引为：{i}，日期：{df_data.iloc[i][s_date_col_name]}")
            if close_price >= ma24:
                unit_adjust_period.period_status = 2

            unit_adjust_period.period_end_index = i
            unit_adjust_period.period_end_date = df_data.iloc[i][s_date_col_name]

            if unit_adjust_period not in unit_adjust_period_list:
                # logger.info(f"添加最后一个周期：{unit_adjust_period}")
                unit_adjust_period_list.append(unit_adjust_period)


    update_unit_adjust_period_deviate_status(unit_adjust_period_list)
    return unit_adjust_period_list

def update_unit_adjust_period_deviate_status(list_adjust_period):
    if not list_adjust_period:
        return
    
    if len(list_adjust_period) == 1:
        if list_adjust_period[0].period_status >= 1:
            list_adjust_period[0].period_deviate_status = 3
            return
    
    # 找到最低的diff的周期
    lowest_diff_period = list_adjust_period[0]
    lowest_diff_period_index = 0
    for i, adjust_period in enumerate(list_adjust_period):
        current_period_lowest_diff = adjust_period.lowest_diff

        if current_period_lowest_diff <= lowest_diff_period.lowest_diff:
            lowest_diff_period = adjust_period
            lowest_diff_period_index = 0
    
    if b_filter_log:  
        logger.info(f"找到的最低diff的周期索引为：{lowest_diff_period_index}, 最低diff值为：{lowest_diff_period.lowest_diff}, \
                    该周期最低价格：{lowest_diff_period.lowest_value}, 该周期最低dea：{lowest_diff_period.lowest_dea}, 该周期最低macd：{lowest_diff_period.lowest_macd}")


    # 从最低diff周期后判断周期间的背离情况
    for i, adjust_period in enumerate(list_adjust_period):
        if i <= lowest_diff_period_index:
            continue

        current_period_lowest_value = adjust_period.lowest_value
        current_period_lowest_diff = adjust_period.lowest_diff
        current_period_lowest_dea = adjust_period.lowest_dea
        current_period_lowest_macd = adjust_period.lowest_macd

        lowest_diff_period_lowest_value = lowest_diff_period.lowest_value
        lowest_diff_period_lowest_diff = lowest_diff_period.lowest_diff
        lowest_diff_period_lowest_dea = lowest_diff_period.lowest_dea
        lowest_diff_period_lowest_macd = lowest_diff_period.lowest_macd

        if current_period_lowest_value >= lowest_diff_period_lowest_value and current_period_lowest_diff > lowest_diff_period_lowest_diff:
            # 动能不足情况
            adjust_period.period_deviate_status = 2
            if current_period_lowest_macd >= 0:
                adjust_period.period_deviate_status = 3


        elif current_period_lowest_value < lowest_diff_period_lowest_value and current_period_lowest_diff > lowest_diff_period_lowest_diff:
            # 背离情况
            adjust_period.period_deviate_status = 1
            if current_period_lowest_macd >= 0:
                adjust_period.period_deviate_status = 4

        if b_filter_log:    
            logger.info(f"第{i + 1}个周期的背离情况：{adjust_period.period_deviate_status}")
                

def log_unit_adjust_period(list_adjust_period):
    logger.info("\n")
    logger.info("===============打印当前周期信息===============")
    if list_adjust_period:
            logger.info(f"调整周期个数：{len(list_adjust_period)}")
            # self.logger.info(f"找到的调整周期：{list_adjust_period}")
            index = 0
            for adjust_period in list_adjust_period:
                index += 1
                # self.logger.info(f"找到的调整周期：{adjust_period}")
                logger.info(f"第{index}个调整周期信息如下：")
                if index == 1:
                    logger.info(f"价格下穿MA52索引：{adjust_period.close_cross_ma52_index}, 日期：{adjust_period.close_cross_ma52_date}")
                    logger.info(f"diff下穿零轴索引：{adjust_period.diff_cross_zero_index}, 日期：{adjust_period.diff_cross_zero_date}")
                    logger.info(f"dea下穿零轴索引：{adjust_period.dea_cross_zero_index}, 日期：{adjust_period.dea_cross_zero_date}")

                logger.info(f"周期状态：{adjust_period.period_status}")

                logger.info(f"周期开始索引：{adjust_period.period_start_index}, 日期：{adjust_period.period_start_date}")

                logger.info(f"周期价格内最低值：{adjust_period.lowest_value:.2f}, 索引：{adjust_period.lowest_value_index}, 日期：{adjust_period.lowest_value_date}")
                logger.info(f"周期内diff最低值：{adjust_period.lowest_diff:.3f}, 索引：{adjust_period.lowest_diff_index}, 日期：{adjust_period.lowest_diff_date}")
                logger.info(f"周期dea内最低值：{adjust_period.lowest_dea:.3f}, 索引：{adjust_period.lowest_dea_index}, 日期：{adjust_period.lowest_dea_date}")
                logger.info(f"周期内macd最低值：{adjust_period.lowest_macd:.3f}, 索引：{adjust_period.lowest_macd_index}, 日期：{adjust_period.lowest_macd_date}")

                logger.info(f"周期结束索引：{adjust_period.period_end_index}, 日期：{adjust_period.period_end_date}")

                logger.info(f"周期间背离情况：{adjust_period.period_deviate_status}")
                
    else:
        logger.info("调整周期数量为0")

    logger.info("===============打印当前周期信息完成===============\n")

class UnitAdjustPeriod:
    """
    单位调整周期类，用于跟踪和管理股票技术分析中的调整周期

        定义：
            1. dea下穿零轴的第一个周期：从dea下穿零轴到价格站上MA24的区间为一个单位调整周期
            2. 之后的周期定义：价格跌破MA24，则开始新的周期，从跌破MA24到再次站上MA24的区间
            3. 调整时dea始终小于0

        周期状态：
            1. 调整中：跌破dea（第一个周期开始标志，此时价格应该跌破MA52、且diff<0），跌破MA24（第二个周期后的开始调整标志）。
            2. 调整完成。价格站上MA24，且diff<0。
            3. 调整确认。价格站上MA24，完成上一个周期调整，但还未跌破MA24开始下一个周期调整的阶段。该阶段算在当前调整周期内（完成），直到跌破MA24开始下一个周期调整。

        周期状态：
        0: 调整中
        1: 调整完成
        2: 确认调整

        period_start_index: 单位调整周期开始的索引   
        period_start_date: 单位调整周期的开始日期
        如果为第一个单位调整周期，则需记录：
            close_cross_ma52_index: 收盘价下穿零轴的位置索引
            diff_cross_zero_index: diff下穿零轴的位置索引
            dea_cross_zero_index: dea下穿零轴的索引

        period_end_index: 单位调整周期的结束索引
        period_end_date: 单位调整周期的结束日期
        
        
        lowest_value: 单位调整周期内最低值
        lowest_value_index: 单位调整周期内最低值的索引
        lowest_value_date: 单位调整周期内最低值的日期

        lowest_diff: 单位调整周期内diff最低值
        lowest_diff_index: 单位调整周期内diff最低值的索引
        lowest_diff_date: 单位调整周期内diff最低值的日期

        lowest_dea: 单位调整周期内dea最低值
        lowest_dea_index: 单位调整周期内dea最低值的索引
        lowest_dea_date: 单位调整周期内dea最低值的日期

        lowest_macd: 单位调整周期内MACD最低值
        lowest_macd_index: 单位调整周期内MACD最低值的索引
        lowest_macd_date: 单位调整周期内MACD最低值的日期

    """
    
    def __init__(self):
        """初始化单位调整周期的各个属性"""
        self.period_status = 0  # 周期状态：0-调整中, 1-调整完成, 2-确认调整
        self.period_start_index = -1
        self.period_start_date = None
        self.period_end_index = -1
        self.period_end_date = None
        self.close_cross_ma52_index = -1
        self.close_cross_ma52_date = None
        self.diff_cross_zero_index = -1
        self.diff_cross_zero_date = None
        self.dea_cross_zero = False
        self.dea_cross_zero_index = -1
        self.dea_cross_zero_date = None
        self.lowest_value = float('inf')
        self.lowest_value_index = -1
        self.lowest_value_date = None
        self.lowest_diff = float('inf')
        self.lowest_diff_index = -1
        self.lowest_diff_date = None
        self.lowest_dea = float('inf')
        self.lowest_dea_index = -1
        self.lowest_dea_date = None
        self.lowest_macd = float('inf')
        self.lowest_macd_index = -1
        self.lowest_macd_date = None

        self.period_deviate_status = 0  # 周期间的状态：0-不背离，1-背离，2-动能不足，3-隐形动能不足，4-隐形背离
    
    def reset(self):
        """重置所有属性到初始状态"""
        self.__init__()
    
    def is_valid_period(self):
        """检查周期是否有效"""
        return self.period_start_index != -1
    
    def update_lowest_values(self, index, low_price, low_diff=None, low_dea=None):
        """更新周期内的最低值"""
        if low_price < self.lowest_value:
            self.lowest_value = low_price
            self.lowest_value_index = index
            
        if low_diff is not None and low_diff < self.lowest_diff:
            self.lowest_diff = low_diff
            self.lowest_diff_index = index
            
        if low_dea is not None and low_dea < self.lowest_dea:
            self.lowest_dea = low_dea
            self.lowest_dea_index = index
    
    def set_period_completed(self, index):
        """标记周期完成"""
        self.period_status = 1
        self.period_end_index = index
        # 可以在这里添加更多周期完成时的逻辑
    
    def to_dict(self):
        """将对象转换为字典格式"""
        return {
            'period_status': self.period_status,
            'period_start_index': self.period_start_index,
            'period_start_date': self.period_start_date,
            'period_end_index': self.period_end_index,
            'period_end_date': self.period_end_date,
            'close_cross_ma52_index': self.close_cross_ma52_index,
            'close_cross_ma52_date': self.close_cross_ma52_date,
            'diff_cross_zero_index': self.diff_cross_zero_index,
            'diff_cross_zero_date': self.diff_cross_zero_date,
            'dea_cross_zero': self.dea_cross_zero,
            'dea_cross_zero_index': self.dea_cross_zero_index,
            'lowest_value': self.lowest_value,
            'lowest_value_index': self.lowest_value_index,
            'lowest_value_date': self.lowest_value_date,
            'lowest_diff': self.lowest_diff,
            'lowest_diff_index': self.lowest_diff_index,
            'lowest_diff_date': self.lowest_diff_date,
            'lowest_dea': self.lowest_dea,
            'lowest_dea_index': self.lowest_dea_index,
            'lowest_dea_date': self.lowest_dea_date,
            'lowest_macd': self.lowest_macd,
            'lowest_macd_index': self.lowest_macd_index,
            'lowest_macd_date': self.lowest_macd_date
        }

