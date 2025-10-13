import pandas as pd

'''
    指标计算
'''

class KLine():
    def __init__(self, stock_data):
        self.stock_data = stock_data
        self.open = stock_data['开盘']
        self.high = stock_data['最高']
        self.low = stock_data['最低']
        self.close = stock_data['收盘']
        self.volume = stock_data['成交量']
        self.amount = stock_data['成交额']
        self.turnover = stock_data['换手率']
        

# 历史数据≤2年 → 全量计算
def macd(stock_data):
    close = stock_data['收盘']
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9, adjust=False).mean()
    macd = 2 * (dif - dea)
    stock_data['DIF'] = dif
    stock_data['DEA'] = dea
    stock_data['MACD'] = macd

def ma(stock_data, column='5', cycle=5):
    close = stock_data['收盘']
    # stock_data['MA24'] = close.rolling(window=24, min_periods=1).mean()
    stock_data[column] = close.rolling(window=cycle, min_periods=1).mean()

def quantity_ratio(stock_data, cycle='5'):
    volume = stock_data['成交量']
    stock_data['量比5日'] = volume / volume.rolling(window=5, min_periods=1).mean()



def macd_deviation(stock_data):
    '''
        零轴下方MACD单位调整周期背离筛选
        零轴下方定义：日线dea第一次下穿零轴到第一次上穿零轴的区间为零轴下方
        单位调整周期的定义有以下几种情况：
            1. 日线diff下穿零轴后远离零轴到回到零轴的区间。
                如何判断回到零轴？当日k收盘价大于MA24，且当前diff小于单位调整区间内的diff最大值的0.3（可动态调整），则可判定为一个单位调整周期。
                单位调整周期失效的情况。当后第一个单位调整周期内的k线收盘价和diff均小于上一个周期最低k线的价格和diff，则判定上一个周期失效。
            2. 日k收盘价（或最高价）与日线MA52的差值小于0.03（可动态调整）

        背离定义：存在至少2个单位调整周期，当前单位调整周期最小的diff小于上一个周期的最低diff，若价格同时低于上个单位调整周期内的最低价格，则判断为背离，若价格高于上个单位调整周期的最低价格，则判断为下跌动能不足。

        单位调整周期结构定义：
            类型：零轴上方或下方。  0：零轴下方 1：零轴上方
            周期内的最低价k线。
            周期内最低价格k线对应的diff值。
            周期是否已走完。        0：未完成 1：完成
            当前周期属于下跌线段中的第几个周期。    
            当前周期是否与上个周期形成背离或下跌动能不足形态。  0：未背离或下跌动能不足 1：背离 2：下跌动能不足


        初始化及每日更新：
            1. 判断当前日线dea是否大于0。
            2. 往前找到dea下穿零轴的k线。
            3. 从dea下穿零轴k线再往前找到diff下穿零轴的k线。
            4. 从diff第一次下穿零轴k线开始到当前k线，计算中间的单位调整周期。
            5. 判断调整调整周期间是否背离或下跌动能不足。
    '''
    df = stock_data.copy()
    first_dea_down_cross_zero_index = -1
    first_diff_down_cross_zero_index = -1
    cur_index = -1
    for index, row in df.iloc[::-1].iterrows():
        print("row的类型：", type(row))

        if cur_index == -1:
            cur_index = index

        cur_dea = row['DEA']
        cur_diff = row['DIF']
        if cur_dea > 0:
            return

        if cur_dea > 0 and first_dea_down_cross_zero_index == -1:
            first_dea_down_cross_zero_index = index + 1

        if cur_diff > 0 and first_diff_down_cross_zero_index == -1:
            first_diff_down_cross_zero_index = index
            break

    
    # 当前线段区间：[first_diff_down_cross_zero_index, cur_index]
    lowest_price = 9999
    lowset_diff = 99



    selected_rows = df.iloc[first_diff_down_cross_zero_index:cur_index+1]
    for index, row in selected_rows.iterrows():
        cur_lowest_price = row['最低']
        cur_diff = row['DIF']
        cur_close_price = row['收盘']
        cur_top_price = row['最高']

        # 更新周期内的最低价和最低diff
        if cur_lowest_price < lowest_price:
            lowest_price = cur_lowest_price

        if cur_diff < lowset_diff:
            lowset_diff = cur_diff

        # 判断周期是否走完
        ma24_price = row['MA24']
        ma52_price = row['MA52']

        if cur_diff >= lowest_price * 0.03:
            # lowest_price = 9999
            # lowset_diff = 99
            if cur_close_price < ma24_price:
                return True



