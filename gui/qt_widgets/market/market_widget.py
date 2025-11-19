from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout
from PyQt5.QtCore import pyqtSlot

from processor.baostock_processor import BaoStockProcessor

from common.common_api import *
import datetime
from common.logging_manager import get_logger

from gui.qt_widgets.MComponents.candlestick_item import CandlestickItem
from gui.qt_widgets.MComponents.volume_item import VolumeItem
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
        self.other_indicator_widgets = {} 

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
        self.kline_plot_widget.hideAxis('bottom')
        self.kline_plot_widget.getAxis('left').setWidth(60)
        self.kline_plot_widget.setBackground('w')
        # self.kline_plot_widget.setLabel('left', 'Price')
        # self.kline_plot_widget.setLabel('bottom', 'Time')
        self.kline_plot_widget.showGrid(x=True, y=True)
        self.kline_plot_widget.setMouseEnabled(x=True, y=False)
        widget_k_line_layout.addWidget(self.kline_plot_widget)


        volume_widget_layout = self.widget_volume.layout()
        if volume_widget_layout is None:
            self.widget_volume.setLayout(QVBoxLayout())
        self.volume_plot_widget = pg.PlotWidget()
        self.volume_plot_widget.hideAxis('bottom')
        self.volume_plot_widget.getAxis('left').setWidth(60)
        self.volume_plot_widget.setBackground('w')
        self.volume_plot_widget.showGrid(x=True, y=True)
        self.volume_plot_widget.setMouseEnabled(x=True, y=False)
        volume_widget_layout.addWidget(self.volume_plot_widget)

        self.volume_plot_widget.setXLink(self.kline_plot_widget)


    def init_connect(self):
        pass

    def draw_charts(self):
        # ."绘制所有图表…
        self.draw_kline()
        self.draw_volume()
        # self.draw_macd()
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
        
        # 设置样式
        self.kline_plot_widget.setXRange(-1, len(self.df_data) + 1, padding=0)
        self.kline_plot_widget.setYRange(data_low * 0.95, data_high * 1.05, padding=0)
        
        # 设置坐标轴颜色
        self.kline_plot_widget.getAxis('left').setPen(QtGui.QColor(110, 110, 110))
        self.kline_plot_widget.getAxis('bottom').setPen(QtGui.QColor(110, 110, 110))
        self.kline_plot_widget.getAxis('left').setTextPen(QtGui.QColor(110, 110, 110))
        self.kline_plot_widget.getAxis('bottom').setTextPen(QtGui.QColor(110, 110, 110))

    def draw_volume(self):
        # ""绘制交易量图
        self.volume_plot_widget.clear()

        # 检查是否有数据
        if self.df_data is None or self.df_data.empty:
            return
        
        # 确保数据列存在
        required_columns = ['open', 'close', 'volume']
        if not all(col in self.df_data.columns for col in required_columns):
            self.logger.warning("缺少必要的数据列来绘制K线图")
            return

        # 创建交易量图
        vol_item = VolumeItem(self.df_data)

        self.volume_plot_widget.addItem(vol_item)

        #设置坐标范围
        self.volume_plot_widget.setXRange(-1, len(self.df_data) + 1, padding=0)
        max_vol = np.max(self.df_data['volume'])
        self.volume_plot_widget.setYRange(0, max_vol * 1.1, padding=0)

        #设置坐标轴颜色
        self.volume_plot_widget.getAxis('left').setPen(QtGui.QColor(110, 110, 110))
        self.volume_plot_widget.getAxis('bottom').setPen(QtGui.QColor(110, 110, 110))
        self.volume_plot_widget.getAxis('left').setTextPen(QtGui.QColor(110, 110, 110))
        self.volume_plot_widget.getAxis('bottom').setTextPen(QtGui.QColor(110, 110, 110))

    def draw_amount(self, plot_widget):
        pass

    def draw_macd(self, plot_widget):
        pass

    def draw_kdj(self, plot_widget):
        pass

    def draw_rsi(self, plot_widget):
        pass

    def draw_boll(self, plot_widget):
        pass

    def update_info_labels(self):
        pass

    def add_indicator_chart(self, indicator_name):
        '''
            动态添加指标图
        '''
        # 先检查是否支持该指标
        supported_indicators = ['成交额', 'MACD', 'KDJ', 'RSI', 'BOLL']
        if indicator_name not in supported_indicators:
            self.logger.warning(f"不支持的指标：{indicator_name}")
            return None
        
        # 检查是否已经添加了该指标
        if indicator_name in self.other_indicator_widgets:
            self.logger.info(f"指标 {indicator_name} 已经存在")
            return self.indicator_widgets[indicator_name]

        plot_widget = pg.PlotWidget()
        plot_widget.hideAxis('bottom')
        plot_widget.getAxis('left').setWidth(60)
        plot_widget.setBackground('w')
        plot_widget.showGrid(x=True, y=True)
        plot_widget.setMouseEnabled(x=True, y=False)
        plot_widget.setXLink(self.kline_plot_widget)

        if indicator_name == '成交额':
            self.draw_amount(plot_widget)
        elif indicator_name == 'MACD':
            self.draw_macd(plot_widget)
        elif indicator_name == 'KDJ':
            self.draw_kdj(plot_widget)
        elif indicator_name == 'RSI':
            self.draw_rsi(plot_widget)
        elif indicator_name == 'BOLL':
            self.draw_boll(plot_widget)
        else:
            self.logger.warning(f"不支持的指标：{indicator_name}")
            # 释放PlotWidget

        self.verticalLayout_2.addWidget(plot_widget, 1)

        # 保存图表引用
        self.other_indicator_widgets[indicator_name] = plot_widget
        return plot_widget

    def remove_indicator_chart(self, indicator_name):
        '''
            移除动态添加的指标图
        '''
        # 检查指标是否存在
        if indicator_name not in self.other_indicator_widgets:
            self.logger.warning(f"指标 {indicator_name} 不存在")
            return False

        # 获取要移除的widget
        plot_widget = self.other_indicator_widgets[indicator_name]
        
        # 从布局中移除
        self.verticalLayout_2.removeWidget(plot_widget)
        
        # 隐藏并删除widget
        plot_widget.setParent(None)
        plot_widget.deleteLater()
        
        # 从字典中移除引用
        del self.other_indicator_widgets[indicator_name]
        
        self.logger.info(f"成功移除指标 {indicator_name}")
        return True

    def remove_all_indicator_charts(self):
        '''
            移除所有动态添加的指标图
        '''
        # 创建指标名称列表的副本，因为我们在迭代过程中会修改原字典
        indicator_names = list(self.other_indicator_widgets.keys())
        
        for indicator_name in indicator_names:
            self.remove_indicator_chart(indicator_name)
        
        self.logger.info("成功移除所有指标图表")