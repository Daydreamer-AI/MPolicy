import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime
import pandas as pd
import threading
import time
import numpy as np
from data_base.common_db_manager import CommonDBManager

class DBManagerPool:
    """管理多个 StockDBManager 实例的池（单例模式）"""
    
    # 使用类变量存储唯一实例，并添加volatile语义（通过线程锁保证可见性）
    _instance = None
    _lock = threading.RLock()  # 使用可重入锁
    
    def __new__(cls):
        """重写 __new__ 方法控制实例创建"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    # 初始化实例变量
                    cls._instance._managers = {}
        return cls._instance
    
    def __init__(self):
        """初始化方法"""
        # 确保只初始化一次
        if not hasattr(self, '_initialized'):
            with self._lock:
                if not hasattr(self, '_initialized'):
                    self._managers = {}
                    self._initialized = True
    
    def get_manager(self, db_type, key=None):
        """获取指定类型的数据库管理器实例"""
        if key is None:
            key = f"default_{db_type}"
            
        # 只使用一个锁
        if key not in self._managers:
            with self._lock:  # 使用类级别的锁
                if key not in self._managers:
                    self._managers[key] = StockDBManager(db_type)
        return self._managers[key]
            
    def close_all(self):
        """关闭所有数据库管理器"""
        with self._lock:
            for key, manager in list(self._managers.items()):
                manager.close_connection()
                del self._managers[key]
                
    def __del__(self):
        """析构时自动关闭所有连接"""
        self.close_all()

class StockDBManager(CommonDBManager):
    """
    股票数据库管理类，用于管理stocks/db/stocks.db股票数据库, 存储的是A股所有非ST股票信息
    day目录：存储日线数据
    two_days目录：存储两日线数据
    three_days目录：存储三日线数据
    week目录：存储周线数据
    month目录：存储月线数据
    """
    
    def __init__(self, db_type = 0):
        self.db_type = db_type
        db_path_tmp = self._get_db_path_by_type(db_type)
        
        # 调用父类构造函数
        super().__init__(db_path_tmp)
        print("StockDBManager--self._init_db()")
        self._init_db()

    def _get_db_path_by_type(self, db_type):
        """根据db_type获取数据库路径"""
        if db_type == 1:
            return "./stocks/db/baostock/stocks.db"
        elif db_type == 2:
            return "./stocks/db/efinance/stocks.db"
        else:
            return "./stocks/db/akshare/stocks.db"

    def init_baostock_db(self):
        self.create_table('stock_basic_info', '''
                    CREATE TABLE IF NOT EXISTS stock_basic_info (
                        证券代码 TEXT PRIMARY KEY NOT NULL,
                        交易状态 TEXT NOT NULL UNIQUE,
                        证券名称 TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

    def init_efinance_db(self):
        self.create_table('stock_basic_info', '''
                    CREATE TABLE IF NOT EXISTS stock_basic_info (
                        stock_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        stock_code VARCHAR(10) NOT NULL UNIQUE,
                        stock_name VARCHAR(50) NOT NULL,
                        board_type TEXT CHECK(board_type IN ('MAIN','GEM','STAR','BSE')),
                        is_st BOOLEAN DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

    def _init_db(self):
        """初始化数据库表结构"""
        # with self._lock:
        # 创建股票基本信息表
        #MAIN    ​主板    上交所 + 深交所
        #GEM     ​创业板   深交所
        #STAR    ​科创板   上交所
        #BSE     ​北交所   深交所
        # 调用相应的初始化方法
        if self.db_type == 0:
            self.init_akshare_db()
        elif self.db_type == 1:
            self.init_baostock_db()
        elif self.db_type == 2:
            self.init_efinance_db()
        print(f"股票数据库已初始化: {self.db_path}")

    # ========================================================================AKShare相关接口========================================================================
    # AKShare
    def init_akshare_db(self):
        """初始化AKShare数据库表结构"""
        
        # 1. 创建A股所有股票表 - 使用父类方法（推荐）
        self.create_table('stock_basic_info', '''
            CREATE TABLE IF NOT EXISTS stock_basic_info (
                证券代码 TEXT PRIMARY KEY NOT NULL,
                证券名称 TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 2. 创建同花顺行业板块一览表 - 使用父类方法
        self.create_table('board_industry', '''
            CREATE TABLE IF NOT EXISTS board_industry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                serial_number INTEGER NOT NULL,
                industry_name TEXT NOT NULL,
                change_percent REAL NOT NULL,
                total_volume REAL NOT NULL,
                total_amount REAL NOT NULL,
                net_inflow REAL NOT NULL,
                rising_count INTEGER NOT NULL,
                falling_count INTEGER NOT NULL,
                avg_price REAL NOT NULL,
                leading_stock TEXT NOT NULL,
                leading_stock_price REAL NOT NULL,
                leading_stock_change_percent REAL NOT NULL,
                data_date TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(industry_name, data_date)  -- 关键：基于行业名称和日期的唯一约束
            )
        ''')

        # 3. 创建东方财富股票数据表 - 使用父类方法
        self.create_table('stock_data_eastmoney', '''
            CREATE TABLE IF NOT EXISTS stock_data_eastmoney (
                stock_code TEXT NOT NULL,
                date TEXT NOT NULL,
                latest_price REAL,
                stock_name TEXT,
                total_shares REAL,
                float_shares REAL,
                total_market_cap REAL,
                float_market_cap REAL,
                industry TEXT,
                list_date TEXT,
                PRIMARY KEY (stock_code, date)
            )
        ''')

        # 4. 创建索引 - 使用专门的方法或直接SQL
        try:
            with self._get_connection() as cur:
                # 同花顺行业板块索引
                cur.execute('CREATE INDEX IF NOT EXISTS idx_board_industry_data_date ON board_industry(data_date)')
                cur.execute('CREATE INDEX IF NOT EXISTS idx_board_industry_industry_name ON board_industry(industry_name)')
                cur.execute('CREATE INDEX IF NOT EXISTS idx_board_industry_change_percent ON board_industry(change_percent)')
                
                # 东方财富股票数据索引
                cur.execute('CREATE INDEX IF NOT EXISTS idx_stock_data_eastmoney_stock_code ON stock_data_eastmoney(stock_code)')
                cur.execute('CREATE INDEX IF NOT EXISTS idx_stock_data_eastmoney_data_date ON stock_data_eastmoney(date)')
                cur.execute('CREATE INDEX IF NOT EXISTS idx_stock_data_eastmoney_industry_name ON stock_data_eastmoney(industry)')
                
            print("所有索引创建成功")
            
        except sqlite3.Error as e:
            print(f"创建索引时发生数据库错误: {str(e)}")
            raise
        except Exception as e:
            print(f"创建索引时发生错误: {str(e)}")
            raise
    # ------------------------------------------------------------A股股票信息表接口----------------------------------------------

    # ------------------------------------------------------------同花顺行业板块一览表接口-----------------------------------------
    def insert_ths_board_industry_data_to_db(self, df_industry_data):
        try:
            # 重命名列以匹配数据库表结构
            df = df_industry_data.rename(columns={
                '序号': 'serial_number',
                '板块': 'industry_name',
                '涨跌幅': 'change_percent',
                '总成交量': 'total_volume',
                '总成交额': 'total_amount',
                '净流入': 'net_inflow',
                '上涨家数': 'rising_count',
                '下跌家数': 'falling_count',
                '均价': 'avg_price',
                '领涨股': 'leading_stock',
                '领涨股-最新价': 'leading_stock_price',
                '领涨股-涨跌幅': 'leading_stock_change_percent',
                '日期': 'data_date'
            })
            
            # 使用 replace 模式，配合 UNIQUE(industry_name, data_date) 约束实现更新
            # 问题：会删除掉旧数据，不适用
            # inserted_count = self.insert_dataframe_to_table(
            #     'board_industry', df, 'replace',  # 使用 replace 模式
            #     validate_columns=False, fast_mode=False  # 不使用快速模式以确保约束生效
            # )
        
            # print(f"数据插入完成，处理了 {inserted_count} 条记录")
            # return True
        
            # 方式二：使用 upsert 功能，明确指定冲突列
            upserted_count = self.upsert_data(
                'board_industry',
                df.to_dict('records'),
                conflict_columns=['industry_name', 'data_date']  # 明确指定冲突检测列
            )
            
            print(f"数据upsert完成，处理了 {upserted_count} 条记录")
            # return True

            
        except Exception as e:
            print(f"插入数据失败: {e}")
            return False

    def query_ths_board_industry_data(self, date=None, industry_name=None):
        """查询行业数据"""
        conditions = []
        params = []
        
        if date:
            conditions.append("data_date = ?")
            params.append(date)
        
        if industry_name:
            conditions.append("industry_name LIKE ?")
            params.append(f"%{industry_name}%")

        query = "SELECT * FROM board_industry"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY data_date DESC, change_percent DESC"
        
        try:
            with self._get_connection() as cur:
                cur.execute(query, params)
                column_names = [description[0] for description in cur.description]
                rows = cur.fetchall()
                return pd.DataFrame(rows, columns=column_names)
        except Exception as e:
            print(f"查询同花顺行业板块一览表时出错: {str(e)}")
            return pd.DataFrame()

    def get_latest_ths_board_industry_data(self):
        """获取最新日期的所有行业数据"""
        try:
            with self._get_connection() as cur:
                cur.execute('''
                    SELECT * FROM board_industry 
                    WHERE data_date = (SELECT MAX(data_date) FROM board_industry)
                    ORDER BY change_percent DESC
                ''')
                
                column_names = [description[0] for description in cur.description]
                rows = cur.fetchall()
                
                if rows:
                    return pd.DataFrame(rows, columns=column_names)
                else:
                    return pd.DataFrame()
                    
        except Exception as e:
            print(f"查询同花顺行业板块一览表时出错: {str(e)}")
            return pd.DataFrame()
    # ------------------------------------------------------------东方财富股票数据表stock_data_eastmoney接口-----------------------------------------
    def insert_eastmoney_stock_data_to_db(self, df_stock_data):
        try:
            # 重命名列以匹配数据库表结构
            df_filtered = df_stock_data.rename(columns={
                '股票代码': 'stock_code',
                '日期': 'date',
                '最新': 'latest_price',
                '股票简称': 'stock_name',
                '总股本': 'total_shares',
                '流通股': 'float_shares',
                '总市值': 'total_market_cap',
                '流通市值': 'float_market_cap',
                '行业': 'industry',
                '上市时间': 'list_date'
            })
            
            # 处理特殊数据
            if 'latest_price' in df_filtered.columns:
                df_filtered['latest_price'] = df_filtered['latest_price'].apply(
                    lambda x: None if x == '-' or pd.isna(x) else float(x)
                )
            
            # 使用 upsert 功能，基于股票代码和日期的复合主键进行更新
            upserted_count = self.upsert_data(
                'stock_data_eastmoney',
                df_filtered.to_dict('records'),
                conflict_columns=['stock_code', 'date']  # 基于股票代码和日期的冲突检测
            )
            
            print(f"数据upsert完成，处理了 {upserted_count} 条记录")
            return True
                
        except Exception as e:
            print(f"插入数据失败: {e}")
            return False

    def query_eastmoney_stock_data(self, date=None, stock_code=None, industry_name=None):
        """查询东方财富股票数据"""
        conditions = []
        params = []
        
        if date:
            conditions.append("date = ?")
            params.append(date)
        
        if stock_code:
            conditions.append("stock_code = ?")
            params.append(stock_code)
        
        if industry_name:
            conditions.append("industry LIKE ?")
            params.append(f"%{industry_name}%")

        query = "SELECT * FROM stock_data_eastmoney"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY date DESC, stock_code"
        
        try:
            with self._get_connection() as cur:
                cur.execute(query, params)
                column_names = [description[0] for description in cur.description]
                rows = cur.fetchall()
                return pd.DataFrame(rows, columns=column_names)
        except Exception as e:
            print(f"查询东方财富股票数据表时出错: {str(e)}")
            return pd.DataFrame()

    def get_latest_eastmoney_stock_data(self):
        """获取最新日期的所有股票数据"""
        try:
            with self._get_connection() as cur:
                cur.execute('''
                    SELECT * FROM stock_data_eastmoney 
                    WHERE date = (SELECT MAX(date) FROM stock_data_eastmoney)
                    ORDER BY date DESC
                ''')
                
                column_names = [description[0] for description in cur.description]
                rows = cur.fetchall()
                
                if rows:
                    return pd.DataFrame(rows, columns=column_names)
                else:
                    return pd.DataFrame()
                    
        except Exception as e:
            print(f"查询东方财富股票数据表时出错: {str(e)}")
            return pd.DataFrame()

    def get_stock_data_by_code(self, stock_code, limit_days=30):
        """获取指定股票最近N天的数据"""
        try:
            with self._get_connection() as cur:
                cur.execute('''
                    SELECT * FROM stock_data_eastmoney 
                    WHERE stock_code = ?
                    ORDER BY date DESC
                    LIMIT ?
                ''', (stock_code, limit_days))
                
                column_names = [description[0] for description in cur.description]
                rows = cur.fetchall()
                
                if rows:
                    return pd.DataFrame(rows, columns=column_names)
                else:
                    return pd.DataFrame()
                    
        except Exception as e:
            print(f"查询东方财富股票数据表时出错: {str(e)}")
            return pd.DataFrame()

    # ========================================================================BaoStock相关接口========================================================================
    # 添加以下方法到StockDBManager类
    # Baostock
    def save_tao_stocks_to_db(self, stocks_data, writeWay="replace", table_name="stock_basic_info"):
        """
        线程安全地保存股票数据到数据库
        
        :param stocks_data: 股票数据 (pandas.DataFrame)
        :param writeWay: 写入方式 ("replace", "append", "fail")
        :param table_name: 表名
        :return: 插入的行数
        """
        allowed_table_names = ['stock_basic_info', 'sh_main', 'sz_main', 'gem', 'star', 'bse']
        if table_name not in allowed_table_names:
            raise ValueError(f"Invalid table name: {table_name}")

        # 确保表存在
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            证券代码 TEXT PRIMARY KEY NOT NULL,
            交易状态 TEXT NOT NULL,
            证券名称 TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        self.create_table(table_name, create_table_sql)
        
        # 数据预处理
        if not stocks_data.empty:
            # 确保必要列存在
            required_columns = ['证券代码', '交易状态', '证券名称']
            for col in required_columns:
                if col not in stocks_data.columns:
                    raise ValueError(f"缺少必要列: {col}")
            
            # 使用父类方法处理数据插入
            inserted_count = self.insert_dataframe_to_table(
                table_name, 
                stocks_data, 
                writeWay,
                validate_columns=False,
                fast_mode=True
            )
            
            print(f"成功保存 {inserted_count} 条 {table_name} 股票数据")
            return inserted_count
        
        print(f"没有数据需要保存到 {table_name}")
        return 0

    def get_stocks_with_filter(self, table_name, status_filter=None):
        """
        获取股票数据并支持状态过滤
        
        :param table_name: 表名
        :param status_filter: 交易状态过滤条件
        :return: DataFrame格式的股票数据
        """
        df = self.get_table_data(table_name)
        
        if status_filter and not df.empty:
            df = df[df['交易状态'] == status_filter]
        
        return df
    def get_sh_main_stocks(self):
        return self.get_table_data('sh_main')
        
    def get_sz_main_stocks(self):
        return self.get_table_data('sz_main')

    def get_gem_stocks(self):
        return self.get_table_data('gem')
    
    def get_star_stocks(self):
        return self.get_table_data('star')


# 测试代码
if __name__ == "__main__":
    print("stocks_db_manager.py run")