import pandas as pd

'''
    指标计算
'''

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