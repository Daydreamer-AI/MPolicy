from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout
from PyQt5.QtCore import pyqtSlot

from processor.baostock_processor import BaoStockProcessor

from common.common_api import *
import datetime
from common.logging_manager import get_logger

from gui.qt_widgets.MComponents.candlestick_item import CandlestickItem

from indicators import stock_data_indicators as sdi

import numpy as np
import pyqtgraph as pg
# from gui.qt_widgets.MComponents.custom_date_axisItem import CustomDateAxisItem, NoLabelAxis

from gui.qt_widgets.market.kline_widget import KLineWidget
from gui.qt_widgets.market.volume_widget import VolumeWidget
from gui.qt_widgets.market.amount_widget import AmountWidget
from gui.qt_widgets.market.macd_widget import MacdWidget
from gui.qt_widgets.market.kdj_widget import KdjWidget
from gui.qt_widgets.market.rsi_widget import RsiWidget
from gui.qt_widgets.market.boll_widget import BollWidget

class MarketWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.init_para()
        self.init_ui()
        self.init_connect()

    def init_para(self):
        self.logger = get_logger(__name__)
        self.indicator_widgets = {} 

        # self.df_data列结构：date, code, open, high, low, close, volume, amount, change_percent, turnover_rate, adjustflag, diff, dea, macd, ma5, ma10, ma20, ma24, ma30, ma52, ma60, volume_ratio
        self.df_data = BaoStockProcessor().get_daily_stock_data('sh.600000')    
    def init_ui(self):
        uic.loadUi('./gui/qt_widgets/market/MarketWidget.ui', self)

        self.kline_widget = KLineWidget(self.df_data, self)
        self.verticalLayout_2.addWidget(self.kline_widget, 3)
        self.btn_indicator_ma.setChecked(True)
        self.kline_widget.show_ma()


    def init_connect(self):
        self.btn_indicator_volume.clicked.connect(self.slot_btn_indicator_volume_clicked)
        self.btn_indicator_amount.clicked.connect(self.slot_btn_indicator_amount_clicked)
        self.btn_indicator_macd.clicked.connect(self.slot_btn_indicator_macd_clicked)
        self.btn_indicator_kdj.clicked.connect(self.slot_btn_indicator_kdj_clicked)
        self.btn_indicator_rsi.clicked.connect(self.slot_btn_indicator_rsi_clicked)
        self.btn_indicator_boll.clicked.connect(self.slot_btn_indicator_boll_clicked)

        self.btn_indicator_ma.clicked.connect(self.slot_btn_indicator_ma_clicked)

        kline_plot_widget = self.kline_widget.get_plot_widget()
        if kline_plot_widget:
            kline_plot_widget.sigRangeChanged.connect(self.slot_range_changed)


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
        # 因源数据中没有自带KDJ指标，需要手动计算
        if 'K' not in self.df_data.columns or 'D' not in self.df_data.columns or 'J' not in self.df_data.columns:
            sdi.kdj(self.df_data) 

        widget = KdjWidget(self.df_data, self)
        return widget

    def draw_rsi(self):
        # 因源数据中没有自带RSI指标，需要手动计算
        rsi_columns = ['rsi6', 'rsi12', 'rsi24']
        missing_rsi = [col for col in rsi_columns if col not in self.df_data.columns]
        if missing_rsi:
            sdi.rsi(self.df_data, period=6)   # 计算RSI6
            sdi.rsi(self.df_data, period=12)  # 计算RSI12
            sdi.rsi(self.df_data, period=24)  # 计算RSI24

        widget = RsiWidget(self.df_data, self)
        return widget

    def draw_boll(self):
        # 因源数据中没有自带BOLL指标，需要手动计算
        boll_columns = ['boll_up', 'boll_mb', 'boll_dn']
        missing_boll = [col for col in boll_columns if col not in self.df_data.columns]
        if missing_boll:
            sdi.boll(self.df_data)

        widget = BollWidget(self.df_data, self)
        return widget

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
                kline_plot_widget = self.kline_widget.get_plot_widget()
                if kline_plot_widget:
                    plot_widget.setXLink(kline_plot_widget)
        
        self.verticalLayout_2.addWidget(indicator_widget, 1)

        # 缩放同步
        plot_widget = indicator_widget.get_plot_widget()
        if plot_widget:
            plot_widget.sigRangeChanged.connect(self.slot_range_changed)

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

    def slot_btn_indicator_boll_clicked(self):
        is_checked = self.btn_indicator_boll.isChecked()
        if is_checked:
            self.add_indicator_chart('BOLL')
        else:
            self.remove_indicator_chart('BOLL')

    def slot_btn_indicator_ma_clicked(self):
        is_checked = self.btn_indicator_ma.isChecked()
        self.kline_widget.show_ma(is_checked)

    def slot_range_changed(self):
        '''
            当任何指标图的plot_widget的X轴范围改变时调用
        '''
        self.kline_widget.slot_range_changed()

        # 同步所有指标图表
        for indicator_name, widget in self.indicator_widgets.items():
            widget.slot_range_changed()

