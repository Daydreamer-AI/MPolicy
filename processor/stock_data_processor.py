import akshare as ak
import pandas as pd
import sqlite3
import os
import datetime
from pathlib import Path
from data_base import StockDBManager, StockDbBase
import datetime
from indicators import stock_data_indicators as sdi
import random
import time

class StockDataProcessor:
    '''
    
    维护：
    1. 所有股票日线、周线数据？内存能否扛住？
    2. 不维护股票数据，随用随删。
    '''
    def __init__(self):
        self.stocks_db = StockDBManager(0)
        self.day_stock_db = StockDbBase("./stocks/db/akshare/day")
        self.week_stock_db = StockDbBase("./stocks/db/akshare/week")

    
    # 股票数据接口
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
    def get_main_stocks(self):
        # 获取主板股票信息
        return self.stocks_db.query_stocks(None, 'MAIN')
    
    def get_gem_stocks(self):
        # 获取创业板股票信息
        return self.stocks_db.query_stocks(None, 'GEM')
    
    def get_star_stocks(self):
        # 获取科创版股票信息
        return self.stocks_db.query_stocks(None, 'STAR')
    
    def get_bse_stocks(self):
        # 获取北交所股票信息
        return self.stocks_db.query_stocks(None, 'BSE')
    
    def print_stocks_info(self):
        main_stocks = self.get_main_stocks()
        print("main--main_stocks的类型：", type(main_stocks))
        print("主板股票数量：", len(main_stocks))

        gem_stocks = self.get_gem_stocks()
        print("创业板股票数量：", len(gem_stocks))

        star_stocks = self.get_star_stocks()
        print("科创版股票数量：", len(star_stocks))

        bse_stocks = self.get_bse_stocks()
        print("北交所股票数量：", len(bse_stocks))

    def update_all_stocks_info(self):
        # 初始化数据库  ./stocks/db/stocks.db
        # db_manager = StockDBManager("./stocks/db/stocks.db")

        # 获取股票代码和名称
        # 获取A股所有股票代码和名称
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

        # 创业板
        cyb = df[df["code"].str.startswith("300")]
        print("创业板股票数量：", cyb.shape[0])
        print("cyb: ")
        print(cyb.tail(3))
        print("\n")
        cyb_stocks_data = []
        for _, row in cyb.iterrows():
            stock = {
                "stock_code": row["code"],
                "stock_name": row["name"],
                "board_type": "GEM",
                "is_st": 0             # 非ST股票
            }
            cyb_stocks_data.append(stock)
        
        # 批量插入数据库
        inserted_count = self.stocks_db.batch_insert_stocks(cyb_stocks_data)
        print(f"成功插入 {inserted_count} 条创业板股票记录")


        # 科创板
        kcb = df[df["code"].str.startswith("688")]
        print("科创板股票数量：", kcb.shape[0])
        print("kcb: ")
        print(kcb.tail(3))
        print("\n")
        kcb_stocks_data = []
        for _, row in kcb.iterrows():
            stock = {
                "stock_code": row["code"],
                "stock_name": row["name"],
                "board_type": "STAR",
                "is_st": 0             # 非ST股票
            }
            kcb_stocks_data.append(stock)
        
        # 批量插入数据库
        inserted_count = self.stocks_db.batch_insert_stocks(kcb_stocks_data)
        print(f"成功插入 {inserted_count} 条科创版股票记录")

        # 北交所
        bjs = df[df["code"].str.startswith("8")]
        print("北交所股票数量：", bjs.shape[0])
        print("bjs: ")
        print(bjs.tail(3))
        print("\n")

        bjs_stocks_data = []
        for _, row in bjs.iterrows():
            stock = {
                "stock_code": row["code"],
                "stock_name": row["name"],
                "board_type": "BSE",
                "is_st": 0             # 非ST股票
            }
            bjs_stocks_data.append(stock)
        
        # 批量插入数据库
        inserted_count = self.stocks_db.batch_insert_stocks(bjs_stocks_data)
        print(f"成功插入 {inserted_count} 条北交所股票记录")
    
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

    # 筛选接口
    def daily_filter(self, stock_code):
        # 1.更新最新日线、周线数据
        # if not process_latest_daily_data(stock_code):
        #     print("更新日线数据失败")
        #     return False    

        # if not process_latest_weekly_data(stock_code):
        #     print("更新周线数据失败")
        #     return False    

        # 2.得到最新的日线、周线数据
        end_date = datetime.datetime.now().strftime("%Y%m%d")
        start_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y%m%d")
        print("end_date:", end_date)
        print("start_date:", start_date)

        db_manager = StockDBManager()
        df_dayily = db_manager.get_akshare_stock_data("000001")
        print("近30天日线数据：")
        print(df_dayily.tail(3))

        df_week = db_manager.get_week_stock_data("000001")
        print("近30天周线数据：")
        print(df_dayily.tail(3))

        print("最后一组数据：")
        print("日线收盘：", df_dayily.tail(1)['收盘'])
        print("日线MA24：", df_dayily.tail(1)['MA24'])
        print("日线MA52：", df_dayily.tail(1)['MA52'])
        print("日线MA52*1.1：", df_dayily.tail(1)['MA52']*1.1)

        print("\n周线数据：")
        print("周线收盘：", df_week.tail(1)['收盘'])
        print("周线MA24：", df_week.tail(1)['MA24'])
        print("周线MA52：", df_week.tail(1)['MA52'])

        # 判断逻辑
        # 1. 周线收盘价 > 周线MA52
        # 2. 日线收盘价与日线MA52的差值 < 日线MA52 * 1.1
        if (df_week.tail(1)['收盘'] > df_week.tail(1)['MA52']) and (abs(df_dayily.tail(1)['收盘'] - df_dayily.tail(1)['MA52']) < df_dayily.tail(1)['MA52'] * 1.1):
            print("符合多空逻辑")
            return True
        else:
            print("不符合多空逻辑")
            return False

    def daily_filter(self, day_stock_data, week_stock_data):
        # 检查MA52列是否存在空值
        if week_stock_data['MA52'].isnull().any() or day_stock_data['MA52'].isnull().any():
            print("存在空值，跳过判断")
            return False

        # print("day_stock_data的类型：", type(day_stock_data))     # <class 'pandas.core.frame.DataFrame'>
        # print("week_stock_data的类型：", type(week_stock_data))   # <class 'pandas.core.frame.DataFrame'>

        # 提取单个值代替Series
        last_week_row = week_stock_data.tail(1)
        last_day_row = day_stock_data.tail(1)
        # 检查列是否存在
        if '收盘' in week_stock_data.columns and 'MA52' in week_stock_data.columns:
            week_close = last_week_row['收盘'].item()
            week_ma52 = last_week_row['MA52'].item()
        else:
            print("错误：周线数据必要的列不存在")
            print("可用列：", week_stock_data.columns.tolist())
            return False  # 或者处理错误情况
        
        if '收盘' in day_stock_data.columns and 'MA52' in day_stock_data.columns:
            day_close = last_day_row['收盘'].item()
            day_ma52 = last_day_row['MA52'].item()
        else:
            print("错误：日线数据必要的列不存在")
            print("可用列：", week_stock_data.columns.tolist())
            return False  # 或者处理错误情况

        # last_close = last_week_row['收盘'].item()
        # last_ma52 = last_week_row['MA52'].item()
        # day_close = last_day_row['收盘'].item()
        # day_ma52 = last_day_row['MA52'].item()

        # 修改后条件判断
        if (week_close > week_ma52) and (abs(day_close - day_ma52) < day_ma52 * 0.1):
        # 执行逻辑
        # if (week_stock_data.tail(1)['收盘'] > week_stock_data.tail(1)['MA52']) and (abs(day_stock_data.tail(1)['收盘'] - day_stock_data.tail(1)['MA52']) < day_stock_data.tail(1)['MA52'] * 1.1):
            print("符合多空逻辑")
            return True
        else:
            # print("不符合多空逻辑")
            return False

    # 自动化流程接口
    def auto_process_main_stock_filter(self) :
        result_stock_data = []
        # 步骤一：更新主板股票信息
        # main_board_stocks_info = self.update_main_stocks_info()
        # print("main_board_stocks_info的类型：", type(main_board_stocks_info)) # <class 'list'>
        main_board_stocks_info = self.get_main_stocks()
        # print("main_board_stocks_info的类型：", type(main_board_stocks_info))
        # print(main_board_stocks_info[0][1])

        # 步骤二：更新主板股票日线&周线数据
        i = 1
        for item in main_board_stocks_info:
            stock_code = item[1]
            if i > 1000:
                break
            print(f"正在处理第 {i} 只股票，代码：{stock_code},名称：{item[2]}")
            i += 1

            # if self.day_stock_db.check_stock_db_exists(stock_code):
            #     day_stock_data = self.update_day_stock_data(stock_code)
            #     # print("day_stock_data的类型：", type(day_stock_data)) #<class 'pandas.core.frame.DataFrame'>
            #     if day_stock_data.empty:
            #         print(f"更新股票 {stock_code} 日线数据失败") 
            #         continue
            # else:
            #     day_stock_data = self.process_day_stock_data(stock_code)
            #     if day_stock_data.empty:
            #         print(f"处理股票 {stock_code} 日线数据失败")
            #         continue

            day_stock_data = self.process_day_stock_data(stock_code)

            if day_stock_data.empty:
                # print(f"处理股票 {stock_code} 【日线】数据失败")
                continue
            
            # if day_stock_data.empty:
            #     print(f"处理股票 {stock_code} 日线数据失败")
            #     continue

            # if self.week_stock_db.check_stock_db_exists(stock_code):
            #     if not self.update_week_stock_data(stock_code):
            #         print(f"更新股票 {stock_code} 周线数据失败")
            # else:
            #     if not self.process_week_stock_data(stock_code):
            #         print(f"处理股票 {stock_code} 周线数据失败")

            week_stock_data = self.process_week_stock_data(stock_code)
            
            if week_stock_data.empty:
                # print(f"处理股票 {stock_code} 【周线】数据失败")
                continue

            # # 步骤三：执行主板股票筛选
            if self.daily_filter(day_stock_data, week_stock_data):
                result_stock_data.append(stock_code)

        return result_stock_data


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