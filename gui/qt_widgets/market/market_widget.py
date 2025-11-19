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
# from gui.qt_widgets.MComponents.custom_date_axisItem import CustomDateAxisItem, NoLabelAxis
from gui.qt_widgets.market.volume_widget import VolumeWidget
from gui.qt_widgets.market.amount_widget import AmountWidget
from gui.qt_widgets.market.macd_widget import MacdWidget

class MarketWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.init_para()
        self.init_ui()
        self.init_connect()

        self.draw_charts()

    def init_para(self):
        self.logger = get_logger(__name__)
        self.indicator_widgets = {} 

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


    def init_connect(self):
        self.btn_indicator_volume.clicked.connect(self.slot_btn_indicator_volume_clicked)
        self.btn_indicator_amount.clicked.connect(self.slot_btn_indicator_amount_clicked)
        self.btn_indicator_macd.clicked.connect(self.slot_btn_indicator_macd_clicked)
        self.btn_indicator_kdj.clicked.connect(self.slot_btn_indicator_kdj_clicked)
        self.btn_indicator_rsi.clicked.connect(self.slot_btn_indicator_rsi_clicked)

    def draw_charts(self):
        # ."绘制所有图表…
        self.draw_kline()
        # self.draw_volume()
        # self.draw_macd()
        # self.update_info_labels()


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
        widget = VolumeWidget(self.df_data, self)
        return widget

    def draw_amount(self):
        widget = AmountWidget(self.df_data, self)
        return widget

    def draw_macd(self):
        widget = MacdWidget(self.df_data, self)
        return widget

    def draw_kdj(self):
        pass

    def draw_rsi(self):
        pass

    def draw_boll(self):
        pass

    def update_info_labels(self):
        pass

    def add_indicator_chart(self, indicator_name):
        '''
            动态添加指标图
        '''
        # 先检查是否支持该指标
        supported_indicators = ['成交量', '成交额', 'MACD', 'KDJ', 'RSI', 'BOLL']
        if indicator_name not in supported_indicators:
            self.logger.warning(f"不支持的指标：{indicator_name}")
            return None
        
        # 检查是否已经添加了该指标
        if indicator_name in self.indicator_widgets:
            self.logger.info(f"指标 {indicator_name} 已经存在")
            return self.indicator_widgets[indicator_name]

        indicator_widget = None
        if indicator_name == '成交量':
            indicator_widget = self.draw_volume()
        elif indicator_name == '成交额':
            indicator_widget = self.draw_amount()
        elif indicator_name == 'MACD':
            indicator_widget = self.draw_macd()
        elif indicator_name == 'KDJ':
            indicator_widget = self.draw_kdj()
        elif indicator_name == 'RSI':
            indicator_widget = self.draw_rsi()
        elif indicator_name == 'BOLL':
            indicator_widget = self.draw_boll()
        else:
            self.logger.warning(f"不支持的指标：{indicator_name}")

        # 检查是否成功创建了widget
        if indicator_widget is None:
            self.logger.warning(f"无法创建指标 {indicator_name} 的图表")
            return None

         # 设置图表属性以保持一致性
        if hasattr(indicator_widget, 'get_plot_widget'):
            plot_widget = indicator_widget.get_plot_widget()
            if plot_widget:
                plot_widget.getAxis('left').setWidth(60)
                plot_widget.setXLink(self.kline_plot_widget)
        
        self.verticalLayout_2.addWidget(indicator_widget, 1)

        # 保存图表引用
        self.indicator_widgets[indicator_name] = indicator_widget
        return indicator_widget

    def remove_indicator_chart(self, indicator_name):
        '''
            移除动态添加的指标图
        '''
        # 检查指标是否存在
        if indicator_name not in self.indicator_widgets:
            self.logger.warning(f"指标 {indicator_name} 不存在")
            return False

        # 获取要移除的widget
        widget = self.indicator_widgets[indicator_name]
        
        # 从布局中移除
        self.verticalLayout_2.removeWidget(widget)
        
        # 隐藏并删除widget
        widget.setParent(None)
        widget.deleteLater()
        
        # 从字典中移除引用
        del self.indicator_widgets[indicator_name]
        
        self.logger.info(f"成功移除指标 {indicator_name}")
        return True

    def remove_all_indicator_charts(self):
        '''
            移除所有动态添加的指标图
        '''
        # 创建指标名称列表的副本，因为我们在迭代过程中会修改原字典
        indicator_names = list(self.indicator_widgets.keys())
        
        for indicator_name in indicator_names:
            self.remove_indicator_chart(indicator_name)
        
        self.logger.info("成功移除所有指标图表")


    # ----------------------槽函数-------------------------
    def slot_btn_indicator_volume_clicked(self):
        is_checked = self.btn_indicator_volume.isChecked()
        if is_checked:
            self.add_indicator_chart('成交量')
        else:
            self.remove_indicator_chart('成交量')

    def slot_btn_indicator_amount_clicked(self):
        is_checked = self.btn_indicator_amount.isChecked()
        if is_checked:
            self.add_indicator_chart('成交额')
        else:
            self.remove_indicator_chart('成交额')

    def slot_btn_indicator_macd_clicked(self):
        is_checked = self.btn_indicator_macd.isChecked()
        if is_checked:
            self.add_indicator_chart('MACD')
        else:
            self.remove_indicator_chart('MACD')

    def slot_btn_indicator_kdj_clicked(self):
        is_checked = self.btn_indicator_kdj.isChecked()
        if is_checked:
            self.add_indicator_chart('KDJ')
        else:
            self.remove_indicator_chart('KDJ')

    def slot_btn_indicator_rsi_clicked(self):
        is_checked = self.btn_indicator_rsi.isChecked()
        if is_checked:
            self.add_indicator_chart('RSI')
        else:
            self.remove_indicator_chart('RSI')