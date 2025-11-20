from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout
from PyQt5.QtCore import pyqtSlot

import pyqtgraph as pg
import numpy as np
import pandas as pd

from common.logging_manager import get_logger

from gui.qt_widgets.market.base_indicator_widget import BaseIndicatorWidget
from gui.qt_widgets.MComponents.candlestick_item import CandlestickItem

class KLineWidget(BaseIndicatorWidget):
    def __init__(self, data, parent=None):
        # 调用父类初始化，这会自动调用init_para, init_ui, init_connect
        super(KLineWidget, self).__init__(data, parent)

    def init_para(self, data):
        self.logger = get_logger(__name__)
        # 检查是否有数据
        if data is None or data.empty:
            # raise ValueError("数据为空，无法绘制k线图")
            self.logger.warning("数据为空，无法绘制k线图")
            return
        
        # 确保数据列存在
        required_columns = ['open', 'high', 'low', 'close']
        if not all(col in data.columns for col in required_columns):
            self.logger.warning("缺少必要的数据列来绘制k线图")
            raise ValueError("缺少必要的数据列来绘制k线图")
        
        
        self.df_data = data

    def get_ui_path(self):
        return './gui/qt_widgets/market/KLineWidget.ui'
    
    def validate_data(self):
        required_columns = ['open', 'high', 'low', 'close']
        return all(col in self.df_data.columns for col in required_columns)
    
    def create_and_add_item(self):
        if self.item is None:
            self.item = CandlestickItem(self.df_data)
        else:
            self.item.update_data(self.df_data)
            
        self.plot_widget.addItem(self.item)

    def set_axis_ranges(self):
        data_high = np.max(self.df_data['high'])
        data_low = np.min(self.df_data['low'])
        self.plot_widget.setXRange(-1, len(self.df_data) + 1, padding=0)
        self.plot_widget.setYRange(data_low * 0.95, data_high * 1.05, padding=0)

    def get_chart_name(self):
        return "k线图"
    
    def is_ma_show(self):
        return self.item.is_ma_show() if self.item else False
    
    def show_ma(self, b_show=True):
        if self.item:
            self.item.show_ma(b_show)

    def slot_range_changed(self):
        '''当视图范围改变时调用'''
        # y轴坐标值同步
        # 获取可视范围内的数据
        visible_data, x_min, x_max = self.get_visible_data_range()
        
        if visible_data is None or visible_data.empty:
            return
        
        # 根据当前可视范围内的数据的最大、最小值调整Y轴坐标值范围
        required_columns = []
        if 'high' in visible_data.columns and 'low' in visible_data.columns:
            required_columns.extend(['high', 'low'])
        
        # 如果MA线显示，也需要考虑MA线的值
        ma_columns = ['ma5', 'ma10', 'ma20', 'ma30', 'ma60']
        for col in ma_columns:
            if col in visible_data.columns and self.is_ma_show():
                required_columns.append(col)
                
        if not required_columns:
            return
        
        # 计算可见范围内的最大值和最小值
        max_val = visible_data[required_columns].max().max()
        min_val = visible_data[required_columns].min().min()
        
        # 添加一些padding以确保K线不会触及边界
        padding = (max_val - min_val) * 0.05  # 5%的padding
        y_min = min_val - padding
        y_max = max_val + padding
        
        # 重新设置Y轴刻度
        self.plot_widget.setYRange(y_min, y_max, padding=0)

    def slot_mouse_move(self, pos):
        if self.plot_widget.sceneBoundingRect().contains(pos):
            mouse_point = self.plot_widget.getViewBox().mapSceneToView(pos)
            x_val = mouse_point.x()
            y_val = mouse_point.y()

            # self.logger.info(f"鼠标位置：x={x_val}, y={y_val}")

            bar_centers = list(range(len(self.df_data)))
            
            closest_index = None
            min_distance = float('inf')
            
            for i, center in enumerate(bar_centers):
                distance = abs(center - x_val)
                if distance <= 0.25 / 2:
                    if distance < min_distance:
                        min_distance = distance
                        closest_index = i
            
            if closest_index is not None:
                view_range = self.plot_widget.getViewBox().viewRange()
                closest_x = bar_centers[closest_index]

                self.v_line.setPos(closest_x)
                self.v_line.show()

                self.h_line.setPos(y_val)
                self.h_line.show()

            else:
                self.hide_all_labels()
        else:
            self.hide_all_labels()

            

