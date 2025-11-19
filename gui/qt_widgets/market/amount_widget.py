from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout
from PyQt5.QtCore import pyqtSlot

import pyqtgraph as pg
import numpy as np
import pandas as pd

from common.logging_manager import get_logger

from gui.qt_widgets.MComponents.amount_item import AmountItem

class AmountWidget(QWidget):
    def __init__(self, data, parent=None):
        super(AmountWidget, self).__init__(parent)

        self.init_para(data)
        self.init_ui()
        self.init_connect()

    def init_ui(self):
        uic.loadUi('./gui/qt_widgets/market/AmountWidget.ui', self)

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
            raise ValueError("数据为空，无法绘制成交额指标图")
        
        # 确保数据列存在
        required_columns = ['open', 'close', 'amount']
        if not all(col in data.columns for col in required_columns):
            self.logger.warning("缺少必要的数据列来绘制成交额指标图")
            raise ValueError("缺少必要的数据列来绘制成交额指标图")
        
        # 添加数据类型检查
        if not pd.api.types.is_numeric_dtype(data['amount']):
            self.logger.error(f"amount列数据类型错误: {data['amount'].dtype}")
            raise ValueError("amount列必须是数值类型")
        
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
        # ""绘制交易额指标图
        self.plot_widget.clear()

        # 检查是否有数据
        if self.df_data is None or self.df_data.empty:
            return
        
        # 确保数据列存在
        required_columns = ['open', 'close', 'amount']
        if not all(col in self.df_data.columns for col in required_columns):
            self.logger.warning("缺少必要的数据列来绘制成交额指标图")
            return
        
        # 检查amount列是否有有效数据
        amount_data = self.df_data['amount']
        if amount_data.isna().all():
            self.logger.error("amount列全部为NaN")
            return
        
        if (amount_data == 0).all():
            self.logger.error("amount列全部为0")
            return

        # 创建交易量图
        amount_item = AmountItem(self.df_data)

        self.plot_widget.addItem(amount_item)

        #设置坐标范围
        self.plot_widget.setXRange(-1, len(self.df_data) + 1, padding=0)
        max_vol = np.max(self.df_data['amount'])
        self.logger.info(f"最大成交额-max_vol: {max_vol}")
        self.plot_widget.setYRange(0, max_vol / 100000000 * 1.1, padding=0)       # 单位：亿

        #设置坐标轴颜色
        self.plot_widget.getAxis('left').setPen(QtGui.QColor(110, 110, 110))
        self.plot_widget.getAxis('bottom').setPen(QtGui.QColor(110, 110, 110))
        self.plot_widget.getAxis('left').setTextPen(QtGui.QColor(110, 110, 110))
        self.plot_widget.getAxis('bottom').setTextPen(QtGui.QColor(110, 110, 110))
