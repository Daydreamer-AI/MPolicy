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

        self.label_ma20.hide()
        self.label_ma30.hide()
        self.label_ma60.hide()

        # # k线图中的概览标签
        # main_viewbox = self.plot_widget.getViewBox()
        # self.label_overview = pg.TextItem("", anchor=(0, 0.5))
        # self.label_overview.setZValue(1000)
        
        # font = pg.QtGui.QFont("Arial", 10, pg.QtGui.QFont.Bold)
        # self.label_overview.setFont(font)
        
        # main_viewbox.addItem(self.label_overview, ignoreBounds=True)
        # self.label_overview.hide()

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
    
    def reset_labels(self):
        # self.label_ma_period.setText("")      # 选中周期时设置
        self.label_stock_name.setText("")   # 点击卡片Item时，根据当前选中的股票设置
        self.label_ma5.setText(f"MA5: ")
        self.label_ma10.setText(f"MA10: ")
        self.label_ma20.setText(f"MA20: ")
        self.label_ma24.setText(f"MA24: ")
        self.label_ma30.setText(f"MA30: ")
        self.label_ma52.setText(f"MA52: ")
        self.label_ma60.setText(f"MA60: ")

    # def update_labels(self, closest_index):
    #     self.label_ma5.setText(f"MA5:{self.df_data.iloc[closest_index]['ma5']:.2f}")
    #     self.label_ma10.setText(f"MA10:{self.df_data.iloc[closest_index]['ma10']:.2f}")
    #     self.label_ma20.setText(f"MA20:{self.df_data.iloc[closest_index]['ma20']:.2f}")
    #     self.label_ma24.setText(f"MA24:{self.df_data.iloc[closest_index]['ma24']:.2f}")
    #     self.label_ma30.setText(f"MA30:{self.df_data.iloc[closest_index]['ma30']:.2f}")
    #     self.label_ma52.setText(f"MA52:{self.df_data.iloc[closest_index]['ma52']:.2f}")
    #     self.label_ma60.setText(f"MA60:{self.df_data.iloc[closest_index]['ma60']:.2f}")
    
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
        return "K线图"
    
    def is_ma_show(self):
        return self.item.is_ma_show() if self.item else False
    
    def show_ma(self, b_show=True):
        if self.item:
            self.item.show_ma(b_show)

    def set_period(self, period):
        self.label_ma_period.setText(period)

    def set_stock_name(self, stock_name):
        self.label_stock_name.setText(stock_name)

    def get_overview_text_with_style(self, index, y_val):
        '''获取概览标签的文本，并设置样式'''
        row = self.df_data.iloc[index]
        date = row
        open = row['open']
        close = row['close']
        high = row['high']
        low = row['low']
        change_percent = row['change_percent']
        amplitude = (high - low) / low * 100
        volume = row['volume'] / 10000      # 单位：万
        amount = row['amount'] / 100000000  # 单位：亿
        turnover_rate = row['turnover_rate']


        label_text = f"日期: {date}<br>数值：{y_val:.2f}%<br>开盘：{open:.2f} <br>收盘: {close:.2f} \
            <br>最高: {high:.2f} <br>最低: {low:.2f}<br>涨跌幅: {change_percent}<br>振幅: {amplitude}<br>成交量：{volume:.2f}万<br>成交额{amount}亿<br>换手率{turnover_rate}%"
        
        text_with_style = '<div style="color: black; background-color: white; border: 3px solid black; padding: 2px;">{}</div>'.format(label_text)
        return text_with_style
    
    def show_overview_label(self, index, y_val, bool_show=True):
        if bool_show:
            
            text_with_style = self.get_overview_text_with_style(index, y_val)
            # self.logger.info(f"显示概览标签：\n{text_with_style}")
            self.label_overview.setHtml(text_with_style)
            self.label_overview.show()
        else:
            self.label_overview.hide()
            self.logger.info("隐藏概览标签")

    def hide_overview_label(self):
        self.label_overview.hide()

    def set_indicator_name(self, indicator_name):
        self.label_indicator.setText(indicator_name)

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

    # def slot_mouse_moved(self, pos, widget_source=None):
    #     if self.plot_widget.sceneBoundingRect().contains(pos):
    #         mouse_point = self.plot_widget.getViewBox().mapSceneToView(pos)
    #         x_val = mouse_point.x()
    #         y_val = mouse_point.y()

    #         # self.logger.info(f"鼠标位置：x={x_val}, y={y_val}")

    #         bar_centers = list(range(len(self.df_data)))
            
    #         closest_index = None
    #         min_distance = float('inf')
            
    #         for i, center in enumerate(bar_centers):
    #             distance = abs(center - x_val)
    #             if distance <= 0.25 / 2:
    #                 if distance < min_distance:
    #                     min_distance = distance
    #                     closest_index = i
            
    #         if closest_index is not None:
    #             view_range = self.plot_widget.getViewBox().viewRange()
    #             closest_x = bar_centers[closest_index]

    #             widget_source_plot_widget = widget_source.get_plot_widget()
    #             if widget_source_plot_widget is not None and widget_source_plot_widget == self.plot_widget:
    #                 self.h_line.setPos(y_val)
    #                 self.h_line.show()

    #             if widget_source is not None:
    #                 self.logger.info(f"正在处理{self.get_chart_name()}鼠标移动响应，来源：{widget_source.get_chart_name()}")

    #             self.v_line.setPos(closest_x)
    #             self.v_line.show()
                

    #         # else:
    #         #     self.hide_all_labels()
    #     else:
    #         self.hide_all_labels()

    def slot_golbal_update_labels(self, closest_index):
        # 设置MA值
        # self.label_ma_period.setText("日线")      # 点击卡片Item时，根据当前选中的周期设置
        # self.label_stock_name.setText("股票名称")   # 点击卡片Item时，根据当前选中的股票设置
        self.label_ma5.setText(f"MA5:{self.df_data.iloc[closest_index]['ma5']:.2f}")
        self.label_ma10.setText(f"MA10:{self.df_data.iloc[closest_index]['ma10']:.2f}")
        self.label_ma20.setText(f"MA20:{self.df_data.iloc[closest_index]['ma20']:.2f}")
        self.label_ma24.setText(f"MA24:{self.df_data.iloc[closest_index]['ma24']:.2f}")
        self.label_ma30.setText(f"MA30:{self.df_data.iloc[closest_index]['ma30']:.2f}")
        self.label_ma52.setText(f"MA52:{self.df_data.iloc[closest_index]['ma52']:.2f}")
        self.label_ma60.setText(f"MA60:{self.df_data.iloc[closest_index]['ma60']:.2f}")
            
    def slot_global_show_overview_label(self, index, y_val, x_pos, y_pos, bool_show=True):
        # self.logger.info(f"正在处理{self.get_chart_name()}全局显示数据标签，位置：{x_pos}, 数据索引：{index}, 数据值：{y_val}，是否显示：{bool_show}")
        # 不能在子类中通过self.plot_widget.getViewBox().viewRange() 计算显示位置。

        # self.label_overview.setPos(x_pos, y_pos)
        # view_range = self.plot_widget.getViewBox().viewRange()
        # x_pos_2 = view_range[0][1]
        # y_pos_2 = view_range[1][1]
        # self.logger.info(f"全局显示数据标签位置：{x_pos}, {y_pos}")
        # self.logger.info(f"子类计算出的数据标签位置：{x_pos_2}, {y_pos_2}")
        self.label_overview.setPos(x_pos, y_pos)
        # if x_pos is not None and index is not None:
        #     view_range = self.plot_widget.getViewBox().viewRange()
        #     # self.logger.info(f"view_range:\n{view_range}")
        #     x_view_center = abs(view_range[0][0] - view_range[0][1]) / 2
        #     y_view_center = abs(view_range[1][0] - view_range[1][1]) / 2 
        #     self.logger.info(f"x_view_center:{x_view_center}, y_view_center:{y_view_center}")
        #     self.label_overview.setPos(x_view_center, y_view_center)
        #     # if x_pos >= len(self.df_data) - 3:
        #     #     self.label_overview.setPos(x_view_center, y_view_center)    # view_range[0][0], view_range[1][1]
        #     # else:
        #     #     self.label_overview.setPos(x_view_center, y_view_center)    # view_range[0][1], view_range[1][1]

        self.show_overview_label(index, y_val, bool_show)

