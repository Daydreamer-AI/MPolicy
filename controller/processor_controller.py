from processor.stock_data_processor import StockDataProcessor
from processor.baostock_processor import BaoStockProcessor

class ProcessorController:
    def __init__(self):
        self.stock_processor = StockDataProcessor()
        self.bao_stock_processor = BaoStockProcessor()

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