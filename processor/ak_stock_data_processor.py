import akshare as ak
import pandas as pd
import sqlite3
import os
import datetime
from pathlib import Path
from data_base.stocks_db_manager import DBManagerPool
from data_base import StockDbBase
import datetime
from indicators import stock_data_indicators as sdi
import random
import time
from common.common_api import *
import threading

def singleton(cls):
    """
    一个线程安全的单例装饰器。
    使用双重检查锁模式确保在多线程环境下也只创建一个实例。
    """
    instances = {}  # 用于存储被装饰类的唯一实例
    lock = threading.Lock()  # 创建一个锁对象，用于同步

    def get_instance(*args, **kwargs):
        # 第一次检查（无锁）：如果实例已存在，直接返回，避免绝大多数不必要的锁开销
        if cls not in instances:
            with lock:  # 加锁，确保同一时间只有一个线程能进入下面的代码块
                # 第二次检查（有锁）：防止在等待锁的过程中，已有其他线程创建了实例
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)  # 创建唯一的实例
        return instances[cls]

    return get_instance

# 使用装饰器
@singleton
class AKStockDataProcessor:
    '''
    
    维护：
    1. 所有股票日线、周线数据？内存能否扛住？
    2. 不维护股票数据，随用随删。
    '''
    def __init__(self):
        self.stocks_db = DBManagerPool().get_manager(0)
        self.day_stock_db = StockDbBase("./stocks/db/akshare/day")
        self.week_stock_db = StockDbBase("./stocks/db/akshare/week")

        self.dict_stocks = {}
        self.df_stocks_eastmoney = pd.DataFrame()

    def initialize(self) -> bool:
        self.dict_stocks = self.get_stock_info_from_db()

        if file_exists('./stocks/excel/stocks_eastmoney.xlsx'):
            self.df_stocks_eastmoney = pd.read_excel('./stocks/excel/stocks_eastmoney.xlsx')
        else:
            print('未找到./stocks/excel/stocks_eastmoney.xlsx')
        
        return True
    
    def cleanup(self) -> None:
        pass

    def get_stocks_eastmoney(self):
        return self.df_stocks_eastmoney

    # 股票数据接口
    def get_stocks_info_and_save_to_db(self):
        # 初始化数据库  ./stocks/db/stocks.db
        # db_manager = StockDBManager("./stocks/db/stocks.db")

        # 获取股票代码和名称
        # 获取A股所有股票代码和名称
        df = ak.stock_info_a_code_name()
        # print("原始数据验证:\n", df.tail(3))

        df.columns = ['证券代码', '证券名称']
        # print("验证:\n", df.tail(3))

        # 建表。self.stocks_db初始化时已创建
        # self.stocks_db.create_table("stock_basic_info", "CREATE TABLE IF NOT EXISTS stock_basic_info (证券代码 TEXT PRIMARY KEY, 证券名称 TEXT)")


        # 保存到数据库
        self.stocks_db.insert_dataframe_to_table("stock_basic_info", df, "replace")
    def get_stock_info_from_db(self):
        df_stocks_info = self.stocks_db.get_table_data("stock_basic_info")
        dick_stocks = classify_a_stocks_by_board(df_stocks_info)
        # print("上海主板股票：", dick_stocks['sh_main'].tail(3))
        # print("\n")
        # print("深圳主板股票：", dick_stocks['sz_main'].tail(3))
        # print("\n")
        # print("创业板股票：", dick_stocks['gem'].tail(3))
        # print("\n")
        # print("科创板股票：", dick_stocks['star'].tail(3))
        # print("\n")
        # print("北交所股票：", dick_stocks['bse'].tail(3))

        statistics = get_board_stock_statistics(df_stocks_info)
        for board, count in statistics.items():
            print(f"{board}: {count} 只股票")
        
        return dick_stocks

    def process_and_save_board_industry_ths(self):
        '''
            获取、处理并插入同花顺行业板块一览表，收盘后调用
        '''
        # 获取行业板块数据
        try:
            df = ak.stock_board_industry_summary_ths()
        except Exception as e:
            print(f"获取数据失败: {e}")
            return False
        
        print(df.head(3))

        # 处理百分比字段
        df['涨跌幅'] = df['涨跌幅'].apply(convert_percentage)
        df['领涨股-涨跌幅'] = df['领涨股-涨跌幅'].apply(convert_percentage)
        
        # 处理数值字段
        df['上涨家数'] = df['上涨家数'].fillna(0).astype(int)
        df['下跌家数'] = df['下跌家数'].fillna(0).astype(int)
        df['领涨股'] = df['领涨股'].astype(str)  # 确保领涨股为字符串
        
        # 添加日期字段
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        df['日期'] = today

        return self.stocks_db.insert_board_industry_data_to_db(df)

    def query_board_industry_data(self, date=None, industry_name=None):
        return self.stocks_db.query_board_industry_data(date, industry_name)

    def get_latest_board_industry_data(self):
        return self.stocks_db.get_latest_board_industry_data()

    def process_and_save_stock_fund_flow_industry(self):
        stock_board_industry_name_em_df = ak.stock_board_industry_name_em()
        print(stock_board_industry_name_em_df)


    # --------------------------------------------------------暂无用----------------------------------------------------------
    def process_day_stock_data(self, stock_code):
        '''
        获取股票数据并计算技术指标，保存到数据库
        
        参数:
            stock_code (str): 股票代码，如"000001"
        
        返回:
            bool: 处理成功返回True，否则返回False
        '''
        if self.day_stock_db.check_stock_db_exists(stock_code):
            now_date = datetime.datetime.now()
            tmp_date = now_date - datetime.timedelta(days=1)
            last_date = tmp_date.strftime("%Y-%m-%d")
            day_stock_data = self.day_stock_db.get_akshare_stock_data(stock_code)

            if last_date in day_stock_data['日期'].values:
                print(f"股票 {stock_code} 已是最新日线数据")
                return day_stock_data

        try:
            # 计算近一年的日期范围
            end_date = datetime.datetime.now().strftime("%Y%m%d")
            start_date = (datetime.datetime.now() - datetime.timedelta(days=365)).strftime("%Y%m%d")
            # print(f"获取股票 {stock_code} 数据，时间范围：{start_date} 至 {end_date}")
            
            sleep_time = random.uniform(3, 5)
            time.sleep(sleep_time)

            # 通过akshare获取股票数据
            stock_df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"  # 前复权
            )

            # 打印验证
            # print(stock_df.tail(3))
            
            if stock_df.empty:
                print(f"未获取到股票 {stock_code} 的数据")
                return pd.DataFrame()
            
            # 确保列名符合预期
            expected_columns = ['日期', '开盘', '收盘', '最高', '最低', '成交量', '成交额', '振幅', '涨跌幅', '涨跌额', '换手率']
            for col in expected_columns:
                if col not in stock_df.columns:
                    print(f"股票数据缺少预期列: {col}")
                    return pd.DataFrame()
            
            # 添加股票代码列
            stock_df['股票代码'] = stock_code
            
            # 计算MACD
            close = stock_df['收盘']
            ema12 = close.ewm(span=12, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()
            dif = ema12 - ema26
            dea = dif.ewm(span=9, adjust=False).mean()
            macd = 2 * (dif - dea)
            stock_df['DIF'] = dif
            stock_df['DEA'] = dea
            stock_df['MACD'] = macd
            
            # 计算MA24和MA52
            stock_df['MA24'] = close.rolling(window=24).mean()
            stock_df['MA52'] = close.rolling(window=52).mean()
            
            # 计算5日量比
            volume = stock_df['成交量']
            stock_df['量比5日'] = volume / volume.rolling(window=5).mean()
            
            # 选择需要的列并重命名
            columns_to_save = [
                '日期', '股票代码', '开盘', '收盘', '最高', '最低', 
                '成交量', '成交额', '振幅', '涨跌幅', '换手率',
                'DIF', 'DEA', 'MACD', 'MA24', 'MA52', '量比5日'
            ]
            
            # 确保所有需要的列都存在
            for col in columns_to_save:
                if col not in stock_df.columns:
                    print(f"处理后的数据缺少列: {col}")
                    return pd.DataFrame()
            
            # stockDb = StockDbBase("/Users/richard/PythonProject/MPolicy/stocks/db/day")
            # stockDb.save_akshare_stock_data_to_db(stock_code, stock_df[columns_to_save])
            ret = self.day_stock_db.save_akshare_stock_data_to_db(stock_code, stock_df[columns_to_save])
            if not ret:
                print("保存到数据库失败")
                return pd.DataFrame()
            else:
                return stock_df[columns_to_save]
            
        except Exception as e:
            print(f"处理股票 {stock_code} 【日线】数据时出错: {str(e)}")
            return pd.DataFrame()

    def update_day_stock_data(self, stock_code):
        '''
        更新数据库中最后一个交易日至今的股票信息，并新股票信息追加到数据库中
        
        参数:
            stock_code (str): 股票代码，如"000001"
        
        返回:
            bool: 处理成功返回True，否则返回False
        '''
        if not self.day_stock_db.check_stock_db_exists(stock_code):
            print("{stock_code}.db 不存在", stock_code)
            return []

        # 步骤一：得到当前数据库中的股票数据
        day_stock_data = self.day_stock_db.get_akshare_stock_data(stock_code)
        # print("day_stock_data的类型：", type(day_stock_data))     # <class 'pandas.core.frame.DataFrame'>
        # print(day_stock_data.tail(3))

        # print("日期列的类型：", type(day_stock_data.tail(1)['日期']))     # <class 'pandas.core.series.Series'>

        now_date = datetime.datetime.now().strftime("%Y-%m-%d")
        if now_date in day_stock_data['日期'].values:
            print("已是最新数据")
            return day_stock_data

        last_date = day_stock_data['日期'].iloc[-1]
        print("最后日期（方法2）:", last_date) 
        # print("last_date的类型：", type(last_date))  # <class 'str'>

        parsed_date = datetime.datetime.strptime(last_date, "%Y-%m-%d")  # 解析为日期对象
        last_date = parsed_date + datetime.timedelta(days=1)
        print(last_date.strftime("%Y-%m-%d"))
        # print("next_date的类型：", type(last_date)) #<class 'datetime.datetime'>

        # 步骤二：获取数据库中最后日期至今的股票数据
        start_date = last_date.strftime("%Y%m%d")               # AKShare要求的日期格式
        end_date = datetime.datetime.now().strftime("%Y%m%d")

        print(f"获取股票 {stock_code} 数据，时间范围：{start_date} 至 {end_date}")
        stock_df = ak.stock_zh_a_hist(
                        symbol=stock_code,
                        period="daily",
                        start_date=start_date,
                        end_date=end_date,
                        adjust="qfq"  # 前复权
        )

        # print("stock_df的类型：", type(stock_df))   # <class 'pandas.core.frame.DataFrame'>
        print(stock_df)

        # 步骤三：新获取到的股票数据添加到数据库中
        combined_df = pd.concat([day_stock_data, stock_df], axis=0, ignore_index=True)

        # 输出结果
        print("合并后的DataFrame:")
        print(combined_df)

        # 步骤四：指标计算
        sdi.macd(combined_df)
        sdi.ma(combined_df, '24', 24)
        sdi.ma(combined_df, '52', 52)
        sdi.quantity_ratio(combined_df)
        # print("\n指标计算后的DataFrame:")
        # print(combined_df)

        # 步骤五：更新到数据库
        # 选择需要的列并重命名
        columns_to_save = [
            '日期', '股票代码', '开盘', '收盘', '最高', '最低', 
            '成交量', '成交额', '振幅', '涨跌幅', '换手率',
            'DIF', 'DEA', 'MACD', 'MA24', 'MA52', '量比5日'
        ]
        
        # 确保所有需要的列都存在
        for col in columns_to_save:
            if col not in combined_df.columns:
                print(f"处理后的数据缺少列: {col}")
                return []
        # combined_df_save = pd.concat([day_stock_data, stock_df], axis=0, ignore_index=True)

        ret = self.day_stock_db.save_akshare_stock_data_to_db(stock_code, combined_df[columns_to_save].tail(len(stock_df)), "append")
        if ret:
            return combined_df[columns_to_save]
        else:
            return []


    def process_latest_daily_data(self, stock_code):
        """
        获取指定股票代码的最近一个交易日的日线数据，计算技术指标后追加写入数据库
        如果数据库不存在，则调用process_stock_data获取完整数据
        默认在收盘后调用
        
        参数:
            stock_code (str): 股票代码，如"000001"
        
        返回:
            bool: 处理成功返回True，否则返回False

        暂时无用，已被update_day_stock_data代替

        """

        end_date = datetime.datetime.now().strftime("%Y%m%d")
        start_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y%m%d")
        print(f"获取股票 {stock_code} 最近交易日数据，时间范围：{start_date} 至 {end_date}")
        
        # 通过akshare获取股票数据
        stock_df = ak.stock_zh_a_hist(
            symbol=stock_code,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq"  # 前复权
        )

        if stock_df.empty:
            print(f"未获取到股票 {stock_code} 的最近交易日数据")
            return pd.DataFrame()
        
        return stock_df

        try:
            # 检查数据库是否存在
            db_dir = Path("/Users/richard/PythonProject/MPolicy/stocks/db/day")
            db_path = db_dir / f"{stock_code}.db"
            
            # 如果数据库文件不存在，调用process_stock_data获取完整数据
            if not db_path.exists():
                print(f"数据库 {db_path} 不存在，将获取完整历史数据")
                return process_stock_data(stock_code)
                
            # 连接到数据库检查表是否存在
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stock_data'")
            table_exists = cursor.fetchone() is not None
            conn.close()
            
            # 如果表不存在，调用process_stock_data获取完整数据
            if not table_exists:
                print(f"数据库 {db_path} 中不存在stock_data表，将获取完整历史数据")
                return process_stock_data(stock_code)
            
            # 数据库存在，继续获取最近一个交易日的数据
            # 获取当前日期和前7天日期（为了确保能获取到最近一个交易日的数据）
            end_date = datetime.datetime.now().strftime("%Y%m%d")
            start_date = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y%m%d")
            print(f"获取股票 {stock_code} 最近交易日数据，时间范围：{start_date} 至 {end_date}")
            
            # 通过akshare获取股票数据
            stock_df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"  # 前复权
            )

            if stock_df.empty:
                print(f"未获取到股票 {stock_code} 的最近交易日数据")
                return False
                
            # 只保留最后一个交易日的数据
            latest_data = stock_df.tail(1)
            print(f"获取到最近交易日数据: {latest_data['日期'].values[0]}")
            
            # 确保列名符合预期
            expected_columns = ['日期', '开盘', '收盘', '最高', '最低', '成交量', '成交额', '振幅', '涨跌幅', '涨跌额', '换手率']
            for col in expected_columns:
                if col not in latest_data.columns:
                    print(f"股票数据缺少预期列: {col}")
                    return False
            
            # 添加股票代码列
            latest_data['股票代码'] = stock_code
            
            # 为了计算技术指标，我们需要获取更多的历史数据
            # 获取过去一年的数据用于计算指标
            hist_start_date = (datetime.datetime.now() - datetime.timedelta(days=365)).strftime("%Y%m%d")
            hist_data = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=hist_start_date,
                end_date=end_date,
                adjust="qfq"  # 前复权
            )
            
            if hist_data.empty:
                print(f"未获取到股票 {stock_code} 的历史数据，无法计算技术指标")
                return False
            
            # 计算MACD
            close = hist_data['收盘']
            ema12 = close.ewm(span=12, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()
            dif = ema12 - ema26
            dea = dif.ewm(span=9, adjust=False).mean()
            macd = 2 * (dif - dea)
            
            # 计算MA24和MA52
            ma24 = close.rolling(window=24).mean()
            ma52 = close.rolling(window=52).mean()
            
            # 计算5日量比
            volume = hist_data['成交量']
            volume_ratio = volume / volume.rolling(window=5).mean()
            
            # 获取最后一天的指标值
            latest_date = latest_data['日期'].values[0]
            latest_index = hist_data[hist_data['日期'] == latest_date].index
            
            if len(latest_index) == 0:
                print(f"在历史数据中未找到日期 {latest_date} 的记录")
                return False
                
            latest_idx = latest_index[0]
            
            # 添加指标到最新数据
            latest_data['DIF'] = dif.iloc[latest_idx]
            latest_data['DEA'] = dea.iloc[latest_idx]
            latest_data['MACD'] = macd.iloc[latest_idx]
            latest_data['MA24'] = ma24.iloc[latest_idx]
            latest_data['MA52'] = ma52.iloc[latest_idx]
            latest_data['量比5日'] = volume_ratio.iloc[latest_idx]
            
            # 选择需要的列
            columns_to_save = [
                '日期', '股票代码', '开盘', '收盘', '最高', '最低', 
                '成交量', '成交额', '振幅', '涨跌幅', '换手率',
                'DIF', 'DEA', 'MACD', 'MA24', 'MA52', '量比5日'
            ]
            
            # 确保所有需要的列都存在
            for col in columns_to_save:
                if col not in latest_data.columns:
                    print(f"处理后的数据缺少列: {col}")
                    return False
            
            # 检查是否已存在相同日期的数据
            cursor.execute(f"SELECT COUNT(*) FROM stock_data WHERE 日期 = '{latest_date}'")
            exists = cursor.fetchone()[0] > 0
            if exists:
                print(f"数据库中已存在日期为 {latest_date} 的记录，将更新该记录")
                cursor.execute(f"DELETE FROM stock_data WHERE 日期 = '{latest_date}'")
                conn.commit()

            # stockDb = StockDbBase("/Users/richard/PythonProject/MPolicy/stocks/db/day")
            # stockDb.save_akshare_stock_data_to_db(stock_code, stock_df[columns_to_save], 'append')
            self.day_stock_db.save_akshare_stock_data_to_db(stock_code, stock_df[columns_to_save], 'append')
            
            # # 连接到数据库
            # conn = sqlite3.connect(str(db_path))
            # cursor = conn.cursor()
            # # 保存到数据库（追加模式）
            # latest_data[columns_to_save].to_sql('stock_data', conn, if_exists='append', index=False)
            # conn.close()
            
            print(f"成功处理股票 {stock_code} 的最近交易日数据并追加到数据库 {db_path}")
            return True
            
        except Exception as e:
            print(f"处理股票 {stock_code} 最近交易日数据时出错: {str(e)}")
            return False

    def process_week_stock_data(self, stock_code):
        """
        获取股票周级别数据并计算技术指标，保存到数据库
        
        参数:
            stock_code (str): 股票代码，如"000001"
        
        返回:
            bool: 处理成功返回True，否则返回False

        暂时无用。待实现update_week_stock_data
        """

        # 判断是否已是最新数据
        if self.week_stock_db.check_stock_db_exists(stock_code):
            now_date = datetime.datetime.now().strftime("%Y-%m-%d")
            week_stock_data = self.week_stock_db.get_akshare_stock_data(stock_code)

            if now_date in week_stock_data['日期'].values:
                print(f"股票 {stock_code} 已是最新周线数据")
                return week_stock_data
    
        
        try:
            # 计算近两年的日期范围（周线数据通常需要更长时间来计算指标）
            end_date = datetime.datetime.now().strftime("%Y%m%d")
            start_date = (datetime.datetime.now() - datetime.timedelta(days=730)).strftime("%Y%m%d")
            # print(f"获取股票 {stock_code} 周线数据，时间范围：{start_date} 至 {end_date}")
            
            # sleep_time = random.uniform(3, 10) # 等待时间可以设得稍长一些
            # time.sleep(sleep_time)

            # 通过akshare获取股票周线数据
            stock_df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="weekly",  # 周线数据
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"  # 前复权
            )

            # 打印验证
            # print(stock_df.tail(3))
            
            if stock_df.empty:
                print(f"未获取到股票 {stock_code} 的周线数据")
                return pd.DataFrame()
            
            # 确保列名符合预期
            expected_columns = ['日期', '开盘', '收盘', '最高', '最低', '成交量', '成交额', '振幅', '涨跌幅', '涨跌额', '换手率']
            for col in expected_columns:
                if col not in stock_df.columns:
                    print(f"股票周线数据缺少预期列: {col}")
                    return pd.DataFrame()
            
            # 添加股票代码列
            stock_df['股票代码'] = stock_code
            
            # 计算MACD
            close = stock_df['收盘']
            ema12 = close.ewm(span=12, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()
            dif = ema12 - ema26
            dea = dif.ewm(span=9, adjust=False).mean()
            macd = 2 * (dif - dea)
            stock_df['DIF'] = dif
            stock_df['DEA'] = dea
            stock_df['MACD'] = macd
            
            # 计算MA24和MA52
            stock_df['MA24'] = close.rolling(window=24).mean()
            stock_df['MA52'] = close.rolling(window=52).mean()
            
            # 选择需要的列
            columns_to_save = [
                '日期', '股票代码', '开盘', '收盘', '最高', '最低', 
                '成交量', '成交额', '振幅', '涨跌幅', '换手率',
                'DIF', 'DEA', 'MACD', 'MA24', 'MA52'
            ]
            
            # 确保所有需要的列都存在
            for col in columns_to_save:
                if col not in stock_df.columns:
                    print(f"处理后的周线数据缺少列: {col}")
                    return pd.DataFrame()
            
            # 使用stock_db_base保存到数据库
            # db_dir = Path("/Users/richard/PythonProject/MPolicy/stocks/db/week")
            # db_dir.mkdir(parents=True, exist_ok=True)
            # db_path = db_dir / f"{stock_code}.db"
            
            # stockDb = StockDbBase("/Users/richard/PythonProject/MPolicy/stocks/db/week")
            # stockDb.save_akshare_stock_data_to_db(stock_code, stock_df[columns_to_save])
            if self.week_stock_db.save_akshare_stock_data_to_db(stock_code, stock_df[columns_to_save]):
                print(f"成功处理股票 {stock_code} 的周线数据并保存到数据库")
                return stock_df[columns_to_save]
            else:
                return pd.DataFrame()

            '''
            # 创建周线数据库目录（如果不存在）
            db_dir = Path("/Users/richard/PythonProject/MPolicy/stocks/db/week")
            db_dir.mkdir(parents=True, exist_ok=True)
            
            # 连接到数据库
            db_path = db_dir / f"{stock_code}_week.db"
            conn = sqlite3.connect(str(db_path))
            # 保存到数据库
            stock_df[columns_to_save].to_sql('weekly_stock_data', conn, if_exists='replace', index=False)
            conn.close()
            '''
            
        except Exception as e:
            print(f"处理股票 {stock_code} 【周线】数据时出错: {str(e)}")
            return pd.DataFrame()

    def process_latest_weekly_data(self, stock_code):
        """
        获取指定股票代码的最近一周的周线数据，计算技术指标后追加写入数据库
        如果数据库不存在，则调用process_weekly_stock_data获取完整数据
        默认在收盘后调用
        
        参数:
            stock_code (str): 股票代码，如"000001"
        
        返回:
            bool: 处理成功返回True，否则返回False
        """
        try:
            # 检查数据库是否存在
            db_dir = Path("/Users/richard/PythonProject/MPolicy/stocks/db/week")
            db_path = db_dir / f"{stock_code}_week.db"
            
            # 如果数据库文件不存在，调用process_weekly_stock_data获取完整数据
            if not db_path.exists():
                print(f"数据库 {db_path} 不存在，将获取完整历史周线数据")
                return self.process_weekly_stock_data(stock_code)
                
            # 连接到数据库检查表是否存在
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='weekly_stock_data'")
            table_exists = cursor.fetchone() is not None
            conn.close()
            
            # 如果表不存在，调用process_weekly_stock_data获取完整数据
            if not table_exists:
                print(f"数据库 {db_path} 中不存在weekly_stock_data表，将获取完整历史周线数据")
                return process_weekly_stock_data(stock_code)
            
            # 数据库存在，继续获取最近一周的数据
            # 获取当前日期和前30天日期（为了确保能获取到最近一周的数据）
            end_date = datetime.datetime.now().strftime("%Y%m%d")
            start_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y%m%d")
            print(f"获取股票 {stock_code} 最近周线数据，时间范围：{start_date} 至 {end_date}")
            
            # 通过akshare获取股票周线数据
            stock_df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="weekly",  # 周线数据
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"  # 前复权
            )

            if stock_df.empty:
                print(f"未获取到股票 {stock_code} 的最近周线数据")
                return False
                
            # 只保留最后一周的数据
            latest_data = stock_df.tail(1)
            print(f"获取到最近周线数据: {latest_data['日期'].values[0]}")
            
            # 确保列名符合预期
            expected_columns = ['日期', '开盘', '收盘', '最高', '最低', '成交量', '成交额', '振幅', '涨跌幅', '涨跌额', '换手率']
            for col in expected_columns:
                if col not in latest_data.columns:
                    print(f"股票周线数据缺少预期列: {col}")
                    return False
            
            # 添加股票代码列
            latest_data['股票代码'] = stock_code
            
            # 为了计算技术指标，我们需要获取更多的历史数据
            # 获取过去两年的数据用于计算指标
            hist_start_date = (datetime.datetime.now() - datetime.timedelta(days=730)).strftime("%Y%m%d")
            hist_data = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="weekly",
                start_date=hist_start_date,
                end_date=end_date,
                adjust="qfq"  # 前复权
            )
            
            if hist_data.empty:
                print(f"未获取到股票 {stock_code} 的历史周线数据，无法计算技术指标")
                return False
            
            # 计算MACD
            close = hist_data['收盘']
            ema12 = close.ewm(span=12, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()
            dif = ema12 - ema26
            dea = dif.ewm(span=9, adjust=False).mean()
            macd = 2 * (dif - dea)
            
            # 计算MA24和MA52
            ma24 = close.rolling(window=24).mean()
            ma52 = close.rolling(window=52).mean()
            
            # 获取最后一周的指标值
            latest_date = latest_data['日期'].values[0]
            latest_index = hist_data[hist_data['日期'] == latest_date].index
            
            if len(latest_index) == 0:
                print(f"在历史数据中未找到日期 {latest_date} 的记录")
                return False
                
            latest_idx = latest_index[0]
            
            # 添加指标到最新数据
            latest_data['DIF'] = dif.iloc[latest_idx]
            latest_data['DEA'] = dea.iloc[latest_idx]
            latest_data['MACD'] = macd.iloc[latest_idx]
            latest_data['MA24'] = ma24.iloc[latest_idx]
            latest_data['MA52'] = ma52.iloc[latest_idx]
            
            # 选择需要的列
            columns_to_save = [
                '日期', '股票代码', '开盘', '收盘', '最高', '最低', 
                '成交量', '成交额', '振幅', '涨跌幅', '换手率',
                'DIF', 'DEA', 'MACD', 'MA24', 'MA52'
            ]
            
            # 确保所有需要的列都存在
            for col in columns_to_save:
                if col not in latest_data.columns:
                    print(f"处理后的周线数据缺少列: {col}")
                    return False
            
            # 检查是否已存在相同日期的数据
            cursor.execute(f"SELECT COUNT(*) FROM weekly_stock_data WHERE 日期 = '{latest_date}'")
            exists = cursor.fetchone()[0] > 0
            if exists:
                print(f"数据库中已存在日期为 {latest_date} 的周线记录，将更新该记录")
                cursor.execute(f"DELETE FROM weekly_stock_data WHERE 日期 = '{latest_date}'")
                conn.commit()
            
            # 连接到数据库
            # conn = sqlite3.connect(str(db_path))
            # cursor = conn.cursor()
            # 保存到数据库（追加模式）
            # latest_data[columns_to_save].to_sql('weekly_stock_data', conn, if_exists='append', index=False)
            # conn.close()
            self.week_stock_db.save_akshare_stock_data_to_db(stock_code, latest_data[columns_to_save])
            
            print(f"成功处理股票 {stock_code} 的最近周线数据并追加到数据库 {db_path}")
            return True
            
        except Exception as e:
            print(f"处理股票 {stock_code} 最近周线数据时出错: {str(e)}")
            return False

    def update_week_stock_data(self, stock_code):
        pass

    # 股票信息接口
    def get_main_stocks_from_db(self):
        # 获取主板股票信息
        return self.stocks_db.query_stocks(None, 'MAIN')
    
    def get_gem_stocks_from_db(self):
        # 获取创业板股票信息
        return self.stocks_db.query_stocks(None, 'GEM')
    
    def get_star_stocks_from_db(self):
        # 获取科创版股票信息
        return self.stocks_db.query_stocks(None, 'STAR')
    
    def get_bse_stocks_from_db(self):
        # 获取北交所股票信息
        return self.stocks_db.query_stocks(None, 'BSE')
    
    def print_stocks_info(self):
        main_stocks = self.get_main_stocks_from_db()
        print("main--main_stocks的类型：", type(main_stocks))
        print("主板股票数量：", len(main_stocks))

        gem_stocks = self.get_gem_stocks_from_db()
        print("创业板股票数量：", len(gem_stocks))

        star_stocks = self.get_star_stocks_from_db()
        print("科创版股票数量：", len(star_stocks))

        bse_stocks = self.get_bse_stocks_from_db()
        print("北交所股票数量：", len(bse_stocks))

    def update_main_stocks_info(self):
        df = ak.stock_info_a_code_name()

        # 剔除ST、*ST股票
        df = df[~df["name"].str.contains("ST")]

        # 主板（沪深主板，包括60、00、002开头）
        main_board = df[df["code"].str.startswith(("60", "00", "002"))]
        print("主板股票数量：", main_board.shape[0])
        print("main_board: ")
        print(main_board.tail(3))
        print("\n")

        main_board_stocks_data = []
        for _, row in main_board.iterrows():
            stock = {
                "stock_code": row["code"],
                "stock_name": row["name"],
                "board_type": "MAIN",  # 主板标识
                "is_st": 0             # 非ST股票
            }
            main_board_stocks_data.append(stock)
        
        # 批量插入数据库
        inserted_count = self.stocks_db.batch_insert_stocks(main_board_stocks_data)
        print(f"成功插入 {inserted_count} 条主板股票记录")
        return main_board_stocks_data
    
    # ------------------------------------------------------------------------------------------------------------------

    # --------------------------------------------------------东方财富接口----------------------------------------------------------
    # 获取A股所有股票信息
    def get_all_stocks_from_eastmoney(self):
        # 600561, 002283，300821
        # df_tmp1 = ak.stock_individual_info_em(symbol='600561', timeout=30000)
        # stock_data1 = df_tmp1.set_index('item')['value'].to_dict()        
        # # 转换为DataFrame的一行
        # stock_row1 = pd.DataFrame([stock_data1])
        # print(stock_row1)

        # df_tmp2 = ak.stock_individual_info_em(symbol='002283', timeout=30000)
        # stock_data2 = df_tmp2.set_index('item')['value'].to_dict()        
        # # 转换为DataFrame的一行
        # stock_row2 = pd.DataFrame([stock_data2])
        # print(stock_row2)

        # df_tmp3 = ak.stock_individual_info_em(symbol='300821', timeout=30000)
        # stock_data3 = df_tmp3.set_index('item')['value'].to_dict()        
        # # 转换为DataFrame的一行
        # stock_row3 = pd.DataFrame([stock_data3])
        # print(stock_row3)

        # self.df_stocks_eastmoney = pd.concat([self.df_stocks_eastmoney, stock_row1], ignore_index=True)
        # self.df_stocks_eastmoney = pd.concat([self.df_stocks_eastmoney, stock_row2], ignore_index=True)
        # self.df_stocks_eastmoney = pd.concat([self.df_stocks_eastmoney, stock_row3], ignore_index=True)

        # print("保存数据到Excel中...")
        # self.df_stocks_eastmoney.to_excel('./stocks/excel/stocks_eastmoney.xlsx', index=False)

        # 添加日期字段
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        self.df_stocks_eastmoney['日期'] = today
        print(self.df_stocks_eastmoney.tail(3))
        self.stocks_db.insert_stock_data_from_eastmoney(self.df_stocks_eastmoney)
        return

    
        for key, value in self.dict_stocks.items():
            # 检查 DataFrame 是否为空
            if value.empty:
                continue
            
            index = 1
            for index, row in value.iterrows():
                try:
                    stock_code = row['证券代码']
                    # print("stock_code的类型：", type(stock_code))
                    print(f"正在获取第 {index} 只股票：{stock_code}")
                    stock_individual_info_em_df = ak.stock_individual_info_em(symbol=stock_code, timeout=30000)
                    # print("stock_individual_info_em_df的类型：", type(stock_individual_info_em_df))
                    # add_stock_data(self.df_stocks_eastmoney, stock_individual_info_em_df)
                    # print("stock_individual_info_em_df:", stock_individual_info_em_df)

                    # 将键值对形式的DataFrame转换为一行数据
                    # 方法1: 使用pivot或set_index + unstack
                    stock_data = stock_individual_info_em_df.set_index('item')['value'].to_dict()
                    
                    # 转换为DataFrame的一行
                    stock_row = pd.DataFrame([stock_data])
                    # print("转换后的数据:", stock_row)
                    
                    # 合并到总数据中
                    self.df_stocks_eastmoney = pd.concat([self.df_stocks_eastmoney, stock_row], ignore_index=True)
                    

                    sleep_time = random.uniform(0.5, 1)
                    # time.sleep(sleep_time)

                except Exception as e:
                    print(f"处理股票 {stock_code} 时出错: {e}")
                    continue
        
        # 打印最后处理的股票数据
        print("\n处理后的数据:\n")
        print(self.df_stocks_eastmoney.tail(3))
        # self.df_stocks_eastmoney.to_excel('./stocks/excel/stocks_eastmoney.xlsx', index=False)
        self.stocks_db.insert_stock_data_from_eastmoney(self.df_stocks_eastmoney)

    def query_eastmoney_stock_data(self):
        return self.stocks_db.query_eastmoney_stock_data()

    def get_latest_eastmoney_stock_data(self):
        return self.stocks_db.get_latest_eastmoney_stock_data()

# 测试代码
if __name__ == "__main__":
    # 测试函数
    # test_stock_code = "000001"
    
    # 测试获取最近一个交易日的数据
    # latest_daily_result = process_latest_daily_data(test_stock_code)
    # print(f"最近交易日数据处理结果: {'成功' if latest_daily_result else '失败'}")
    
    # 测试获取最近一周的周线数据
    # latest_weekly_result = process_latest_weekly_data(test_stock_code)
    # print(f"最近周线数据处理结果: {'成功' if latest_weekly_result else '失败'}")
    print("stock_data_processor.py run")