import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime
import pandas as pd

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
        db_path = ""
        if db_type == 1:
            db_path = "./stocks/db/baostock/stocks.db"
        elif db_type == 2:
            db_path = "./stocks/db/efinance/stocks.db"
        else:
            db_path = "./stocks/db/akshare/stocks.db"

        self.db_path = os.path.abspath(db_path)  # 转为绝对路径
        self._ensure_db_directory()  # 确保目录存在
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
        """上下文管理器处理数据库连接"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            yield cursor
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _init_db(self):
        """初始化数据库表结构"""
        with self._get_connection() as cur:
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
                cur.execute('''
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
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS stock_basic_info (
                        证券代码 TEXT PRIMARY KEY NOT NULL,
                        交易状态 TEXT NOT NULL UNIQUE,
                        证券名称 TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            elif self.db_type == 2:
                cur.execute('''
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

    def count_sqlite_tables(self, db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table';")
        table_count = cursor.fetchone()[0]
        conn.close()
        return table_count

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

    def batch_insert_stocks(self, stocks_data):
        """批量插入股票数据
        :param stocks_data: 字典列表格式
        """
        if not stocks_data:
            return
        
        columns = ', '.join(stocks_data[0].keys())
        placeholders = ', '.join('?' * len(stocks_data[0]))
        
        with self._get_connection() as cur:
            cur.executemany(
                f"INSERT OR IGNORE INTO stock_basic_info ({columns}) VALUES ({placeholders})",
                [tuple(stock.values()) for stock in stocks_data]
            )
            return cur.rowcount

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
        allowed_table_names = ['stock_basic_info', 'sh_main', 'sz_main', 'gem', 'star', 'bse'] # 替换为你允许的表名列表
        if table_name not in allowed_table_names:
            raise ValueError(f"Invalid table name: {table_name}")

        # print(f"股票 {stock_code} 的数据库不存在，自动创建")
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            证券代码 TEXT PRIMARY KEY NOT NULL,
            交易状态 TEXT NOT NULL UNIQUE,
            证券名称 TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        conn = sqlite3.connect(self.db_path)
        if conn is not None:
            try:
                cursor = conn.cursor()
                cursor.execute(create_table_sql)
                conn.commit()
                print("表创建成功或已存在")
            except sqlite3.Error as e:
                print(f"创建表失败: {e}")
            finally:
                conn.close()
        else:
            print("无法创建数据库连接")
        # self.create_baostock_table(db_path)

        conn = sqlite3.connect(str(self.db_path))
        stocks_data.to_sql(table_name, conn, if_exists=writeWay, index=False)
        conn.close()
        return True

    def get_stocks(self, table="stock_basic_info"):
        try:
            conn = sqlite3.connect(self.db_path)
            query = f"SELECT * FROM {table}"
            
            df = pd.read_sql_query(query, conn)
            conn.close() 
            return df
        except Exception as e:
            print(f"获取股票数据时出错: {str(e)}")
            return pd.DataFrame()

    def get_sh_main_stocks(self):
        return self.get_stocks('sh_main')
        
    def get_sz_main_stocks(self):
        return self.get_stocks('sz_main')

    def get_gem_stocks(self):
        return self.get_stocks('gem')
    
    def get_star_stocks(self):
        return self.get_stocks('star')


# 调用方式
# db_manager.import_from_dataframe(main_board, "MAIN")
'''
# 查询主板股票数量
def verify_main_board_count():
    db_manager = StockDBManager("stocks.db")
    main_stocks = db_manager.query_stocks(board_type="MAIN")
    print(f"数据库中的主板股票数量: {len(main_stocks)}")
    print("示例数据:")
    for stock in main_stocks[:3]:
        print(stock)

        -----------------------------------

# 初始化数据库
db = StockDBManager("stocks.db")

# 插入单条数据
new_stock = {
    'stock_code': '600000',
    'stock_name': '浦发银行',
    'listing_date': '1999-11-10',
    'board_type': 'MAIN',
    'is_st': 0
}
db.insert_stock(new_stock)

# 批量插入数据
stocks_batch = [
    {'stock_code': '000001', 'stock_name': '平安银行', ...},
    {'stock_code': '300750', 'stock_name': '宁德时代', ...}
]
db.batch_insert_stocks(stocks_batch)

# 更新数据
db.update_stock('600000', {'stock_name': '浦发银行(更新)'})

# 查询数据
# 查询单个股票
print(db.get_stock_by_code('600000'))

# 查询主板非ST股票
main_stocks = db.query_stocks(board_type='MAIN', is_st=False)

# 自定义条件查询
custom_query = db.query_stocks(condition="listing_date > '2020-01-01'")

# 删除数据
db.delete_stock('000001')
'''


# 测试代码
if __name__ == "__main__":
    print("stocks_db_manager.py run")