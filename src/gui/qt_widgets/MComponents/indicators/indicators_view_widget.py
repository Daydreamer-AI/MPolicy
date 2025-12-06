from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout
from PyQt5.QtCore import pyqtSlot

import pyqtgraph as pg
import numpy as np
import pandas as pd

from manager.logging_manager import get_logger

from gui.qt_widgets.MComponents.indicators.base_indicator_widget import BaseIndicatorWidget
from gui.qt_widgets.MComponents.indicators.kline_widget import KLineWidget
from gui.qt_widgets.MComponents.indicators.volume_widget import VolumeWidget
from gui.qt_widgets.MComponents.indicators.amount_widget import AmountWidget
from gui.qt_widgets.MComponents.indicators.macd_widget import MacdWidget
from gui.qt_widgets.MComponents.indicators.kdj_widget import KdjWidget
from gui.qt_widgets.MComponents.indicators.rsi_widget import RsiWidget
from gui.qt_widgets.MComponents.indicators.boll_widget import BollWidget

from indicators import stock_data_indicators as sdi

from manager.period_manager import TimePeriod
from manager.bao_stock_data_manager import BaostockDataManager

class IndicatorsViewWidget(QWidget):
    _shared_object_id = 0
    def __init__(self, parent=None):
        super(IndicatorsViewWidget, self).__init__(parent)
        uic.loadUi('./src/gui/qt_widgets/MComponents/indicators/IndicatorsViewWidget.ui', self)

        self.init_para()
        self.init_ui()
        self.init_connect()

    # 清理资源
    def __del__(self):
        self.logger.info(f"开始清理类型{self.type}指标视图及其资源。当前共有{IndicatorsViewWidget._shared_object_id}个对象。")
        IndicatorsViewWidget._shared_object_id -= 1
        self.logger.info(f"清理后共有{IndicatorsViewWidget._shared_object_id}个对象。")

    def init_para(self):
        self.logger = get_logger(__name__)

        self.type = IndicatorsViewWidget._shared_object_id    # type    # 0：行情，1：策略，2：复盘
        IndicatorsViewWidget._shared_object_id += 1

        self.indicator_widgets = {} 
        self.kline_widget = None

        # self.df_data列结构：date, code, name, open, high, low, close, volume, amount, change_percent, turnover_rate, adjustflag, diff, dea, macd, ma5, ma10, ma20, ma24, ma30, ma52, ma60, volume_ratio
        self.df_data = None                 # pd.DataFrame

        self.dict_stock_data = None         # {TimePeriod: DataFrame}，只保存选中code的各个级别的k线数据

    def init_ui(self):
        
        self.period_button_group = QtWidgets.QButtonGroup(self)
        self.period_button_group.addButton(self.btn_time)
        self.period_button_group.addButton(self.btn_1d)
        self.period_button_group.addButton(self.btn_1w)
        self.period_button_group.addButton(self.btn_1m)
        self.period_button_group.addButton(self.btn_5m)
        self.period_button_group.addButton(self.btn_10m)
        self.period_button_group.addButton(self.btn_15m)
        self.period_button_group.addButton(self.btn_30m)
        self.period_button_group.addButton(self.btn_60m)
        self.period_button_group.addButton(self.btn_120m)

        self.btn_time.setEnabled(False)
        self.btn_1m.setEnabled(False)
        self.btn_5m.setEnabled(False)
        self.btn_10m.setEnabled(False)
        self.btn_120m.setEnabled(False)

        # self.init_stock_card_list()

        self.kline_widget = KLineWidget(self.df_data, self.type, self)
        self.verticalLayout.addWidget(self.kline_widget, 3)
        self.btn_indicator_ma.setChecked(True)
        self.kline_widget.show_ma()
        self.kline_widget.set_period("日线")
        self.kline_widget.set_indicator_name("均线")

    def init_connect(self):
        self.period_button_group.buttonClicked.connect(self.slot_period_button_clicked)
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
                # 注意和slot_mouse_moved处理的区别。每个视图的y轴坐标值不一致，所以需要子类重写单独处理。而鼠标移动时，可复用部分代码，所以放在父类中实现，同时抛出全局信号，让子类定制处理
                kline_plot_widget.sigRangeChanged.connect(self.slot_range_changed)
                kline_plot_widget.scene().sigMouseMoved.connect(self.kline_widget.slot_mouse_moved)
                # kline_plot_widget.scene().sigMouseMoved.connect(
                #     lambda pos, widget_source=self.kline_widget: self.slot_mouse_moved(pos, widget_source)
                # )

        self.btn_review.clicked.connect(self.slot_btn_review_clicked)

    def show_period_frame(self, b_show=True):
        if b_show:
            self.frame_period.show()
        else:
            self.frame_period.hide()

    def show_review_btn(self, b_show=True):
        if b_show:
            self.btn_review.show()
        else:
            self.btn_review.hide()

    def get_stock_data_by_period(self, code):
        checked_btn = self.period_button_group.checkedButton()
        if checked_btn is None:
            return pd.DataFrame()
        
        period_text = checked_btn.text()
        time_period = TimePeriod.from_label(period_text)

        if time_period not in self.dict_stock_data:   # 暂无该级别数据
            return pd.DataFrame()
    
        return self.dict_stock_data[time_period]

    def update_stock_data_dict(self, code):
        bao_stock_data_manager = BaostockDataManager()
        df_1d_stock_data = bao_stock_data_manager.get_stock_data_from_db_by_period(code, TimePeriod.DAY)
        df_1w_stock_data = bao_stock_data_manager.get_stock_data_from_db_by_period(code, TimePeriod.WEEK)
        df_15m_stock_data = bao_stock_data_manager.get_stock_data_from_db_by_period(code, TimePeriod.MINUTE_15)
        df_30m_stock_data = bao_stock_data_manager.get_stock_data_from_db_by_period(code, TimePeriod.MINUTE_30)
        df_60m_stock_data = bao_stock_data_manager.get_stock_data_from_db_by_period(code, TimePeriod.MINUTE_60)

        # 直接从数据库中获取的


        self.dict_stock_data = {
            TimePeriod.DAY: df_1d_stock_data,
            TimePeriod.WEEK: df_1w_stock_data,
            TimePeriod.MINUTE_15: df_15m_stock_data,
            TimePeriod.MINUTE_30: df_30m_stock_data,
            TimePeriod.MINUTE_60: df_60m_stock_data
        }

    def show_default_indicator(self):
        self.btn_indicator_volume.setChecked(True)
        self.slot_btn_indicator_volume_clicked()

        self.btn_indicator_macd.setChecked(True)
        self.slot_btn_indicator_macd_clicked()

    def update_chart(self, data):
        code = data['code']
        self.update_stock_data_dict(code)
        self.kline_widget.set_stock_name(data['name'])

        self.df_data = self.get_stock_data_by_period(code)

        if self.df_data is None or self.df_data.empty:  # 获取数据失败
            return

        # if self.kline_widget is None:
        #     self.kline_widget = KLineWidget(self.df_data, self)
        #     self.verticalLayout.addWidget(self.kline_widget, 3)
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
        widget = VolumeWidget(self.df_data, self.type, self)
        return widget

    def draw_amount(self):
        widget = AmountWidget(self.df_data, self.type, self)
        return widget

    def draw_macd(self):
        widget = MacdWidget(self.df_data, self.type, self)
        return widget

    def draw_kdj(self):
        # 因源数据中没有自带KDJ指标，需要手动计算
        if 'K' not in self.df_data.columns or 'D' not in self.df_data.columns or 'J' not in self.df_data.columns:
            sdi.kdj(self.df_data) 

        widget = KdjWidget(self.df_data, self.type, self)
        return widget

    def draw_rsi(self):
        # 因源数据中没有自带RSI指标，需要手动计算
        rsi_columns = ['rsi6', 'rsi12', 'rsi24']
        missing_rsi = [col for col in rsi_columns if col not in self.df_data.columns]
        if missing_rsi:
            sdi.rsi(self.df_data, period=6)   # 计算RSI6
            sdi.rsi(self.df_data, period=12)  # 计算RSI12
            sdi.rsi(self.df_data, period=24)  # 计算RSI24

        widget = RsiWidget(self.df_data, self.type, self)
        return widget

    def draw_boll(self):
        # 因源数据中没有自带BOLL指标，需要手动计算
        boll_columns = ['boll_up', 'boll_mb', 'boll_dn']
        missing_boll = [col for col in boll_columns if col not in self.df_data.columns]
        if missing_boll:
            sdi.boll(self.df_data)

        widget = BollWidget(self.df_data, self.type, self)
        return widget

    def add_indicator_chart(self, indicator_name):
        '''
            动态添加指标图
        '''
        # if self.df_data is None or self.df_data.empty:
        #     # self.logger.warning(f"数据为空，无法添加指标图：{indicator_name}")
        #     return None
        
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
                    kline_plot_widget.setXLink(plot_widget)
        
        self.verticalLayout.addWidget(indicator_widget, 1)

        # 缩放同步和鼠标移动
        plot_widget = indicator_widget.get_plot_widget()
        if plot_widget:
            plot_widget.sigRangeChanged.connect(self.slot_range_changed)
            plot_widget.scene().sigMouseMoved.connect(indicator_widget.slot_mouse_moved)
            # plot_widget.scene().sigMouseMoved.connect(
            #     lambda pos, widget_source=indicator_widget: self.slot_mouse_moved(pos, widget_source)
            # )

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
        self.verticalLayout.removeWidget(widget)
        
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

    def slot_period_button_clicked(self, btn):
        if self.df_data is None or self.df_data.empty:
            self.logger.warning("数据为空，无法切换图表周期数据")
            return
        
        self.kline_widget.set_period(btn.text())
        self.update_chart(self.df_data.iloc[0])

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

    def slot_btn_review_clicked(self):
        from gui.qt_widgets.review.review_dialog import ReviewDialog
        dlg = ReviewDialog()
        dlg.exec()

