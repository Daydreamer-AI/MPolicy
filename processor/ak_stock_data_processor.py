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
        self.stock_db_base = StockDbBase("./stocks/db/akshare")

        self.dict_stocks = {}   # key: 板块，value：板块对应的股票信息（证券代码、证券名称）- pandas.DataFrame对象
        self.df_stocks_eastmoney = pd.DataFrame() # 带有市值信息的股票数据 - pandas.DataFrame对象
        self.dict_chip_distribution_data_eastmoney = {}   # 东方财富的筹码分布数据 - 字典对象，key：股票代码，value： pandas.DataFrame对象

    def initialize(self) -> bool:
        self.dict_stocks = self.get_stock_info_from_db()
        self.df_stocks_eastmoney = self.stocks_db.get_latest_eastmoney_stock_data()
        # if file_exists('./stocks/excel/stocks_eastmoney.xlsx'):
        #     self.df_stocks_eastmoney = pd.read_excel('./stocks/excel/stocks_eastmoney.xlsx')
        # else:
        #     print('未找到./stocks/excel/stocks_eastmoney.xlsx')

        self.query_eastmoney_stock_chip_distribution_data()

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


    # ------------------------------------------------------------同花顺行业板块一览表接口-----------------------------------------
    def process_and_save_ths_board_industry(self):
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

        return self.stocks_db.insert_ths_board_industry_data_to_db(df)

    def query_ths_board_industry_data(self, date=None, industry_name=None):
        return self.stocks_db.query_ths_board_industry_data(date, industry_name)

    def get_latest_ths_board_industry_data(self):
        return self.stocks_db.get_latest_ths_board_industry_data()

    def process_and_save_stock_fund_flow_industry(self):
        stock_board_industry_name_em_df = ak.stock_board_industry_name_em()
        print(stock_board_industry_name_em_df)


    # --------------------------------------------------------暂无用----------------------------------------------------------
    
    # ------------------------------------------------------------------------------------------------------------------

    # ======================================================================东方财富接口============================================================

    # ------------------------------------------------------------东方财富股票数据表stock_data_eastmoney接口-----------------------------------------
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
        # today = datetime.datetime.now().strftime('%Y-%m-%d')
        # self.df_stocks_eastmoney['日期'] = today
        # print(self.df_stocks_eastmoney.tail(3))
        # self.stocks_db.insert_stock_data_from_eastmoney(self.df_stocks_eastmoney)
        # return

        print(self.df_stocks_eastmoney.tail(3))
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        if self.df_stocks_eastmoney is not None and not self.df_stocks_eastmoney.empty and today in self.df_stocks_eastmoney['date'].values:
            print("已是最新日期数据")
            return

        self.df_stocks_eastmoney = pd.DataFrame()
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
        self.df_stocks_eastmoney['日期'] = today
        print("\n处理后的数据:\n")
        print(self.df_stocks_eastmoney.tail(3))
        # self.df_stocks_eastmoney.to_excel('./stocks/excel/stocks_eastmoney.xlsx', index=False)
        self.stocks_db.insert_eastmoney_stock_data_to_db(self.df_stocks_eastmoney)

    def query_eastmoney_stock_data(self):
        return self.stocks_db.query_eastmoney_stock_data()

    def get_latest_eastmoney_stock_data(self):
        return self.stocks_db.get_latest_eastmoney_stock_data()
    
    # ------------------------------------------------------------东方财富股票筹码分布表stock_chip_distribution_data_eastmoney接口-----------------------------------------
    def get_and_insert_eastmoney_stock_chip_distribution_data_to_db(self):
        pass

    def update_and_insert_eastmoney_stock_chip_distribution_data_to_db(self):
        pass

    def process_and_insert_eastmoney_stock_chip_distribution_data_to_db(self):
        # self.dict_chip_distribution_data_eastmoney.clear()
        if self.dict_chip_distribution_data_eastmoney == {}:
            pass

        for board, df_data in self.dict_stocks.items():
            # 检查 DataFrame 是否为空
            if board == "" or df_data.empty:
                continue

            if board == "bse" or board == "star":
                continue
            
            db_dir = self.stock_db_base.get_src_db_dir()
            db_dir = db_dir / board
            print("db_dir: ", db_dir)
            self.stock_db_base.set_db_dir(db_dir)

            for index, row in df_data.iterrows():
                stock_code = row['证券代码']
                # print("stock_code的类型：", type(stock_code))

                print(f"正在获取第 {index} 只股票的筹码分布信息：{stock_code}")

                try:
                    stock_cyq_em_df = ak.stock_cyq_em(symbol=stock_code, adjust="qfq")
                    # print("stock_cyq_em_df的类型：", stock_cyq_em_df)

                    # if self.dict_chip_distribution_data_eastmoney[stock_code].empty:
                    #     # 不存在则全量更新
                    #     self.stock_db_base.insert_eastmoney_stock_chip_distribution_data_to_db(stock_code, stock_cyq_em_df)
                    #     # 优化：策略筛选只需要最后一行数据
                    #     self.dict_chip_distribution_data_eastmoney[stock_code] = stock_cyq_em_df
                    # else:
                    #     # 存在则增量更新
                    #     # combined_df = pd.concat([self.dict_chip_distribution_data_eastmoney[stock_code], stock_cyq_em_df], axis=0, ignore_index=True)
                    #     # 删除重复行（基于所有列）
                    #     # unique_df = combined_df.drop_duplicates()

                    #     self.dict_chip_distribution_data_eastmoney[stock_code]['日期'] = pd.to_datetime(self.dict_chip_distribution_data_eastmoney[stock_code]['日期'])
                    #     stock_cyq_em_df['日期'] = pd.to_datetime(stock_cyq_em_df['日期'])

                    #     # 找到 df1 中的最大日期（最后日期）
                    #     last_date_in_df1 = self.dict_chip_distribution_data_eastmoney[stock_code]['日期'].max()
                    #     print(f"df1 中的最后日期是: {last_date_in_df1}")

                    #     # 在 df2 中筛选所有日期大于 df1 最后日期的行
                    #     new_data_in_df2 = stock_cyq_em_df[stock_cyq_em_df['日期'] > last_date_in_df1] # 使用布尔索引进行条件筛选[2](@ref)

                    #     # 显示新增的数据
                    #     print(f"df2 中在 {last_date_in_df1} 之后的新增数据行数为: {len(new_data_in_df2)}")
                    #     print(new_data_in_df2)

                        # # 新增数据添加到数据库中
                        # self.stock_db_base.insert_eastmoney_stock_chip_distribution_data_to_db(stock_code, new_data_in_df2)

                    # 获取到的数据直接插入，接口内部会做去重
                    self.stock_db_base.insert_eastmoney_stock_chip_distribution_data_to_db(stock_code, stock_cyq_em_df)

                    sleep_time = random.uniform(0.1, 0.5)
                    time.sleep(sleep_time)
                    
                except Exception as e:
                        print(f"处理股票 {stock_code} 的筹码分布信息时出错: {e}")
                        continue
                

    def query_eastmoney_stock_chip_distribution_data(self):
        self.dict_chip_distribution_data_eastmoney.clear()
        for board, df_data in self.dict_stocks.items():
            # 检查 DataFrame 是否为空
            if board == "" or df_data.empty:
                continue
            
            db_dir = self.stock_db_base.get_src_db_dir()
            db_dir = db_dir / board
            print("db_dir: ", db_dir)
            self.stock_db_base.set_db_dir(db_dir)
            for index, row in df_data.iterrows():
                stock_code = row['证券代码']
                df_chip_distribution_data = self.stock_db_base.query_eastmoney_stock_chip_distribution_data(stock_code)

                # 优化：策略筛选只需要最后一行数据
                self.dict_chip_distribution_data_eastmoney[stock_code] = df_chip_distribution_data

    def get_latest_eastmoney_stock_chip_distribution_data(self, code):
        pass

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