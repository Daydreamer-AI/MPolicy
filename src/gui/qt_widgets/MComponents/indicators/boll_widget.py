# file: gui/qt_widgets/market/boll_widget.py
from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout
from PyQt5.QtCore import pyqtSlot

import pyqtgraph as pg
import numpy as np

from manager.logging_manager import get_logger
from gui.qt_widgets.market.base_indicator_widget import BaseIndicatorWidget
from gui.qt_widgets.MComponents.boll_item import BOLLItem

from manager.indicators_config_manager import *

class BollWidget(BaseIndicatorWidget):
    def __init__(self, data, type, parent=None):
        super(BollWidget, self).__init__(data, type, parent)

        self.load_qss()

    def init_para(self, data):
        self.logger = get_logger(__name__)
        # 检查是否有数据
        if data is None or data.empty:
            # raise ValueError("数据为空，无法绘制BOLL指标图")
            self.logger.warning("数据为空，无法绘制BOLL指标图")
            return
        
        # 确保数据列存在
        required_columns = ['close', 'boll_up', 'boll_mb', 'boll_dn']
        if not all(col in data.columns for col in required_columns):
            self.logger.warning("缺少必要的数据列来绘制BOLL指标图")
            raise ValueError("缺少必要的数据列来绘制BOLL指标图")
        
        self.df_data = data
        
    def load_qss(self):
        self.label_mid.setStyleSheet(f"color: {dict_boll_color_hex['mid']}")
        self.label_upper.setStyleSheet(f"color: {dict_boll_color_hex['up']}")
        self.label_lower.setStyleSheet(f"color: {dict_boll_color_hex['down']}")

    def get_ui_path(self):
        return './gui/qt_widgets/market/BollWidget.ui'

    def validate_data(self):
        required_columns = ['close', 'boll_up', 'boll_mb', 'boll_dn']
        return all(col in self.df_data.columns for col in required_columns)

    def create_and_add_item(self):
        if self.item is None:
            self.item = BOLLItem(self.df_data)
        else:
            self.item.update_data(self.df_data)

        self.plot_widget.addItem(self.item)

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
    
    def slot_range_changed(self):
        '''当视图范围改变时调用'''
        # y轴坐标值同步
        # 获取当前x轴视图范围内的数据
        visible_data, x_min, x_max = self.get_visible_data_range()
        if visible_data is None:
            return

        # 根据当前可视范围内的数据的最大、最小值调整Y轴坐标值范围
        # BOLL指标需要考虑close、boll_up、boll_mb、boll_dn四条线
        required_columns = ['close', 'boll_up', 'boll_dn']
        # 检查所需列是否存在
        if not all(col in visible_data.columns for col in required_columns):
            return
        
        # 计算可视范围内的最大值和最小值
        y_min = visible_data[required_columns].min().min()
        y_max = visible_data[required_columns].max().max()
        
        # 添加一些padding以确保线条不会触及边界
        padding = (y_max - y_min) * 0.05  # 5%的padding
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
        mid = self.df_data.iloc[closest_index]['boll_mb']
        upper = self.df_data.iloc[closest_index]['boll_up']
        lower = self.df_data.iloc[closest_index]['boll_dn']

        self.label_mid.setText(f"MID:{mid:.2f}")
        self.label_upper.setText(f"UPPER:{upper:.2f}")
        self.label_lower.setText(f"LOWER:{lower:.2f}")

    def slot_global_reset_labels(self, sender):
        self.slot_global_update_labels(sender, -1)

    def slot_v_line_mouse_moved(self, sender, x_pos):
        # self.logger.info(f"正在处理{self.get_chart_name()}鼠标移动响应, self: {self}, sender: {sender}")
        if self.type != sender.type:
            # self.logger.info(f"不响应其他窗口的鼠标移动事件")
            return
        self.v_line.setPos(x_pos)
        self.v_line.show()