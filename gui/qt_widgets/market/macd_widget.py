# file: gui/qt_widgets/market/macd_widget.py
from PyQt5 import QtCore
from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout
from PyQt5.QtCore import pyqtSlot

import pyqtgraph as pg
import numpy as np

from common.logging_manager import get_logger

from gui.qt_widgets.MComponents.macd_item import MACDItem

class MacdWidget(QWidget):
    def __init__(self, data, parent=None):
        super(MacdWidget, self).__init__(parent)

        self.init_para(data)
        self.init_ui()
        self.init_connect()

    def init_ui(self):
        uic.loadUi('./gui/qt_widgets/market/MacdWidget.ui', self)

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

    def update_data(self, data):
        self.df_data = data
        self.draw()

    def get_data(self):
        return self.df_data
    
    def get_plot_widget(self):
        return self.plot_widget

    def draw(self):
        """绘制MACD指标图"""
        self.plot_widget.clear()

        # 检查是否有数据
        if self.df_data is None or self.df_data.empty:
            return
        
        # 确保数据列存在
        required_columns = ['diff', 'dea', 'macd']
        if not all(col in self.df_data.columns for col in required_columns):
            self.logger.warning("缺少必要的数据列来绘制MACD指标图")
            return

        # 创建MACD图
        macd_item = MACDItem(self.df_data)
        self.plot_widget.addItem(macd_item)

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

        # 设置坐标轴颜色
        self.plot_widget.getAxis('left').setPen(QtGui.QColor(110, 110, 110))
        self.plot_widget.getAxis('bottom').setPen(QtGui.QColor(110, 110, 110))
        self.plot_widget.getAxis('left').setTextPen(QtGui.QColor(110, 110, 110))
        self.plot_widget.getAxis('bottom').setTextPen(QtGui.QColor(110, 110, 110))

        # 添加零轴线，已有无需重复
        # zero_line = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen('k', width=0.5, style=QtCore.Qt.DashLine))
        # self.plot_widget.addItem(zero_line)