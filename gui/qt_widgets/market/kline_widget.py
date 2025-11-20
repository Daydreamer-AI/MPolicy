from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout
from PyQt5.QtCore import pyqtSlot

import pyqtgraph as pg
import numpy as np
import pandas as pd

from common.logging_manager import get_logger

from gui.qt_widgets.MComponents.candlestick_item import CandlestickItem

class KLineWidget(QWidget):
    def __init__(self, data, parent=None):
        super(KLineWidget, self).__init__(parent)

        self.init_para(data)
        self.init_ui()
        self.init_connect()

    def init_ui(self):
        uic.loadUi('./gui/qt_widgets/market/KLineWidget.ui', self)

        self.candlestick_item = None

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
            raise ValueError("数据为空，无法绘制k线图")
        
        # 确保数据列存在
        required_columns = ['open', 'high', 'low', 'close']
        if not all(col in data.columns for col in required_columns):
            self.logger.warning("缺少必要的数据列来绘制k线图")
            raise ValueError("缺少必要的数据列来绘制k线图")
        
        
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
    
    def is_ma_show(self):
        return self.candlestick_item.is_ma_show()
    
    def show_ma(self, b_show=True):
        self.candlestick_item.show_ma(b_show)

    def draw(self):
        # ""绘制交易额指标图
        self.plot_widget.clear()

        # 检查是否有数据
        if self.df_data is None or self.df_data.empty:
            return
        
        # 确保数据列存在
        required_columns = ['open', 'high', 'low', 'close']
        if not all(col in self.df_data.columns for col in required_columns):
            self.logger.warning("缺少必要的数据列来绘制k线图")
            return

        # 创建交易量图
        if self.candlestick_item is None:
            self.candlestick_item = CandlestickItem(self.df_data)
            self.plot_widget.addItem(self.candlestick_item)
        else:
            # 更新现有item的数据
            self.candlestick_item.update_data(self.df_data)

        #设置坐标范围
        # 计算数据范围
        data_high = np.max(self.df_data['high'])
        data_low = np.min(self.df_data['low'])
        self.plot_widget.setXRange(-1, len(self.df_data) + 1, padding=0)
        self.plot_widget.setYRange(data_low * 0.95, data_high * 1.05, padding=0)

        #设置坐标轴颜色
        self.plot_widget.getAxis('left').setPen(QtGui.QColor(110, 110, 110))
        self.plot_widget.getAxis('bottom').setPen(QtGui.QColor(110, 110, 110))
