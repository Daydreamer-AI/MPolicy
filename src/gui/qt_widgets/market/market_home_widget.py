from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout
from PyQt5.QtCore import pyqtSlot, QFile

from manager.logging_manager import get_logger

from gui.qt_widgets.market.market_wait_widget import MarketWaitWidget
from gui.qt_widgets.market.market_widget import MarketWidget
from processor.baostock_processor import BaoStockProcessor

class MarketHomeWidget(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent) 

        uic.loadUi('./src/gui/qt_widgets/market/MarketHomeWidget.ui', self)

        self.init_para()
        self.init_ui()
        self.init_connect()

    def init_para(self):
        self.logger = get_logger(__name__)

    def init_ui(self):
        self.market_wait_widget = MarketWaitWidget(self)
        self.market_widget = MarketWidget(self)

        self.stackedWidget.addWidget(self.market_wait_widget)
        self.stackedWidget.addWidget(self.market_widget)
        self.stackedWidget.setCurrentWidget(self.market_wait_widget)

        self.load_qss()

    def init_connect(self):
        BaoStockProcessor().sig_stock_data_load_finished.connect(self.slot_bao_stock_data_load_finished)
        BaoStockProcessor().sig_stock_data_load_progress.connect(self.slot_bao_stock_data_load_progress)
        BaoStockProcessor().sig_stock_data_load_error.connect(self.slot_bao_stock_data_load_error)

    def load_qss(self, theme="default"):
        qss_file_name = f":/theme/{theme}/market/market.qss"
        qssFile = QFile(qss_file_name)
        if qssFile.open(QFile.ReadOnly):
            self.setStyleSheet(str(qssFile.readAll(), encoding='utf-8'))
        else:
            self.logger.warning("无法打开行情模块样式表文件")
        qssFile.close()

        # 测试：
        # qss = '''
        #     #MarketHomeWidget #MarketWidget #StockCardWidget {border-bottom: 1px solid #000000;}
        #     #MarketHomeWidget #MarketWidget #StockCardWidget #label_stock_name {font-size: 20px;}
        #     #MarketHomeWidget #MarketWidget #StockCardWidget #label_stock_code {font-size: 18px; }
        #     #MarketHomeWidget #MarketWidget #StockCardWidget #label_price[change_status="up"] {font-size: 20px; font-weight: bold; color: rgb(255, 0, 0);}
        #     #MarketHomeWidget #MarketWidget #StockCardWidget #label_price[change_status="down"] {font-size: 20px; font-weight: bold; color: rgb(21, 130, 42);}
        #     #MarketHomeWidget #MarketWidget #StockCardWidget #label_price[change_status="flat"] {font-size: 20px; font-weight: bold; color: rgb(0, 0, 0);}
        #     #MarketHomeWidget #MarketWidget #StockCardWidget #label_change_percent[change_status="up"] {font-size: 18px; color: rgb(255, 0, 0);}
        #     #MarketHomeWidget #MarketWidget #StockCardWidget #label_change_percent[change_status="down"] {font-size: 18px; color: rgb(21, 130, 42);}
        #     #MarketHomeWidget #MarketWidget #StockCardWidget #label_change_percent[change_status="flat"] {font-size: 18px; color: rgb(0, 0, 0);}
        # '''
        # self.setStyleSheet(qss)

    def slot_bao_stock_data_load_finished(self, succsess):
        self.logger.info(f"Baostock股票数据加载完成，结果为：{succsess}")
        if succsess:
            self.market_widget.slot_bao_stock_data_load_finished(succsess)
            self.stackedWidget.setCurrentWidget(self.market_widget)
    def slot_bao_stock_data_load_progress(self, progress):
        self.logger.info(f"Baostock股票数据加载进度：{progress}")
        
    def slot_bao_stock_data_load_error(self, error):
        self.logger.error(f"Baostock股票数据加载出错：{error}")


    def showEvent(self, event):
        """
        重写showEvent方法，在窗口显示时执行初始化操作
        """
        super().showEvent(event)

        # if self.stackedWidget.currentWidget() == self.market_widget:
            # self.logger.info("MarketHomeWidget显示，更新股票数据")
            # self.market_widget.slot_bao_stock_data_load_finished(True)

        
        # 检查当前是否处于等待状态，如果是则启动数据加载
        # if self.stackedWidget.currentWidget() == self.market_wait_widget:
        #     self.logger.info("MarketHomeWidget显示，开始检查数据加载状态")
            
        #     # 检查BaoStockProcessor是否已经加载完数据
        #     bao_stock_processor = BaoStockProcessor()
            
        #     # 这里可以根据实际需要添加数据加载检查逻辑
        #     # 例如检查数据是否已经准备好
        #     try:
        #         # 如果数据尚未加载，则启动后台加载
        #         if not hasattr(bao_stock_processor, '_data_loaded') or not bao_stock_processor._data_loaded:
        #             self.logger.info("开始启动Baostock数据后台加载")
        #             bao_stock_processor.start_background_loading()
        #         else:
        #             # 如果数据已经加载完成，直接切换到市场界面
        #             self.logger.info("Baostock数据已准备就绪，直接显示市场界面")
        #             self.stackedWidget.setCurrentWidget(self.market_widget)
        #     except Exception as e:
        #         self.logger.error(f"检查数据加载状态时发生异常: {e}")