# file: d:\PythonProject\MPolicy\common\common_api.py

import pandas as pd
import re

class StockCodeAnalyzer:
    """
    股票代码分析器，用于识别股票代码所属的板块
    """
    
    # 板块代码规则定义
    BOARD_RULES = {
        'sh_main': {  # 上海主板
            'patterns': [
                r'^sh\.60[0-5]\d{3}$',  # sh.600xxx, sh.601xxx, sh.602xxx, sh.603xxx
                r'^SH\.60[0-5]\d{3}$',  # SH.600xxx, SH.601xxx, SH.602xxx, SH.603xxx
                r'^60[0-5]\d{3}$',      # 600xxx, 601xxx, 602xxx, 603xxx
            ],
            'prefixes': ['sh.60', 'SH.60', '600', '601', '602', '603', '605']
        },
        'sz_main': {  # 深圳主板
            'patterns': [
                r'^sz\.00[0-3]\d{3}$',  # sz.000xxx, sz.001xxx
                r'^SZ\.00[0-3]\d{3}$',  # SZ.000xxx, SZ.001xxx
                r'^00[0-3]\d{3}$',      # 000xxx, 001xxx
            ],
            'prefixes': ['sz.00', 'SZ.00', '000', '001', '002', '003']
        },
        'gem': {  # 创业板
            'patterns': [
                r'^sz\.30[0-1]\d{3}$',  # sz.300xxx, sz.301xxx
                r'^SZ\.30[0-1]\d{3}$',  # SZ.300xxx, SZ.301xxx
                r'^30[0-1]\d{3}$',      # 300xxx, 301xxx
            ],
            'prefixes': ['sz.30', 'SZ.30', '300', '301']
        },
        'star': {  # 科创板
            'patterns': [
                r'^sh\.68[8-9]\d{3}$',  # sh.688xxx, sh.689xxx
                r'^SH\.68[8-9]\d{3}$',  # SH.688xxx, SH.689xxx
                r'^68[8-9]\d{3}$',      # 688xxx, 689xxx
            ],
            'prefixes': ['sh.68', 'SH.68', '688', '689']
        },
        'bse': {  # 北交所
            'patterns': [
                r'^bj\.[0-9]{6}$',      # bj.xxxxxx
                r'^BJ\.[0-9]{6}$',      # BJ.xxxxxx
                r'^83[0-9]{4}$',          # xxxxxx (6位数字，需要额外判断)
                r'^87[0-9]{4}$', 
                r'^92[0-9]{4}$', 
            ],
            'prefixes': ['bj.', 'BJ.', '83', '87', '92']
        }
        ,
        'ohter': {  # 北交所
            'patterns': [
                r'^43[0-9]{4}$',          # xxxxxx (6位数字，需要额外判断)
            ],
            'prefixes': ['43']
        }
    }
    
    @classmethod
    def normalize_code(cls, code):
        """
        标准化股票代码格式
        
        :param code: 原始股票代码
        :return: 标准化后的股票代码
        """
        if not isinstance(code, str):
            code = str(code)
        
        # 转换为小写以便统一处理
        code_lower = code.lower()
        
        # 处理带市场前缀的代码
        if code_lower.startswith('sh.') or code_lower.startswith('sz.') or code_lower.startswith('bj.'):
            return code_lower
        
        # 处理不带市场前缀的6位数字代码
        if re.match(r'^\d{6}$', code):
            first_digit = code[0]
            if first_digit in ['6']:  # 上海市场
                return f'sh.{code}'
            elif first_digit in ['0', '3']:  # 深圳市场
                return f'sz.{code}'
            elif first_digit in ['4', '8']:  # 北交所
                return f'bj.{code}'
        
        return code
    
    @classmethod
    def identify_board(cls, code):
        """
        识别股票代码所属板块
        
        :param code: 股票代码字符串
        :return: 板块名称 ('sh_main', 'sz_main', 'gem', 'star', 'bse', 'unknown')
        """
        if not isinstance(code, str):
            code = str(code)
        
        # 遍历所有板块规则进行匹配
        for board, rules in cls.BOARD_RULES.items():
            for pattern in rules['patterns']:
                if re.match(pattern, code):
                    return board
        
        # 特殊处理：6位数字代码可能是北交所
        if re.match(r'^[48][0-9]{5}$', code):
            return 'bse'
        
        return 'unknown'
    
    @classmethod
    def is_sh_main(cls, code):
        """
        判断是否为上海主板股票
        
        :param code: 股票代码
        :return: True/False
        """
        return cls.identify_board(code) == 'sh_main'
    
    @classmethod
    def is_sz_main(cls, code):
        """
        判断是否为深圳主板股票
        
        :param code: 股票代码
        :return: True/False
        """
        return cls.identify_board(code) == 'sz_main'
    
    @classmethod
    def is_gem(cls, code):
        """
        判断是否为创业板股票
        
        :param code: 股票代码
        :return: True/False
        """
        return cls.identify_board(code) == 'gem'
    
    @classmethod
    def is_star(cls, code):
        """
        判断是否为科创板股票
        
        :param code: 股票代码
        :return: True/False
        """
        return cls.identify_board(code) == 'star'
    
    @classmethod
    def is_bse(cls, code):
        """
        判断是否为北交所股票
        
        :param code: 股票代码
        :return: True/False
        """
        return cls.identify_board(code) == 'bse'
    
    @classmethod
    def get_board_name(cls, code):
        """
        获取股票代码对应的板块中文名称
        
        :param code: 股票代码
        :return: 板块中文名称
        """
        board_map = {
            'sh_main': '上海主板',
            'sz_main': '深圳主板',
            'gem': '创业板',
            'star': '科创板',
            'bse': '北交所',
            'unknown': '未知板块'
        }
        
        board = cls.identify_board(code)
        return board_map.get(board, '未知板块')
    
    @classmethod
    def batch_identify_boards(cls, codes):
        """
        批量识别股票代码所属板块
        
        :param codes: 股票代码列表
        :return: 包含代码和对应板块的DataFrame
        """
        results = []
        for code in codes:
            board = cls.identify_board(code)
            board_name = cls.get_board_name(code)
            results.append({
                'code': code,
                'board': board,
                'board_name': board_name
            })
        
        return pd.DataFrame(results)
    
    @classmethod
    def classify_stocks_by_board(cls, stocks_df):
        """
        将A股所有股票数据按板块分类
        
        :param stocks_df: 包含所有股票数据的DataFrame，应包含股票代码列
        :return: dict对象，key为板块标识，value为对应板块的股票数据DataFrame
        """
        if stocks_df is None or stocks_df.empty:
            return {
                'sh_main': pd.DataFrame(),
                'sz_main': pd.DataFrame(),
                'gem': pd.DataFrame(),
                'star': pd.DataFrame(),
                'bse': pd.DataFrame()
            }
        
        # 确定股票代码列名（支持多种可能的列名）
        code_columns = ['证券代码', 'code', 'stock_code', '股票代码']
        code_column = None
        for col in code_columns:
            if col in stocks_df.columns:
                code_column = col
                break
        
        if code_column is None:
            # 如果找不到标准列名，尝试查找包含"代码"的列
            for col in stocks_df.columns:
                if '代码' in col or 'code' in col.lower():
                    code_column = col
                    break
        
        if code_column is None:
            raise ValueError("无法找到股票代码列，请确保DataFrame包含'证券代码'、'code'、'stock_code'或'股票代码'列")
        
        # 初始化各板块DataFrame
        classified_stocks = {
            'sh_main': pd.DataFrame(),
            'sz_main': pd.DataFrame(),
            'gem': pd.DataFrame(),
            'star': pd.DataFrame(),
            'bse': pd.DataFrame()
        }
        
        print("匹配的列名：", code_column)

        # 按板块分类股票
        for index, row in stocks_df.iterrows():
            code = row[code_column]
            board = cls.identify_board(code)
            
            if board in classified_stocks:
                # 使用pd.concat添加行到对应板块DataFrame
                classified_stocks[board] = pd.concat([
                    classified_stocks[board], 
                    row.to_frame().T
                ], ignore_index=True)
        
        return classified_stocks

    @classmethod
    def get_board_statistics(cls, stocks_df):
        """
        获取各板块股票数量统计
        
        :param stocks_df: 包含所有股票数据的DataFrame
        :return: 包含各板块股票数量的字典
        """
        classified_stocks = cls.classify_stocks_by_board(stocks_df)
        
        statistics = {}
        for board, df in classified_stocks.items():
            statistics[board] = len(df)
        
        return statistics

