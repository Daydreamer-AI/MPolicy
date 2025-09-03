from processor.stock_data_processor import StockDataProcessor
from processor.baostock_processor import BaoStockProcessor

class ProcessorController:
    def __init__(self):
        self.stock_processor = StockDataProcessor()
        self.bao_stock_processor = BaoStockProcessor()

    def test(self):
        print("ProcessorController test")

    def process_gem_stock_data(self):
        print("process_gem_stock_data")
        self.bao_stock_processor.process_gem_stock_daily_data()
        self.bao_stock_processor.process_gem_stock_weekly_data()

processor_controller_instance = ProcessorController()