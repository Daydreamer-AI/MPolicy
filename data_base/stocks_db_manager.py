import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime
import pandas as pd
import threading
import time



class DBManagerPool:
    """管理多个 StockDBManager 实例的池（单例模式）"""
    
    # 使用类变量存储唯一实例，并添加volatile语义（通过线程锁保证可见性）
    _instance = None
    _lock = threading.RLock()  # 使用可重入锁
    
    def __new__(cls):
        """重写 __new__ 方法控制实例创建"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                # 初始化实例变量
                cls._instance._managers = {}
                cls._instance._init_lock = threading.RLock()
        return cls._instance
    
    def __init__(self):
        """初始化方法（由于__new__已控制创建，这里可避免重复初始化）"""
        # 确保只初始化一次
        if not hasattr(self, '_initialized'):
            with self._init_lock:
                if not hasattr(self, '_initialized'):
                    self._managers = {}
                    self._initialized = True
    
    def get_manager(self, db_type, key=None):
        """获取指定类型的数据库管理器实例"""
        if key is None:
            key = f"default_{db_type}"
            
        with self._init_lock:  # 使用实例级别的锁
            if key not in self._managers:
                self._managers[key] = StockDBManager(db_type)
            return self._managers[key]
            
    def close_all(self):
        """关闭所有数据库管理器"""
        with self._init_lock:
            for key, manager in list(self._managers.items()):
                manager.close_connection()
                del self._managers[key]
                
    def __del__(self):
        """析构时自动关闭所有连接"""
        self.close_all()

class StockDBManager:
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
        db_path_tmp = ""
        if db_type == 1:
            db_path_tmp = "./stocks/db/baostock/stocks.db"
        elif db_type == 2:
            db_path_tmp = "./stocks/db/efinance/stocks.db"
        else:
            db_path_tmp = "./stocks/db/akshare/stocks.db"

        self.db_path = os.path.abspath(db_path_tmp)  # 转为绝对路径
        self._ensure_db_directory()  # 确保目录存在

        self._local = threading.local()     # 多线程隔离
        self._lock = threading.Lock()       # 保护​​共享资源​​

        self._init_db()

    def _ensure_db_directory(self):
        """确保数据库目录存在且有写入权限"""
        db_dir = os.path.dirname(self.db_path)
        if not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)  # 递归创建目录
                print(f"创建目录: {db_dir}")
            except OSError as e:
                raise PermissionError(f"无法创建目录 {db_dir}: {str(e)}")
        
        # 验证目录可写性
        if not os.access(db_dir, os.W_OK):
            raise PermissionError(f"目录无写入权限: {db_dir}")
        
    @contextmanager
    def _get_connection(self):
        """线程安全的数据库连接获取"""
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect(
                self.db_path, 
                check_same_thread=False,
                timeout=30
            )
            self._local.conn.execute('PRAGMA journal_mode=WAL')
        
        try:
            cursor = self._local.conn.cursor()
            yield cursor
            self._local.conn.commit()
        except sqlite3.Error as e:
            self._local.conn.rollback()
            raise e

    def close_connection(self):
        """关闭当前线程的数据库连接"""
        if hasattr(self._local, 'conn'):
            self._local.conn.close()
            del self._local.conn

    def _init_db(self):
        """初始化数据库表结构"""
        with self._lock:
            # 创建股票基本信息表
            #MAIN    ​主板    上交所 + 深交所
            #GEM     ​创业板   深交所
            #STAR    ​科创板   上交所
            #BSE     ​北交所   深交所
            '''
                'MAIN'应该对应主板板块，包括沪市主板和深市主板

                'GEM'对应创业板，英文全称是Growth Enterprise Market

                'STAR'对应科创板，英文全称是Sci-Tech innovAtion boaRd

                'BSE'对应北京证券交易所，英文全称是Beijing Stock Exchange
            '''
            if self.db_type == 0:
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
            elif self.db_type == 1:
                self.create_table('stock_basic_info', '''
                    CREATE TABLE IF NOT EXISTS stock_basic_info (
                        证券代码 TEXT PRIMARY KEY NOT NULL,
                        交易状态 TEXT NOT NULL UNIQUE,
                        证券名称 TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            elif self.db_type == 2:
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

            print(f"数据库已初始化: {self.db_path}")

    def get_db_path(self, stock_code):
        """
        获取指定股票代码的数据库路径
        
        参数:
            stock_code (str): 股票代码
            
        返回:
            Path: 数据库文件路径
        """
        return self.db_dir / f"{stock_code}.db"

    def check_stock_db_exists(self, stock_code):
        """
        检查指定股票的数据库是否存在
        
        参数:
            stock_code (str): 股票代码
            
        返回:
            bool: 存在返回True，否则返回False
        """
        db_path = self.get_db_path(stock_code)
        return db_path.exists()

    def count_sqlite_tables(self, db_path, max_retries: int = 3):
        """
        线程安全地统计SQLite数据库中的表数量
        
        参数:
            db_path: 数据库文件路径
            max_retries: 最大重试次数
            
        返回:
            表数量，如果出错返回None
        """
        for attempt in range(max_retries):
            try:
                with self._get_external_connection(db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table';")
                    table_count = cursor.fetchone()[0]
                    return table_count
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    # 数据库被锁定，等待后重试
                    wait_time = 0.1 * (attempt + 1)
                    print(f"数据库 {db_path} 被锁定，等待 {wait_time} 秒后重试...")
                    threading.Event().wait(wait_time)
                    continue
                else:
                    print(f"查询数据库 {db_path} 表数量失败: {e}")
                    return None
            except sqlite3.Error as e:
                print(f"查询数据库 {db_path} 表数量时发生错误: {e}")
                return None
        
        return None  # 所有重试尝试都失败

    def get_table_data(self, table="stock_basic_info"):
        """
        线程安全地获取股票数据
        
        :param table: 表名
        :return: pandas.DataFrame 格式的股票数据
        """
        try:
            # 使用线程安全的连接方式执行查询
            with self._get_connection() as cur:
                query = f"SELECT * FROM {table}"
                cur.execute(query)
                # 获取列名
                column_names = [description[0] for description in cur.description]
                # 获取所有数据
                rows = cur.fetchall()
                
                # 转换为 DataFrame
                df = pd.DataFrame(rows, columns=column_names)
                return df
        except Exception as e:
            print(f"获取股票数据时出错: {str(e)}")
            return pd.DataFrame()

    def create_table(self, table_name, create_table_sql):
        """
        根据自定义SQL语句创建数据表
        
        :param table_name: 表名
        :param create_table_sql: 建表SQL语句
        :return: True 表示成功
        """
        # 参数验证
        if not table_name:
            raise ValueError("表名不能为空")
        
        if not create_table_sql:
            raise ValueError("建表SQL语句不能为空")
        
        # 确保SQL语句是创建表的语句
        if not create_table_sql.strip().upper().startswith("CREATE TABLE"):
            raise ValueError("SQL语句必须是CREATE TABLE语句")
        
        # 使用线程安全的连接方式创建表
        with self._get_connection() as cur:
            try:
                cur.execute(create_table_sql)
                print(f"表 {table_name} 创建成功或已存在")
                return True
            except sqlite3.Error as e:
                print(f"创建表 {table_name} 失败: {str(e)}")
                raise

    # AKShare
    def insert_stock(self, stock_data):
        """插入单条股票数据
        :param stock_data: 字典格式 {
            'stock_code': '600000', 
            'stock_name': '浦发银行',
            'listing_date': '1999-11-10',
            'board_type': 'MAIN',
            'is_st': 0
        }
        """
        columns = ', '.join(stock_data.keys())
        placeholders = ', '.join('?' * len(stock_data))
        
        with self._get_connection() as cur:
            cur.execute(
                f"INSERT INTO stock_basic_info ({columns}) VALUES ({placeholders})",
                tuple(stock_data.values())
            )
            return cur.lastrowid

    def batch_insert_stocks(self, stocks_data, max_retries=3):
        """批量插入股票数据
        :param stocks_data: 字典列表格式
        """
        # if not stocks_data:
        #     return
        
        # columns = ', '.join(stocks_data[0].keys())
        # placeholders = ', '.join('?' * len(stocks_data[0]))
        
        # with self._get_connection() as cur:
        #     cur.executemany(
        #         f"INSERT OR IGNORE INTO stock_basic_info ({columns}) VALUES ({placeholders})",
        #         [tuple(stock.values()) for stock in stocks_data]
        #     )
        #     return cur.rowcount

        """批量插入股票数据 - 带重试机制"""
        if not stocks_data:
            return
        
        for attempt in range(max_retries):
            try:
                with self._get_connection() as cur:
                    columns = ', '.join(stocks_data[0].keys())
                    placeholders = ', '.join('?' * len(stocks_data[0]))
                    
                    cur.executemany(
                        f"INSERT OR IGNORE INTO stock_basic_info ({columns}) VALUES ({placeholders})",
                        [tuple(stock.values()) for stock in stocks_data]
                    )
                    return cur.rowcount
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    time.sleep(0.1 * (attempt + 1))
                    continue
                raise

    def update_stock(self, stock_code, update_data):
        """更新股票信息
        :param stock_code: 要更新的股票代码
        :param update_data: 待更新的字段字典
        """
        set_clause = ', '.join([f"{k}=?" for k in update_data.keys()])
        params = list(update_data.values())
        params.append(stock_code)
        
        with self._get_connection() as cur:
            cur.execute(
                f"UPDATE stock_basic_info SET {set_clause}, updated_at=CURRENT_TIMESTAMP WHERE stock_code=?",
                tuple(params)
            )
            return cur.rowcount

    def delete_stock(self, stock_code):
        """删除股票记录
        :param stock_code: 要删除的股票代码
        """
        with self._get_connection() as cur:
            cur.execute(
                "DELETE FROM stock_basic_info WHERE stock_code=?",
                (stock_code,)
            )
            return cur.rowcount

    def get_stock_by_code(self, stock_code):
        """根据股票代码查询单条记录"""
        with self._get_connection() as cur:
            cur.execute(
                "SELECT * FROM stock_basic_info WHERE stock_code=?",
                (stock_code,)
            )
            return cur.fetchone()

    def query_stocks(self, condition=None, board_type=None, is_st=False):
        """条件查询股票数据
        :param condition: 自定义WHERE条件字符串
        :param board_type: 筛选板块类型
        :param is_st: 是否筛选ST股票
        """
        query = "SELECT * FROM stock_basic_info"
        params = []
        
        # 构建查询条件
        conditions = []
        if condition:
            conditions.append(condition)
        if board_type:
            conditions.append("board_type=?")
            params.append(board_type)
        if is_st:
            conditions.append("is_st=1")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        with self._get_connection() as cur:
            cur.execute(query, tuple(params))
            return cur.fetchall()

    def get_all_stocks(self):
        """获取所有股票数据"""
        return self.query_stocks()

    # 添加以下方法到StockDBManager类
    def import_from_dataframe(self, df, board_type):
        """直接从DataFrame导入板块数据"""
        # 准备数据转换
        df = df.rename(columns={
            "code": "stock_code",
            "name": "stock_name"
        })
        df["board_type"] = board_type
        df["is_st"] = 0  # 默认非ST
        
        # 批量插入
        return self.batch_insert_stocks(df.to_dict("records"))

    # Baostock
    def save_tao_stocks_to_db(self, stocks_data, writeWay="replace", table_name="stock_basic_info"):
        """
        线程安全地保存股票数据到数据库
        
        :param stocks_data: 股票数据 (pandas.DataFrame)
        :param writeWay: 写入方式 ("replace", "append", "fail")
        :param table_name: 表名
        :return: True 表示成功
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
        
        # 使用线程安全的连接方式创建表
        with self._get_connection() as cur:
            cur.execute(create_table_sql)
            print("表创建成功或已存在")
        
        # 将 DataFrame 数据转换为列表形式以便使用线程安全的插入方式
        if not stocks_data.empty:
            # 为避免 UNIQUE 约束冲突，先删除原有数据（当 writeWay 为 replace 时）
            if writeWay == "replace":
                with self._get_connection() as cur:
                    cur.execute(f"DELETE FROM {table_name}")
            
            # 转换 DataFrame 为记录列表
            records = stocks_data.to_dict('records')
            
            # 准备插入语句
            columns = ['证券代码', '交易状态', '证券名称']
            placeholders = ', '.join('?' * len(columns))
            insert_sql = f"INSERT OR REPLACE INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            
            # 批量插入数据
            with self._get_connection() as cur:
                cur.executemany(insert_sql, [
                    (record.get('证券代码', ''), record.get('交易状态', ''), record.get('证券名称', '')) 
                    for record in records
                ])
        
        return True

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