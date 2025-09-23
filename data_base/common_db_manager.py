import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime
import pandas as pd
import threading
import time
import numpy as np

class CommonDBManagerPool:
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
                self._managers[key] = CommonDBManager(db_type)
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

class CommonDBManager:
    """
    通用数据库管理器
    """
    def __init__(self, db_path=''):
        self.db_path = os.path.abspath(db_path)  # 转为绝对路径
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
        
    @contextmanager
    def _get_connection_object(self):
        """线程安全的数据库连接获取（返回连接对象）"""
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect(
                self.db_path, 
                check_same_thread=False,
                timeout=30
            )
            self._local.conn.execute('PRAGMA journal_mode=WAL')
        
        try:
            yield self._local.conn
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
        # 建表检查
        pass

    def get_db_path(self, stock_code):
        return self.db_path
    
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
    
    def insert_dataframe_to_table(self, table_name, df_data, if_exists="replace"):
        """
        将pandas.DataFrame数据插入到指定表中
        
        :param table_name: 表名
        :param df_data: pandas.DataFrame格式的数据
        :param if_exists: 如果表已存在数据时的处理方式
                        "replace" - 替换原有数据（默认）
                        "append" - 追加数据
                        "fail" - 如果表中有数据则抛出异常
                        "ignore" - 忽略重复数据
        :return: 插入的行数
        """
        # 参数验证
        if not table_name:
            raise ValueError("表名不能为空")
        
        if df_data is None or df_data.empty:
            print(f"警告: 要插入的数据为空，未执行插入操作")
            return 0
        
        if not isinstance(df_data, pd.DataFrame):
            raise ValueError("df_data必须是pandas.DataFrame类型")
            
        if if_exists not in ["replace", "append", "fail", "ignore"]:
            raise ValueError("if_exists参数必须是'replace', 'append', 'fail', 'ignore'之一")

        try:
            # 检查表是否存在数据
            with self._get_connection() as cur:
                cur.execute(f"SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                table_exists = cur.fetchone()[0] > 0
                
                if table_exists:
                    cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                    row_count = cur.fetchone()[0]
                    
                    if row_count > 0:
                        if if_exists == "fail":
                            raise ValueError(f"表 {table_name} 中已存在数据，根据if_exists='fail'参数，操作被终止")
                        elif if_exists == "replace":
                            cur.execute(f"DELETE FROM {table_name}")
                            print(f"已清空表 {table_name} 中的 {row_count} 行数据")
                        elif if_exists == "ignore":
                            # 对于ignore模式，我们检查主键冲突，只插入不重复的数据
                            print(f"表 {table_name} 中已存在数据，将忽略重复数据进行插入")
                else:
                    print(f"表 {table_name} 不存在，将创建新表")

            # 获取DataFrame的列名
            columns = list(df_data.columns)
            if not columns:
                raise ValueError("DataFrame没有有效的列")
            
            # 准备插入语句
            placeholders = ', '.join('?' * len(columns))
            columns_str = ', '.join([f'"{col}"' for col in columns])  # 用引号包围列名防止关键字冲突
            
            # 根据if_exists参数选择不同的插入策略
            if if_exists == "ignore":
                insert_sql = f'INSERT OR IGNORE INTO "{table_name}" ({columns_str}) VALUES ({placeholders})'
            else:
                insert_sql = f'INSERT OR REPLACE INTO "{table_name}" ({columns_str}) VALUES ({placeholders})'
            
            # 将DataFrame转换为记录列表
            records = df_data.to_dict('records')
            
            # 处理缺失值，将NaN替换为None
            processed_records = []
            for record in records:
                processed_record = {}
                for key, value in record.items():
                    # 处理NaN值
                    if pd.isna(value):
                        processed_record[key] = None
                    # 处理numpy数据类型
                    elif isinstance(value, (np.integer, np.floating)):
                        processed_record[key] = value.item()  # 转换为Python原生类型
                    elif isinstance(value, np.bool_):
                        processed_record[key] = bool(value)
                    else:
                        processed_record[key] = value
                processed_records.append(tuple(processed_record.values()))
            
            # 执行批量插入
            with self._get_connection() as cur:
                cur.executemany(insert_sql, processed_records)
                row_count = cur.rowcount
                print(f"成功向表 {table_name} {if_exists} {row_count} 行数据")
                return row_count
                
        except sqlite3.Error as e:
            error_msg = f"向表 {table_name} 插入数据时发生数据库错误: {str(e)}"
            print(error_msg)
            raise
        except Exception as e:
            error_msg = f"向表 {table_name} 插入数据时发生错误: {str(e)}"
            print(error_msg)
            raise