from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QFile

from processor.baostock_processor import BaoStockProcessor

from manager.logging_manager import get_logger

from gui.qt_widgets.strategy.strategy_wait_widget import StrategyWaitWidget
from gui.qt_widgets.strategy.strategy_widget import StrategyWidget

class StrategyHomeWidget(QWidget):
    def __init__(self, parent=None):
        super(StrategyHomeWidget, self).__init__(parent)
        self.ui = uic.loadUi("./src/gui/qt_widgets/strategy/StrategyHomeWidget.ui", self)

        self.init_para()
        self.init_ui()
        self.init_connect()

    def init_para(self):
        self.logger = get_logger(__name__)

    def init_ui(self):
        self.strategy_wait_widget = StrategyWaitWidget()
        self.strategy_widget = StrategyWidget()

        self.stackedWidget.addWidget(self.strategy_wait_widget)
        self.stackedWidget.addWidget(self.strategy_widget)

        self.stackedWidget.setCurrentWidget(self.strategy_wait_widget)

        self.load_qss()

    def init_connect(self):
        BaoStockProcessor().sig_stock_data_load_finished.connect(self.slot_bao_stock_data_load_finished)
        # BaoStockProcessor().sig_stock_data_load_progress.connect(self.slot_bao_stock_data_load_progress)
        # BaoStockProcessor().sig_stock_data_load_error.connect(self.slot_bao_stock_data_load_error)

    def load_qss(self, theme="default"):
        qss_file_name = f":/theme/{theme}/strategy/strategy.qss"
        qssFile = QFile(qss_file_name)
        if qssFile.open(QFile.ReadOnly):
            self.setStyleSheet(str(qssFile.readAll(), encoding='utf-8'))
        else:
            self.logger.warning("无法打开策略模块样式表文件")
        qssFile.close()

    def slot_bao_stock_data_load_finished(self, succsess):
        self.logger.info(f"Baostock股票数据加载完成，结果为：{succsess}")
        if succsess:
            self.strategy_widget.show_default_strategy()
            self.stackedWidget.setCurrentWidget(self.strategy_widget)