# 便捷函数
def identify_stock_board(code):
    """
    识别单个股票代码所属板块
    
    :param code: 股票代码
    :return: 板块名称
    """
    return StockCodeAnalyzer.identify_board(code)

def get_stock_board_name(code):
    """
    获取股票代码对应的板块中文名称
    
    :param code: 股票代码
    :return: 板块中文名称
    """
    return StockCodeAnalyzer.get_board_name(code)

def is_shanghai_main_board(code):
    """
    判断是否为上海主板股票
    
    :param code: 股票代码
    :return: True/False
    """
    return StockCodeAnalyzer.is_sh_main(code)

def is_shenzhen_main_board(code):
    """
    判断是否为深圳主板股票
    
    :param code: 股票代码
    :return: True/False
    """
    return StockCodeAnalyzer.is_sz_main(code)

def is_gem_board(code):
    """
    判断是否为创业板股票
    
    :param code: 股票代码
    :return: True/False
    """
    return StockCodeAnalyzer.is_gem(code)

def is_star_board(code):
    """
    判断是否为科创板股票
    
    :param code: 股票代码
    :return: True/False
    """
    return StockCodeAnalyzer.is_star(code)

def is_bse_board(code):
    """
    判断是否为北交所股票
    
    :param code: 股票代码
    :return: True/False
    """
    return StockCodeAnalyzer.is_bse(code)

