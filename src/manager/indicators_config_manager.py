
# k线涨跌幅颜色
dict_kline_color = {
'desc': (0, 168, 67), #绿色－下跌 (0, 169, 178), (0, 168, 67), (43, 186, 146)
'asc': (255, 61, 61) #红色 -上涨
}

dict_kline_color_hex = {
'desc': '#00a84b', #绿色－下跌
'asc': '#ff3d3d' #红色 -上涨
}


# 均线
dict_ma_color = {
'ma5': (0, 0, 0), 
'ma10': (217, 186, 38), 
'ma20': (25, 160, 255), 
'ma24': (239, 57, 178),
'ma30': (255, 154, 117),
'ma52': (10, 204, 90),
'ma60': (119, 60, 178),
'ma120': (176, 187, 242),
'ma250': (175, 117, 234)
}

dict_ma_color_hex = {
    'ma5': '#000000', 
    'ma10': '#d9ba26', 
    'ma20': '#1fa0ff', 
    'ma24': '#ef39ae',
    'ma30': '#ff9a75',
    'ma52': '#0acc5a',
    'ma60': '#7777ff',
    'ma120': '#afafef',
    'ma250': '#af77ef'
}

# 成交量
dict_volume_color = {
'ma5': dict_ma_color['ma5'],
'ma10': dict_ma_color['ma10'],
'ma20': dict_ma_color['ma20']
}

dict_volume_color_hex = {
    'ma5': dict_ma_color_hex['ma5'],
    'ma10': dict_ma_color_hex['ma10'],
    'ma20': dict_ma_color_hex['ma20']
}



# 成交额
dict_amount_color = {
'ma5': dict_ma_color['ma5'],
'ma10': dict_ma_color['ma10'],
'ma20': dict_ma_color['ma20']
}

dict_amount_color_hex = {
    'ma5': dict_ma_color_hex['ma5'],
    'ma10': dict_ma_color_hex['ma10'],
    'ma20': dict_ma_color_hex['ma20']
}


# MACD
dict_macd_color = {
'diff': (0, 0, 0),
'dea': (217, 186, 38),
}

dict_macd_color_hex = {
    'diff': '#000000',
    'dea': '#d9ba26'
}

# KDJ
dict_kdj_color = { 
'k': (217, 186, 38),
'd': (25, 160, 255),
'j': (244, 134, 208)
}

dict_kdj_color_hex = { 
    'k': '#d9ba26',
    'd': '#1fa0ff',
    'j': '#ef39ae'
}

# RSI
dict_rsi_color = { 
'rsi1': (217, 186, 38),
'rsi2': (10, 204, 90),
'rsi3': (25, 160, 255)
}

dict_rsi_color_hex = { 
    'rsi1': '#d9ba26',
    'rsi2': '#0acc5a',
    'rsi3': '#1fa0ff'
}

# BOLL
dict_boll_color = { 
'up': (255, 61, 61),
'mid': (25, 160, 255),
'down': (10, 204, 90),
'close': (0, 0, 0)
}

dict_boll_color_hex = { 
    'up': '#ff3d3d',
    'mid': '#1fa0ff',
    'down': '#0acc5a',
    'close': '#000000'
}
