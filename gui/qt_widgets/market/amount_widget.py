from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout
from PyQt5.QtCore import pyqtSlot

import pyqtgraph as pg
import numpy as np
import pandas as pd

from common.logging_manager import get_logger
from gui.qt_widgets.market.base_indicator_widget import BaseIndicatorWidget
from gui.qt_widgets.MComponents.amount_item import AmountItem

class AmountWidget(BaseIndicatorWidget):
    def __init__(self, data, parent=None):
        super(AmountWidget, self).__init__(data, parent)

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

    def get_ui_path(self):
        return './gui/qt_widgets/market/AmountWidget.ui'
    
    def validate_data(self):
        required_columns = ['open', 'close', 'amount']
        return all(col in self.df_data.columns for col in required_columns)

    def create_and_add_item(self):
        # 检查amount列是否有有效数据
        amount_data = self.df_data['amount']
        if amount_data.isna().all():
            self.logger.error("amount列全部为NaN")
            return
        
        if (amount_data == 0).all():
            self.logger.error("amount列全部为0")
            return

        # 创建或更新成交额图
        if self.item is None:
            self.item = AmountItem(self.df_data)
            self.plot_widget.addItem(self.item)
        else:
            self.item.update_data(self.df_data)

    def set_axis_ranges(self):
        # 设置坐标范围
        self.plot_widget.setXRange(-1, len(self.df_data) + 1, padding=0)
        max_amount = np.max(self.df_data['amount'])
        self.logger.info(f"最大成交额-max_amount: {max_amount}")
        self.plot_widget.setYRange(0, max_amount / 100000000 * 1.1, padding=0)       # 单位：亿

    def get_chart_name(self):
        return "成交额"
    
    def slot_range_changed(self):
        '''当视图范围改变时调用'''
        # y轴坐标值同步
        # 获取当前x轴视图范围内的数据
        visible_data, x_min, x_max = self.get_visible_data_range()
        if visible_data is None:
            return

        # 根据当前可视范围内的数据的最大、最小值调整Y轴坐标值范围
        # 成交额图只需要考虑amount列的最大值，最小值始终为0
        max_amount = visible_data['amount'].max()
        max_amount = max_amount / 100000000     # 单位：亿
        
        # 添加一些padding以确保柱状图不会触及顶部边界
        padding = max_amount * 0.05  # 5%的padding
        y_min = 0  # 成交额最小值始终为0
        y_max = max_amount + padding
        
        # 重新设置Y轴刻度
        self.plot_widget.setYRange(y_min, y_max, padding=0)