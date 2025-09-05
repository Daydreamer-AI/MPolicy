import os
import sqlite3
import pandas as pd
from pathlib import Path

'''
    常规插入：executemany+ 分批提交
    超大数据：DataFrame.to_sql或原生 LOAD DATA/COPY
'''

class StockDbBase:
    """
    股票数据库管理基类
    """
    def __init__(self, db_dir=None):
        """
        初始化数据库管理器
        
        参数:
            db_dir (str, optional): 数据库目录路径，默认为./stocks/db/day
            
        """
        if db_dir is None:
            self.db_dir = Path("./stocks/akshare/db/day")
        else:
            self.db_dir = Path(db_dir)
        
        # 确保目录存在
        self.db_dir.mkdir(parents=True, exist_ok=True)

    def create_connection(self, db_path):
        """创建数据库连接"""
        try:
            conn = sqlite3.connect(db_path)
            return conn
        except sqlite3.Error as e:
            print(f"连接数据库失败: {e}")
            return None
        
    # def get_stock_data(self, stock_code, start_date=None, end_date=None):
    #     """
    #     获取股票数据
    #     :param stock_code: 股票代码
    #     :param start_date: 开始日期
    #     :param end_date: 结束日期
    #     :return: 查询结果
    #     """
    #     conn = self.create_connection()
    #     if conn is not None:
    #         try:
    #             cursor = conn.cursor()
                
    #             if start_date and end_date:
    #                 sql = "SELECT * FROM stock_data WHERE 股票代码 = ? AND 日期 BETWEEN ? AND ? ORDER BY 日期"
    #                 cursor.execute(sql, (stock_code, start_date, end_date))
    #             else:
    #                 sql = "SELECT * FROM stock_data WHERE 股票代码 = ? ORDER BY 日期"
    #                 cursor.execute(sql, (stock_code,))
                
    #             results = cursor.fetchall()
    #             return results
    #         except sqlite3.Error as e:
    #             print(f"查询数据失败: {e}")
    #             return []
    #         finally:
    #             conn.close()
    #     else:
    #         print("无法创建数据库连接")
    #         return []

    def create_table(self, db_path, create_table_sql):
        conn = self.create_connection(db_path)
        if conn is not None:
            try:
                cursor = conn.cursor()
                cursor.execute(create_table_sql)
                conn.commit()
                # print("表创建成功或已存在")
            except sqlite3.Error as e:
                print(f"创建表失败: {e}")
            finally:
                conn.close()
        else:
            print("无法创建数据库连接")

    # 数据库文件相关
    def list_all_stocks(self):
        """
        列出所有已存在的股票数据库
        
        返回:
            list: 股票代码列表
        """
        stock_codes = []
        for file in self.db_dir.glob("*.db"):
            stock_code = file.stem  # 获取文件名（不含扩展名）
            stock_codes.append(stock_code)
        return stock_codes

    def set_db_dir(self, db_dir):
        if db_dir is None:
            self.db_dir = Path("./stocks/akshare/db/day")
        else:
            self.db_dir = Path(db_dir)

        # 确保目录存在
        self.db_dir.mkdir(parents=True, exist_ok=True)

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
    
    def delete_stock_db(self, stock_code):  
        """
        删除指定股票的数据库
        
        参数:
            stock_code (str): 股票代码
            
        返回:
            bool: 删除成功返回True，否则返回False
        """
        if not self.check_stock_db_exists(stock_code):
            print(f"股票 {stock_code} 的数据库不存在")
            return False
        
        try:
            db_path = self.get_db_path(stock_code)
            os.remove(db_path)
            print(f"成功删除股票 {stock_code} 的数据库")
            return True
        except Exception as e:
            print(f"删除股票 {stock_code} 数据库时出错: {str(e)}")
            return False  

    # TODO: 添加股票数据库文件，修改股票数据库文件
    def add_stock_db(self, stock_code):
        pass

    def update_stock_db_info(self, stock_code, new_stock_code):
        pass

    # 表结构相关接口
    # 一个日期只能有一条数据，因此主键为日期
    def get_table_info(self, stock_code, table_name="stock_data"):
        """
        获取数据库表结构信息
        
        参数:
            stock_code (str): 股票代码
            table_name (str, optional): 表名，默认为stock_data
            
        返回:
            list: 表字段信息列表
        """
        if not self.check_stock_db_exists(stock_code):
            print(f"股票 {stock_code} 的数据库不存在")
            return None
        
        allowed_tables = {"stock_data", "user_info", "transaction_log"}  # 合法表名白名单
        if table_name not in allowed_tables:
            # raise ValueError("非法表名！")
            return None
        
        try:
            conn = sqlite3.connect(str(self.get_db_path(stock_code)))
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns_info = cursor.fetchall()
            conn.close()
            return columns_info
        except Exception as e:
            print(f"获取股票 {stock_code} 数据库表结构时出错: {str(e)}")
            return None

    def check_column_exists(self, stock_code, column_name, table_name="stock_data"):
        """
        检查指定表中是否存在某个字段
        
        参数:
            stock_code (str): 股票代码
            column_name (str): 字段名
            table_name (str, optional): 表名，默认为stock_data
            
        返回:
            bool: 字段存在返回True，否则返回False
        """

        allowed_tables = {"stock_data", "user_info", "transaction_log"}  # 合法表名白名单
        if table_name not in allowed_tables:
            # raise ValueError("非法表名！")
            return False

        columns_info = self.get_table_info(stock_code, table_name)
        if columns_info is None:
            return False
        
        for col in columns_info:
            if col[1] == column_name:
                return True
        
        return False

    def add_column(self, stock_code, column_name, column_type, default_value=None, table_name="stock_data"):
        """
        为指定数据库表添加新字段
        
        参数:
            stock_code (str): 股票代码
            column_name (str): 新字段名
            column_type (str): 字段类型，如TEXT, INTEGER, REAL等
            default_value (any, optional): 默认值，如果为None则不设置默认值
            table_name (str, optional): 表名，默认为stock_data
            
        返回:
            bool: 添加成功返回True，否则返回False
        """
        if not self.check_stock_db_exists(stock_code):
            print(f"股票 {stock_code} 的数据库不存在")
            return False
        
        allowed_tables = {"stock_data", "user_info", "transaction_log"}  # 合法表名白名单
        if table_name not in allowed_tables:
            # raise ValueError("非法表名！")
            return False
        
        # 检查字段是否已存在
        if self.check_column_exists(stock_code, column_name, table_name):
            print(f"字段 {column_name} 已存在于表 {table_name} 中")
            return True
        
        try:
            conn = sqlite3.connect(str(self.get_db_path(stock_code)))
            cursor = conn.cursor()
            
            # 构建SQL语句
            sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
            if default_value is not None:
                if isinstance(default_value, str):
                    sql += f" DEFAULT '{default_value}'"
                else:
                    sql += f" DEFAULT {default_value}"
            
            cursor.execute(sql)
            conn.commit()
            conn.close()
            
            print(f"成功为表 {table_name} 添加字段 {column_name} ({column_type})")
            return True
        except Exception as e:
            print(f"为表 {table_name} 添加字段 {column_name} 时出错: {str(e)}")
            return False

    def add_columns(self, stock_code, columns_info, table_name="stock_data"):
        """
        为指定数据库表批量添加多个新字段
        
        参数:
            stock_code (str): 股票代码
            columns_info (list): 字段信息列表，每个元素为包含字段名、类型和默认值的元组或列表
                                 格式为 [(column_name, column_type, default_value), ...]
                                 default_value可以为None
            table_name (str, optional): 表名，默认为stock_data
            
        返回:
            dict: 字段名和添加结果的字典
        """
        if not self.check_stock_db_exists(stock_code):
            print(f"股票 {stock_code} 的数据库不存在")
            return {}
        
        allowed_tables = {"stock_data", "user_info", "transaction_log"}  # 合法表名白名单
        if table_name not in allowed_tables:
            # raise ValueError("非法表名！")
            return False
        
        results = {}
        for column_info in columns_info:
            column_name = column_info[0]
            column_type = column_info[1]
            default_value = column_info[2] if len(column_info) > 2 else None
            
            result = self.add_column(stock_code, column_name, column_type, default_value, table_name)
            results[column_name] = result
        
        return results

    def calculate_and_add_column(self, stock_code, column_name, calculation_func, column_type="REAL", table_name="stock_data"):
        """
        计算新的指标并添加为数据库表的新字段
        
        参数:
            stock_code (str): 股票代码
            column_name (str): 新字段名
            calculation_func (function): 计算函数，接收DataFrame作为参数，返回Series或列表
            column_type (str, optional): 字段类型，默认为REAL
            table_name (str, optional): 表名，默认为stock_data
            
        返回:
            bool: 添加成功返回True，否则返回False
        """
        # 获取股票数据
        df = self.get_stock_data(stock_code)
        if df is None or df.empty:
            print(f"无法获取股票 {stock_code} 的数据")
            return False
        
        allowed_tables = {"stock_data", "user_info", "transaction_log"}  # 合法表名白名单
        if table_name not in allowed_tables:
            # raise ValueError("非法表名！")
            return False
        
        try:
            # 计算新指标
            new_column_data = calculation_func(df)
            
            # 添加到DataFrame
            df[column_name] = new_column_data
            
            # 检查字段是否已存在，如果存在则先添加
            if not self.check_column_exists(stock_code, column_name, table_name):
                self.add_column(stock_code, column_name, column_type, None, table_name)
            
            # 更新数据库
            conn = sqlite3.connect(str(self.get_db_path(stock_code)))
            
            # 更新每一行
            for index, row in df.iterrows():
                date = row['日期']
                value = row[column_name]
                
                # 更新该日期的记录
                sql = f"UPDATE {table_name} SET {column_name} = ? WHERE 日期 = ?"
                conn.execute(sql, (value, date))
            
            conn.commit()
            conn.close()
            
            print(f"成功计算并添加字段 {column_name} 到表 {table_name}")
            return True
        except Exception as e:
            print(f"计算并添加字段 {column_name} 时出错: {str(e)}")
            return False

    # TODO: 修改指定table的指定列，删除指定table指定列 
    def update_column(self, stock_code, column_name, new_column_name, table_name="stock_data"):
        # 不支持修改列数据类型或约束
        pass

    def delete_column(self, stock_code, column_name, table_name="stock_data"):
        # 不支持直接删除列（需通过创建新表迁移数据）
        pass

    def rename_table(self, stock_code, old_table_name, new_table_name):
        try:
            conn = sqlite3.connect(self.get_db_path())
            cursor = conn.cursor()
            
            # 重命名表
            cursor.execute(f"ALTER TABLE {old_table_name} RENAME TO {new_table_name};")
            conn.commit()
            print(f"表名已从 '{old_table_name}' 改为 '{new_table_name}'")
        
        except sqlite3.OperationalError as e:
            print(f"操作失败：{e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()


    # AKShare表数据相关
    def create_akshare_table(self, db_path):
        """
        创建股票数据表
        根据图片中的表结构创建包含所有必要字段的表
        """
        # SQL语句 - 根据图片中的表结构
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS stock_data (
            日期 DATE NOT NULL,
            股票代码 TEXT NOT NULL,
            开盘 REAL,
            收盘 REAL,
            最高 REAL,
            最低 REAL,
            成交量 INTEGER,
            成交额 REAL,
            振幅 REAL,
            涨跌幅 REAL,
            换手率 REAL,
            DIF REAL,
            DEA REAL,
            MACD REAL,
            MA24 REAL,
            MA52 REAL,
            PRIMARY KEY (日期, 股票代码)
        )
        """
        self.create_table(create_table_sql)
    

    def get_akshare_stock_data(self, stock_code, start_date=None, end_date=None, table_name="stock_data"):
        """
        获取指定股票的数据
        
        参数:
            stock_code (str): 股票代码
            start_date (str, optional): 开始日期，格式为YYYY-MM-DD
            end_date (str, optional): 结束日期，格式为YYYY-MM-DD
            
        返回:
            DataFrame: 股票数据，如果数据库不存在则返回None
        """
        if not self.check_stock_db_exists(stock_code):
            print(f"股票 {stock_code} 的数据库不存在")
            return None
        
        allowed_tables = {"stock_data", "user_info", "transaction_log"}  # 合法表名白名单
        if table_name not in allowed_tables:
            raise ValueError("非法表名！")

        try:
            conn = sqlite3.connect(str(self.get_db_path(stock_code)))
            query = f"SELECT * FROM {table_name}"
            
            # 添加日期过滤条件
            if start_date or end_date:
                conditions = []
                if start_date:
                    conditions.append(f"日期 >= '{start_date}'")
                if end_date:
                    conditions.append(f"日期 <= '{end_date}'")
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
            
            # 按日期排序
            query += " ORDER BY 日期"
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            print(f"获取股票 {stock_code} 数据时出错: {str(e)}")
            return None

    def get_latest_data(self, stock_code, count=1):
        """
        获取指定股票最近几天的数据
        
        参数:
            stock_code (str): 股票代码
            days (int, optional): 获取最近几天的数据，默认为1天
            
        返回:
            DataFrame: 最近几天的股票数据
        """
        df = self.get_stock_data(stock_code)
        if df is None or df.empty:
            return None
        
        return df.tail(count)


    def update_stock_data(self, stock_code, stock_data):
        """
        更新指定股票的数据库
        
        参数:
            stock_code (str): 股票代码
            stock_data (dict): 股票数据
            
        返回:
            bool: 更新成功返回True，否则返回False
        """
        pass

    def update_all_stocks(self):
        """
        更新所有股票的数据库
        
        返回:
            dict: 股票代码和更新结果的字典
        """
        pass

    # TODO: 指定table中添加数据，删除指定table数据
    def add_stock_data(self, stock_code, stock_data, table="stock_data"):
        pass

    def delete_stock_data(self, stock_code, date):
        pass

    def save_akshare_stock_data_to_db(self, stock_code, stock_data, writeWay="replace", table_name="stock_data"):
        db_path = self.get_db_path(stock_code)
        if not self.check_stock_db_exists(stock_code):
            # print(f"股票 {stock_code} 的数据库不存在，自动创建")
            self.create_akshare_table(db_path)
        
        conn = sqlite3.connect(str(db_path))
        stock_data.to_sql(table_name, conn, if_exists=writeWay, index=False)
        conn.close()
        return True

    def insert_dict_to_table(self, data_dict, table_name="stock_data"):
        db_path = self.get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 提取字典的键（列名）和值（数据）
        columns = ', '.join(data_dict.keys())
        placeholders = ', '.join(['?'] * len(data_dict))
        values = tuple(data_dict.values())
        
        # 构建并执行 SQL
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        cursor.execute(sql, values)
        
        conn.commit()
        conn.close()


    # Baostock表数据相关
    def create_baostock_table(self, db_path):
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS stock_data (
            日期 DATE NOT NULL,
            股票代码 TEXT NOT NULL,
            开盘 REAL,
            最高 REAL,
            最低 REAL,
            收盘 REAL,
            成交量 INTEGER,
            成交额 REAL,
            涨跌幅 REAL,
            换手率 REAL,
            复权方式 INTEGER,
            是否ST BOOLEAN,
            DIF REAL,
            DEA REAL,
            MACD REAL,
            MA5 REAL,
            MA10 REAL,
            MA20 REAL,
            MA24 REAL,
            MA30 REAL,
            MA52 REAL,
            MA60 REAL,
            PRIMARY KEY (日期, 股票代码)
        )
        """
        self.create_table(db_path, create_table_sql)

    def get_bao_stock_data(self, stock_code, start_date=None, end_date=None, table_name="stock_data"):
        if not self.check_stock_db_exists(stock_code):
            print(f"股票 {stock_code} 的数据库不存在")
            return None
        
        allowed_tables = {"stock_data", "user_info", "transaction_log"}  # 合法表名白名单
        if table_name not in allowed_tables:
            raise ValueError("非法表名！")

        try:
            conn = sqlite3.connect(str(self.get_db_path(stock_code)))
            query = f"SELECT * FROM {table_name}"
            
            # 添加日期过滤条件
            if start_date or end_date:
                conditions = []
                if start_date:
                    conditions.append(f"日期 >= '{start_date}'")
                if end_date:
                    conditions.append(f"日期 <= '{end_date}'")
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
            
            # 按日期排序
            query += " ORDER BY 日期"
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            print(f"获取股票 {stock_code} 数据时出错: {str(e)}")
            return None

    def save_bao_stock_data_to_db(self, stock_code, stock_data, writeWay="replace", table_name="stock_data"):
        db_path = self.get_db_path(stock_code)
        if not self.check_stock_db_exists(stock_code):
            # print(f"股票 {stock_code} 的数据库不存在，自动创建")
            self.create_baostock_table(db_path)
        
        # 列对齐检查

        conn = sqlite3.connect(str(db_path))
        stock_data.to_sql(table_name, conn, if_exists=writeWay, index=False)
        conn.close()
        return True
    
    def delete_last_row(self, stock_code, table_name="stock_data"):
        """
        删除SQLite3数据库中指定表的最后一行数据（通过自增ID定位）

        参数:
            stock_code (str): 股票代码，数据库文件名
            table_name (str): 要操作的表名
        """
        # 连接到数据库
        conn = sqlite3.connect(self.get_db_path(stock_code))
        cursor = conn.cursor()

        try:
            # 开始一个事务
            conn.execute("BEGIN")

            # 1. 查询表中最大的ID值，即最后一行的ID
            cursor.execute(f"SELECT MAX(id) FROM {table_name}")
            last_id = cursor.fetchone()[0]  # 获取查询结果的第一行第一列

            # 如果表不为空，则执行删除操作
            if last_id is not None:
                # 2. 构建DELETE语句，使用参数化查询以防止SQL注入
                delete_sql = f"DELETE FROM {table_name} WHERE id = ?"
                cursor.execute(delete_sql, (last_id,))
                print(f"已删除 {table_name} 表中ID为 {last_id} 的最后一行数据。")
            else:
                print(f"表 {table_name} 为空，无数据可删除。")

            # 提交事务，使删除操作生效
            conn.commit()

        except sqlite3.Error as e:
            # 如果发生任何错误，回滚事务
            conn.rollback()
            print(f"操作过程中发生数据库错误: {e}")
        except Exception as e:
            conn.rollback()
            print(f"发生未知错误: {e}")
        finally:
            # 最后，确保关闭游标和数据库连接以释放资源
            cursor.close()
            conn.close()

    def delete_last_row_directly(self, stock_code, table_name="stock_data"):
        """
        直接删除SQLite3数据库中指定表的最后一行数据（通过rowid定位）

        参数:
            db_path (str): 数据库文件的路径
            table_name (str): 要操作的表名
        """
        conn = sqlite3.connect(self.get_db_path(stock_code))
        cursor = conn.cursor()

        try:
            conn.execute("BEGIN") # 开始事务
            # 使用子查询直接定位并删除rowid最大的那一行
            delete_sql = f"""
                DELETE FROM {table_name} 
                WHERE rowid = (
                    SELECT rowid FROM {table_name} 
                    ORDER BY rowid DESC 
                    LIMIT 1
                )
            """
            cursor.execute(delete_sql)
            # 获取受影响的行数
            rows_affected = cursor.rowcount
            if rows_affected > 0:
                print(f"已直接删除 {table_name} 表的最后一行数据。")
            else:
                print(f"表 {table_name} 可能为空，无数据被删除。")
            conn.commit() # 提交事务

        except sqlite3.Error as e:
            conn.rollback() # 回滚事务
            print(f"操作过程中发生数据库错误: {e}")
        except Exception as e:
            conn.rollback()
            print(f"发生未知错误: {e}")
        finally:
            cursor.close()
            conn.close()

    # 测试代码
if __name__ == "__main__":
    print("stock_db_base.py run")