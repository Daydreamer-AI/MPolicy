import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime
import pandas as pd
import threading
import time
import numpy as np

from db_base.common_db_base import CommonDBBase
from manager.logging_manager import get_logger
from common.common_api import *
from manager.period_manager import TimePeriod

class FilterResultDBBase(CommonDBBase):
    
    def __init__(self, db_type = 0):
        self.logger = get_logger(__name__)
        self.db_type = db_type
        db_path_tmp = self._get_db_path_by_type(db_type)
        
        # 调用父类构造函数
        super().__init__(db_path_tmp)
        self.logger.info("StockDBManager--self._init_db()")
        self._init_db()

    def _get_db_path_by_type(self, db_type):
        """根据db_type获取数据库路径"""
        if db_type == 0:
            return "./data/database/policy_filter/filter_result/zero_up_ma52/filter_result.db"
        elif db_type == 1:
            return "./data/database/policy_filter/filter_result/zero_up_ma24/filter_result.db"
        elif db_type == 2:
            return "./data/database/policy_filter/filter_result/zero_up_ma10/filter_result.db"
        elif db_type == 3:
            return "./data/database/policy_filter/filter_result/zero_up_ma5/filter_result.db"
        elif db_type == 4:
            return "./data/database/policy_filter/filter_result/zero_down_ma52/filter_result.db"
        elif db_type == 5:
            return "./data/database/policy_filter/filter_result/zero_down_ma5/filter_result.db"
        elif db_type == 6:
            return "./data/database/policy_filter/filter_result/zero_down_breakthrough_ma52/filter_result.db"
        elif db_type == 7:
            return "./data/database/policy_filter/filter_result/zero_down_breakthrough_ma24/filter_result.db"
        elif db_type == 8:
            return "./data/database/policy_filter/filter_result/zero_down_double_bottom/filter_result.db"
        elif db_type == 9:
            return "./data/database/policy_filter/filter_result/zero_down_double_bottom/背离/filter_result.db"
        elif db_type == 10:
            return "./data/database/policy_filter/filter_result/zero_down_double_bottom/动能不足/filter_result.db"
        elif db_type == 11:
            return "./data/database/policy_filter/filter_result/zero_down_double_bottom/隐形背离/filter_result.db"
        elif db_type == 12:
            return "./data/database/policy_filter/filter_result/zero_down_double_bottom/隐形动能不足/filter_result.db"
        elif db_type == 13:
            return "./data/database/policy_filter/filter_result/limit_copy/filter_result.db"
        else:
            return "./data/database/policy_filter/filter_result/zero_up_ma52/filter_result.db"
        
    def _init_db(self):
        allowed_period_list = TimePeriod.get_period_list()
        for period in allowed_period_list:
            self.create_filter_result_table(period)

    def get_create_table_sql(self, table_name='filter_result'):
        sql = f"""CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                code TEXT NOT NULL,
                filter_params TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, code, filter_params)
                )"""
        
        return sql
    def create_filter_result_table(self, period=TimePeriod.DAY):
        table_name = f"filter_result_{period.value}"

        create_table_sql = self.get_create_table_sql(table_name)
        self.create_table(table_name, create_table_sql)

    def save_filter_result_to_db(self, df_result, period=TimePeriod.DAY):

        table_name = f"filter_result_{period.value}"

        try:
            # 修改冲突列为新的唯一约束字段
            self.upsert_data(table_name, df_result.to_dict('records'), 
                           conflict_columns=['date', 'code', 'filter_params'])
            return True
        except Exception as e:
            self.logger.info(f"插入数据失败: {e}")
            return False
        
    def query_filter_result(self, date=None, period=TimePeriod.DAY, code=None):
        """查询筛选结果数据"""
        conditions = []
        params = []

        table_name = f"filter_result_{period.value}"
        
        if date:
            conditions.append("date = ?")
            params.append(date)
        
        if code:
            conditions.append("code LIKE ?")
            params.append(f"%{code}%")

        query = f"SELECT * FROM {table_name}"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY date DESC"
        
        try:
            with self._get_connection() as cur:
                cur.execute(query, params)
                column_names = [description[0] for description in cur.description]
                rows = cur.fetchall()
                return pd.DataFrame(rows, columns=column_names)
        except Exception as e:
            self.logger.info(f"查询策略筛选结果时出错: {str(e)}")
            return pd.DataFrame()
        
    def get_latest_filter_result(self, period=TimePeriod.DAY):
        """获取最新日期的筛选结果数据"""
        table_name = f"filter_result_{period.value}"
        try:
            with self._get_connection() as cur:
                cur.execute(f'''
                    SELECT * FROM {table_name} 
                    WHERE date = (SELECT MAX(date) FROM {table_name})
                ''')
                
                column_names = [description[0] for description in cur.description]
                rows = cur.fetchall()
                
                if rows:
                    return pd.DataFrame(rows, columns=column_names)
                else:
                    return pd.DataFrame()
                    
        except Exception as e:
            self.logger.info(f"查询最新策略筛选结果时出错: {str(e)}")
            return pd.DataFrame()


