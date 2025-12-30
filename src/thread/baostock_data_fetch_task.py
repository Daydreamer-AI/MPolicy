from processor.baostock_processor import BaoStockProcessor
from thread.base_task import BaseTask

import random
import time

class BaostockDataFetchTask(BaseTask):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def execute(self):
        # BaoStockProcessor().process_sh_main_stock_data()

        # sleep_time = random.uniform(0.3, 0.5)
        # time.sleep(sleep_time)

        # BaoStockProcessor().process_sz_main_stock_data()

        board_types = ['sh_main', 'sz_main']
        levels = ['15', '30', '60']
        for board_type in board_types:

            sleep_time = random.uniform(0.3, 0.5)
            time.sleep(sleep_time)

            for level in levels:
                BaoStockProcessor().process_minute_level_stock_data_with_board_type(board_type, level)

        # 校验更新结果