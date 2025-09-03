import os
import sqlite3
import pandas as pd
from pathlib import Path
import datetime
# from stock_data_processor import process_stock_data

class DayStockDBManager:
    """
    股票数据库管理类，用于管理stocks/db/day目录下的股票数据库
    """
    def __init__(self, db_dir="../stocks/db/day"):
        """
        初始化数据库管理器
        
        参数:
            db_dir (str, optional): 数据库目录路径，默认为stocks/db
            
        """
        if db_dir is None:
            self.db_dir = Path("../stocks/db/day")
        else:
            self.db_dir = Path(db_dir)
        
        # 确保目录存在
        self.db_dir.mkdir(parents=True, exist_ok=True)
    
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
    
    def get_db_path(self, stock_code):
        """
        获取指定股票代码的数据库路径
        
        参数:
            stock_code (str): 股票代码
            
        返回:
            Path: 数据库文件路径
        """
        return self.db_dir / f"{stock_code}.db"

    def get_week_db_path(self, stock_code):
        return self.db_dir / f"week" / f"{stock_code}_week.db"
    
    def check_stock_exists(self, stock_code):
        """
        检查指定股票的数据库是否存在
        
        参数:
            stock_code (str): 股票代码
            
        返回:
            bool: 存在返回True，否则返回False
        """
        db_path = self.get_db_path(stock_code)
        return db_path.exists()
    
    def get_stock_data(self, stock_code, start_date=None, end_date=None):
        """
        获取指定股票的数据
        
        参数:
            stock_code (str): 股票代码
            start_date (str, optional): 开始日期，格式为YYYY-MM-DD
            end_date (str, optional): 结束日期，格式为YYYY-MM-DD
            
        返回:
            DataFrame: 股票数据，如果数据库不存在则返回None
        """
        if not self.check_stock_exists(stock_code):
            print(f"股票 {stock_code} 的数据库不存在")
            return None
        
        try:
            conn = sqlite3.connect(str(self.get_db_path(stock_code)))
            query = "SELECT * FROM stock_data"
            
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

    def get_week_stock_data(self, stock_code, start_date=None, end_date=None):
        if not self.check_stock_exists(stock_code):
            print(f"股票 {stock_code} 的数据库不存在")
            return None
        
        try:
            conn = sqlite3.connect(str(self.get_week_db_path(stock_code)))
            query = "SELECT * FROM weekly_stock_data"
            
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
    
    def update_stock_data(self, stock_code):
        """
        更新指定股票的数据库
        
        参数:
            stock_code (str): 股票代码
            
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
        results = {}
        stock_codes = self.list_all_stocks()
        
        for stock_code in stock_codes:
            result = self.update_stock_data(stock_code)
            results[stock_code] = result
        
        return results
    
    def delete_stock_db(self, stock_code):
        """
        删除指定股票的数据库
        
        参数:
            stock_code (str): 股票代码
            
        返回:
            bool: 删除成功返回True，否则返回False
        """
        if not self.check_stock_exists(stock_code):
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
    
    def get_latest_data(self, stock_code, days=1):
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
        
        return df.tail(days)
    
    def get_table_info(self, stock_code, table_name="stock_data"):
        """
        获取数据库表结构信息
        
        参数:
            stock_code (str): 股票代码
            table_name (str, optional): 表名，默认为stock_data
            
        返回:
            list: 表字段信息列表
        """
        if not self.check_stock_exists(stock_code):
            print(f"股票 {stock_code} 的数据库不存在")
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
        if not self.check_stock_exists(stock_code):
            print(f"股票 {stock_code} 的数据库不存在")
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
        if not self.check_stock_exists(stock_code):
            print(f"股票 {stock_code} 的数据库不存在")
            return {}
        
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

# 测试代码
if __name__ == "__main__":
    # 创建数据库管理器
    db_manager = DayStockDBManager()
    
    # 列出所有股票
    stocks = db_manager.list_all_stocks()
    print(f"当前数据库中的股票: {stocks}")
    
    # 获取一个股票的数据
    if stocks:
        test_stock = stocks[0]
        print(f"\n获取股票 {test_stock} 的最新数据:")
        latest_data = db_manager.get_latest_data(test_stock, days=3)
        if latest_data is not None:
            print(latest_data[['日期', '股票代码', '收盘', 'DIF', 'DEA', 'MACD', 'MA24', 'MA52']])
        
        # 获取表结构
        print(f"\n股票 {test_stock} 的数据库表结构:")
        table_info = db_manager.get_table_info(test_stock)
        if table_info:
            for col in table_info:
                print(f"字段: {col[1]}, 类型: {col[2]}")
        
        # 测试添加新字段
        print("\n测试添加新字段:")
        db_manager.add_column(test_stock, "RSI14", "REAL", None)
        
        # 测试计算并添加新字段
        print("\n测试计算并添加新字段:")
        def calculate_price_change(df):
            """计算价格变化百分比"""
            return df['收盘'].pct_change() * 100
        
        db_manager.calculate_and_add_column(test_stock, "价格变化率", calculate_price_change)
    
    # 测试更新数据
    print("\n测试更新一个股票数据:")
    if not stocks:
        # 如果没有股票，添加一个
        db_manager.update_stock_data("000001")
    else:
        # 更新第一个股票
        db_manager.update_stock_data(stocks[0])