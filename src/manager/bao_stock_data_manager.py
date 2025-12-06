
from PyQt5.QtCore import QObject, pyqtSignal
from db_base.stock_info_db_base import StockInfoDBBasePool
from db_base.stock_db_base import StockDbBase
from indicators import stock_data_indicators as sdi
from manager.logging_manager import get_logger
from common.common_api import *

from manager.period_manager import TimePeriod

import time
import traceback
import pandas as pd

class BaostockDataManager(QObject):
    def __init__(self, parent=None):
        super().__init__() 
        self.logger = get_logger(__name__)

        self.dict_stocks_info = {}  # {'board': pd.DataFrame()}, 示例：{'sh_main' : pd.DataFrame()}
        self.dict_stock_data = {}   # {'level': {'code': DataFrame}}，示例：{'1d': {'sh.600000': pd.DataFrame()}}

        self.stocks_db_manager = StockInfoDBBasePool().get_manager(1)
        self.stock_db_base = StockDbBase("./data/database/stocks/db/baostock")

        self.get_all_stocks_from_db()

    def get_all_stocks_from_db(self):
        self.dict_stocks_info['sh_main'] = self.stocks_db_manager.get_sh_main_stocks()
        self.dict_stocks_info['sz_main'] = self.stocks_db_manager.get_sz_main_stocks()
        self.dict_stocks_info['gem'] = self.stocks_db_manager.get_gem_stocks()
        self.dict_stocks_info['star'] = self.stocks_db_manager.get_star_stocks()

        # sh_main_count = len(self.dict_stocks_info['sh_main'])
        # sz_main_count = len(self.dict_stocks_info['sz_main'])
        # self.logger.info(f"沪A主板股票数量：{sh_main_count}")
        # self.logger.info(f"深A主板股票数量：{sz_main_count}")

    def get_stock_name_by_code(self, code):
        board_name = identify_stock_board(code)
        df_board_data = self.dict_stocks_info[board_name]
        
        # 使用布尔索引查找匹配的行
        mask = df_board_data['证券代码'] == code
        matched_rows = df_board_data[mask]
        
        if not matched_rows.empty:
            return matched_rows.iloc[0]['证券名称']
        else:
            return None

    def get_stock_data_from_db_by_period(self, code, period=TimePeriod.DAY):
        table_name = period.get_table_name()
        # self.logger.info(f"处理股票: {code}, 表名：{table_name}")

        df_data = self.stock_db_base.get_bao_stock_data(code, table_name)
        if df_data is None or df_data.empty:
            return pd.DataFrame()

        df_data['name'] = self.get_stock_name_by_code(code)
        sdi.default_indicators_auto_calculate(df_data)

        return df_data
    
    def get_all_lastest_row_data_dict_by_period(self, period=TimePeriod.DAY):
        dict_result = {}    # {'code': DataFrame}
        table_name = period.get_table_name()

        # 遍历所有板块
        board_index = 0
        total_count = 0
        self.logger.info(f"开始读取本地数据库日线、周线股票数据...")
        start_time = time.time()  # 记录开始时间
        for board_name, board_data in self.dict_stocks_info.items():
            if board_index > 1:
                break
            board_index += 1

            self.logger.info(f"读取 {board_name} 板块...")
            board_start_time = time.time()  # 记录开始时间
            
            # 遍历该板块的每一行数据
            for index, row in board_data.iterrows():
                if index > 100:
                    break

                try:
                    code = row['证券代码']
                    name = row['证券名称'] if '证券名称' in row else '未知'
                    
                    lastest_1d_data = self.stock_db_base.get_lastest_stock_data(code, table_name)     

                    if lastest_1d_data is None or lastest_1d_data.empty:
                        self.logger.debug(f"股票 {code} 日线数据为空，跳过指标计算")
                        continue 

                    # 只对非空数据进行指标计算
                    lastest_1d_data['name'] = name
                    sdi.default_indicators_auto_calculate(lastest_1d_data)
                    dict_result[code] = lastest_1d_data
                        
                    total_count += 1
                    
                except Exception as e:
                    self.logger.error(f"处理股票 {code} 时发生错误: {str(e)}")
                    self.logger.error(traceback.format_exc())
                    # 继续处理下一个股票
                    continue



            board_read_elapsed_time = time.time() - board_start_time  # 计算耗时
            self.logger.info(f"读取完成，共读取{total_count}只股票，耗时: {board_read_elapsed_time:.2f}秒，即{board_read_elapsed_time/60:.2f}分钟")

        
        all_read_elapsed_time = time.time() - start_time  # 计算耗时
        self.logger.info(f"读取完成，总耗时: {all_read_elapsed_time:.2f}秒，即{all_read_elapsed_time/60:.2f}分钟")

        return dict_result
    
    def get_lastest_stock_data_dict_by_code_list(self, code_list=[], period=TimePeriod.DAY):
        if code_list is None or len(code_list) == 0:
            self.logger.info(f"没有指定股票代码，返回空字典")
            return {}
        
        dict_result = {}
        table_name = period.get_table_name()
        for code in code_list:
            try:
                lastest_1d_data = self.stock_db_base.get_lastest_stock_data(code, table_name)     

                if lastest_1d_data is None or lastest_1d_data.empty:
                    self.logger.debug(f"股票 {code} 日线数据为空，跳过指标计算")
                    continue 

                # 只对非空数据进行指标计算
                lastest_1d_data['name'] = self.get_stock_name_by_code(code)
                sdi.default_indicators_auto_calculate(lastest_1d_data)
                dict_result[code] = lastest_1d_data
                
            except Exception as e:
                self.logger.error(f"处理股票 {code} 时发生错误: {str(e)}")
                self.logger.error(traceback.format_exc())
                # 继续处理下一个股票
                continue

        return dict_result
