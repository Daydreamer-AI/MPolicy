# file: gui/qt_widgets/market/kdj_widget.py
from PyQt5 import QtCore
from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout
from PyQt5.QtCore import pyqtSlot

import pyqtgraph as pg
import numpy as np

from common.logging_manager import get_logger

from gui.qt_widgets.MComponents.kdj_item import KDJItem

class KdjWidget(QWidget):
    def __init__(self, data, parent=None):
        super(KdjWidget, self).__init__(parent)

        self.init_para(data)
        self.init_ui()
        self.init_connect()

    def init_ui(self):
        uic.loadUi('./gui/qt_widgets/market/KdjWidget.ui', self)

        layout = self.layout()
        if layout is None:
            self.logger.info("没有布局，创建一个")
            self.setLayout(QVBoxLayout())
            layout = self.layout()

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.hideAxis('bottom')
        self.plot_widget.getAxis('left').setWidth(60)
        self.plot_widget.setBackground('w')
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setMouseEnabled(x=True, y=False)
        layout.addWidget(self.plot_widget)

        self.draw()

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

    def update_data(self, data):
        self.df_data = data
        self.draw()

    def get_data(self):
        return self.df_data
    
    def get_plot_widget(self):
        return self.plot_widget

    def draw(self):
        """绘制KDJ指标图"""
        self.plot_widget.clear()

        # 检查是否有数据
        if self.df_data is None or self.df_data.empty:
            return
        
        # 确保数据列存在
        required_columns = ['K', 'D', 'J']
        if not all(col in self.df_data.columns for col in required_columns):
            self.logger.warning("缺少必要的数据列来绘制KDJ指标图")
            return

        # 创建KDJ图
        kdj_item = KDJItem(self.df_data)
        self.plot_widget.addItem(kdj_item)

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

        # 设置坐标轴颜色
        self.plot_widget.getAxis('left').setPen(QtGui.QColor(110, 110, 110))
        self.plot_widget.getAxis('bottom').setPen(QtGui.QColor(110, 110, 110))
        self.plot_widget.getAxis('left').setTextPen(QtGui.QColor(110, 110, 110))
        self.plot_widget.getAxis('bottom').setTextPen(QtGui.QColor(110, 110, 110))

        # 添加参考线
        # 超买线 (80)
        overbought_line = pg.InfiniteLine(pos=80, angle=0, pen=pg.mkPen('r', width=1, style=QtCore.Qt.DashLine))
        self.plot_widget.addItem(overbought_line)
        
        # 超卖线 (20)
        oversold_line = pg.InfiniteLine(pos=20, angle=0, pen=pg.mkPen('g', width=1, style=QtCore.Qt.DashLine))
        self.plot_widget.addItem(oversold_line)
        
        # 中轴线 (50)
        mid_line = pg.InfiniteLine(pos=50, angle=0, pen=pg.mkPen('gray', width=1, style=QtCore.Qt.DashLine))
        self.plot_widget.addItem(mid_line)