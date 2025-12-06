# file: gui/qt_widgets/market/macd_widget.py
from PyQt5 import QtCore
from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout
from PyQt5.QtCore import pyqtSlot

import pyqtgraph as pg
import numpy as np

from manager.logging_manager import get_logger
from gui.qt_widgets.market.base_indicator_widget import BaseIndicatorWidget
from gui.qt_widgets.MComponents.macd_item import MACDItem

from manager.indicators_config_manager import *

class MacdWidget(BaseIndicatorWidget):
    def __init__(self, data, type, parent=None):
        super(MacdWidget, self).__init__(data, type, parent)

        self.load_qss()

    def init_para(self, data):
        self.logger = get_logger(__name__)
        # 检查是否有数据
        if data is None or data.empty:
            # raise ValueError("数据为空，无法绘制MACD指标图")
            self.logger.warning("数据为空，无法绘制MACD指标图")
            return
        
        # 确保数据列存在
        required_columns = ['diff', 'dea', 'macd']
        if not all(col in data.columns for col in required_columns):
            self.logger.warning("缺少必要的数据列来绘制MACD指标图")
            raise ValueError("缺少必要的数据列来绘制MACD指标图")
        
        self.df_data = data

    def load_qss(self):
        self.label_diff.setStyleSheet(f"color: {dict_macd_color_hex['diff']};")
        self.label_dea.setStyleSheet(f"color: {dict_macd_color_hex['dea']};")

    def get_ui_path(self):
        return './gui/qt_widgets/market/MacdWidget.ui'

    def validate_data(self):
        required_columns = ['diff', 'dea', 'macd']
        return all(col in self.df_data.columns for col in required_columns)

    def create_and_add_item(self):
        if self.item is None:
            self.item = MACDItem(self.df_data)
        else:
            self.item.update_data(self.df_data)
        
        self.plot_widget.addItem(self.item)

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

    def slot_range_changed(self):
        '''当视图范围改变时调用'''
        # y轴坐标值同步
        # 获取当前x轴视图范围内的数据
        visible_data, x_min, x_max = self.get_visible_data_range()
        if visible_data is None:
            return

        # 根据当前可视范围内的数据的最大、最小值调整Y轴坐标值范围
        # MACD指标需要考虑diff、dea、macd三列数据
        required_columns = ['diff', 'dea', 'macd']
        # 检查所需列是否存在
        if not all(col in visible_data.columns for col in required_columns):
            return
        
        # 计算可视范围内的绝对值最大值（MACD通常围绕0轴对称）
        y_max = visible_data[required_columns].abs().max().max()
        
        # 防止y_max为0的情况
        y_max = y_max * 1.2 if y_max > 0 else 1
        
        # 重新设置Y轴刻度（保持对称）
        self.plot_widget.setYRange(-y_max, y_max, padding=0)

    def slot_global_update_labels(self, sender, closest_index):
        if self.df_data is None or self.df_data.empty:
            return
        
        if self.type != sender.type:
            # self.logger.info(f"不响应其他窗口的鼠标移动事件")
            return
        macd = self.df_data.iloc[closest_index]['macd']
        diff = self.df_data.iloc[closest_index]['diff']
        dea = self.df_data.iloc[closest_index]['dea']

        self.label_macd.setText(f"MACD:{macd:.3f}")
        self.label_diff.setText(f"DIFF:{diff:.3f}")
        self.label_dea.setText(f"DEA:{dea:.3f}")

        if macd > 0:
            self.label_macd.setStyleSheet(f"color: {dict_kline_color_hex['asc']};")
        else:
            self.label_macd.setStyleSheet(f"color: {dict_kline_color_hex['desc']};")

    def slot_global_reset_labels(self, sender):
        self.slot_global_update_labels(sender, -1)

    def slot_v_line_mouse_moved(self, sender, x_pos):
        # self.logger.info(f"正在处理{self.get_chart_name()}鼠标移动响应, self: {self}, sender: {sender}")
        if self.type != sender.type:
            # self.logger.info(f"不响应其他窗口的鼠标移动事件")
            return
        self.v_line.setPos(x_pos)
        self.v_line.show()