from PyQt5 import QtCore
from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout
from PyQt5.QtCore import pyqtSlot

import pyqtgraph as pg
import numpy as np

from manager.logging_manager import get_logger
from gui.qt_widgets.MComponents.indicators.base_indicator_widget import BaseIndicatorWidget
from gui.qt_widgets.MComponents.indicators.item.rsi_item import RSIItem

from manager.indicators_config_manager import *

class RsiWidget(BaseIndicatorWidget):
    def __init__(self, data, type, parent=None):
        super(RsiWidget, self).__init__(data, type, parent)

        self.load_qss()

    def init_para(self, data):
        self.logger = get_logger(__name__)
        # 检查是否有数据
        if data is None or data.empty:
            # raise ValueError("数据为空，无法绘制RSI指标图")
            self.logger.warning("数据为空，无法绘制RSI指标图")
            return
        
        # 确保至少有一个RSI数据列存在
        rsi_columns = ['rsi6', 'rsi12', 'rsi24']
        has_rsi = any(col in data.columns for col in rsi_columns)
        if not has_rsi:
            self.logger.warning("缺少必要的RSI数据列")
            raise ValueError("缺少必要的RSI数据列")
        
        self.df_data = data

    def load_qss(self):
        self.label_rsi6.setStyleSheet(f"color: {dict_rsi_color_hex['rsi1']}")
        self.label_rsi12.setStyleSheet(f"color: {dict_rsi_color_hex['rsi2']}")
        self.label_rsi24.setStyleSheet(f"color: {dict_rsi_color_hex['rsi3']}")

    def get_ui_path(self):
        return './src/gui/qt_widgets/MComponents/indicators/RsiWidget.ui'

    def validate_data(self):
        # 确保至少有一个RSI数据列存在
        rsi_columns = ['rsi6', 'rsi12', 'rsi24']
        available_rsi = [col for col in rsi_columns if col in self.df_data.columns]
        return len(available_rsi) > 0

    def create_and_add_item(self):
        if self.item is None:
            self.item = RSIItem(self.df_data)
        else:
            self.item.update_data(self.df_data)

        self.plot_widget.addItem(self.item)

    def set_axis_ranges(self):
        # 确保至少有一个RSI数据列存在
        rsi_columns = ['rsi6', 'rsi12', 'rsi24']
        available_rsi = [col for col in rsi_columns if col in self.df_data.columns]
        
        # 设置坐标范围
        self.plot_widget.setXRange(-1, len(self.df_data) + 1, padding=0)
        
        # 计算Y轴范围 (RSI指标通常在0-100范围内)
        all_rsi_values = []
        for col in available_rsi:
            values = self.df_data[col].dropna()
            if len(values) > 0:
                all_rsi_values.extend(values.tolist())
        
        if all_rsi_values:
            y_min = min(all_rsi_values)
            y_max = max(all_rsi_values)
            
            # 确保显示范围包含0-100
            y_min = min(y_min, 0)
            y_max = max(y_max, 100)
            
            # 添加一些padding
            padding = (y_max - y_min) * 0.1
            self.plot_widget.setYRange(y_min - padding, y_max + padding, padding=0)

    def get_chart_name(self):
        return "RSI"
    
    def update_widget_labels(self):
        self.slot_global_update_labels(self, -1)

    def additional_draw(self):
        """添加参考线"""
        # 超买线 (70)
        overbought_line = pg.InfiniteLine(pos=70, angle=0, pen=pg.mkPen('r', width=1, style=QtCore.Qt.DashLine))
        self.plot_widget.addItem(overbought_line)
        
        # 超卖线 (30)
        oversold_line = pg.InfiniteLine(pos=30, angle=0, pen=pg.mkPen('g', width=1, style=QtCore.Qt.DashLine))
        self.plot_widget.addItem(oversold_line)
        
        # 中轴线 (50)
        mid_line = pg.InfiniteLine(pos=50, angle=0, pen=pg.mkPen('gray', width=1, style=QtCore.Qt.DashLine))
        self.plot_widget.addItem(mid_line)

    def slot_range_changed(self):
        '''当视图范围改变时调用'''
        # y轴坐标值同步
        # 获取当前x轴视图范围内的数据
        visible_data, x_min, x_max = self.get_visible_data_range()
        if visible_data is None:
            return

        # 根据当前可视范围内的数据的最大、最小值调整Y轴坐标值范围
        # RSI指标需要考虑可用的RSI列（rsi6, rsi12, rsi24）
        rsi_columns = ['rsi6', 'rsi12', 'rsi24']
        available_rsi = [col for col in rsi_columns if col in visible_data.columns]
        
        # 确保至少有一个RSI数据列存在
        if not available_rsi:
            return
        
        # 计算可视范围内的最大值和最小值
        all_rsi_values = []
        for col in available_rsi:
            values = visible_data[col].dropna()
            if len(values) > 0:
                all_rsi_values.extend(values.tolist())
        
        if not all_rsi_values:
            return
            
        y_min = min(all_rsi_values)
        y_max = max(all_rsi_values)
        
        # 确保显示范围包含0-100的重要参考线
        y_min = min(y_min, 0)
        y_max = max(y_max, 100)
        
        # 添加一些padding以确保线条不会触及边界
        padding = (y_max - y_min) * 0.1  # 10%的padding
        y_min -= padding
        y_max += padding
        
        # 重新设置Y轴刻度
        self.plot_widget.setYRange(y_min, y_max, padding=0)

    def slot_global_update_labels(self, sender, closest_index):
        if self.df_data is None or self.df_data.empty:
            return
        if self.type != sender.type:
            # self.logger.info(f"不响应其他窗口的鼠标移动事件")
            return
        rsi_6 = self.df_data.iloc[closest_index]['rsi6']
        rsi_12 = self.df_data.iloc[closest_index]['rsi12']
        rsi_24 = self.df_data.iloc[closest_index]['rsi24']

        self.label_rsi6.setText(f"RSI6:{rsi_6:.2f}")
        self.label_rsi12.setText(f"RSI12:{rsi_12:.2f}")
        self.label_rsi24.setText(f"RSI24:{rsi_24:.2f}")

    def slot_global_reset_labels(self, sender):
        self.slot_global_update_labels(sender, -1)

    def slot_v_line_mouse_moved(self, sender, x_pos):
        # self.logger.info(f"正在处理{self.get_chart_name()}鼠标移动响应, self: {self}, sender: {sender}")
        if self.type != sender.type:
            # self.logger.info(f"不响应其他窗口的鼠标移动事件")
            return
        self.v_line.setPos(x_pos)
        self.v_line.show()
