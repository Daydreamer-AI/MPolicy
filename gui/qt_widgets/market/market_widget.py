from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout
from PyQt5.QtCore import pyqtSlot, QTimer

from processor.baostock_processor import BaoStockProcessor

from common.common_api import *
import datetime
from common.logging_manager import get_logger

from indicators import stock_data_indicators as sdi

import numpy as np
import pyqtgraph as pg

from gui.qt_widgets.market.kline_widget import KLineWidget
from gui.qt_widgets.market.volume_widget import VolumeWidget
from gui.qt_widgets.market.amount_widget import AmountWidget
from gui.qt_widgets.market.macd_widget import MacdWidget
from gui.qt_widgets.market.kdj_widget import KdjWidget
from gui.qt_widgets.market.rsi_widget import RsiWidget
from gui.qt_widgets.market.boll_widget import BollWidget

from gui.qt_widgets.MComponents.stock_card_widget import StockCardWidget

class MarketWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.init_para()
        self.init_ui()
        self.init_connect()

    def init_para(self):
        self.logger = get_logger(__name__)
        self.indicator_widgets = {} 
        self.kline_widget = None

        # self.df_data列结构：date, code, open, high, low, close, volume, amount, change_percent, turnover_rate, adjustflag, diff, dea, macd, ma5, ma10, ma20, ma24, ma30, ma52, ma60, volume_ratio
        self.df_data = None #BaoStockProcessor().get_daily_stock_data('sh.600000')    
        self.dict_daily_stock_data = BaoStockProcessor().get_all_daily_stock_data_dict_readonly()
        self.dict_weekly_stock_data = BaoStockProcessor().get_all_weekly_stock_data_dict_readonly()
    def init_ui(self):
        uic.loadUi('./gui/qt_widgets/market/MarketWidget.ui', self)

        self.init_stock_card_list()

        self.kline_widget = KLineWidget(self.df_data, self)
        self.verticalLayout_2.addWidget(self.kline_widget, 3)
        self.btn_indicator_ma.setChecked(True)
        self.kline_widget.show_ma()
        self.kline_widget.auto_scale_to_latest()


    def init_stock_card_list(self):
        self.listWidget_card.clear()

        first_item_data = None  # 保存第一个item的数据
        for code, df_data in self.dict_daily_stock_data.items():
            # 确保数据不为空
            if df_data.empty:
                continue

            row = df_data.iloc[-1]
            stock_card_widget = StockCardWidget(2)
            stock_card_widget.set_data(row)
            stock_card_widget.update_ui()

            stock_card_widget.clicked.connect(self.slot_stock_card_clicked)
            # stock_card_widget.hovered.connect(self.slot_stock_card_hovered)
            # stock_card_widget.hoverLeft.connect(self.slot_stock_card_hover_left)
            # stock_card_widget.doubleClicked.connect(self.slot_stock_card_double_clicked)

            item = QtWidgets.QListWidgetItem()
            item.setSizeHint(stock_card_widget.sizeHint())
            
            self.listWidget_card.addItem(item)

            self.listWidget_card.setItemWidget(item, stock_card_widget)

            # 保存第一个item的数据
            if first_item_data is None:
                first_item_data = row

        # 如果有数据，自动选择第一个item（使用定时器延迟执行）
        if first_item_data is not None:
            # 使用单次定时器确保UI完全初始化后再执行
            QTimer.singleShot(100, lambda: self.select_first_item(first_item_data))

    def init_connect(self):
        self.btn_indicator_volume.clicked.connect(self.slot_btn_indicator_volume_clicked)
        self.btn_indicator_amount.clicked.connect(self.slot_btn_indicator_amount_clicked)
        self.btn_indicator_macd.clicked.connect(self.slot_btn_indicator_macd_clicked)
        self.btn_indicator_kdj.clicked.connect(self.slot_btn_indicator_kdj_clicked)
        self.btn_indicator_rsi.clicked.connect(self.slot_btn_indicator_rsi_clicked)
        self.btn_indicator_boll.clicked.connect(self.slot_btn_indicator_boll_clicked)

        self.btn_indicator_ma.clicked.connect(self.slot_btn_indicator_ma_clicked)

        if self.kline_widget is not None:
            kline_plot_widget = self.kline_widget.get_plot_widget()
            if kline_plot_widget:
                kline_plot_widget.sigRangeChanged.connect(self.slot_range_changed)

    def select_first_item(self, first_item_data):
        """选择第一个item的独立方法"""
        # 设置列表选中第一个
        self.listWidget_card.setCurrentRow(0)

        # 调用槽函数
        self.slot_stock_card_clicked(first_item_data)

    def update_chart(self, data):

        # self.df_data = BaoStockProcessor().get_daily_stock_data('sh.600004')  
        # self.logger.info(f"更新数据：\n{self.df_data.tail(1)}")
        # self.kline_widget.update_data(self.df_data)
        # return  

        code = data['code']
        self.df_data = BaoStockProcessor().get_daily_stock_data(code)
        self.logger.info(f"self.df_data类型：{type(self.df_data)}")

        # if self.kline_widget is None:
        #     self.kline_widget = KLineWidget(self.df_data, self)
        #     self.verticalLayout_2.addWidget(self.kline_widget, 3)
        #     self.btn_indicator_ma.setChecked(True)
        #     self.kline_widget.show_ma()

        #     kline_plot_widget = self.kline_widget.get_plot_widget()
        #     if kline_plot_widget:
        #         kline_plot_widget.sigRangeChanged.connect(self.slot_range_changed)
        
        self.kline_widget.update_data(self.df_data)

        is_ma_checked = self.btn_indicator_ma.isChecked()
        self.kline_widget.show_ma(is_ma_checked)

        is_volume_checked = self.btn_indicator_volume.isChecked()
        if is_volume_checked:
            # self.add_indicator_chart('成交量')
            volume_widget = self.indicator_widgets['成交量']
            if volume_widget is None:
                self.btn_indicator_volume.setChecked(False)
            else:
                volume_widget.update_data(self.df_data)
            

        is_amount_checked = self.btn_indicator_amount.isChecked()
        if is_amount_checked:
            # self.add_indicator_chart('成交额')
            amount_widget = self.indicator_widgets['成交额']
            if amount_widget is None:
                self.btn_indicator_amount.setChecked(False)
            else:
                amount_widget.update_data(self.df_data)

        is_macd_checked = self.btn_indicator_macd.isChecked()
        if is_macd_checked:
            # self.add_indicator_chart('MACD')
            macd_widget = self.indicator_widgets['MACD']
            if macd_widget is None:
                self.btn_indicator_macd.setChecked(False)
            else:
                macd_widget.update_data(self.df_data)

        is_kdj_checked = self.btn_indicator_kdj.isChecked()
        if is_kdj_checked:
            # self.add_indicator_chart('KDJ')
            kdj_widget = self.indicator_widgets['KDJ']
            if kdj_widget is None:
                self.btn_indicator_kdj.setChecked(False)
            else:
                kdj_widget.update_data(self.df_data)

        is_rsi_checked = self.btn_indicator_rsi.isChecked()
        if is_rsi_checked:
            # self.add_indicator_chart('RSI')
            rsi_widget = self.indicator_widgets['RSI']
            if rsi_widget is None:
                self.btn_indicator_rsi.setChecked(False)
            else:
                rsi_widget.update_data(self.df_data)

        is_boll_checked = self.btn_indicator_boll.isChecked()
        if is_boll_checked:
            # self.add_indicator_chart('BOLL')
            boll_widget = self.indicator_widgets['BOLL']
            if boll_widget is None:
                self.btn_indicator_boll.setChecked(False)
            else:
                boll_widget.update_data(self.df_data)

        self.kline_widget.auto_scale_to_latest()

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
    def slot_stock_card_clicked(self, data):
        '''
            点击股票列表中的股票时，更新图表
            data: pandas Series
        '''
        # self.logger.info(f"点击的股票数据为：{data}")
        self.update_chart(data)

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

