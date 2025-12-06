import pandas as pd

'''
    指标计算
'''

class KLine():
    def __init__(self, stock_data):
        self.stock_data = stock_data
        self.open = stock_data['open']
        self.high = stock_data['high']
        self.low = stock_data['low']
        self.close = stock_data['close']
        self.volume = stock_data['volume']
        self.amount = stock_data['amount']
        self.turnover = stock_data['turnover_rate']
        

# 历史数据≤2年 → 全量计算
def macd(stock_data):
    close = stock_data['close']
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9, adjust=False).mean()
    macd = 2 * (dif - dea)
    stock_data['diff'] = dif
    stock_data['dea'] = dea
    stock_data['macd'] = macd

# 在你的指标计算模块中添加
def kdj(data, n=9, m1=3, m2=3):
    """
    计算KDJ指标
    参数:
    data: DataFrame，包含high, low, close列
    n: 周期，默认9
    m1: K值平滑周期，默认3
    m2: D值平滑周期，默认3
    """
    if 'high' not in data.columns or 'low' not in data.columns or 'close' not in data.columns:
        raise ValueError("缺少必要的数据列：high, low, close")
    
    # 计算未成熟随机值RSV
    low_min = data['low'].rolling(window=n).min()
    high_max = data['high'].rolling(window=n).max()
    data['RSV'] = (data['close'] - low_min) / (high_max - low_min) * 100
    
    # 计算K值
    data['K'] = data['RSV'].ewm(alpha=1/m1, adjust=False).mean()
    
    # 计算D值
    data['D'] = data['K'].ewm(alpha=1/m2, adjust=False).mean()
    
    # 计算J值
    data['J'] = 3 * data['K'] - 2 * data['D']
    
    return data

# def rsi(data, period=14):
#     """
#     计算RSI指标
#     参数:
#     data: DataFrame，包含close列
#     period: 计算周期，默认14
#     """
#     if 'close' not in data.columns:
#         raise ValueError("缺少必要的数据列：close")
    
#     # 计算价格变化
#     delta = data['close'].diff()
    
#     # 分离上涨和下跌
#     gain = delta.where(delta > 0, 0)
#     loss = -delta.where(delta < 0, 0)
    
#     # 计算平均上涨和下跌
#     avg_gain = gain.rolling(window=period, min_periods=1).mean()
#     avg_loss = loss.rolling(window=period, min_periods=1).mean()
    
#     # 计算RS
#     rs = avg_gain / avg_loss
    
#     # 计算RSI
#     rsi_name = f'rsi{period}'
#     data[rsi_name] = 100 - (100 / (1 + rs))
    
