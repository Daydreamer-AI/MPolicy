import baostock as bs
import pandas as pd
import numpy as np
from data_base.stocks_db_manager import DBManagerPool
from data_base import StockDbBase
from indicators import stock_data_indicators as sdi
import random
import time
import datetime
from policy_filter import policy_filter as pf
import threading
from datetime import date, timedelta
from common.config_manager import ConfigManager
import threading
from common.common_api import *
from common.logging_manager import get_logger
import traceback
from types import MappingProxyType

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
class BaoStockProcessor:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.stocks_db_manager = DBManagerPool().get_manager(1)
        self.stock_db_base = StockDbBase("./stocks/db/baostock")

        self.dict_all_stocks = {}

        self.dict_daily_stock_data = {}
        self.dict_weekly_stock_data = {}

        self.b_stop_process = False
        self.lock = threading.Lock()  # 创建一把锁
        self._is_initialized = False # 状态标志

        self.dict_daily_null_codes = {}
        self.dict_weekly_null_codes = {}

    
    # def __del__(self):
    #     self.logger.info("登出Baostock系统")
    #     bs.logout()
    def initialize(self) -> bool:
        """显式登录Baostock系统。应在程序开始时调用。"""
        try:
            self.get_all_stocks_from_db()
            sh_main_count = len(self.dict_all_stocks['sh_main'])
            sz_main_count = len(self.dict_all_stocks['sz_main'])
            self.logger.info(f"沪A主板股票数量：{sh_main_count}")
            self.logger.info(f"深A主板股票数量：{sz_main_count}")

            # 读取本地k线数据
            # self.load_all_local_stock_data()

            config_manager = ConfigManager()
            config_manager.set_config_path("./resources/config/config.ini")
            policy_filter_turn_config = config_manager.get('PolicyFilter', 'turn')
            policy_filter_lb_config = config_manager.get('PolicyFilter', 'lb')
            weekly_condition = config_manager.get('PolicyFilter', 'weekly_condition', '1')
            s_filter_date = config_manager.get('PolicyFilter', 'filter_date', '')
            s_target_code = config_manager.get('PolicyFilter', 'target_code', '')

            self.logger.info(f"Config from config.ini: {policy_filter_turn_config}, {policy_filter_lb_config}, {weekly_condition}, {s_filter_date}, {s_target_code}")

            self.set_policy_filter_turn(float(policy_filter_turn_config))
            self.set_policy_filter_lb(float(policy_filter_lb_config))
            if weekly_condition == '1':
                b_weekly_condition = True
            else:
                b_weekly_condition = False
            self.set_weekly_condition(b_weekly_condition)
            self.set_filter_date(s_filter_date)
            self.set_target_code(s_target_code)

            config_manager.set('PolicyFilter', 'turn', policy_filter_turn_config)
            config_manager.set('PolicyFilter', 'lb', policy_filter_lb_config)
            config_manager.set('PolicyFilter', 'weekly_condition', weekly_condition)
            config_manager.set('PolicyFilter', 'filter_date', s_filter_date)
            config_manager.set('PolicyFilter', 'target_code', s_target_code)
            config_manager.save()

            self.logger.info("登录Baostock系统")
            lg = bs.login()
            # 显示登陆返回信息
            self.logger.info('login respond error_code:'+lg.error_code)
            self.logger.info('login respond  error_msg:'+lg.error_msg)

            if lg.error_code == '0':
                self._is_initialized = True
                self.logger.info("Baostock login successful.")

                self.df_trade_dates = self.get_current_trade_dates()
                if self.is_trading_day_today():
                    self.logger.info("今天是交易日")
                    # self.can_update_today_data()
                else:
                    self.logger.info("今天不是交易日")
                
                return True
            else:
                self.logger.info(f"Baostock login failed: {lg.error_msg}")
                return False
        except Exception as e:
            self.logger.info("An error occurred during Baostock login.")
            self.logger.info(f"Traceback: {traceback.format_exc()}")
            return False

    def cleanup(self) -> None:
        """显式登出Baostock系统。应在程序结束时调用。"""
        if self._is_initialized:
            try:
                bs.logout()
                self.logger.info("Baostock logged out successfully.")
            except Exception as e:
                # 此时发生异常可能由于解释器正在关闭，记录警告即可
                self.logger.info(f"Baostock logout encountered an error (may be during shutdown): {e}")
            finally:
                self._is_initialized = False

    def load_all_local_stock_data(self):
        """
        遍历所有股票代码并进行处理
        """
        total_count = 0
        
        # 遍历所有板块
        board_index = 0
        for board_name, board_data in self.dict_all_stocks.items():
            # if board_index > 0:
            #     break
            board_index += 1

            self.logger.info(f"处理 {board_name} 板块...")
            
            # 遍历该板块的每一行数据
            for index, row in board_data.iterrows():
                # if index > 100:
                #     break

                try:
                    stock_code = row['证券代码']
                    stock_name = row['证券名称'] if '证券名称' in row else '未知'
                    
                    # 获取日线和周线数据
                    daily_data = self.stock_db_base.get_bao_stock_data(stock_code, table_name="stock_data_1d")
                    weekly_data = self.stock_db_base.get_bao_stock_data(stock_code, table_name="stock_data_1w")
                    
                    # 检查数据是否为None，如果是则创建空的DataFrame
                    if daily_data is None or daily_data.empty:
                        continue
                        self.logger.warning(f"股票 {stock_code} 日线数据为None，创建空DataFrame")
                        daily_data = pd.DataFrame()
                    
                    if weekly_data is None or weekly_data.empty:
                        continue
                        self.logger.warning(f"股票 {stock_code} 周线数据为None，创建空DataFrame")
                        weekly_data = pd.DataFrame()
                    
                    # 存储数据
                    self.dict_daily_stock_data[stock_code] = daily_data
                    self.dict_weekly_stock_data[stock_code] = weekly_data

                    # 只对非空数据进行指标计算
                    if not self.dict_daily_stock_data[stock_code].empty:
                        sdi.default_indicators_auto_calculate(self.dict_daily_stock_data[stock_code])
                    else:
                        self.logger.debug(f"股票 {stock_code} 日线数据为空，跳过指标计算")
                        
                    if not self.dict_weekly_stock_data[stock_code].empty:
                        sdi.default_indicators_auto_calculate(self.dict_weekly_stock_data[stock_code])
                    else:
                        self.logger.debug(f"股票 {stock_code} 周线数据为空，跳过指标计算")

                    total_count += 1
                    
                except Exception as e:
                    self.logger.error(f"处理股票 {stock_code} 时发生错误: {str(e)}")
                    self.logger.error(traceback.format_exc())
                    # 继续处理下一个股票
                    continue
        
        self.logger.info(f"总共处理了 {total_count} 只股票")
    def get_daily_stock_data(self, code, start_date = None, end_date=None) -> pd.DataFrame:
        '''
            获取股票日K线数据
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期

            返回:
                DataFrame: 股票日K线数据
        '''
        # 检查股票代码是否存在于字典中
        if code not in self.dict_daily_stock_data:
            self.logger.warning(f"股票代码 {code} 不存在于日线数据中")
            return pd.DataFrame()
        
        # 获取该股票的所有日线数据
        result = self.dict_daily_stock_data[code]
        
        # 如果没有数据，直接返回空DataFrame
        if result.empty:
            return result
        
        # 如果提供了日期范围，则进行过滤
        if start_date is not None or end_date is not None:
            # 确保'date'列是datetime类型
            result = result.copy()  # 避免修改原始数据
            result['date'] = pd.to_datetime(result['date'])
            
            # 应用开始日期过滤
            if start_date is not None:
                start_date = pd.to_datetime(start_date)
                result = result[result['date'] >= start_date]
            
            # 应用结束日期过滤
            if end_date is not None:
                end_date = pd.to_datetime(end_date)
                result = result[result['date'] <= end_date]
        
        return result
    
    def get_weekly_stock_data(self, code, start_date = None, end_date=None) -> pd.DataFrame:
        '''
            获取股票周K线数据
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期

            返回:
                DataFrame: 股票周K线数据
        '''
        # 检查股票代码是否存在于字典中
        if code not in self.dict_weekly_stock_data:
            self.logger.warning(f"股票代码 {code} 不存在于周线数据中")
            return pd.DataFrame()
        
        # 获取该股票的所有周线数据
        result = self.dict_weekly_stock_data[code]
        
        # 如果没有数据，直接返回空DataFrame
        if result.empty:
            return result
        
        # 如果提供了日期范围，则进行过滤
        if start_date is not None or end_date is not None:
            # 确保'date'列是datetime类型
            result = result.copy()  # 避免修改原始数据
            result['date'] = pd.to_datetime(result['date'])
            
            # 应用开始日期过滤
            if start_date is not None:
                start_date = pd.to_datetime(start_date)
                result = result[result['date'] >= start_date]
            
            # 应用结束日期过滤
            if end_date is not None:
                end_date = pd.to_datetime(end_date)
                result = result[result['date'] <= end_date]
        
        return result

    def get_all_daily_stock_data_dict(self):
        '''
            获取所有股票日K线数据
            返回:
                dict: 所有股票日K线数据
        '''
        return self.dict_daily_stock_data
    
    def get_all_daily_stock_data_dict_copy(self):
        '''返回浅拷贝'''
        return self.dict_daily_stock_data.copy()
    
    def get_all_daily_stock_data_dict_readonly(self):
        '''
            获取所有股票日K线数据（只读）
            返回:
                MappingProxyType: 所有股票日K线数据的只读视图
        '''
        return MappingProxyType(self.dict_daily_stock_data)
    
    
    def get_all_weekly_stock_data_dict(self):
        '''
            获取所有股票周K线数据
            返回:
                dict: 所有股票周K线数据
        '''
        return self.dict_weekly_stock_data
    
    def get_all_weekly_stock_data_dict_copy(self):
        return self.dict_weekly_stock_data.copy()
    
    def get_all_weekly_stock_data_dict_readonly(self):
        '''
            获取所有股票周K线数据（只读）
            返回:
                MappingProxyType: 所有股票周K线数据的只读视图
        '''
        return MappingProxyType(self.dict_weekly_stock_data)

    def data_type_conversion(self, result):
        # 1. 转换日期列
        if 'date' in result.columns:
            result['date'] = pd.to_datetime(result['date'], format='%Y-%m-%d').dt.date  # 转换为 datetime.date 类型，或者用 .dt.normalize() 取日期部分

        # 2. 转换数值列 (开盘, 最高, 最低, 收盘, 成交额, 涨跌幅, 换手率)
        numeric_columns = ['open', 'high', 'low', 'close', 'amount', 'change_percent', 'turnover_rate']
        for col in numeric_columns:
            result[col] = pd.to_numeric(result[col], errors='coerce')  # errors='coerce' 将无效解析转换为NaN

        # 3. 转换成交量 (整数)
        if 'volume' in result.columns:
            result['volume'] = pd.to_numeric(result['volume'], errors='coerce').astype('Int64')  # 使用 Pandas 的可空整数类型

        # 4. 转换复权方式 (整数)
        if 'adjustflag' in result.columns:
            result['adjustflag'] = pd.to_numeric(result['adjustflag'], errors='coerce').astype('Int64')

        # 5. 转换是否ST (布尔值) - 根据你的数据实际情况定义如何映射
        # 假设你的字符串可能是 '是'/'否' 或 '1'/'0'
        if 'isST' in result.columns:
            result['isST'] = result['isST'].map({'是': True, '否': False, '1': True, '0': False, 'True': True, 'False': False})
        # 或者如果原本是字符串形式的 'True'/'False'
        # result['是否ST'] = result['是否ST'].astype(bool)
        # else:
            # self.logger.info("result中没有 是否ST 列")

        # 打印转换后的数据类型检查
        # self.logger.info(result.dtypes)

    def get_current_year_dates(self):
        """
        获取当前年份的起始和结束日期
        
        Returns:
            tuple: (start_date, end_date) 格式为 "YYYY-MM-DD"
        """
        current_year = datetime.datetime.now().year
        start_date = f"{current_year}-01-01"
        end_date = f"{current_year}-12-31"
        return start_date, end_date

    # 获取当年交易日信息
    def get_current_trade_dates(self):
        # bs.login()
        #### 获取交易日信息 ####
        start_date, end_date = self.get_current_year_dates()
        rs = bs.query_trade_dates(start_date=start_date, end_date=end_date)
        self.logger.info('query_trade_dates respond error_code:'+rs.error_code)
        self.logger.info('query_trade_dates respond  error_msg:'+rs.error_msg)

        #### 打印结果集 ####
        data_list = []
        while (rs.error_code == '0') & rs.next():
            # 获取一条记录，将记录合并在一起
            data_list.append(rs.get_row_data())
        result = pd.DataFrame(data_list, columns=rs.fields)

        #### 结果集输出到csv文件 ####   
        # result.to_csv("D:\\trade_datas.csv", encoding="gbk", index=False)
        # self.logger.info("2025年交易日：", result)
        # bs.login()
        return result

    def is_trading_day(self, day_str=''):
        if day_str in self.df_trade_dates['calendar_date'].values:
            trading_status = self.df_trade_dates.loc[self.df_trade_dates['calendar_date'] == day_str, 'is_trading_day'].iloc[0]
            return trading_status == '1'
        else:
            return False # 或者根据你的需求返回 None 或抛出异常

    # 判断当天是否是交易日
    def is_trading_day_today(self):
        today_str = datetime.datetime.now().strftime('%Y-%m-%d')
        return self.is_trading_day(today_str)

    # 判断能否更新当天交易数据
    def can_update_today_data(self):
        # 获取当前日期和时间
        now = datetime.datetime.now()

        # 创建今天17:30的datetime对象
        target_datetime = datetime.datetime(now.year, now.month, now.day, 18, 00)

        # 直接比较
        if now > target_datetime:
            # self.logger.info("当前时间在17:30之后")
            return True
        else:
            # self.logger.info("当前时间在17:30之前或等于20:30")
            return False

    def count_fridays_since(self, specific_date_str):
        """
        计算从指定日期到今天之间有多少个星期五。

        参数:
        specific_date_str (str): 字符串格式的日期，期望格式为 "YYYY-MM-DD"，例如 "2025-08-29"。

        返回:
        int: 星期五的数量。
        """
        try:
            # 1. 将字符串转换为日期对象
            specific_date = datetime.datetime.strptime(specific_date_str, '%Y-%m-%d').date()
        except ValueError:
            raise ValueError("日期格式错误，请使用 'YYYY-MM-DD' 格式。")

        # 2. 获取今天的日期
        today = date.today()

        # 确保输入的日期不晚于今天
        if specific_date > today:
            return 0

        # 3. 初始化计数器
        friday_count = 0
        # 4. 循环遍历从指定日期到今天的每一天
        current_date = specific_date
        while current_date <= today:
            # 5. 判断当前日期是否为星期五 (Monday=0, Sunday=6)
            if current_date.weekday() == 4:
                friday_count += 1
            # 6. 移动到下一天
            current_date += timedelta(days=1)

        return friday_count
    
    def count_trading_days(self, s_begin_date, s_end_date=None):
        '''计算指定日期范围内的交易日天数'''
        try:
            # 1. 将字符串转换为日期对象
            start_date = datetime.datetime.strptime(s_begin_date, '%Y-%m-%d').date()
            
            # 如果未指定结束日期，则使用今天
            if s_end_date is None:
                end_date = date.today()
            else:
                end_date = datetime.datetime.strptime(s_end_date, '%Y-%m-%d').date()
        except ValueError:
            raise ValueError("日期格式错误，请使用 'YYYY-MM-DD' 格式。")

        # 确保日期合理
        if end_date < start_date:
            return 0
        
        # 确保交易日数据已加载
        if not hasattr(self, 'df_trade_dates') or self.df_trade_dates is None:
            self.logger.warning("交易日数据未初始化，返回0")
            return 0
        
        # 筛选指定日期范围内的交易日
        mask = (
            (pd.to_datetime(self.df_trade_dates['calendar_date']).dt.date >= start_date) &
            (pd.to_datetime(self.df_trade_dates['calendar_date']).dt.date <= end_date) &
            (self.df_trade_dates['is_trading_day'] == '1')
        )
        
        return len(self.df_trade_dates[mask])
        

    # 全量更新
    def process_daily_stock_data(self, code, start_date=None, end_date=None):
        if start_date == None or end_date == None:
            # 默认计算近3年的日期范围
            end_date = (datetime.datetime.now()).strftime("%Y-%m-%d")
            start_date = (datetime.datetime.now() - datetime.timedelta(days=365*3)).strftime("%Y-%m-%d")
            # self.logger.info(f"获取股票 {stock_code} 数据，时间范围：{start_date} 至 {end_date}")
        
        sleep_time = random.uniform(0, 1)
        # time.sleep(sleep_time)

        # 判断是否是否交易

        # lg = bs.login()
        rs = bs.query_history_k_data_plus(code,
            "date,code,open,high,low,close,volume,amount,pctChg,turn,adjustflag",
            start_date=start_date, end_date=end_date,
            frequency="d", adjustflag="2")
        # self.logger.info(rs.error_code)      # 0
        # self.logger.info(rs.error_msg)       # success
        # self.logger.info("rs的类型：", type(rs))       # <class 'baostock.data.resultset.ResultData'>

        # 获取具体的信息
        result_list = []
        while (rs.error_code == '0') & rs.next():
            # 分页查询，将每页信息合并在一起
            result_list.append(rs.get_row_data())

        # self.logger.info("result_list的类型：", type(result_list))     # <class 'list'>
        new_columns = ['date', 'code', 'open', 'high', 'low', 'close', 'volume', 'amount', 'change_percent', 'turnover_rate', 'adjustflag']
        result = pd.DataFrame(result_list, columns=new_columns)

        self.data_type_conversion(result)

        result = result.dropna()

        # 登出系统
        # bs.logout()
        return result

    def process_and_save_daily_stock_data(self, code):
        result = pd.DataFrame()

        if not self.stock_db_base.check_stock_db_exists(code) or not self.stock_db_base.check_table_exists(code, "stock_data_1d"):
            # self.logger.info(f"{code}.db 不存在，即将从Baostock获取")
            result = self.process_daily_stock_data(code)

            # 指标不再入库，使用时按需计算
            if not result.empty:
            #     sdi.macd(result)
            #     sdi.ma(result, 'ma5', 5)
            #     sdi.ma(result, 'ma10', 10)
            #     sdi.ma(result, 'ma20', 20)
            #     sdi.ma(result, 'ma24', 24)
            #     sdi.ma(result, 'ma30', 30)
            #     sdi.ma(result, 'ma52', 52)
            #     sdi.ma(result, 'ma60', 60)
            #     sdi.quantity_ratio(result)
                self.stock_db_base.save_bao_stock_data_to_db(code, result, 'replace', "stock_data_1d")
        else:
            # self.logger.info(f"{code}.db 存在，即将从本地数据库更新")
            result = self.update_daily_stock_data(code)
        
        # if result.empty:
        #     self.logger.info("process_daily_stock_data执行结果为空！")
        #     return False

        # self.logger.info(result.tail(3))
        
        # 优化：策略筛选只需要最后一行数据即可
        self.dict_daily_stock_data[code] = result
        # 对内存数据进行指标计算
        sdi.default_indicators_auto_calculate(self.dict_daily_stock_data[code])

        return result
       
    # 增量维护，收盘后调用
    def update_daily_stock_data(self, code):
        if not self.stock_db_base.check_stock_db_exists(code):
            self.logger.info("{stock_code}.db 不存在", code)
            return pd.DataFrame()

        # 步骤一：得到当前数据库中的股票数据
        day_stock_data = self.stock_db_base.get_bao_stock_data(code, table_name="stock_data_1d")
        # self.logger.info("code: ", code)
        # self.logger.info("day_stock_data的类型：", type(day_stock_data))
        # self.logger.info(day_stock_data.tail(1))
        if day_stock_data is None or day_stock_data.empty:
            self.logger.info("day_stock_data为空")
            return pd.DataFrame()

        # 判断是否存在空值
        if day_stock_data.isnull().values.any():
            # self.logger.info("存在空值")
            # 获取所有包含空值的行
            rows_with_nulls = day_stock_data[day_stock_data.isnull().any(axis=1)]
            # self.logger.info("\n所有包含空值的行:")
            # self.logger.info(rows_with_nulls)
            
            # 提取第一个包含空值的行（按索引顺序）
            first_row_with_null = rows_with_nulls.iloc[0]
            # self.logger.info("\n第一个包含空值的行:")
            # self.logger.info(first_row_with_null)

            null_data_code = first_row_with_null['code']
            # self.logger.info(f"第一个包含空值行的股票代码: {null_data_code}")
            first_null_date = first_row_with_null['date']
            # self.logger.info("第一个包含空值的行日期类型是: ", type(first_null_date))  # <class 'str'>
            # self.logger.info(f"第一个包含空值的行日期是: {first_null_date}")
        

        #     # 查找第一个出现空值的行索引
        #     first_null_index = day_stock_data.isnull().any(axis=1).idxmax()

        #     # 删除该行及之后的所有行
        #     day_stock_data = day_stock_data.loc[:first_null_index-1]  # 保留到第一个空值行之前的所有行

        #     # 数据库同步
        #     self.stock_db_base.delete_data_by_date(null_data_code, first_null_date)

            # 移除空列以便后面合并
            day_stock_data = day_stock_data.dropna()
        

        now_date = datetime.datetime.now().strftime("%Y-%m-%d")
        if now_date in day_stock_data['date'].values:
            # self.logger.info("已是最新日线数据")
            return day_stock_data
        
        last_date = None
        if day_stock_data.empty or day_stock_data is None:
            self.logger.info("数据库表为空，默认获取近3年股票数据")
            last_date = (datetime.datetime.now() - datetime.timedelta(days=365*3)).strftime("%Y-%m-%d")
        else:
            last_date = day_stock_data['date'].iloc[-1]
        # self.logger.info("最后日期（方法2）:", last_date) 

        parsed_date = datetime.datetime.strptime(last_date, "%Y-%m-%d")  # 解析为日期对象
        last_date = parsed_date + datetime.timedelta(days=1)

        # 获取数据库中最后日期至今的股票数据
        start_date = last_date.strftime("%Y-%m-%d")               # Baostock要求的日期格式
        end_date = (datetime.datetime.now()).strftime("%Y-%m-%d")   #  + datetime.timedelta(days=1)
        # self.logger.info(f"获取股票 {code} 数据，时间范围：{start_date} 至 {end_date}")
        
        # 判断数据库最后日期至今有无交易日数据需更新
        if self.is_trading_day_today():
            # 交易日18:00后才能更新当天数据
            if not self.can_update_today_data():
                # self.logger.info("今天不是交易日，未到数据更新时间，请稍后再试")
                return day_stock_data
        else:
            self.logger.info("今天不是交易日，判断数据库中是否是最新数据")
            trading_day_count = self.count_trading_days(start_date, end_date)
            self.logger.info(f"交易日数量：{trading_day_count}")
            if trading_day_count == 0:
                self.logger.info("数据库中已是最新数据，直接返回现有数据")
                return day_stock_data

        
        df_new_stock_data = self.process_daily_stock_data(code, start_date, end_date)
        # 判断获取到的数据是否存在空值
        # if df_new_stock_data.isnull().values.any():
        #     self.logger.info(f"股票 {code} 的数据存在空值")
        #     return day_stock_data
        # if df_new_stock_data.empty:
        #     self.logger.info("process_daily_stock_data执行结果为空！")
        #     return False
        
        # self.logger.info("获取到的新数据：")
        # self.logger.info(df_new_stock_data)

        df_new_stock_data = df_new_stock_data.dropna()

        if not df_new_stock_data.empty:
            # 处理空 DataFrame 的情况
            if day_stock_data.empty:
                combined_df = df_new_stock_data.copy()
                self.logger.info("原数据为空，直接使用新获取的数据")
            else:
                # 合并计算指标
                combined_df = pd.concat([day_stock_data, df_new_stock_data], axis=0, ignore_index=True)

            # 指标数据不再入库
            # sdi.macd(combined_df)
            # sdi.ma(combined_df, 'ma5', 5)
            # sdi.ma(combined_df, 'ma10', 10)
            # sdi.ma(combined_df, 'ma20', 20)
            # sdi.ma(combined_df, 'ma24', 24)
            # sdi.ma(combined_df, 'ma30', 30)
            # sdi.ma(combined_df, 'ma52', 52)
            # sdi.ma(combined_df, 'ma60', 60)
            # sdi.quantity_ratio(combined_df)
        
            # self.logger.info("新数据指标计算结果：")
            data_to_save = combined_df.tail(len(df_new_stock_data))
            # self.logger.info(data_to_save)
            self.stock_db_base.save_bao_stock_data_to_db(code, data_to_save, "append", "stock_data_1d")
            self.dict_daily_stock_data[code] = combined_df
            return combined_df
        
        # self.logger.info("未获取到新数据")
        self.dict_daily_stock_data[code] = day_stock_data
        return day_stock_data

    # 空值修复
    def fix_null_value(self, code, data_to_save):
        pass

    # 全量更新
    def process_weekly_stock_data(self, code, start_date=None, end_date=None):
        if start_date == None or end_date == None:
            # 默认计算近3年的日期范围（周线数据通常需要更长时间来计算指标）
            end_date = datetime.datetime.now().strftime("%Y-%m-%d")
            # end_date = (datetime.datetime.now() - datetime.timedelta(days=3)).strftime("%Y-%m-%d")
            start_date = (datetime.datetime.now() - datetime.timedelta(days=365*3)).strftime("%Y-%m-%d")

        # self.logger.info(f"获取股票 {code} 周线数据，时间范围：{start_date} 至 {end_date}")
        
        sleep_time = random.uniform(0, 1) # 等待时间可以设得稍长一些
        # time.sleep(sleep_time)

        # lg = bs.login()
        rs = bs.query_history_k_data_plus(code,
            "date,code,open,high,low,close,volume,amount,pctChg,turn,adjustflag",
            start_date=start_date, end_date=end_date,
            frequency="w", adjustflag="2")
        # self.logger.info(rs.error_code)      # 0
        # self.logger.info(rs.error_msg)       # success
        # self.logger.info("rs的类型：", type(rs))       # <class 'baostock.data.resultset.ResultData'>

        # 获取具体的信息
        result_list = []
        while (rs.error_code == '0') & rs.next():
            # 分页查询，将每页信息合并在一起
            result_list.append(rs.get_row_data())

        # self.logger.info("result_list的类型：", type(result_list))     # <class 'list'>
        chinese_columns = ['date', 'code', 'open', 'high', 'low', 'close', 'volume', 'amount', 'change_percent', 'turnover_rate', 'adjustflag']
        result = pd.DataFrame(result_list, columns=chinese_columns)

        self.data_type_conversion(result)

        result = result.dropna()

        # self.logger.info("process_weekly_stock_data执行结果：")
        # self.logger.info(result.tail(3))

        # 登出系统
        # bs.logout()
        return result

    def process_and_save_weekly_stock_data(self, code):
        result = pd.DataFrame()
        if not self.stock_db_base.check_stock_db_exists(code) or not self.stock_db_base.check_table_exists(code, "stock_data_1w"):
            # self.logger.info(f"周线 {code}.db 不存在，即将从Baostock获取")
            result = self.process_weekly_stock_data(code)

            if not result.empty:
                # sdi.macd(result)
                # sdi.ma(result, 'ma5', 5)
                # sdi.ma(result, 'ma10', 10)
                # sdi.ma(result, 'ma20', 20)
                # sdi.ma(result, 'ma24', 24)
                # sdi.ma(result, 'ma30', 30)
                # sdi.ma(result, 'ma52', 52)
                # sdi.ma(result, 'ma60', 60)
                # sdi.quantity_ratio(result)
                self.stock_db_base.save_bao_stock_data_to_db(code, result, 'replace', "stock_data_1w")
        else:
            # self.logger.info(f"周线 {code}.db 存在，即将从本地数据库更新")
            result = self.update_weekly_stock_data(code)

        # if result.empty:
        #     self.logger.info("process_weekly_stock_data执行结果为空！")
        #     return False

        # self.logger.info(f"周线 {code} 数据：")
        # self.logger.info(result.tail(3))
        
        # 优化：策略筛选只需要最后一行数据即可
        self.dict_weekly_stock_data[code] = result

        # 对内存数据进行指标计算
        sdi.default_indicators_auto_calculate(self.dict_weekly_stock_data[code])

        return result

    # 增量维护，周线数据不好增量维护，追加后原表中还会存在周中数据。建议：每周末（或本周收盘后）调用一次更新本周周线数据
    # 例如：周二第一次update，表中会存在周二时的周线数据，当周线再update时，周二数据（已过时）依旧会在表中。
    # 补充：周线接口只能每周最后一个交易日才可以获取，月线每月最后一个交易日才可以获取。
    def update_weekly_stock_data(self, code):
        if not self.stock_db_base.check_stock_db_exists(code):
            self.logger.info("{stock_code}.db 不存在", code)
            return pd.DataFrame()

        # 步骤一：得到当前数据库中的股票数据
        week_stock_data = self.stock_db_base.get_bao_stock_data(code, table_name="stock_data_1w")
        if week_stock_data is None or week_stock_data.empty:
            self.logger.info("{stock_code}.db 中无周线数据", code)
            return pd.DataFrame()

        week_stock_data = week_stock_data.dropna()
        
        # 最后一行数据日期 + 1，至今有几个周五？一个也没有说明是最新数据，无需更新。
        # now_date = datetime.datetime.now().strftime("%Y-%m-%d")
        # if now_date in week_stock_data['date'].values:
        #     self.logger.info("已是最新数据")
        #     return week_stock_data
        last_date = week_stock_data['date'].iloc[-1]
        parsed_date = datetime.datetime.strptime(last_date, "%Y-%m-%d")  # 解析为日期对象
        last_date = parsed_date + datetime.timedelta(days=1)
        num_fridays = self.count_fridays_since(last_date.strftime("%Y-%m-%d"))
        if not num_fridays > 0:
            # self.logger.info("已是最新周线数据")
            return week_stock_data
        
        if self.is_trading_day_today():
            # 交易日17:30后才能更新当天数据
            if not self.can_update_today_data():
                return week_stock_data
        
        last_date = week_stock_data['date'].iloc[-1]
        # self.logger.info("最后周线日期:", last_date) 

        parsed_date = datetime.datetime.strptime(last_date, "%Y-%m-%d")  # 解析为日期对象
        last_date = parsed_date + datetime.timedelta(days=1)
        # self.logger.info(last_date.strftime("%Y-%m-%d"))

        # 步骤二：获取数据库中最后日期至今的股票数据
        start_date = last_date.strftime("%Y-%m-%d")               # Baostock要求的日期格式
        end_date = datetime.datetime.now().strftime("%Y-%m-%d")

        df_new_weekly_stock_data = self.process_weekly_stock_data(code, start_date, end_date)
        # if df_new_weekly_stock_data.empty:
        #     self.logger.info("process_weekly_stock_data执行结果为空！")
        #     return False
        
        # self.logger.info("获取到的新周线数据：", df_new_weekly_stock_data)

        # if not df_new_weekly_stock_data.empty:
        #     self.stock_db_base.save_bao_stock_data_to_db(code, df_new_weekly_stock_data, "append")

        df_new_weekly_stock_data = df_new_weekly_stock_data.dropna()

        if not df_new_weekly_stock_data.empty:
            # 合并计算指标
            combined_df = pd.concat([week_stock_data, df_new_weekly_stock_data], axis=0, ignore_index=True)
            # self.logger.info("合并后的combined_df:")
            # self.logger.info(combined_df.tail(3))

            # sdi.macd(combined_df)
            # sdi.ma(combined_df, 'ma5', 5)
            # sdi.ma(combined_df, 'ma10', 10)
            # sdi.ma(combined_df, 'ma20', 20)
            # sdi.ma(combined_df, 'ma24', 24)
            # sdi.ma(combined_df, 'ma30', 30)
            # sdi.ma(combined_df, 'ma52', 52)
            # sdi.ma(combined_df, 'ma60', 60)
            # sdi.quantity_ratio(combined_df)
        
            # self.logger.info("新周线数据指标计算结果：")
            data_to_save = combined_df.tail(len(df_new_weekly_stock_data))
            # self.logger.info(data_to_save)
            self.stock_db_base.save_bao_stock_data_to_db(code, data_to_save, "append", "stock_data_1w")
            self.dict_weekly_stock_data[code] = combined_df
            return combined_df
        
        # self.logger.info("未获取到新数据")
        self.dict_weekly_stock_data[code] = week_stock_data
        return week_stock_data


    # 全量获取
    def process_sh_main_stock_daily_data(self):
        i = 1
        for value in self.dict_all_stocks['sh_main']['证券代码']:
            # self.logger.info(f"获取第 {i} 只沪市主板股票 {value} 【日线】数据")
            i += 1

            # 判断是否已加载到内存
            # if value in self.dict_daily_stock_data.keys():
            #     self.logger.info(f"股票 {value} 数据已存在")
            #     continue

            self.process_and_save_daily_stock_data(value)
            # if i > 3:
            #     self.logger.info(f"已获取到所有沪市股票日线数据, i: {i}")
            #     break

            self.logger.info(f"获取第 {i} 只沪市主板股票 {value} 【日线】数据完成")
        
        self.logger.info("沪市主板股票日线数据获取完成")

    def process_sh_main_stock_weekly_data(self):
        i = 1
        for value in self.dict_all_stocks['sh_main']['证券代码']:
            # self.logger.info(f"获取第 {i} 只沪市主板股票 {value} 【周线】数据")
            i += 1
            self.process_and_save_weekly_stock_data(value)

            # if i > 3:
            #     self.logger.info(f"已获取到所有沪市股票周线数据, i: {i}")
            #     break
            self.logger.info(f"获取第 {i} 只沪市主板股票 {value} 【周线】数据完成")

        self.logger.info("沪市主板股票周线数据获取完成")

    def process_sz_main_stock_daily_data(self):
        i = 1
        for value in self.dict_all_stocks['sz_main']['证券代码']:
            # self.logger.info(f"获取第 {i} 只深市主板股票 {value} 【日线】数据")
            i += 1
            self.process_and_save_daily_stock_data(value)

            # if i > 1:
            #     self.logger.info(f"已获取到所有深市股票日线数据, i: {i}")
            #     break

            self.logger.info(f"获取第 {i} 只深市主板股票 {value} 【日线】数据完成")

        self.logger.info("深市主板股票日线数据获取完成")
    def process_sz_main_stock_weekly_data(self):
        i = 1
        for value in self.dict_all_stocks['sz_main']['证券代码']:
            # self.logger.info(f"获取第 {i} 只深市主板股票 {value} 【周线】数据")
            i += 1
            self.process_and_save_weekly_stock_data(value)

            # if i > 1:
            #     self.logger.info(f"已获取到所有深市股票周线数据, i: {i}")
            #     break

            self.logger.info(f"获取第 {i} 只深市主板股票 {value} 【周线】数据完成")

        self.logger.info("深市主板股票周线数据获取完成")

    def process_gem_stock_daily_data(self):
        i = 1
        for value in self.dict_all_stocks['gem']['证券代码']:
            # self.logger.info(f"获取第 {i} 只创业板股票 {value} 【日线】数据")
            i += 1
            self.process_and_save_daily_stock_data(value)

            # if i > 3:
            #     self.logger.info(f"已获取到所有创业板股票日线数据, i: {i}")
            #     break

    def process_gem_stock_weekly_data(self):
        i = 1
        for value in self.dict_all_stocks['gem']['证券代码']:
            # self.logger.info(f"获取第 {i} 只创业板股票 {value} 【周线】数据")
            i += 1
            self.process_and_save_weekly_stock_data(value)

            # if i > 3:
            #     self.logger.info(f"已获取到所有创业板股票周线数据, i: {i}")
            #     break

    def process_star_stock_daily_data(self):
        i = 1
        for value in self.dict_all_stocks['star']['证券代码']:
            # self.logger.info(f"获取第 {i} 只科创板股票 {value} 【日线】数据")
            i += 1
            self.process_and_save_daily_stock_data(value)
            # if i > 1:
            #     self.logger.info(f"已获取到所有科创板股票日线数据, i: {i}")
            #     break

    def process_star_stock_weekly_data(self):
        i = 1
        for value in self.dict_all_stocks['star']['证券代码']:
            # self.logger.info(f"获取第 {i} 只科创板股票 {value} 【周线】数据")
            i += 1
            self.process_and_save_weekly_stock_data(value)

            # if i > 1:
            #     self.logger.info(f"已获取到所有科创板股票周线数据, i: {i}")
            #     break


    def get_and_save_all_stocks_from_bao(self):
        #### 登陆系统 ####
        # lg = bs.login()
        # 显示登陆返回信息
        # self.logger.info('login respond error_code:'+lg.error_code)
        # self.logger.info('login respond  error_msg:'+lg.error_msg)

        #### 获取证券信息 ####
        query_date = datetime.datetime.now().strftime("%Y-%m-%d")
        rs = bs.query_all_stock(query_date)
        self.logger.info('query_all_stock respond error_code:'+rs.error_code)
        self.logger.info('query_all_stock respond  error_msg:'+rs.error_msg)

        #### 打印结果集 ####
        data_list = []
        while (rs.error_code == '0') & rs.next():
            # 获取一条记录，将记录合并在一起
            data_list.append(rs.get_row_data())

        chinese_columns = ['证券代码', '交易状态', '证券名称']
        result = pd.DataFrame(data_list, columns=chinese_columns)

        self.dict_all_stocks = self.filter_stocks_by_board(result)

        # 打印各板块股票数量
        for board_name, df_board in self.dict_all_stocks.items():
            self.logger.info(f"{board_name} 股票数量: {len(df_board)}")

            # self.logger.info(df_board.tail(1))

            # 如需查看具体代码，可取消下一行的注释
            # self.logger.info(f"{board_name} 股票代码:\n {df_board['code'].tolist()}\n")
            if board_name == '沪市主板':
                self.stocks_db_manager.save_tao_stocks_to_db(df_board, "replace", 'sh_main')
            elif board_name == '深市主板':
                self.stocks_db_manager.save_tao_stocks_to_db(df_board, "replace", 'sz_main')
            elif board_name == '创业板':
                self.stocks_db_manager.save_tao_stocks_to_db(df_board, "replace", 'gem')
            elif board_name == '科创板':
                self.stocks_db_manager.save_tao_stocks_to_db(df_board, "replace", 'star')
            # elif board_name == '北交所':
            #    self.stocks_db_manager.save_tao_stocks_to_db(df_board, "replace", 'bse')

        #### 结果集输出到csv文件 ####   
        # result.to_csv("./stocks/db/baostock/all_stock.csv", encoding="utf-8", index=False)
        # self.logger.info(result)
        # self.stocks_db_manager.save_tao_stocks_to_db(result)

        #### 登出系统 ####
        # bs.logout()

    def get_all_stocks_from_db(self):
        self.dict_all_stocks['sh_main'] = self.stocks_db_manager.get_sh_main_stocks()
        self.dict_all_stocks['sz_main'] = self.stocks_db_manager.get_sz_main_stocks()
        self.dict_all_stocks['gem'] = self.stocks_db_manager.get_gem_stocks()
        self.dict_all_stocks['star'] = self.stocks_db_manager.get_star_stocks()

    def filter_stocks_by_board(self, df):
        """
        根据证券代码前缀筛选出不同板块的股票
        """
        # 初始化空 DataFrame，用于存储各板块股票
        sh_main = pd.DataFrame()   # 沪市主板
        sz_main = pd.DataFrame()   # 深市主板
        gem = pd.DataFrame()       # 创业板
        star = pd.DataFrame()      # 科创板
        bse = pd.DataFrame()       # 北交所

        # 遍历每一行数据
        for index, row in df.iterrows():
            code = row['证券代码']
            
            if code.startswith('sh.600') or code.startswith('sh.601') or code.startswith('sh.603') or code.startswith('sh.605'):
                sh_main = pd.concat([sh_main, row.to_frame().T], ignore_index=True)
            elif code.startswith('sz.000') or code.startswith('sz.001') or code.startswith('sz.002') or code.startswith('sz.003'):
                sz_main = pd.concat([sz_main, row.to_frame().T], ignore_index=True)
            elif code.startswith('sz.300'):
                gem = pd.concat([gem, row.to_frame().T], ignore_index=True)
            elif code.startswith('sh.688'):
                star = pd.concat([star, row.to_frame().T], ignore_index=True)
            elif code.startswith('bj.'):  # 北交所股票前缀
                bse = pd.concat([bse, row.to_frame().T], ignore_index=True)
        
        return {
            '沪市主板': sh_main,
            '深市主板': sz_main,
            '创业板': gem,
            '科创板': star,
            '北交所': bse
        }

    def auto_test(self):
        filter_result = []
        # sh_main = self.stocks_db_manager.get_sh_main_stocks()
        # i = 1
        # for value in sh_main['证券代码']:
        #     self.logger.info(f"获取第 {i} 只股票 {value} 日线数据")
        #     stock_data = self.process_stock_daily_data(value)
        #     if self.daily_filter(stock_data):
        #         filter_result.append(value)

        sz_main = self.stocks_db_manager.get_sz_main_stocks()
        i = 1
        for value in sz_main['证券代码']:
            self.logger.info(f"获取第 {i} 只股票 {value} 日线数据")
            stock_data = self.process_daily_stock_data(value)
            # if self.daily_filter(stock_data):
            if pf.daily_ma52_filter(stock_data):
                filter_result.append(value)

        return filter_result

    # 增量更新
    def update_sh_main_daily_data(self):
        # i = 1
        # for value in self.dict_all_stocks['sh_main']['证券代码']:
        #     self.logger.info(f"获取第 {i} 只沪市主板股票 {value} 日线数据")
        #     i += 1
        self.update_daily_stock_data('sh.600000')

     # 策略筛选
    
    
    # 策略筛选
    def get_policy_filter_turn(self):
        return pf.get_policy_filter_turn()
    
    def get_policy_filter_lb(self):
        return pf.get_policy_filter_lb()
    
    def get_weekly_condition(self):
        return pf.get_weekly_condition()
    
    def get_filter_date(self):
        return pf.get_filter_date()
    
    def get_target_code(self):
        return pf.get_target_code()

    def set_policy_filter_turn(self, turn=3.0):
        self.logger.info(f"set_policy_filter_turn--换手率：{turn}")
        pf.set_policy_filter_turn(turn)

    def set_policy_filter_lb(self, lb=1.0):
        self.logger.info(f"set_policy_filter_lb--量比：{lb}")
        pf.set_policy_filter_lb(lb)

    def set_weekly_condition(self, b_weekly=True):
        self.logger.info(f"set_weekly_condition--启用周线筛选条件：{b_weekly}")
        pf.set_weekly_condition(b_weekly)

    def set_filter_date(self, date):
        self.logger.info(f"set_filter_date--筛选日期：{date}")
        pf.set_filter_date(date)

    def set_target_code(self, code):
        self.logger.info(f"set_target_code--目标股票代码：{code}")
        pf.set_target_code(code)

    def filter_check(self, code, condition=None, b_use_weekly_data=True):
        if b_use_weekly_data and code not in self.dict_weekly_stock_data.keys():
            self.logger.info(f"{code} 未在周线数据中")
            return False

        if condition is None or condition.empty:
            self.logger.info(f"筛选条件为空")
            return True
        else:
            # 特定股票代码筛选
            s_target_code = self.get_target_code()
            if s_target_code != '':
                # self.logger.info(f"目标股票代码：{s_target_code}，当前股票代码：{code}")
                if s_target_code in code:
                    return True
                else:
                    return False

            # 筛选市值大于50亿的股票
            standard_code = extract_pure_stock_code(code)

            # 根据实际列名调整
            code_column = 'stock_code' if 'stock_code' in condition.columns else '股票代码'
            market_value_column = 'float_market_cap' if 'float_market_cap' in condition.columns else '流通市值'

            if code_column not in condition.columns or market_value_column not in condition.columns:
                self.logger.info(f"condition DataFrame中缺少必要的列，跳过市值筛选，股票代码：{code}")
                return True
            else:
                exists = standard_code in condition[code_column].values
                if exists:
                    circulating_market_value = condition.loc[condition[code_column] == standard_code, market_value_column].iloc[0]
                    if circulating_market_value < 50 * 10000 * 10000:
                        # self.logger.info(f"流通市值小于50亿的股票被过滤掉: {code}")
                        return False
                    else:
                        return True

    def get_filter_result_file_suffix(self):
        turn = pf.get_policy_filter_turn()
        lb = pf.get_policy_filter_lb()
        b_weekly = pf.get_weekly_condition()
        filter_date = pf.get_filter_date()
        today_str = datetime.datetime.now().strftime('%m%d')
        s_target_code = pf.get_target_code()
        return f"{today_str}_{turn}_{lb}_{b_weekly}_{filter_date}_{s_target_code}"

    def daily_up_ma52_filter(self, condition=None):
        filter_result = []
        turn = pf.get_policy_filter_turn()
        lb = pf.get_policy_filter_lb()
        self.logger.info(f"开始执行日线零轴上方MA52筛选，换手率： {turn}, 量比：{lb}")
        for code, df_data in self.dict_daily_stock_data.items():
            if not self.filter_check(code, condition):
                continue

            if pf.daily_up_ma52_filter(df_data, self.dict_weekly_stock_data[code]):
                filter_result.append(code)


        save_list_to_txt(filter_result, f"./policy_filter/filter_result/daily_up_ma52/{self.get_filter_result_file_suffix()}.txt", ', ', "零轴上方MA52筛选结果：\n")
        return filter_result
    
    def daily_up_ma24_filter(self, condition=None):
        filter_result = []
        turn = pf.get_policy_filter_turn()
        lb = pf.get_policy_filter_lb()
        self.logger.info(f"开始执行日线零轴上方MA24筛选，换手率：{turn}, 量比：{lb}")
        for code, df_data in self.dict_daily_stock_data.items():
            if not self.filter_check(code, condition):
                continue

            if pf.daily_up_ma24_filter(df_data, self.dict_weekly_stock_data[code]):
                filter_result.append(code)

 
        save_list_to_txt(filter_result, f"./policy_filter/filter_result/daily_up_ma24/{self.get_filter_result_file_suffix()}.txt", ', ', "零轴上方MA24筛选结果：\n")
        return filter_result

    def daily_up_ma10_filter(self, condition=None):
        filter_result = []
        turn = pf.get_policy_filter_turn()
        lb = pf.get_policy_filter_lb()
        self.logger.info(f"开始执行日线零轴上方MA10筛选，换手率：{turn}, 量比：{lb}")
        for code, df_data in self.dict_daily_stock_data.items():
            if not self.filter_check(code, condition, False):
                continue

            if pf.daily_up_ma10_filter(df_data):
                filter_result.append(code)


        save_list_to_txt(filter_result, f"./policy_filter/filter_result/daily_up_ma10/{self.get_filter_result_file_suffix()}.txt", ', ', "零轴上方MA10筛选结果：\n")
        return filter_result
    
    def daily_down_between_ma24_ma52_filter(self, condition=None):
        
        filter_result = []
        turn = pf.get_policy_filter_turn()
        lb = pf.get_policy_filter_lb()
        self.logger.info(f"开始执行日线零轴下方方MA24-MA52筛选，换手率：{turn}, 量比：{lb}")
        for code, df_data in self.dict_daily_stock_data.items():
            if not self.filter_check(code, condition):
                continue

            if pf.daily_down_between_ma24_ma52_filter(df_data, self.dict_weekly_stock_data[code]):
                filter_result.append(code)

        save_list_to_txt(filter_result, f"./policy_filter/filter_result/daily_down_ma52/{self.get_filter_result_file_suffix()}.txt", ', ', "零轴下方MA52筛选结果：\n")
        return filter_result
    
    def daily_down_between_ma5_ma52_filter(self, condition=None):
        
        filter_result = []
        turn = pf.get_policy_filter_turn()
        lb = pf.get_policy_filter_lb()
        self.logger.info(f"开始执行日线零轴下方方MA5-MA52筛选，换手率：{turn}, 量比：{lb}")
        for code, df_data in self.dict_daily_stock_data.items():
            if not self.filter_check(code, condition):
                continue

            if pf.daily_down_between_ma5_ma52_filter(df_data, self.dict_weekly_stock_data[code]):
                filter_result.append(code)


        save_list_to_txt(filter_result, f"./policy_filter/filter_result/daily_down_ma5/{self.get_filter_result_file_suffix()}.txt", ', ', "零轴下方MA5筛选结果：\n")
        return filter_result
    

    def daily_down_breakthrough_ma24_filter(self, condition=None):
        filter_result = []
        turn = pf.get_policy_filter_turn()
        lb = pf.get_policy_filter_lb()
        self.logger.info(f"开始执行日线零轴下方MA24突破筛选，换手率：{turn}, 量比：{lb}")
        for code, df_data in self.dict_daily_stock_data.items():
            if not self.filter_check(code, condition, False):
                continue

            if pf.daily_down_breakthrough_ma24_filter(df_data):
                filter_result.append(code)

        save_list_to_txt(filter_result, f"./policy_filter/filter_result/daily_down_breakthrough_ma24_filter/{self.get_filter_result_file_suffix()}.txt", ', ', "零轴下方MA24突破筛选结果：\n")
        return filter_result

    def daily_down_breakthrough_ma52_filter(self, condition=None):
        filter_result = []
        turn = pf.get_policy_filter_turn()
        lb = pf.get_policy_filter_lb()
        self.logger.info(f"开始执行日线零轴下方MA52突破筛选，换手率：{turn}, 量比：{lb}")
        for code, df_data in self.dict_daily_stock_data.items():
            if not self.filter_check(code, condition, False):
                continue

            if pf.daily_down_breakthrough_ma52_filter(df_data):
                filter_result.append(code)

        save_list_to_txt(filter_result, f"./policy_filter/filter_result/daily_down_breakthrough_ma52_filter/{self.get_filter_result_file_suffix()}.txt", ', ', "零轴下方MA52突破筛选结果：\n")
        return filter_result

    def daily_down_double_bottom_filter(self, condition=None):
        filter_result = []
        turn = pf.get_policy_filter_turn()
        lb = pf.get_policy_filter_lb()
        self.logger.info(f"开始执行日线零轴下方双底筛选，换手率：{turn}, 量比：{lb}")
        for code, df_data in self.dict_daily_stock_data.items():
            if not self.filter_check(code, condition, False):
                continue
            
            if pf.daily_down_double_bottom_filter(df_data, self.dict_weekly_stock_data[code]):
                filter_result.append(code)

        save_list_to_txt(filter_result, f"./policy_filter/filter_result/daily_down_double_bottom_filter/{self.get_filter_result_file_suffix()}.txt", ', ', "零轴下方双底筛选结果：\n")
        return filter_result

    def stop_process(self):
        self.b_stop_process = True

if __name__ == "__main__":
    bao_stock_processor = BaoStockProcessor()
    bao_stock_processor.test()