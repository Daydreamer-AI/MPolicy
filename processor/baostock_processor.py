import baostock as bs
import pandas as pd
import numpy as np
from data_base import StockDBManager, StockDbBase
from indicators import stock_data_indicators as sdi
import random
import time
import datetime
from policy_filter import policy_filter as pf

class BaoStockProcessor:
    def __init__(self):
        # self.chinese_columns = ['日期', '股票代码', '开盘', '最高', '最低', '收盘', '成交量', '成交额', '涨跌幅', '换手率', '复权方式', '是否ST']
        # self.chinese_columns_add = ['日期', '股票代码', '开盘', '最高', '最低', '收盘', '成交量', '成交额', '涨跌幅', '换手率', '复权方式', '是否ST', 'DIF', 'DEA', 'MACD', 'MA24', 'MA52']
        self.stocks_db = StockDBManager(1)
        self.day_stock_db = StockDbBase("./stocks/db/baostock/day")
        self.week_stock_db = StockDbBase("./stocks/db/baostock/week")

        self.dict_all_stocks = {}

        self.dict_daily_stock_data = {}
        self.dict_weekly_stock_data = {}

        self.get_all_stocks_from_db()

    def data_type_conversion(self, result):
        # 1. 转换日期列
        if '日期' in result.columns:
            result['日期'] = pd.to_datetime(result['日期']).dt.date  # 转换为 datetime.date 类型，或者用 .dt.normalize() 取日期部分

        # 2. 转换数值列 (开盘, 最高, 最低, 收盘, 成交额, 涨跌幅, 换手率)
        numeric_columns = ['开盘', '最高', '最低', '收盘', '成交额', '涨跌幅', '换手率']
        for col in numeric_columns:
            result[col] = pd.to_numeric(result[col], errors='coerce')  # errors='coerce' 将无效解析转换为NaN

        # 3. 转换成交量 (整数)
        if '成交量' in result.columns:
            result['成交量'] = pd.to_numeric(result['成交量'], errors='coerce').astype('Int64')  # 使用 Pandas 的可空整数类型

        # 4. 转换复权方式 (整数)
        if '复权方式' in result.columns:
            result['复权方式'] = pd.to_numeric(result['复权方式'], errors='coerce').astype('Int64')

        # 5. 转换是否ST (布尔值) - 根据你的数据实际情况定义如何映射
        # 假设你的字符串可能是 '是'/'否' 或 '1'/'0'
        if '是否ST' in result.columns:
            result['是否ST'] = result['是否ST'].map({'是': True, '否': False, '1': True, '0': False, 'True': True, 'False': False})
        # 或者如果原本是字符串形式的 'True'/'False'
        # result['是否ST'] = result['是否ST'].astype(bool)
        else:
            print("result中没有 是否ST 列")

        # 打印转换后的数据类型检查
        # print(result.dtypes)

    # 全量更新
    def process_daily_stock_data(self, code, start_date=None, end_date=None):

        if start_date == None or end_date == None:
            # 默认计算近一年的日期范围
            end_date = datetime.datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.datetime.now() - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
            # print(f"获取股票 {stock_code} 数据，时间范围：{start_date} 至 {end_date}")
        
        sleep_time = random.uniform(1, 3)
        time.sleep(sleep_time)

        lg = bs.login()
        rs = bs.query_history_k_data_plus(code,
            "date,code,open,high,low,close,volume,amount,pctChg,turn,adjustflag,isST",
            start_date=start_date, end_date=end_date,
            frequency="d", adjustflag="2")
        # print(rs.error_code)      # 0
        # print(rs.error_msg)       # success
        # print("rs的类型：", type(rs))       # <class 'baostock.data.resultset.ResultData'>

        # 获取具体的信息
        result_list = []
        while (rs.error_code == '0') & rs.next():
            # 分页查询，将每页信息合并在一起
            result_list.append(rs.get_row_data())

        # print("result_list的类型：", type(result_list))     # <class 'list'>
        chinese_columns = ['日期', '股票代码', '开盘', '最高', '最低', '收盘', '成交量', '成交额', '涨跌幅', '换手率', '复权方式', '是否ST']
        result = pd.DataFrame(result_list, columns=chinese_columns)

        self.data_type_conversion(result)

        # 登出系统
        bs.logout()
        return result

    def process_and_save_daily_stock_data(self, code):
        result = self.process_daily_stock_data(code)
        # if result.empty:
        #     print("process_daily_stock_data执行结果为空！")
        #     return False
        
        if not result.empty:
            sdi.macd(result)
            sdi.ma(result, 'MA5', 5)
            sdi.ma(result, 'MA10', 10)
            sdi.ma(result, 'MA20', 20)
            sdi.ma(result, 'MA24', 24)
            sdi.ma(result, 'MA30', 30)
            sdi.ma(result, 'MA52', 52)
            sdi.ma(result, 'MA60', 60)
            sdi.quantity_ratio(result)
            self.day_stock_db.save_bao_stock_data_to_db(code, result)
            self.dict_daily_stock_data[code] = result
        
        return result
       
    # 增量维护，收盘后调用
    def update_daily_stock_data(self, code):
        if not self.day_stock_db.check_stock_db_exists(code):
            print("{stock_code}.db 不存在", code)
            return pd.DataFrame()

        # 步骤一：得到当前数据库中的股票数据
        day_stock_data = self.day_stock_db.get_tao_stock_data(code)
        
        now_date = datetime.datetime.now().strftime("%Y-%m-%d")
        if now_date in day_stock_data['日期'].values:
            print("已是最新数据")
            return day_stock_data

        last_date = day_stock_data['日期'].iloc[-1]
        print("最后日期（方法2）:", last_date) 

        parsed_date = datetime.datetime.strptime(last_date, "%Y-%m-%d")  # 解析为日期对象
        last_date = parsed_date + datetime.timedelta(days=1)
        print(last_date.strftime("%Y-%m-%d"))

        # 步骤二：获取数据库中最后日期至今的股票数据
        start_date = last_date.strftime("%Y-%m-%d")               # Baostock要求的日期格式
        end_date = datetime.datetime.now().strftime("%Y-%m-%d")

        df_new_stock_data = self.process_daily_stock_data(code, start_date, end_date)
        # if df_new_stock_data.empty:
        #     print("process_daily_stock_data执行结果为空！")
        #     return False
        
        print(df_new_stock_data)

        if not df_new_stock_data.empty:
            # 合并计算指标
            combined_df = pd.concat([day_stock_data, df_new_stock_data], axis=0, ignore_index=True)
            print("合并后的combined_df:")
            print(combined_df.tail(6))

            sdi.macd(combined_df)
            sdi.ma(combined_df, 'MA5', 5)
            sdi.ma(combined_df, 'MA10', 10)
            sdi.ma(combined_df, 'MA20', 20)
            sdi.ma(combined_df, 'MA24', 24)
            sdi.ma(combined_df, 'MA30', 30)
            sdi.ma(combined_df, 'MA52', 52)
            sdi.ma(combined_df, 'MA60', 60)
            sdi.quantity_ratio(combined_df)
        
            print("新数据指标计算结果：")
            data_to_save = combined_df.tail(len(df_new_stock_data))
            print(data_to_save)
            self.day_stock_db.save_bao_stock_data_to_db(code, data_to_save, "append")
            self.dict_daily_stock_data[code] = combined_df
            return combined_df
        
        return day_stock_data


    # 全量更新
    def process_weekly_stock_data(self, code, start_date=None, end_date=None):
        if start_date == None or end_date == None:
            # 默认计算近两年的日期范围（周线数据通常需要更长时间来计算指标）
            end_date = datetime.datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.datetime.now() - datetime.timedelta(days=730)).strftime("%Y-%m-%d")

        print(f"获取股票 {code} 周线数据，时间范围：{start_date} 至 {end_date}")
        
        sleep_time = random.uniform(1, 3) # 等待时间可以设得稍长一些
        time.sleep(sleep_time)

        lg = bs.login()
        rs = bs.query_history_k_data_plus(code,
            "date,code,open,high,low,close,volume,amount,pctChg,turn,adjustflag",
            start_date=start_date, end_date=end_date,
            frequency="w", adjustflag="2")
        print(rs.error_code)      # 0
        print(rs.error_msg)       # success
        # print("rs的类型：", type(rs))       # <class 'baostock.data.resultset.ResultData'>

        # 获取具体的信息
        result_list = []
        while (rs.error_code == '0') & rs.next():
            # 分页查询，将每页信息合并在一起
            result_list.append(rs.get_row_data())

        # print("result_list的类型：", type(result_list))     # <class 'list'>
        chinese_columns = ['日期', '股票代码', '开盘', '最高', '最低', '收盘', '成交量', '成交额', '涨跌幅', '换手率', '复权方式']
        result = pd.DataFrame(result_list, columns=chinese_columns)

        self.data_type_conversion(result)

        # 登出系统
        bs.logout()
        return result

    def process_and_save_weekly_stock_data(self, code):
        result = self.process_weekly_stock_data(code)
        # if result.empty:
        #     print("process_weekly_stock_data执行结果为空！")
        #     return False
        
        if not result.empty:
            sdi.macd(result)
            sdi.ma(result, 'MA24', 24)
            sdi.ma(result, 'MA52', 52)
            sdi.quantity_ratio(result)
            self.week_stock_db.save_bao_stock_data_to_db(code, result)
            self.dict_weekly_stock_data[code] = result

        return result

    # 增量维护，周线数据不好增量维护，追加后原表中还会存在周中数据。建议：每周末（或本周收盘后）调用一次更新本周周线数据
    # 例如：周二第一次update，表中会存在周二时的周线数据，当周线再update时，周二数据（已过时）依旧会在表中。
    # 补充：周线接口只能每周最后一个交易日才可以获取，月线每月最后一个交易日才可以获取。
    def update_weekly_stock_data(self, code):
        if not self.week__stock_db.check_stock_db_exists(code):
            print("{stock_code}.db 不存在", code)
            return pd.DataFrame()

        # 步骤一：得到当前数据库中的股票数据
        week_stock_data = self.week_stock_db.get_tao_stock_data(code)
        
        now_date = datetime.datetime.now().strftime("%Y-%m-%d")
        if now_date in week_stock_data['日期'].values:
            print("已是最新数据")
            return week_stock_data
        
        last_date = week_stock_data['日期'].iloc[-1]
        print("最后周线日期:", last_date) 

        parsed_date = datetime.datetime.strptime(last_date, "%Y-%m-%d")  # 解析为日期对象
        last_date = parsed_date + datetime.timedelta(days=1)
        print(last_date.strftime("%Y-%m-%d"))

        # 步骤二：获取数据库中最后日期至今的股票数据
        start_date = last_date.strftime("%Y-%m-%d")               # Baostock要求的日期格式
        end_date = datetime.datetime.now().strftime("%Y-%m-%d")

        df_new_weekly_stock_data = self.process_weekly_stock_data(code, start_date, end_date)
        # if df_new_weekly_stock_data.empty:
        #     print("process_weekly_stock_data执行结果为空！")
        #     return False
        
        print(df_new_weekly_stock_data)

        # if not df_new_weekly_stock_data.empty:
        #     self.day_stock_db.save_bao_stock_data_to_db(code, df_new_weekly_stock_data, "append")

        if not df_new_weekly_stock_data.empty:
            # 合并计算指标
            combined_df = pd.concat([week_stock_data, df_new_weekly_stock_data], axis=0, ignore_index=True)
            print("合并后的combined_df:")
            print(combined_df.tail(3))

            sdi.macd(combined_df)
            sdi.ma(combined_df, 'MA24', 24)
            sdi.ma(combined_df, 'MA52', 52)
            sdi.quantity_ratio(combined_df)
        
            print("新周线数据指标计算结果：")
            data_to_save = combined_df.tail(len(df_new_weekly_stock_data))
            print(data_to_save)
            self.day_stock_db.save_bao_stock_data_to_db(code, data_to_save, "append")
            self.dict_weekly_stock_data[code] = combined_df
            return combined_df
        
        return week_stock_data

    def process_sh_main_stock_daily_data(self):
        self.day_stock_db.set_db_dir("./stocks/db/baostock/day/sh_main")
        i = 1
        for value in self.dict_all_stocks['sh_main']['证券代码']:
            print(f"获取第 {i} 只沪市主板股票 {value} 日线数据")
            i += 1
            self.process_and_save_daily_stock_data(value)

    def process_sh_main_stock_weekly_data(self):
        self.day_stock_db.set_db_dir("./stocks/db/baostock/week/sh_main")
        i = 1
        for value in self.dict_all_stocks['sh_main']['证券代码']:
            print(f"获取第 {i} 只沪市主板股票 {value} 日线数据")
            i += 1
            self.process_and_save_weekly_stock_data(value)

    def process_sz_main_stock_daily_data(self):
        self.day_stock_db.set_db_dir("./stocks/db/baostock/day/sz_main")
        i = 1
        for value in self.dict_all_stocks['sz_main']['证券代码']:
            print(f"获取第 {i} 只深市主板股票 {value} 日线数据")
            i += 1
            self.process_and_save_daily_stock_data(value)

    def process_sz_main_stock_weekly_data(self):
        self.day_stock_db.set_db_dir("./stocks/db/baostock/week/sz_main")
        i = 1
        for value in self.dict_all_stocks['sz_main']['证券代码']:
            print(f"获取第 {i} 只深市主板股票 {value} 日线数据")
            i += 1
            self.process_and_save_weekly_stock_data(value)


    def process_gem_stock_daily_data(self):
        self.day_stock_db.set_db_dir("./stocks/db/baostock/day/gem")
        i = 1
        for value in self.dict_all_stocks['gem']['证券代码']:
            print(f"获取第 {i} 只创业板股票 {value} 日线数据")
            i += 1
            self.process_and_save_daily_stock_data(value)

    def process_gem_stock_weekly_data(self):
        self.day_stock_db.set_db_dir("./stocks/db/baostock/week/gem")
        i = 1
        for value in self.dict_all_stocks['gem']['证券代码']:
            print(f"获取第 {i} 只创业板股票 {value} 日线数据")
            i += 1
            self.process_and_save_weekly_stock_data(value)

    def process_star_stock_daily_data(self):
        self.day_stock_db.set_db_dir("./stocks/db/baostock/day/star")
        i = 1
        for value in self.dict_all_stocks['star']['证券代码']:
            print(f"获取第 {i} 只科创板股票 {value} 日线数据")
            i += 1
            self.process_and_save_daily_stock_data(value)

    def process_star_stock_weekly_data(self):
        self.day_stock_db.set_db_dir("./stocks/db/baostock/week/star")
        i = 1
        for value in self.dict_all_stocks['star']['证券代码']:
            print(f"获取第 {i} 只科创板股票 {value} 日线数据")
            i += 1
            self.process_and_save_weekly_stock_data(value)


    def get_and_save_all_stocks_from_bao(self):
        #### 登陆系统 ####
        lg = bs.login()
        # 显示登陆返回信息
        print('login respond error_code:'+lg.error_code)
        print('login respond  error_msg:'+lg.error_msg)

        #### 获取证券信息 ####
        query_date = datetime.datetime.now().strftime("%Y-%m-%d")
        rs = bs.query_all_stock(query_date)
        print('query_all_stock respond error_code:'+rs.error_code)
        print('query_all_stock respond  error_msg:'+rs.error_msg)

        #### 打印结果集 ####
        data_list = []
        while (rs.error_code == '0') & rs.next():
            # 获取一条记录，将记录合并在一起
            data_list.append(rs.get_row_data())

        chinese_columns = ['证券代码', '交易状态', '证券名称']
        result = pd.DataFrame(data_list, columns=chinese_columns)

        self.dict_all_stocks = self.filter_stocks_by_board(result)

        # 打印各板块股票数量
        for board_name, df_board in self.dict_all_stocks.items():
            print(f"{board_name} 股票数量: {len(df_board)}")

            # print(df_board.tail(1))

            # 如需查看具体代码，可取消下一行的注释
            # print(f"{board_name} 股票代码:\n {df_board['code'].tolist()}\n")
            if board_name == '沪市主板':
                self.stocks_db.save_tao_stocks_to_db(df_board, "replace", 'sh_main')
            elif board_name == '深市主板':
                self.stocks_db.save_tao_stocks_to_db(df_board, "replace", 'sz_main')
            elif board_name == '创业板':
                self.stocks_db.save_tao_stocks_to_db(df_board, "replace", 'gem')
            elif board_name == '科创板':
                self.stocks_db.save_tao_stocks_to_db(df_board, "replace", 'star')
            # elif board_name == '北交所':
            #    self.stocks_db.save_tao_stocks_to_db(df_board, "replace", 'bse')

        #### 结果集输出到csv文件 ####   
        # result.to_csv("./stocks/db/baostock/all_stock.csv", encoding="utf-8", index=False)
        # print(result)
        # self.stocks_db.save_tao_stocks_to_db(result)

        #### 登出系统 ####
        bs.logout()

    def get_all_stocks_from_db(self):
        self.dict_all_stocks['sh_main'] = self.stocks_db.get_sh_main_stocks()
        self.dict_all_stocks['sz_main'] = self.stocks_db.get_sz_main_stocks()
        self.dict_all_stocks['gem'] = self.stocks_db.get_gem_stocks()
        self.dict_all_stocks['star'] = self.stocks_db.get_star_stocks()

    def filter_stocks_by_board(self, df):
        """
        根据证券代码前缀筛选出不同板块的股票
        """
        # 初始化空 DataFrame，用于存储各板块股票
        sh_main = pd.DataFrame()   # 沪市主板
        sz_main = pd.DataFrame()   # 深市主板
        gem = pd.DataFrame()       # 创业板
        star = pd.DataFrame()      # 科创板
        bse = pd.DataFrame()       # 北交所

        # 遍历每一行数据
        for index, row in df.iterrows():
            code = row['证券代码']
            
            if code.startswith('sh.600') or code.startswith('sh.601') or code.startswith('sh.603') or code.startswith('sh.605'):
                sh_main = pd.concat([sh_main, row.to_frame().T], ignore_index=True)
            elif code.startswith('sz.000') or code.startswith('sz.001') or code.startswith('sz.002') or code.startswith('sz.003'):
                sz_main = pd.concat([sz_main, row.to_frame().T], ignore_index=True)
            elif code.startswith('sz.300'):
                gem = pd.concat([gem, row.to_frame().T], ignore_index=True)
            elif code.startswith('sh.688'):
                star = pd.concat([star, row.to_frame().T], ignore_index=True)
            elif code.startswith('bj.'):  # 北交所股票前缀
                bse = pd.concat([bse, row.to_frame().T], ignore_index=True)
        
        return {
            '沪市主板': sh_main,
            '深市主板': sz_main,
            '创业板': gem,
            '科创板': star,
            '北交所': bse
        }

    def auto_test(self):
        filter_result = []
        # sh_main = self.stocks_db.get_sh_main_stocks()
        # i = 1
        # for value in sh_main['证券代码']:
        #     print(f"获取第 {i} 只股票 {value} 日线数据")
        #     stock_data = self.process_stock_daily_data(value)
        #     if self.daily_filter(stock_data):
        #         filter_result.append(value)

        sz_main = self.stocks_db.get_sz_main_stocks()
        i = 1
        for value in sz_main['证券代码']:
            print(f"获取第 {i} 只股票 {value} 日线数据")
            stock_data = self.process_daily_stock_data(value)
            # if self.daily_filter(stock_data):
            if pf.daily_ma52_filter(stock_data):
                filter_result.append(value)

        return filter_result

    def auto_process_daily_data(self, code):
        df_daily_data = self.process_daily_stock_data(code)
        return pf.daily_ma52_filter(df_daily_data)
        

    # 策略筛选
    def daily_ma52_filter(self):
        filter_result = []
        for code, df_data in self.dict_daily_stock_data:
            if pf.daily_ma52_filter(df_data):
                filter_result.append(code)
        
        return filter_result
    
    def daily_and_weekly_ma52_filter(self):
        filter_result = []

        for code, df_data in self.dict_daily_stock_data:
            if pf.daily_and_weekly_ma52_filter(df_data, self.dict_weekly_stock_data[code]):
                filter_result.append(code)

        return filter_result
    
    def daily_ma24_filter(self):
        filter_result = []

        for code, df_data in self.dict_daily_stock_data:
            if pf.daily_ma24_filter(df_data, self.dict_weekly_stock_data[code]):
                filter_result.append(code)

        return filter_result

    def daily_ma52_ma24_filter(self, isUp=False):
        filter_result = []

        for code, df_data in self.dict_daily_stock_data:
            if pf.daily_ma52_ma24_filter(df_data, self.dict_weekly_stock_data[code]):
                filter_result.append(code)

        return filter_result
    
    def daily_ma10_filter(self):
        filter_result = []

        for code, df_data in self.dict_daily_stock_data:
            if pf.daily_ma10_filter(df_data):
                filter_result.append(code)

        return filter_result
    
    def daily_ma20_filter(self):
        filter_result = []

        for code, df_data in self.dict_daily_stock_data:
            if pf.daily_ma20_filter(df_data):
                filter_result.append(code)

        return filter_result

if __name__ == "__main__":
    bao_stock_processor = BaoStockProcessor()
    bao_stock_processor.test()