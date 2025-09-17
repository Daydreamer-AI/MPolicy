from processor.stock_data_processor import StockDataProcessor
from processor.baostock_processor import BaoStockProcessor
from common.config_manager import ConfigManager

class ProcessorController:
    _instance = None
    # def __init__(self):
        # self.stock_processor = StockDataProcessor()
        # self.bao_stock_processor = BaoStockProcessor()

        # ConfigManager接口测试
        # config_manager = ConfigManager()
        # config_manager.set_config_path("./resources/config/config.ini")
        # policy_filter_turn_config = config_manager.getint('PolicyFilter', 'turn', 1)
        # policy_filter_lb_config = config_manager.getint('PolicyFilter', 'lb', 1)
        # print("turn 的类型: ", type(policy_filter_turn_config))
        # print("lb 的类型: ", type(policy_filter_lb_config))
        # print(f"Config from config.ini: {policy_filter_turn_config}, {policy_filter_lb_config}")

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # 初始化成员变量
            cls._instance.stock_processor = StockDataProcessor()
            cls._instance.bao_stock_processor = BaoStockProcessor() # 创建实例
            cls._instance._is_initialized = False # 控制器自身状态
        return cls._instance

    def initialize_all(self) -> bool:
        """初始化所有处理器。"""
        try:
            if self.bao_stock_processor.initialize():
                self._is_initialized = True
                return True
            return False
        except Exception as e:
            # logging.exception("Failed to initialize all processors.")
            return False

    def cleanup_all(self) -> None:
        """清理所有处理器占用的资源。"""
        if self._is_initialized:
            try:
                self.bao_stock_processor.cleanup() # 调用成员的清理方法
            finally:
                self._is_initialized = False

    def test(self):
        print("ProcessorController test")

    # 全量获取
    def process_sh_main_stock_data(self):
        print("process_sh_main_stock_data")
        self.bao_stock_processor.process_sh_main_stock_daily_data()
        self.bao_stock_processor.process_sh_main_stock_weekly_data()

        # 接口测试
        # friday_count = self.bao_stock_processor.count_fridays_since("2025-08-30")
        # print("周五个数：", friday_count)

    def process_sz_main_stock_data(self):
        print("process_sz_main_stock_data")
        self.bao_stock_processor.process_sz_main_stock_daily_data()
        self.bao_stock_processor.process_sz_main_stock_weekly_data()

    def process_gem_stock_data(self):
        print("process_gem_stock_data")
        self.bao_stock_processor.process_gem_stock_daily_data()
        self.bao_stock_processor.process_gem_stock_weekly_data()

    def process_star_stock_data(self):
        print("process_star_stock_data")
        self.bao_stock_processor.process_star_stock_daily_data()
        self.bao_stock_processor.process_star_stock_weekly_data()

    # 增量更新
    def update_sh_main_daily_data(self):
        print("update_sh_main_daily_data")
        self.bao_stock_processor.update_sh_main_daily_data()

    # 策略筛选
    

    def process_daily_up_ma52_filter(self):
        print("process_daily_up_ma52_filter")
        result = self.bao_stock_processor.daily_up_ma52_filter()
        print("process_daily_up_ma52_filter done.")
        print(result)

    def process_daily_up_ma24_filter(self):
        print("process_daily_up_ma24_filter")
        result = self.bao_stock_processor.daily_up_ma24_filter()
        print("process_daily_up_ma24_filter done.")
        print(result)

    def process_daily_up_ma10_filter(self):
        print("process_daily_up_ma10_filter")
        result = self.bao_stock_processor.daily_up_ma10_filter()
        print("process_daily_up_ma10_filter done.")
        print(result)

    def process_daily_down_between_ma24_ma52_filter(self):
        print("process_daily_down_between_ma24_ma52_filter")
        result = self.bao_stock_processor.daily_down_between_ma24_ma52_filter()
        print("process_daily_down_between_ma24_ma52_filter done.")
        print(result)

    def process_daily_down_between_ma5_ma52_filter(self):
        print("process_daily_down_between_ma5_ma52_filter")
        result = self.bao_stock_processor.daily_down_between_ma5_ma52_filter()
        print("process_daily_down_between_ma5_ma52_filter done.")
        print(result)

    def stop_process(self):
        print("stop_process")
        self.bao_stock_processor.stop_process()
    

processor_controller_instance = ProcessorController()