def batch_identify_stock_boards(codes):
    """
    批量识别股票代码所属板块
    
    :param codes: 股票代码列表
    :return: 包含代码和对应板块的DataFrame
    """
    return StockCodeAnalyzer.batch_identify_boards(codes)

def classify_a_stocks_by_board(stocks_df):
    """
    将A股所有股票数据按板块分类
    
    :param stocks_df: 包含所有股票数据的DataFrame
    :return: dict对象，key为板块标识，value为对应板块的股票数据DataFrame
    """
    return StockCodeAnalyzer.classify_stocks_by_board(stocks_df)

def get_board_stock_statistics(stocks_df):
    """
    获取各板块股票数量统计
    
    :param stocks_df: 包含所有股票数据的DataFrame
    :return: 包含各板块股票数量的字典
    """
    return StockCodeAnalyzer.get_board_statistics(stocks_df)

def normalize_code_to_baostock_code(code):
    if is_shanghai_main_board(code) or is_star_board(code):
        return "sh." + code
    elif is_shenzhen_main_board(code) or is_gem_board(code):
        return "sz." + code
    elif is_bse_board(code):
        return "bj." + code
    else:
        return code
    

def save_dataframe_to_txt(df_data, file_path, sep='\t', encoding='utf-8', index=False, header=True):
    """
    将pandas.DataFrame数据保存为txt文件
    
    :param df_data: 要保存的pandas.DataFrame数据
    :param file_path: 保存文件的路径（包含文件名）
    :param sep: 分隔符，默认为制表符'\t'
    :param encoding: 文件编码，默认为'utf-8'
    :param index: 是否保存行索引，默认为False
    :param header: 是否保存列标题，默认为True
    :return: 保存成功返回True，失败返回False
    """
    # 参数验证
    if df_data is None:
        raise ValueError("数据不能为空")
    
    if not isinstance(df_data, pd.DataFrame):
        raise ValueError("数据必须是pandas.DataFrame类型")
    
    if not file_path:
        raise ValueError("文件路径不能为空")
    
    try:
        # 确保文件路径的目录存在
        import os
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        
        # 保存DataFrame到txt文件
        df_data.to_csv(file_path, sep=sep, encoding=encoding, index=index, header=header)
        print(f"数据已成功保存到: {file_path}")
        return True
        
    except Exception as e:
        print(f"保存数据到 {file_path} 时发生错误: {str(e)}")
        return False

def save_dataframe_to_csv(df_data, file_path, sep=',', encoding='utf-8', index=False, header=True):
    """
    将pandas.DataFrame数据保存为csv文件（逗号分隔）
    
    :param df_data: 要保存的pandas.DataFrame数据
    :param file_path: 保存文件的路径（包含文件名）
    :param sep: 分隔符，默认为逗号','
    :param encoding: 文件编码，默认为'utf-8'
    :param index: 是否保存行索引，默认为False
    :param header: 是否保存列标题，默认为True
    :return: 保存成功返回True，失败返回False
    """
    # 参数验证
    if df_data is None:
        raise ValueError("数据不能为空")
    
    if not isinstance(df_data, pd.DataFrame):
        raise ValueError("数据必须是pandas.DataFrame类型")
    
    if not file_path:
        raise ValueError("文件路径不能为空")
    
    try:
        # 确保文件路径的目录存在
        import os
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        
        # 保存DataFrame到csv文件
        df_data.to_csv(file_path, sep=sep, encoding=encoding, index=index, header=header)
        print(f"数据已成功保存到: {file_path}")
        return True
        
    except Exception as e:
        print(f"保存数据到 {file_path} 时发生错误: {str(e)}")
        return False

