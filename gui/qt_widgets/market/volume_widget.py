from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout
from PyQt5.QtCore import pyqtSlot

import pyqtgraph as pg
import numpy as np

from common.logging_manager import get_logger

from gui.qt_widgets.MComponents.volume_item import VolumeItem

class VolumeWidget(QWidget):
    def __init__(self, data, parent=None):
        super(VolumeWidget, self).__init__(parent)

        self.init_para(data)
        self.init_ui()
        self.init_connect()

    def init_ui(self):
        uic.loadUi('./gui/qt_widgets/market/VolumeWidget.ui', self)

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
            raise ValueError("数据为空，无法绘制成交量")
        
        # 确保数据列存在
        required_columns = ['open', 'close', 'volume']
        if not all(col in data.columns for col in required_columns):
            self.logger.warning("缺少必要的数据列来绘制成交量")
            raise ValueError("缺少必要数据列")
        
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
        # ""绘制交易量图
        self.plot_widget.clear()

        # 检查是否有数据
        if self.df_data is None or self.df_data.empty:
            return
        
        # 确保数据列存在
        required_columns = ['open', 'close', 'volume']
        if not all(col in self.df_data.columns for col in required_columns):
            self.logger.warning("缺少必要的数据列来绘制成交量")
            return

        # 创建交易量图
        vol_item = VolumeItem(self.df_data)

        self.plot_widget.addItem(vol_item)

        #设置坐标范围
        self.plot_widget.setXRange(-1, len(self.df_data) + 1, padding=0)
        max_vol = np.max(self.df_data['volume'])
        self.plot_widget.setYRange(0, max_vol * 1.1, padding=0)

        #设置坐标轴颜色
        self.plot_widget.getAxis('left').setPen(QtGui.QColor(110, 110, 110))
        self.plot_widget.getAxis('bottom').setPen(QtGui.QColor(110, 110, 110))
        self.plot_widget.getAxis('left').setTextPen(QtGui.QColor(110, 110, 110))
        self.plot_widget.getAxis('bottom').setTextPen(QtGui.QColor(110, 110, 110))
