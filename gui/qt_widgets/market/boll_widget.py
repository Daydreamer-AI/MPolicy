# file: gui/qt_widgets/market/boll_widget.py
from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout
from PyQt5.QtCore import pyqtSlot

import pyqtgraph as pg
import numpy as np

from common.logging_manager import get_logger
from gui.qt_widgets.market.base_indicator_widget import BaseIndicatorWidget
from gui.qt_widgets.MComponents.boll_item import BOLLItem

class BollWidget(BaseIndicatorWidget):
    def __init__(self, data, parent=None):
        super(BollWidget, self).__init__(data, parent)

    def init_para(self, data):
        # 检查是否有数据
        if data is None or data.empty:
            raise ValueError("数据为空，无法绘制BOLL指标图")
        
        # 确保数据列存在
        required_columns = ['close', 'boll_up', 'boll_mb', 'boll_dn']
        if not all(col in data.columns for col in required_columns):
            self.logger.warning("缺少必要的数据列来绘制BOLL指标图")
            raise ValueError("缺少必要的数据列来绘制BOLL指标图")
        
        self.df_data = data
        self.logger = get_logger(__name__)

    def init_connect(self):
        pass

    def get_ui_path(self):
        return './gui/qt_widgets/market/BollWidget.ui'

    def validate_data(self):
        required_columns = ['close', 'boll_up', 'boll_mb', 'boll_dn']
        return all(col in self.df_data.columns for col in required_columns)

    def create_and_add_item(self):
        if self.item is None:
            self.item = BOLLItem(self.df_data)
            self.plot_widget.addItem(self.item)
        else:
            self.item.update_data(self.df_data)

    def set_axis_ranges(self):
        # 设置坐标范围
        self.plot_widget.setXRange(-1, len(self.df_data) + 1, padding=0)
        
        # 计算Y轴范围
        close_values = self.df_data['close'].dropna()
        up_values = self.df_data['boll_up'].dropna()
        dn_values = self.df_data['boll_dn'].dropna()
        
        if len(close_values) > 0 and len(up_values) > 0 and len(dn_values) > 0:
            y_min = min(np.min(close_values), np.min(dn_values))
            y_max = max(np.max(close_values), np.max(up_values))
            
            # 添加一些padding
            padding = (y_max - y_min) * 0.05
            self.plot_widget.setYRange(y_min - padding, y_max + padding, padding=0)

    def get_chart_name(self):
        return "BOLL"