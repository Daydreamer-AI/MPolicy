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