#     return data
def rsi(data, period=14):
    """
    计算RSI指标（修正版，使用指数移动平均以接近同花顺等软件的结果）
    参数:
    data: DataFrame，包含'close'列
    period: 计算周期，默认14
    """
    if 'close' not in data.columns:
        raise ValueError("缺少必要的数据列：close")
    
    # 计算价格变化
    delta = data['close'].diff()
    
    # 分离上涨和下跌
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    # 核心修正：使用指数移动平均 (EMA) 替代简单移动平均 (SMA)
    # 使用span参数，其等于周期period
    avg_gain = gain.ewm(span=period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(span=period, min_periods=period, adjust=False).mean()
    
    # 计算RS
    rs = avg_gain / avg_loss
    
    # 计算RSI
    rsi_name = f'rsi{period}'
    data[rsi_name] = 100 - (100 / (1 + rs))
    
    return data

def boll(data, n=20, m=2):
    """
    计算BOLL指标
    参数:
    data: DataFrame，包含close列
    n: 周期，默认20
    m: 标准差倍数，默认2
    """
    if 'close' not in data.columns:
        raise ValueError("缺少必要的数据列：close")
    
    # 计算中轨线(MB)
    data['boll_mb'] = data['close'].rolling(window=n).mean()
    
    # 计算标准差
    std = data['close'].rolling(window=n).std()
    
    # 计算上轨线(UP)
    data['boll_up'] = data['boll_mb'] + m * std
    
    # 计算下轨线(DN)
    data['boll_dn'] = data['boll_mb'] - m * std
    
    return data

def ma(stock_data, column='5', cycle=5):
    close = stock_data['close']
    # stock_data['MA24'] = close.rolling(window=24, min_periods=1).mean()
    stock_data[column] = close.rolling(window=cycle, min_periods=1).mean()

def ma_corrected(stock_data, column='5', cycle=5, ma_type='EMA'):
    """
    计算移动平均线，支持多种算法以匹配同花顺。
    
    参数:
    stock_data: DataFrame，包含'close'列
    column: 输出列的名称
    cycle: 移动平均周期
    ma_type: 算法类型，可选 'SMA', 'EMA', 'WMA'
    """
    close = stock_data['close']
    
    if ma_type.upper() == 'SMA':
        # 您的原始算法：简单移动平均
        stock_data[column] = close.rolling(window=cycle, min_periods=cycle).mean()
    elif ma_type.upper() == 'EMA':
        # 修正算法：指数移动平均 (更可能匹配同花顺)
        stock_data[column] = close.ewm(span=cycle, min_periods=cycle, adjust=False).mean()
    elif ma_type.upper() == 'WMA':
        # 另一种算法：加权移动平均
        weights = np.arange(1, cycle+1)  # 生成线性权重 [1, 2, ..., cycle]
        def wma_func(x):
            return np.dot(x, weights) / weights.sum()
        stock_data[column] = close.rolling(window=cycle, min_periods=cycle).apply(wma_func, raw=True)
    else:
        raise ValueError("ma_type 参数应为 'SMA', 'EMA' 或 'WMA'")
    
    return stock_data

def quantity_ratio(stock_data, cycle=5):
    volume = stock_data['volume']

    volume_ma = volume.rolling(window=cycle, min_periods=1).mean()
    stock_data['volume_ratio'] = volume / volume_ma


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
        if cur_index == -1:
            cur_index = index

        cur_dea = row['dea']
        cur_diff = row['diff']
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
        cur_lowest_price = row['low']
        cur_diff = row['diff']
        cur_close_price = row['close']
        cur_top_price = row['high']

        # 更新周期内的最低价和最低diff
        if cur_lowest_price < lowest_price:
            lowest_price = cur_lowest_price

        if cur_diff < lowset_diff:
            lowset_diff = cur_diff

        # 判断周期是否走完
        ma24_price = row['ma24']
        ma52_price = row['ma52']

        if cur_diff >= lowest_price * 0.03:
            # lowest_price = 9999
            # lowset_diff = 99
            if cur_close_price < ma24_price:
                return True
            
def calc_change_percent(stock_data):
    """
    计算涨跌幅百分比
    涨跌幅 = (当前收盘价 - 上一交易日收盘价) / 上一交易日收盘价 * 100%
    
    参数:
    stock_data: DataFrame，包含'close'列的股票数据
    
    返回:
    stock_data: 添加了'change_percent'列的DataFrame
    """
    if 'change_percent' in stock_data.columns:
        return
    
    if 'close' not in stock_data.columns:
        # raise ValueError("缺少必要的数据列：close")
        stock_data['close'] = 0
        return
    
    # 计算涨跌幅百分比
    stock_data['change_percent'] = stock_data['close'].pct_change() * 100
    
    return stock_data
    


def calc_turnover_rate(stock_data):
    """
    计算换手率
    换手率 = 成交量 / 流通股本 × 100%
    
    注意：此实现假设数据中已包含流通股本信息，或者使用简化方式计算
    如果没有实际流通股本数据，通常用成交量与历史平均成交量比较来估算相对换手率
    
    参数:
    stock_data: DataFrame，包含'volume'列的股票数据
    
    返回:
    stock_data: 添加了'turnover_rate'列的DataFrame
    """
    if 'turnover_rate' in stock_data.columns:
        return
    
    # 检查是否包含必要数据列
    if 'volume' not in stock_data.columns:
        # 如果没有成交量数据，则无法计算换手率
        stock_data['turnover_rate'] = 0
        return
    
    # 简化计算方式：使用5日平均成交量作为参考计算相对换手率
    # 实际应用中应该使用真实的流通股本数据
    volume_5d_mean = stock_data['volume'].rolling(window=5, min_periods=1).mean()
    
    # 避免除以零的情况
    turnover_rate = (stock_data['volume'] / volume_5d_mean) * 100
    turnover_rate = turnover_rate.fillna(0)
    
    stock_data['turnover_rate'] = turnover_rate
    
    return stock_data
    


def default_indicators_auto_calculate(stock_data):
    if stock_data is None or stock_data.empty:
        raise ValueError("数据为空，无法计算指标")

    macd(stock_data)
    ma(stock_data, 'ma5', 5)
    ma(stock_data, 'ma10', 10)
    ma(stock_data, 'ma20', 20)
    ma(stock_data, 'ma24', 24)
    ma(stock_data, 'ma30', 30)
    ma(stock_data, 'ma52', 52)
    ma(stock_data, 'ma60', 60)
    quantity_ratio(stock_data)

    kdj(stock_data) 

    rsi(stock_data, period=6)   # 计算RSI6
    rsi(stock_data, period=12)  # 计算RSI12
    rsi(stock_data, period=24)  # 计算RSI24

    boll(stock_data)

    calc_change_percent(stock_data)
    calc_turnover_rate(stock_data)


