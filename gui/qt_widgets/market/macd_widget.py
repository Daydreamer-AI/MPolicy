# file: gui/qt_widgets/market/macd_widget.py
from PyQt5 import QtCore
from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout
from PyQt5.QtCore import pyqtSlot

import pyqtgraph as pg
import numpy as np

from common.logging_manager import get_logger
from gui.qt_widgets.market.base_indicator_widget import BaseIndicatorWidget
from gui.qt_widgets.MComponents.macd_item import MACDItem

class MacdWidget(BaseIndicatorWidget):
    def __init__(self, data, parent=None):
        super(MacdWidget, self).__init__(data, parent)

    def init_para(self, data):
        # 检查是否有数据
        if data is None or data.empty:
            raise ValueError("数据为空，无法绘制MACD指标图")
        
        # 确保数据列存在
        required_columns = ['diff', 'dea', 'macd']
        if not all(col in data.columns for col in required_columns):
            self.logger.warning("缺少必要的数据列来绘制MACD指标图")
            raise ValueError("缺少必要的数据列来绘制MACD指标图")
        
        self.df_data = data
        self.logger = get_logger(__name__)

    def init_connect(self):
        pass

    def get_ui_path(self):
        return './gui/qt_widgets/market/MacdWidget.ui'

    def validate_data(self):
        required_columns = ['diff', 'dea', 'macd']
        return all(col in self.df_data.columns for col in required_columns)

    def create_and_add_item(self):
        if self.item is None:
            self.item = MACDItem(self.df_data)
            self.plot_widget.addItem(self.item)
        else:
            self.item.update_data(self.df_data)

    def set_axis_ranges(self):
        # 设置坐标范围
        self.plot_widget.setXRange(-1, len(self.df_data) + 1, padding=0)
        
        # 计算Y轴范围
        diff_values = self.df_data['diff'].dropna()
        dea_values = self.df_data['dea'].dropna()
        macd_values = self.df_data['macd'].dropna()
        
        if len(diff_values) > 0 and len(dea_values) > 0 and len(macd_values) > 0:
            y_max = max(np.max(np.abs(diff_values)), np.max(np.abs(dea_values)), np.max(np.abs(macd_values)))
            y_max = y_max * 1.2 if y_max > 0 else 1
            self.plot_widget.setYRange(-y_max, y_max, padding=0)

    def get_chart_name(self):
        return "MACD"

    def additional_draw(self):
        """添加零轴线"""
        # 添加零轴线
        zero_line = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen('g', width=1, style=QtCore.Qt.DashLine))
        self.plot_widget.addItem(zero_line)