from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout
from PyQt5.QtCore import pyqtSlot

import pyqtgraph as pg
import numpy as np

from common.logging_manager import get_logger
from gui.qt_widgets.market.base_indicator_widget import BaseIndicatorWidget
from gui.qt_widgets.MComponents.volume_item import VolumeItem

class VolumeWidget(BaseIndicatorWidget):
    def __init__(self, data, parent=None):
        super(VolumeWidget, self).__init__(data, parent)

    def init_para(self, data):
        if data is None or data.empty:
            raise ValueError("数据为空，无法绘制成交量指标图")
        
        required_columns = ['open', 'close', 'volume']
        if not all(col in data.columns for col in required_columns):
            raise ValueError("缺少必要的数据列来绘制成交量指标图")
        
        self.df_data = data
        self.logger = get_logger(__name__)

    def get_ui_path(self):
        return './gui/qt_widgets/market/VolumeWidget.ui'
    
    def validate_data(self):
        required_columns = ['open', 'close', 'volume']
        return all(col in self.df_data.columns for col in required_columns)
    
    def create_and_add_item(self):
        self.item = VolumeItem(self.df_data)
        self.plot_widget.addItem(self.item)
    
    def set_axis_ranges(self):
        self.plot_widget.setXRange(-1, len(self.df_data) + 1, padding=0)
        max_vol = np.max(self.df_data['volume'])
        self.logger.info(f"最大成交量-max_vol: {max_vol}")
        self.plot_widget.setYRange(0, max_vol / 10000 * 1.1, padding=0)
    
    def get_chart_name(self):
        return "成交量"
    
    def slot_range_changed(self):
        '''当视图范围改变时调用'''
        # y轴坐标值同步
        # 获取可视范围内的数据
        visible_data, x_min, x_max = self.get_visible_data_range()
        if visible_data is None or visible_data.empty:
            return
        
        # 根据当前可视范围内的数据的最大、最小值调整Y轴坐标值范围
        # 成交量图只需要考虑volume列的最大值，最小值始终为0
        max_volume = visible_data['volume'].max()
        max_volume = max_volume / 10000     # 单位：万
        
        # 添加一些padding以确保柱状图不会触及顶部边界
        padding = max_volume * 0.05  # 5%的padding
        y_min = 0  # 成交量最小值始终为0
        y_max = max_volume + padding
        
        # 重新设置Y轴刻度
        self.plot_widget.setYRange(y_min, y_max, padding=0)
