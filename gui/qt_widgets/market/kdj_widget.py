# file: gui/qt_widgets/market/kdj_widget.py
from PyQt5 import QtCore
from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout
from PyQt5.QtCore import pyqtSlot

import pyqtgraph as pg
import numpy as np

from common.logging_manager import get_logger
from gui.qt_widgets.market.base_indicator_widget import BaseIndicatorWidget
from gui.qt_widgets.MComponents.kdj_item import KDJItem

class KdjWidget(BaseIndicatorWidget):
    def __init__(self, data, parent=None):
        super(KdjWidget, self).__init__(data, parent)

    def init_para(self, data):
        # 检查是否有数据
        if data is None or data.empty:
            raise ValueError("数据为空，无法绘制KDJ指标图")
        
        # 确保数据列存在
        required_columns = ['K', 'D', 'J']
        if not all(col in data.columns for col in required_columns):
            self.logger.warning("缺少必要的数据列来绘制KDJ指标图")
            raise ValueError("缺少必要的数据列来绘制KDJ指标图")
        
        self.df_data = data
        self.logger = get_logger(__name__)

    def init_connect(self):
        pass

    def get_ui_path(self):
        return './gui/qt_widgets/market/KdjWidget.ui'

    def validate_data(self):
        required_columns = ['K', 'D', 'J']
        return all(col in self.df_data.columns for col in required_columns)

    def create_and_add_item(self):
        if self.item is None:
            self.item = KDJItem(self.df_data)
            self.plot_widget.addItem(self.item)
        else:
            self.item.update_data(self.df_data)

    def set_axis_ranges(self):
        # 设置坐标范围
        self.plot_widget.setXRange(-1, len(self.df_data) + 1, padding=0)
        
        # 计算Y轴范围 (KDJ指标通常在0-100范围内)
        k_values = self.df_data['K'].dropna()
        d_values = self.df_data['D'].dropna()
        j_values = self.df_data['J'].dropna()
        
        if len(k_values) > 0 and len(d_values) > 0 and len(j_values) > 0:
            y_min = min(np.min(k_values), np.min(d_values), np.min(j_values))
            y_max = max(np.max(k_values), np.max(d_values), np.max(j_values))
            
            # 确保显示范围包含0-100
            y_min = min(y_min, 0)
            y_max = max(y_max, 100)
            
            # 添加一些padding
            padding = (y_max - y_min) * 0.1
            self.plot_widget.setYRange(y_min - padding, y_max + padding, padding=0)

    def get_chart_name(self):
        return "KDJ"

    def additional_draw(self):
        """添加参考线"""
        # 超买线 (80)
        overbought_line = pg.InfiniteLine(pos=80, angle=0, pen=pg.mkPen('r', width=1, style=QtCore.Qt.DashLine))
        self.plot_widget.addItem(overbought_line)
        
        # 超卖线 (20)
        oversold_line = pg.InfiniteLine(pos=20, angle=0, pen=pg.mkPen('g', width=1, style=QtCore.Qt.DashLine))
        self.plot_widget.addItem(oversold_line)
        
        # 中轴线 (50)
        mid_line = pg.InfiniteLine(pos=50, angle=0, pen=pg.mkPen('gray', width=1, style=QtCore.Qt.DashLine))
        self.plot_widget.addItem(mid_line)