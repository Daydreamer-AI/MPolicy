from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtWidgets import QDialog, QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import pyqtSlot

from manager.logging_manager import get_logger
# from gui.qt_widgets.MComponents.indicators.indicators_view_widget import IndicatorsViewWidget

from processor.baostock_processor import BaoStockProcessor
from manager.bao_stock_data_manager import BaostockDataManager

class ReviewDialog(QDialog):
    def __init__(self, parent=None):
        super(ReviewDialog, self).__init__(parent) 
        uic.loadUi('./src/gui/qt_widgets/review/ReviewDialog.ui', self)

        self.init_para()
        self.init_ui()
        self.init_connect()

        self.load_data_test()

    def init_para(self):
        self.logger = get_logger(__name__)

    def init_ui(self):
        from gui.qt_widgets.MComponents.indicators.indicators_view_widget import IndicatorsViewWidget
        self.indicators_view_widget = IndicatorsViewWidget(self)
        self.indicators_view_widget.show_review_btn(False)
        main_h_layout = self.layout()
        if main_h_layout is None:
            self.setLayout(QHBoxLayout())
            main_h_layout = self.layout()

        main_h_layout.addWidget(self.indicators_view_widget)


    def init_connect(self):
        pass

    def load_data_test(self):
        filter_result = ['sh.600000']
        bao_stock_data_manager = BaostockDataManager()
        new_dict_lastest_1d_stock_data = bao_stock_data_manager.get_lastest_row_data_dict_by_code_list_auto(filter_result)
        self.logger.info(f"new_dict_lastest_1d_stock_data: {new_dict_lastest_1d_stock_data}")

        if new_dict_lastest_1d_stock_data:
            self.indicators_view_widget.update_stock_data_dict('sh.600000')
            data = new_dict_lastest_1d_stock_data['sh.600000'].iloc[-1]
            self.indicators_view_widget.update_chart(data)
        else:
            self.logger.info(f"结果为空")


