from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout
from PyQt5.QtCore import pyqtSlot

import pyqtgraph as pg
import numpy as np
import pandas as pd

from common.logging_manager import get_logger

from gui.qt_widgets.market.base_indicator_widget import BaseIndicatorWidget
from gui.qt_widgets.MComponents.candlestick_item import CandlestickItem

class KLineWidget(BaseIndicatorWidget):
    def __init__(self, data, parent=None):
        # 调用父类初始化，这会自动调用init_para, init_ui, init_connect
        super(KLineWidget, self).__init__(data, parent)

    def init_para(self, data):
        # 检查是否有数据
        if data is None or data.empty:
            raise ValueError("数据为空，无法绘制k线图")
        
        # 确保数据列存在
        required_columns = ['open', 'high', 'low', 'close']
        if not all(col in data.columns for col in required_columns):
            self.logger.warning("缺少必要的数据列来绘制k线图")
            raise ValueError("缺少必要的数据列来绘制k线图")
        
        
        self.df_data = data
        self.logger = get_logger(__name__)

    def get_ui_path(self):
        return './gui/qt_widgets/market/KLineWidget.ui'
    
    def validate_data(self):
        required_columns = ['open', 'high', 'low', 'close']
        return all(col in self.df_data.columns for col in required_columns)
    
    def create_and_add_item(self):
        if self.item is None:
            self.item = CandlestickItem(self.df_data)
            self.plot_widget.addItem(self.item)
        else:
            self.item.update_data(self.df_data)

    def set_axis_ranges(self):
        data_high = np.max(self.df_data['high'])
        data_low = np.min(self.df_data['low'])
        self.plot_widget.setXRange(-1, len(self.df_data) + 1, padding=0)
        self.plot_widget.setYRange(data_low * 0.95, data_high * 1.05, padding=0)

    def get_chart_name(self):
        return "k线图"
    
    def is_ma_show(self):
        return self.item.is_ma_show() if self.item else False
    
    def show_ma(self, b_show=True):
        if self.item:
            self.item.show_ma(b_show)
