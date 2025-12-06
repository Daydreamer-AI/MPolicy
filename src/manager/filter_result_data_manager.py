import threading
import os
import re
from datetime import datetime
import pandas as pd
import json


from db_base.filter_result_db_base import FilterResultDBBase
from manager.logging_manager import get_logger

def singleton(cls):
    """
    一个线程安全的单例装饰器。
    使用双重检查锁模式确保在多线程环境下也只创建一个实例。
    """
    instances = {}  # 用于存储被装饰类的唯一实例
    lock = threading.Lock()  # 创建一个锁对象，用于同步

    def get_instance(*args, **kwargs):
        if cls not in instances:
            with lock:
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)
        
        # 每次调用时更新类型
        instance = instances[cls]
        if hasattr(instance, 'switch_to_type') and args:
            instance.switch_to_type(args[0])
        elif hasattr(instance, 'switch_to_type') and 'type' in kwargs:
            instance.switch_to_type(kwargs['type'])
            
        return instance

    return get_instance

# 使用装饰器
# @singleton
class FilterResultDataManger():
    def __init__(self, type=0):
        self.type_count = 12
        if type > self.type_count:
            raise ValueError("Invalid type")

        self.type = type
        self.filter_result_db_manager = FilterResultDBBase(type)
        self.logger = get_logger(__name__)

    def switch_to_type(self, type):
        """切换到指定类型"""
        if type > self.type_count:
            raise ValueError("Invalid type")
        
        if self.type != type:
            self.type = type
            self.filter_result_db_manager = FilterResultDBBase(type)

    def get_old_filter_result_dir(self):
        if self.type == 0:
            return "./data/database/policy_filter/filter_result/old/daily_up_ma52"
        elif self.type == 1:
            return "./data/database/policy_filter/filter_result/old/daily_up_ma24"
        elif self.type == 2:
            return "./data/database/policy_filter/filter_result/old/daily_up_ma10"
        elif self.type == 3:
            return "./data/database/policy_filter/filter_result/old/daily_up_ma5"
        elif self.type == 4:
            return "./data/database/policy_filter/filter_result/old/daily_down_ma52"
        elif self.type == 5:
            return "./data/database/policy_filter/filter_result/old/daily_down_ma5"
        elif self.type == 6:
            return "./data/database/policy_filter/filter_result/old/daily_down_breakthrough_ma52_filter"
        elif self.type == 7:
            return "./data/database/policy_filter/filter_result/old/daily_down_breakthrough_ma24_filter"
        elif self.type == 8:
            return "./data/database/policy_filter/filter_result/old/daily_down_double_bottom_filter"
        elif self.type == 9:
            return "./data/database/policy_filter/filter_result/old/daily_down_double_bottom_filter/背离"
        elif self.type == 10:
            return "./data/database/policy_filter/filter_result/old/daily_down_double_bottom_filter/动能不足"
        elif self.type == 11:
            return "./data/database/policy_filter/filter_result/old/daily_down_double_bottom_filter/隐形背离"
        elif self.type == 12:
            return "./data/database/policy_filter/filter_result/old/daily_down_double_bottom_filter/隐形动能不足"
        else:
            return "./data/database/policy_filter/filter_result/old/daily_up_ma52"
        
    def get_new_filter_result_dir(self):
        if self.type == 0:
            return "./data/database/policy_filter/filter_result/zero_up_ma52"
        elif self.type == 1:
            return "./data/database/policy_filter/filter_result/zero_up_ma24"
        elif self.type == 2:
            return "./data/database/policy_filter/filter_result/zero_up_ma10"
        elif self.type == 3:
            return "./data/database/policy_filter/filter_result/zero_up_ma5"
        elif self.type == 4:
            return "./data/database/policy_filter/filter_result/zero_down_ma52"
        elif self.type == 5:
            return "./data/database/policy_filter/filter_result/zero_down_ma5"
        elif self.type == 6:
            return "./data/database/policy_filter/filter_result/zero_down_breakthrough_ma52"
        elif self.type == 7:
            return "./data/database/policy_filter/filter_result/zero_down_breakthrough_ma24"
        elif self.type == 8:
            return "./data/database/policy_filter/filter_result/zero_down_double_bottom"
        elif self.type == 9:
            return "./data/database/policy_filter/filter_result/zero_down_double_bottom/背离"
        elif self.type == 10:
            return "./data/database/policy_filter/filter_result/zero_down_double_bottom/动能不足"
        elif self.type == 11:
            return "./data/database/policy_filter/filter_result/zero_down_double_bottom/隐形背离"
        elif self.type == 12:
            return "./data/database/policy_filter/filter_result/zero_down_double_bottom/隐形动能不足"
        else:
            return "./data/database/policy_filter/filter_result/zero_up_ma52"
        
    def get_relative_path(self, level='1d'):
        """
        获取相对路径
        
        :param level: 数据级别，默认为'1d'，可选值为'1d'或'5m'
        :return: 相对路径字符串
        """
        return f"txt/{level}"
    
    def get_txt_context_header(self):
        if self.type == 0:
            return "零轴上方MA52筛选结果"
        elif self.type == 1:
            return "零轴上方MA24筛选结果"
        elif self.type == 2:
            return "零轴上方MA10筛选结果"
        elif self.type == 3:
            return "零轴上方MA5筛选结果"
        elif self.type == 4:
            return "零轴下方MA52筛选结果"
        elif self.type == 5:
            return "零轴下方MA5筛选结果"
        elif self.type == 6:
            return "零轴下方MA52突破筛选结果"
        elif self.type == 7:
            return "零轴下方MA24突破筛选结果"
        elif self.type == 8:
            return "零轴下方双底筛选结果："
        elif self.type == 9:
            return "零轴下方双底【背离】筛选结果"
        elif self.type == 10:
            return "零轴下方双底【动能不足】筛选结果"
        elif self.type == 11:
            return "零轴下方双底【隐形背离】筛选结果"
        elif self.type == 12:
            return "零轴下方双底【隐形动能不足】筛选结果"
        else:
            return "筛选结果"

        
    def save_result_list_to_txt(self, data_list, file_name, separator='\n', level='1d', str_header=None, encoding='utf-8'):
        """
        将列表数据保存为txt文件
        
        :param data_list: 要保存的列表数据
        :param file_path: 保存文件的路径（包含文件名）
        :param encoding: 文件编码，默认为'utf-8'
        :param separator: 列表元素之间的分隔符，默认为换行符
        :return: 保存成功返回True，失败返回False
        """
        # 拼接save_dir
        relative_path = os.path.join(self.get_relative_path(level), file_name)
        
        file_path = os.path.join(self.get_new_filter_result_dir(), relative_path)

        # 参数验证
        if data_list is None:
            raise ValueError("数据不能为空")
        
        if not isinstance(data_list, list):
            raise ValueError("数据必须是列表类型")
        
        if not file_path:
            raise ValueError("文件路径不能为空")
        
        try:
            # 确保文件路径的目录存在
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            # 将列表数据转换为字符串
            if separator == '\n':
                # 如果分隔符是换行符，直接将每个元素转换为字符串并写入
                content = separator.join(str(item) for item in data_list)
            else:
                # 如果是其他分隔符，同样处理
                content = separator.join(str(item) for item in data_list)
            
            # 写入文件
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(str_header)
                f.write(content)
            
            self.logger.info(f"列表数据已成功保存到: {file_path}")
            return True
            
        except Exception as e:
            self.logger.info(f"保存列表数据到 {file_path} 时发生错误: {str(e)}")
            return False
        
    def save_filter_result_from_db_to_txt(self, date=None, level='1d'):
        allowed_levels = ['1d', '1w', '1m', '5m', '15m', '30m', '60m', '120m']
        if level not in allowed_levels:
            self.logger.info(f"Invalid level: {level}")
            return

        df_result = self.get_filter_result_with_params(date, level)

        if df_result is None or df_result.empty:
            self.logger.info(f"未查询到数据库中有{date}的{level}级别数据")
            return

        self.logger.info(f"{date}, 级别{level} 读取结果: \n{df_result.tail(3)}")

        dict_file_name = {}
        for index, row in df_result.iterrows():
            s_date = row['date']
            code = row['code']
            turnover_rate_limit = row['turnover_rate_limit']
            volume_ratio_limit = row['volume_ratio_limit']
            weekly_condition = row['weekly_condition']
            target_date = row['target_date']
            target_code = row['target_code']
            less_than_ma5 = row['less_than_ma5']

            file_name = f"{s_date}_{turnover_rate_limit}_{volume_ratio_limit}_{weekly_condition}_{target_date}_{target_code}_{less_than_ma5}.txt"

            if index == 0:
                self.logger.info(f"生成的file_name: {file_name}")

            if file_name not in dict_file_name.keys():
                list_code = []
                list_code.append(code)
                dict_file_name[file_name] = list_code
            else:
                dict_file_name[file_name].append(code)

        tatol_save_count = 0
        for key, value in dict_file_name.items():
            # key: file_name
            # value: list_code
            current_list_len = len(value)
            tatol_save_count += current_list_len
            self.save_result_list_to_txt(value, key, ',', level, f"{self.get_txt_context_header()}, 共{current_list_len}只股票：\n")

        self.logger.info(f"保存{date}，{level} 级别筛选结果成功，共保存了{tatol_save_count}只股票")
        
    def save_old_filter_result_to_db(self):
        dir = self.get_old_filter_result_dir()

        txt_files = []
    
        # 遍历目录中的所有文件
        for filename in os.listdir(dir):
            # 使用正则表达式检查是否以数字开头且以 .txt 结尾
            if re.match(r'^\d+.*\.txt$', filename):
                full_path = os.path.join(dir, filename)
                txt_files.append(full_path)
        
        for file_path in txt_files:
            self.logger.info(f"Processing file: {file_path}")

            # 获取不带路径的纯文件名
            filename = os.path.basename(file_path)
            
            # 去掉扩展名 ".txt"
            name_without_ext = os.path.splitext(filename)[0]
            
            # 使用 '_' 分割字段
            parts = name_without_ext.split('_')
            
            # 初始化默认值
            parsed_data = {
                'date': '',
                'turnover_rate_limit': 1.0,
                'volume_ratio_limit': 0.3,
                'weekly_condition': False,
                'target_date': '',
                'target_code': '',
                'less_than_ma5': False
            }
            
            # 根据实际分割的部分赋值
            # 文件名格式: date_turnoverRate_volumeRatio_weeklyCondition_targetDate_targetCode_lessThanMa5
            if len(parts) >= 1 and parts[0]:  # date
                short_date = parts[0]
                if len(short_date) == 4 and short_date.isdigit():
                    # 获取文件的最后修改时间
                    file_mtime = os.path.getmtime(file_path)
                    file_year = datetime.fromtimestamp(file_mtime).year
                    
                    # 组合成完整日期格式
                    month_day = short_date[:2] + '-' + short_date[2:]
                    parsed_data['date'] = f"{file_year}-{month_day}"
                else:
                    # 如果不是4位数字格式，保持原样
                    parsed_data['date'] = short_date

            if len(parts) >= 2 and parts[1]:  # turnover_rate_limit
                try:
                    parsed_data['turnover_rate_limit'] = float(parts[1])
                except ValueError:
                    pass  # 保留默认值 1.0

            if len(parts) >= 3 and parts[2]:  # volume_ratio_limit
                try:
                    parsed_data['volume_ratio_limit'] = float(parts[2])
                except ValueError:
                    pass  # 保留默认值 0.3

            if len(parts) >= 4 and parts[3]:  # weekly_condition
                if parts[3].lower() in ['true', 'false']:
                    parsed_data['weekly_condition'] = parts[3].lower() == 'true'
                # 非法值保留默认值 False

            if len(parts) >= 5 and parts[4]:  # target_date
                parsed_data['target_date'] = parts[4]

            if len(parts) >= 6 and parts[5]:  # target_code
                parsed_data['target_code'] = parts[5]

            if len(parts) >= 7 and parts[6]:  # less_than_ma5
                if parts[6].lower() in ['true', 'false']:
                    parsed_data['less_than_ma5'] = parts[6].lower() == 'true'
                # 非法值保留默认值 False
            
            # self.logger.info.info(parsed_data)
            

            self.save_filter_result_from_file_to_db(file_path, parsed_data)

    def _generate_filter_params(self, parsed_data):
        """生成筛选参数的标准化JSON字符串"""
        filter_params = {
            'turnover_rate_limit': parsed_data.get('turnover_rate_limit', 1.0),
            'volume_ratio_limit': parsed_data.get('volume_ratio_limit', 0.3),
            'weekly_condition': parsed_data.get('weekly_condition', False),
            'target_date': parsed_data.get('target_date', ''),
            'target_code': parsed_data.get('target_code', ''),
            'less_than_ma5': parsed_data.get('less_than_ma5', False)
            # 后续可添加新的筛选条件
            # 'less_than_ma10': parsed_data.get('less_than_ma10', False),
            # 'price_upper_limit': parsed_data.get('price_upper_limit', 0.0),
            # 'min_market_value': parsed_data.get('min_market_value', 0.0)
        }
        
        # 按键排序以确保一致性
        params_str = json.dumps(filter_params, sort_keys=True, separators=(',', ':'))
        return params_str

    def save_filter_result_from_file_to_db(self, file_path, parsed_data):
        # --- 新增：读取文件内容并提取股票代码 ---
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 使用正则表达式提取股票代码（sh.或sz.开头的代码）
            # 修复正则表达式，捕获完整代码
            stock_codes = re.findall(r'(sh\.\d{6}|sz\.\d{6})', content)
            
            # 去重并排序
            stock_codes = sorted(list(set(stock_codes)))
            
            # 添加到parsed_data中
            parsed_data['code'] = stock_codes
            
            self.logger.info(f"Extracted {len(stock_codes)} stock codes: {stock_codes}")
            
            # 将解析的数据转换为DataFrame格式以便写入数据库
            data_records = []

            # 为每个股票代码创建一条记录
            for stock_code in parsed_data['code']:
                # 生成筛选参数JSON
                filter_params_json = self._generate_filter_params(parsed_data)
                
                record = {
                    'date': parsed_data['date'],
                    'code': stock_code,
                    'filter_params': filter_params_json
                }
                data_records.append(record)

            # 转换为DataFrame
            if data_records:
                df_to_save = pd.DataFrame(data_records)
                
                # 写入数据库（使用1d级别作为默认）
                success = self.filter_result_db_manager.save_filter_result_to_db(df_to_save, level='1d')
                
                if success:
                    self.logger.info(f"Successfully saved {len(data_records)} records to database")
                else:
                    self.logger.info("Failed to save records to database")
            else:
                self.logger.info("No stock codes extracted, skipping database save")
            
        except Exception as e:
            self.logger.info(f"Error reading file {file_path}: {e}")

    def save_filter_result_to_db(self, df_to_save, level='1d'):
        if df_to_save is None or df_to_save.empty:
            self.logger.info.info("No valid records to save")
            return False
        
        try:
            success = self.filter_result_db_manager.save_filter_result_to_db(df_to_save, level=level)
            
            if success:
                self.logger.info(f"Successfully saved {len(df_to_save)} records to database")
            else:
                self.logger.info("Failed to save records to database")

            return success
        except Exception as e:
            self.logger.info(f"保存筛选结果出错: {e}")

        return False


    def query_filter_result(self, date=None, level='1d', code=None):
        """
        查询筛选结果
        
        Args:
            date (str, optional): 日期，格式为 'YYYY-MM-DD'
            level (str): 时间级别，默认为 '1d'
            code (str, optional): 股票代码，支持模糊查询
            
        Returns:
            pd.DataFrame: 查询结果
        """
        return self.filter_result_db_manager.query_filter_result(date=date, level=level, code=code)
    
    def get_latest_filter_result(self, level='1d'):
        """
        获取最新日期的筛选结果
        
        Args:
            level (str): 时间级别，默认为 '1d'
            
        Returns:
            pd.DataFrame: 最新筛选结果
        """
        return self.filter_result_db_manager.get_latest_filter_result(level=level)


    def parse_filter_params(self, filter_params_json):
        """
        解析筛选参数JSON字符串为字典
        
        Args:
            filter_params_json (str): 筛选参数的JSON字符串
            
        Returns:
            dict: 筛选参数字典
        """
        try:
            return json.loads(filter_params_json)
        except json.JSONDecodeError:
            return {}
    
    def get_filter_result_with_params(self, date=None, level='1d', code=None):
        """
        获取筛选结果并解析筛选参数
        
        Args:
            date (str, optional): 日期，格式为 'YYYY-MM-DD'
            level (str): 时间级别，默认为 '1d'
            code (str, optional): 股票代码，支持模糊查询
            
        Returns:
            pd.DataFrame: 包含解析后筛选参数的查询结果
        """
        # 查询原始数据
        df = self.query_filter_result(date=date, level=level, code=code)
        
        if df.empty:
            return df
        
        # 解析筛选参数
        parsed_params = []
        for _, row in df.iterrows():
            params = self.parse_filter_params(row['filter_params'])
            parsed_params.append(params)
        
        # 将解析后的参数转换为DataFrame并与原数据合并
        params_df = pd.DataFrame(parsed_params)
        result_df = pd.concat([df.drop(columns=['filter_params']), params_df], axis=1)
        
        return result_df
    
    def get_lastest_filter_result_date(self, level='1d'):
        df = self.get_latest_filter_result(level=level)
        if df is None or df.empty:
            return None
        return df['date'].iloc[0]
    
    def get_lastest_filter_result_with_params(self, level='1d'):
        date = self.get_lastest_filter_result_date(level=level)
        return self.get_filter_result_with_params(date=date, level=level)