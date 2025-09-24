import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime, timedelta
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
        self._lock = threading.Lock()       # 保护共享资源
        
        # 连接管理相关属性
        self._connection_timestamps = {}    # 记录每个线程连接的最后使用时间
        self._cleanup_interval = 300        # 连接清理间隔（秒），默认5分钟
        self._connection_timeout = 1800     # 连接超时时间（秒），默认30分钟
        self._cleanup_timer = None          # 清理定时器
        self._start_cleanup_timer()         # 启动清理定时器

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
        
    def _start_cleanup_timer(self):
        """启动连接清理定时器"""
        if self._cleanup_timer is not None:
            self._cleanup_timer.cancel()
        
        self._cleanup_timer = threading.Timer(
            self._cleanup_interval, 
            self._cleanup_idle_connections
        )
        self._cleanup_timer.daemon = True  # 设置为守护线程
        self._cleanup_timer.start()

    def _cleanup_idle_connections(self):
        """清理空闲连接"""
        try:
            current_time = time.time()
            idle_threads = []
            
            # 查找超时的连接
            with self._lock:
                for thread_id, timestamp in list(self._connection_timestamps.items()):
                    if current_time - timestamp > self._connection_timeout:
                        idle_threads.append(thread_id)
                
                # 从时间戳记录中移除超时连接
                for thread_id in idle_threads:
                    if thread_id in self._connection_timestamps:
                        del self._connection_timestamps[thread_id]
            
            # 关闭超时连接
            if idle_threads:
                print(f"清理了 {len(idle_threads)} 个空闲数据库连接")
                
        except Exception as e:
            print(f"清理空闲连接时出错: {e}")
        finally:
            # 重新启动定时器
            self._start_cleanup_timer()

    def set_cleanup_config(self, interval_seconds=300, timeout_seconds=1800):
        """
        设置连接清理配置
        
        :param interval_seconds: 清理间隔（秒）
        :param timeout_seconds: 连接超时时间（秒）
        """
        self._cleanup_interval = interval_seconds
        self._connection_timeout = timeout_seconds
        
        # 重启清理定时器以应用新配置
        if self._cleanup_timer:
            self._cleanup_timer.cancel()
        self._start_cleanup_timer()

    @contextmanager
    def _get_connection(self):
        """线程安全的数据库连接获取"""
        thread_id = threading.get_ident()
        
        # 更新连接使用时间戳
        with self._lock:
            self._connection_timestamps[thread_id] = time.time()
        
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
            # 更新连接使用时间戳
            with self._lock:
                self._connection_timestamps[thread_id] = time.time()
            self._local.conn.commit()
        except sqlite3.Error as e:
            self._local.conn.rollback()
            raise e
        
    @contextmanager
    def _get_connection_object(self):
        """线程安全的数据库连接获取（返回连接对象）"""
        thread_id = threading.get_ident()
        
        # 更新连接使用时间戳
        with self._lock:
            self._connection_timestamps[thread_id] = time.time()
        
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect(
                self.db_path, 
                check_same_thread=False,
                timeout=30
            )
            self._local.conn.execute('PRAGMA journal_mode=WAL')
        
        try:
            yield self._local.conn
            # 更新连接使用时间戳
            with self._lock:
                self._connection_timestamps[thread_id] = time.time()
            self._local.conn.commit()
        except sqlite3.Error as e:
            self._local.conn.rollback()
            raise e

    def close_connection(self):
        """关闭当前线程的数据库连接"""
        thread_id = threading.get_ident()
        
        # 从时间戳记录中移除
        with self._lock:
            if thread_id in self._connection_timestamps:
                del self._connection_timestamps[thread_id]
        
        if hasattr(self._local, 'conn'):
            self._local.conn.close()
            del self._local.conn

    def get_active_connections_count(self):
        """
        获取当前活跃连接数
        
        :return: 活跃连接数
        """
        with self._lock:
            return len(self._connection_timestamps)

    def force_cleanup_all_connections(self):
        """
        强制清理所有连接（用于特殊场景）
        """
        try:
            # 关闭所有线程的连接
            if hasattr(self._local, 'conn'):
                self._local.conn.close()
                del self._local.conn
                
            # 清空时间戳记录
            with self._lock:
                self._connection_timestamps.clear()
                
            print("已强制清理所有数据库连接")
        except Exception as e:
            print(f"强制清理所有连接时出错: {e}")

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
            df_columns = list(df_data.columns)
            if not df_columns:
                raise ValueError("DataFrame没有有效的列")
            
            # 获取表的列信息
            table_columns = []
            with self._get_connection() as cur:
                try:
                    cur.execute(f"PRAGMA table_info({table_name})")
                    columns_info = cur.fetchall()
                    table_columns = [col[1] for col in columns_info]  # 第二列是列名
                except sqlite3.Error:
                    # 如果表不存在或无法获取列信息，使用DataFrame的列
                    table_columns = df_columns.copy()
                    print(f"无法获取表 {table_name} 的列信息，将使用DataFrame的列名")
            
            # 处理列匹配
            if not table_columns:
                # 如果无法获取表列信息，使用DataFrame的所有列
                columns_to_insert = df_columns
                print(f"使用DataFrame的所有列进行插入: {columns_to_insert}")
            else:
                # 找出DataFrame中存在且表中也存在的列
                columns_to_insert = [col for col in df_columns if col in table_columns]
                
                # 找出DataFrame中有但表中没有的列
                extra_columns = [col for col in df_columns if col not in table_columns]
                if extra_columns:
                    print(f"警告: DataFrame中的以下列在表 {table_name} 中不存在，将被忽略: {extra_columns}")
                
                # 找出表中有但DataFrame中没有的列
                missing_columns = [col for col in table_columns if col not in df_columns]
                if missing_columns:
                    print(f"注意: 表 {table_name} 中的以下列在DataFrame中不存在: {missing_columns}")
                    print("这些列将使用默认值或NULL填充")
            
            if not columns_to_insert:
                raise ValueError(f"DataFrame的列与表 {table_name} 的列没有匹配项，无法插入数据")
            
            print(f"将插入以下列的数据: {columns_to_insert}")
            
            # 准备插入语句
            placeholders = ', '.join('?' * len(columns_to_insert))
            columns_str = ', '.join([f'"{col}"' for col in columns_to_insert])  # 用引号包围列名防止关键字冲突
            
            # 根据if_exists参数选择不同的插入策略
            if if_exists == "ignore":
                insert_sql = f'INSERT OR IGNORE INTO "{table_name}" ({columns_str}) VALUES ({placeholders})'
            else:
                insert_sql = f'INSERT OR REPLACE INTO "{table_name}" ({columns_str}) VALUES ({placeholders})'
            
            # 筛选出需要插入的列数据
            df_filtered = df_data[columns_to_insert].copy()
            
            # 将DataFrame转换为记录列表
            records = df_filtered.to_dict('records')
            
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

    # ======================== 数据删除接口 ========================
    def delete_data(self, table_name, condition=None, params=None):
        """
        删除表中的数据
        
        :param table_name: 表名
        :param condition: 删除条件（WHERE子句，不包含WHERE关键字）
        :param params: 条件参数列表
        :return: 删除的行数

        示例：db_manager.delete_data("users", "age < ?", [18])
        """
        if not table_name:
            raise ValueError("表名不能为空")
            
        try:
            with self._get_connection() as cur:
                if condition:
                    sql = f"DELETE FROM {table_name} WHERE {condition}"
                    if params:
                        cur.execute(sql, params)
                    else:
                        cur.execute(sql)
                else:
                    # 删除表中所有数据
                    sql = f"DELETE FROM {table_name}"
                    cur.execute(sql)
                    
                row_count = cur.rowcount
                print(f"成功从表 {table_name} 删除 {row_count} 行数据")
                return row_count
                
        except sqlite3.Error as e:
            error_msg = f"从表 {table_name} 删除数据时发生数据库错误: {str(e)}"
            print(error_msg)
            raise
        except Exception as e:
            error_msg = f"从表 {table_name} 删除数据时发生错误: {str(e)}"
            print(error_msg)
            raise

    def delete_data_by_ids(self, table_name, ids, id_column="id"):
        """
        根据ID列表删除数据
        
        :param table_name: 表名
        :param ids: ID列表
        :param id_column: ID列名，默认为"id"
        :return: 删除的行数

        示例：db_manager.delete_data_by_ids("users", [1, 2, 3])
        """
        if not table_name:
            raise ValueError("表名不能为空")
            
        if not ids:
            print("警告: ID列表为空，未执行删除操作")
            return 0
            
        try:
            # 构造占位符
            placeholders = ','.join(['?' for _ in ids])
            sql = f"DELETE FROM {table_name} WHERE {id_column} IN ({placeholders})"
            
            with self._get_connection() as cur:
                cur.execute(sql, ids)
                row_count = cur.rowcount
                print(f"成功从表 {table_name} 删除 {row_count} 行数据")
                return row_count
                
        except sqlite3.Error as e:
            error_msg = f"根据ID从表 {table_name} 删除数据时发生数据库错误: {str(e)}"
            print(error_msg)
            raise
        except Exception as e:
            error_msg = f"根据ID从表 {table_name} 删除数据时发生错误: {str(e)}"
            print(error_msg)
            raise

    def truncate_table(self, table_name):
        """
        清空表中所有数据（比DELETE FROM更快）
        
        :param table_name: 表名
        :return: True表示成功

        示例：db_manager.truncate_table("logs")
        """
        if not table_name:
            raise ValueError("表名不能为空")
            
        try:
            with self._get_connection() as cur:
                cur.execute(f"DELETE FROM {table_name}")
                print(f"成功清空表 {table_name}")
                return True
                
        except sqlite3.Error as e:
            error_msg = f"清空表 {table_name} 时发生数据库错误: {str(e)}"
            print(error_msg)
            raise
        except Exception as e:
            error_msg = f"清空表 {table_name} 时发生错误: {str(e)}"
            print(error_msg)
            raise

    # ======================== 数据更新接口 ========================
    def update_data(self, table_name, update_data, condition=None, params=None):
        """
        更新表中的数据
        
        :param table_name: 表名
        :param update_data: 要更新的字段和值的字典
        :param condition: 更新条件（WHERE子句，不包含WHERE关键字）
        :param params: 条件参数列表
        :return: 更新的行数

        示例：db_manager.update_data("users", {"name": "New Name", "age": 25}, "id = ?", [1])
        """
        if not table_name:
            raise ValueError("表名不能为空")
            
        if not update_data:
            print("警告: 更新数据为空，未执行更新操作")
            return 0
            
        try:
            # 构造SET子句
            set_clause = ', '.join([f"{key} = ?" for key in update_data.keys()])
            values = list(update_data.values())
            
            with self._get_connection() as cur:
                if condition:
                    sql = f"UPDATE {table_name} SET {set_clause} WHERE {condition}"
                    if params:
                        cur.execute(sql, values + params)
                    else:
                        cur.execute(sql, values)
                else:
                    # 更新表中所有行
                    sql = f"UPDATE {table_name} SET {set_clause}"
                    cur.execute(sql, values)
                    
                row_count = cur.rowcount
                print(f"成功更新表 {table_name} 中的 {row_count} 行数据")
                return row_count
                
        except sqlite3.Error as e:
            error_msg = f"更新表 {table_name} 数据时发生数据库错误: {str(e)}"
            print(error_msg)
            raise
        except Exception as e:
            error_msg = f"更新表 {table_name} 数据时发生错误: {str(e)}"
            print(error_msg)
            raise

    def update_data_by_id(self, table_name, record_id, update_data, id_column="id"):
        """
        根据ID更新单条记录
        
        :param table_name: 表名
        :param record_id: 记录ID
        :param update_data: 要更新的字段和值的字典
        :param id_column: ID列名，默认为"id"
        :return: 更新的行数

        示例：db_manager.update_data_by_id("users", 1, {"name": "Updated Name"})
        """
        if not table_name:
            raise ValueError("表名不能为空")
            
        if not record_id:
            raise ValueError("记录ID不能为空")
            
        if not update_data:
            print("警告: 更新数据为空，未执行更新操作")
            return 0
            
        try:
            # 构造SET子句
            set_clause = ', '.join([f"{key} = ?" for key in update_data.keys()])
            values = list(update_data.values())
            
            sql = f"UPDATE {table_name} SET {set_clause} WHERE {id_column} = ?"
            
            with self._get_connection() as cur:
                cur.execute(sql, values + [record_id])
                row_count = cur.rowcount
                if row_count == 0:
                    print(f"警告: 未找到ID为 {record_id} 的记录进行更新")
                else:
                    print(f"成功更新表 {table_name} 中ID为 {record_id} 的记录")
                return row_count
                
        except sqlite3.Error as e:
            error_msg = f"根据ID更新表 {table_name} 数据时发生数据库错误: {str(e)}"
            print(error_msg)
            raise
        except Exception as e:
            error_msg = f"根据ID更新表 {table_name} 数据时发生错误: {str(e)}"
            print(error_msg)
            raise

    def batch_update_data(self, table_name, update_list, id_column="id"):
        """
        批量更新数据
        
        :param table_name: 表名
        :param update_list: 更新数据列表，每个元素为包含ID和更新数据的字典
                           格式: [{"id": 1, "field1": "value1", "field2": "value2"}, ...]
        :param id_column: ID列名，默认为"id"
        :return: 更新的行数

        示例：
            update_list = [
                {"id": 1, "name": "User1", "age": 20},
                {"id": 2, "name": "User2", "age": 21}
            ]
            db_manager.batch_update_data("users", update_list)
        """
        if not table_name:
            raise ValueError("表名不能为空")
            
        if not update_list:
            print("警告: 更新数据列表为空，未执行更新操作")
            return 0
            
        try:
            updated_count = 0
            
            with self._get_connection() as cur:
                for record in update_list:
                    if id_column not in record:
                        print(f"警告: 记录缺少 {id_column} 字段，跳过该记录")
                        continue
                        
                    record_id = record.pop(id_column)  # 移除ID字段
                    if not record:  # 如果没有其他字段需要更新
                        print(f"警告: ID为 {record_id} 的记录没有需要更新的字段，跳过该记录")
                        continue
                    
                    # 构造SET子句
                    set_clause = ', '.join([f"{key} = ?" for key in record.keys()])
                    values = list(record.values())
                    
                    sql = f"UPDATE {table_name} SET {set_clause} WHERE {id_column} = ?"
                    cur.execute(sql, values + [record_id])
                    updated_count += cur.rowcount
                    
            print(f"成功批量更新表 {table_name} 中的 {updated_count} 行数据")
            return updated_count
            
        except sqlite3.Error as e:
            error_msg = f"批量更新表 {table_name} 数据时发生数据库错误: {str(e)}"
            print(error_msg)
            raise
        except Exception as e:
            error_msg = f"批量更新表 {table_name} 数据时发生错误: {str(e)}"
            print(error_msg)
            raise

    def upsert_data(self, table_name, data, conflict_columns=None):
        """
        插入或更新数据（upsert操作）
        
        :param table_name: 表名
        :param data: 要插入或更新的数据（字典或字典列表）
        :param conflict_columns: 冲突检测列（用于ON CONFLICT子句），如果为None则使用主键
        :return: 操作的行数

        示例：db_manager.upsert_data("users", {"id": 1, "name": "User1", "email": "user1@example.com"}, ["id"])
        """
        if not table_name:
            raise ValueError("表名不能为空")
            
        if not data:
            print("警告: 数据为空，未执行操作")
            return 0
            
        # 确保data是列表格式
        if isinstance(data, dict):
            data = [data]
            
        if not isinstance(data, list):
            raise ValueError("数据必须是字典或字典列表")
            
        try:
            inserted_count = 0
            
            with self._get_connection() as cur:
                for record in data:
                    if not record:
                        continue
                        
                    # 构造INSERT语句
                    columns = list(record.keys())
                    placeholders = ','.join(['?' for _ in columns])
                    columns_str = ','.join(columns)
                    
                    sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                    
                    # 如果指定了冲突列，则添加ON CONFLICT子句
                    if conflict_columns:
                        conflict_cols_str = ','.join(conflict_columns)
                        # 构造UPDATE子句（排除冲突列）
                        update_columns = [col for col in columns if col not in conflict_columns]
                        if update_columns:
                            update_clause = ','.join([f"{col} = excluded.{col}" for col in update_columns])
                            sql += f" ON CONFLICT({conflict_cols_str}) DO UPDATE SET {update_clause}"
                        else:
                            sql += f" ON CONFLICT({conflict_cols_str}) DO NOTHING"
                    else:
                        # 如果没有指定冲突列，使用INSERT OR REPLACE
                        sql = f"INSERT OR REPLACE INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                    
                    values = list(record.values())
                    cur.execute(sql, values)
                    inserted_count += cur.rowcount
                    
            print(f"成功对表 {table_name} 执行 {inserted_count} 次upsert操作")
            return inserted_count
            
        except sqlite3.Error as e:
            error_msg = f"对表 {table_name} 执行upsert操作时发生数据库错误: {str(e)}"
            print(error_msg)
            raise
        except Exception as e:
            error_msg = f"对表 {table_name} 执行upsert操作时发生错误: {str(e)}"
            print(error_msg)
            raise

    def __del__(self):
        """析构时清理资源"""
        # 取消定时器
        if self._cleanup_timer:
            self._cleanup_timer.cancel()
        
        # 关闭所有连接
        self.force_cleanup_all_connections()