def save_classified_stocks_to_txt(classified_stocks_dict, base_path="./output/stocks"):
    """
    将按板块分类的股票数据保存为多个txt文件
    
    :param classified_stocks_dict: 按板块分类的股票数据字典
    :param base_path: 保存文件的基础路径
    :return: 保存成功返回True，失败返回False
    """
    # 参数验证
    if classified_stocks_dict is None:
        raise ValueError("分类股票数据不能为空")
    
    if not isinstance(classified_stocks_dict, dict):
        raise ValueError("分类股票数据必须是字典类型")
    
    try:
        import os
        # 确保基础路径存在
        os.makedirs(base_path, exist_ok=True)
        
        # 板块名称映射
        board_names = {
            'sh_main': '上海主板',
            'sz_main': '深圳主板',
            'gem': '创业板',
            'star': '科创板',
            'bse': '北交所'
        }
        
        # 保存各板块数据
        for board_key, df_data in classified_stocks_dict.items():
            if not df_data.empty:
                # 构造文件路径
                board_chinese_name = board_names.get(board_key, board_key)
                file_name = f"{board_chinese_name}_{board_key}.txt"
                file_path = os.path.join(base_path, file_name)
                
                # 保存数据
                success = save_dataframe_to_txt(df_data, file_path)
                if success:
                    print(f"{board_chinese_name}数据已保存到: {file_path}")
                else:
                    print(f"保存{board_chinese_name}数据失败")
            else:
                print(f"{board_names.get(board_key, board_key)}没有数据需要保存")
        
        return True
        
    except Exception as e:
        print(f"保存分类股票数据时发生错误: {str(e)}")
        return False
    

def save_list_to_txt(data_list, file_path, separator='\n', str_header=None, encoding='utf-8'):
    """
    将列表数据保存为txt文件
    
    :param data_list: 要保存的列表数据
    :param file_path: 保存文件的路径（包含文件名）
    :param encoding: 文件编码，默认为'utf-8'
    :param separator: 列表元素之间的分隔符，默认为换行符
    :return: 保存成功返回True，失败返回False
    """
    # 参数验证
    if data_list is None:
        raise ValueError("数据不能为空")
    
    if not isinstance(data_list, list):
        raise ValueError("数据必须是列表类型")
    
    if not file_path:
        raise ValueError("文件路径不能为空")
    
    try:
        # 确保文件路径的目录存在
        import os
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
        
        print(f"列表数据已成功保存到: {file_path}")
        return True
        
    except Exception as e:
        print(f"保存列表数据到 {file_path} 时发生错误: {str(e)}")
        return False

def save_stock_codes_to_txt(stock_codes, file_path, encoding='utf-8'):
    """
    专门用于保存股票代码列表到txt文件的接口
    
    :param stock_codes: 股票代码列表
    :param file_path: 保存文件的路径（包含文件名）
    :param encoding: 文件编码，默认为'utf-8'
    :return: 保存成功返回True，失败返回False
    """
    # 参数验证
    if stock_codes is None:
        raise ValueError("股票代码列表不能为空")
    
    if not isinstance(stock_codes, list):
        raise ValueError("股票代码必须是列表类型")
    
    if not file_path:
        raise ValueError("文件路径不能为空")
    
    try:
        # 确保文件路径的目录存在
        import os
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        
        # 写入股票代码，每个代码占一行
        with open(file_path, 'w', encoding=encoding) as f:
            for code in stock_codes:
                f.write(str(code) + '\n')
        
        print(f"股票代码列表已成功保存到: {file_path}")
        return True
        
    except Exception as e:
        print(f"保存股票代码列表到 {file_path} 时发生错误: {str(e)}")
        return False

def save_classified_stock_codes_to_txt(classified_stock_codes_dict, base_path="./output/stock_codes"):
    """
    将按板块分类的股票代码列表保存为多个txt文件
    
    :param classified_stock_codes_dict: 按板块分类的股票代码字典
    :param base_path: 保存文件的基础路径
    :return: 保存成功返回True，失败返回False
    """
    # 参数验证
    if classified_stock_codes_dict is None:
        raise ValueError("分类股票代码数据不能为空")
    
    if not isinstance(classified_stock_codes_dict, dict):
        raise ValueError("分类股票代码数据必须是字典类型")
    
    try:
        import os
        # 确保基础路径存在
        os.makedirs(base_path, exist_ok=True)
        
        # 板块名称映射
        board_names = {
            'sh_main': '上海主板',
            'sz_main': '深圳主板',
            'gem': '创业板',
            'star': '科创板',
            'bse': '北交所'
        }
        
        # 保存各板块股票代码
        for board_key, stock_codes in classified_stock_codes_dict.items():
            if stock_codes and isinstance(stock_codes, list) and len(stock_codes) > 0:
                # 构造文件路径
                board_chinese_name = board_names.get(board_key, board_key)
                file_name = f"{board_chinese_name}_{board_key}_codes.txt"
                file_path = os.path.join(base_path, file_name)
                
                # 保存数据
                success = save_stock_codes_to_txt(stock_codes, file_path)
                if success:
                    print(f"{board_chinese_name}股票代码已保存到: {file_path}")
                else:
                    print(f"保存{board_chinese_name}股票代码失败")
            else:
                print(f"{board_names.get(board_key, board_key)}没有股票代码需要保存")
        
        return True
        
    except Exception as e:
        print(f"保存分类股票代码时发生错误: {str(e)}")
        return False