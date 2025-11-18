from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout
from PyQt5.QtCore import pyqtSlot
# from controller.processor_controller import processor_controller_instance
from gui.qt_widgets.setting.policy_filter_setting_dialog import PolicyFilterSettingDialog
from processor.baostock_processor import BaoStockProcessor
from processor.ak_stock_data_processor import AKStockDataProcessor
from common.common_api import *
import datetime
from common.logging_manager import get_logger

class MarketWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.init_para()
        self.init_ui()
        self.init_connect()

    def init_para(self):
        self.logger = get_logger(__name__)

    def init_ui(self):
        uic.loadUi('./gui/qt_widgets/market/MarketWidget.ui', self)

    def init_connect(self):
        pass