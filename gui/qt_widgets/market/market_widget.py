from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout
from PyQt5.QtCore import pyqtSlot

from processor.baostock_processor import BaoStockProcessor

from common.common_api import *
import datetime
from common.logging_manager import get_logger

from gui.qt_widgets.MComponents.candlestick_item import CandlestickItem
import numpy as np
import pyqtgraph as pg
from gui.qt_widgets.MComponents.custom_date_axisItem import CustomDateAxisItem, NoLabelAxis

class MarketWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.init_para()
        self.init_ui()
        self.init_connect()

        self.draw_charts()

    def init_para(self):
        self.logger = get_logger(__name__)
        # self.df_data列结构：date, code, open, high, low, close, volume, amount, change_percent, turnover_rate, adjustflag, diff, dea, macd, ma5, ma10, ma20, ma24, ma30, ma52, ma60, volume_ratio
        self.df_data = BaoStockProcessor().get_daily_stock_data('sh.600000')    
    def init_ui(self):
        uic.loadUi('./gui/qt_widgets/market/MarketWidget.ui', self)

        widget_k_line_layout = self.widget_k_line.layout()
        if widget_k_line_layout is None:
            self.widget_k_line.setLayout(QVBoxLayout())


        # self.date_axis_main = NoLabelAxis(orientation='bottom')
        # self.plot_widget = pg.PlotWidget(axisItems={'bottom': self.date_axis_main})
        self.kline_plot_widget = pg.PlotWidget()
        self.kline_plot_widget.setBackground('w')  # 设置背景为白色
        # self.kline_plot_widget.setLabel('left', 'Price')
        # self.kline_plot_widget.setLabel('bottom', 'Time')
        self.kline_plot_widget.showGrid(x=False, y=True)
        self.kline_plot_widget.setMouseEnabled(x=True, y=False)
        widget_k_line_layout.addWidget(self.kline_plot_widget)




    def init_connect(self):
        pass

    def draw_charts(self):
        # ."绘制所有图表…
        self.draw_kline()
        self.draw_volume()
        self.draw_macd()
        self.update_info_labels()


    def draw_kline(self):
        self.kline_plot_widget.clear()
        
        # 检查是否有数据
        if self.df_data is None or self.df_data.empty:
            return
        
        # 确保数据列存在
        required_columns = ['high', 'low', 'open', 'close', 'date']
        if not all(col in self.df_data.columns for col in required_columns):
            self.logger.warning("缺少必要的数据列来绘制K线图")
            return
        
        # 计算数据范围
        data_high = np.max(self.df_data['high'])
        data_low = np.min(self.df_data['low'])
        
        # 创建蜡烛图
        candle_item = CandlestickItem(self.df_data)
        self.kline_plot_widget.addItem(candle_item)
        
        # 绘制均线（如果存在）
        # x_axis = list(range(len(self.df_data)))
        
        # # MA5
        # if 'ma5' in self.df_data.columns:
        #     self.kline_plot_widget.plot(x_axis, self.df_data['ma5'].values, 
        #                             pen=pg.mkPen(color=(255, 0, 0), width=1), name='MA5')
        
        # # MA10
        # if 'ma10' in self.df_data.columns:
        #     self.kline_plot_widget.plot(x_axis, self.df_data['ma10'].values, 
        #                             pen=pg.mkPen(color=(0, 255, 0), width=1), name='MA10')
        
        # # MA20
        # if 'ma20' in self.df_data.columns:
        #     self.kline_plot_widget.plot(x_axis, self.df_data['ma20'].values, 
        #                             pen=pg.mkPen(color=(0, 0, 255), width=1), name='MA20')
        
        # 设置样式
        self.kline_plot_widget.setXRange(-1, len(self.df_data) + 1, padding=0)
        self.kline_plot_widget.setYRange(data_low * 0.95, data_high * 1.05, padding=0)
        
        # 设置坐标轴颜色
        self.kline_plot_widget.getAxis('left').setPen(QtGui.QColor(110, 110, 110))
        self.kline_plot_widget.getAxis('bottom').setPen(QtGui.QColor(110, 110, 110))
        self.kline_plot_widget.getAxis('left').setTextPen(QtGui.QColor(110, 110, 110))
        self.kline_plot_widget.getAxis('bottom').setTextPen(QtGui.QColor(110, 110, 110))
        
        # 设置X轴标签（显示日期）
        # dates = self.df_data['date'].tolist()
        # if len(dates) > 0:
        #     # 只显示部分日期标签以避免过于拥挤
        #     step = max(1, len(dates) // 10)
        #     date_labels = [(i, str(date)) for i, date in enumerate(dates) if i % step == 0]
        #     axis = self.kline_plot_widget.getAxis('bottom')
        #     axis.setTicks([date_labels])

    def draw_volume(self):
        pass

    def draw_macd(self):
        pass

    def update_info_labels(self):
        pass
