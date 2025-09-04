from processor.stock_data_processor import StockDataProcessor
from processor.baostock_processor import BaoStockProcessor

class ProcessorController:
    def __init__(self):
        self.stock_processor = StockDataProcessor()
        self.bao_stock_processor = BaoStockProcessor()

    def test(self):
        print("ProcessorController test")

    def process_sh_main_stock_data(self):
        print("process_sh_main_stock_data")
        self.bao_stock_processor.process_sh_main_stock_daily_data()
        self.bao_stock_processor.process_sh_main_stock_weekly_data()

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

    # 策略筛选
    def process_ma52_filter(self):
        print("process_ma52_filter")
        result = self.bao_stock_processor.daily_and_weekly_ma52_filter()
        print("process_ma52_filter done.")
        print(result)

    def process_ma24_filter(self):
        print("process_ma24_filter")
        result = self.bao_stock_processor.daily_ma24_filter()
        print("process_ma24_filter done.")
        print(result)

    def process_ma10_filter(self):
        print("process_ma10_filter")
        result = self.bao_stock_processor.daily_ma10_filter()
        print("process_ma10_filter done.")
        print(result)

    def process_ma20_filter(self):
        print("process_ma20_filter")
        result = self.bao_stock_processor.daily_ma20_filter()
        print("process_ma20_filter done.")
        print(result)

    def process_ma52_ma24_filter(self):
        print("process_ma52_ma24_filter")
        result = self.bao_stock_processor.daily_ma52_ma24_filter()
        print("process_ma52_ma24_filter done.")
        print(result)
    

processor_controller_instance = ProcessorController()