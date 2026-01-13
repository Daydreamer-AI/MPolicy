import pyqtgraph as pg
from pyqtgraph import DateAxisItem
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from PyQt5.QtCore import QDateTime, Qt, pyqtSlot, QPointF, QTimer

from gui.qt_widgets.MComponents.custom_date_axisItem import CustomDateAxisItem, NoLabelAxis

from manager.logging_manager import get_logger


class BoardChangePercentChartWidget(QWidget):
    def __init__(self, type=0):
        super().__init__()
        self.logger = get_logger(__name__)
        self.x_positions = []

        self.board_type = type
        self.setup_ui()
        
    def setup_ui(self):
        self.setMinimumSize(1366, 768)
        layout = QVBoxLayout(self)
        
        self.date_axis_main = NoLabelAxis(orientation='bottom')
        self.plot_widget = pg.PlotWidget(axisItems={'bottom': self.date_axis_main})
        # self.plot_widget = pg.PlotWidget()
        layout.addWidget(self.plot_widget)
        
        self.setup_plot_style()

    def setup_plot_style(self):
        # 主图表样式设置
        self.plot_widget.setBackground('w')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.addLegend()
        self.plot_widget.setMouseEnabled(x=False, y=False)
        
        # 初始化主图表十字线
        self.v_line_main = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('#808286', width=2, style=Qt.DashLine))
        self.h_line_main = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('#808286', width=2, style=Qt.DashLine))
        self.v_line_main.setZValue(1000)
        self.h_line_main.setZValue(1000)
        
        main_viewbox = self.plot_widget.getViewBox()
        # 明确添加到主视图
        main_viewbox.addItem(self.v_line_main, ignoreBounds=True)
        main_viewbox.addItem(self.h_line_main, ignoreBounds=True)
        
        # 初始化主图表标签（优化样式）
        self.label_main = pg.TextItem("", anchor=(0, 1))
        self.label_main.setZValue(1000)
        font = pg.QtGui.QFont("Arial", 10, pg.QtGui.QFont.Bold)
        self.label_main.setFont(font)
        main_viewbox.addItem(self.label_main, ignoreBounds=True)

        self.label_main_2 = pg.TextItem("", anchor=(0, 1))
        self.label_main_2.setZValue(1000)
        font = pg.QtGui.QFont("Arial", 10, pg.QtGui.QFont.Bold)
        self.label_main_2.setFont(font)
        main_viewbox.addItem(self.label_main_2, ignoreBounds=True)
        
        # 主图表左y轴标签
        self.left_y_label_main = pg.TextItem("", anchor=(0, 0.5))  # 左侧Y轴标签
        self.left_y_label_main.setZValue(1000)
        self.left_y_label_main.setFont(pg.QtGui.QFont("Arial", 9))
        self.left_y_label_main.setColor(pg.QtGui.QColor(255, 0, 0))  # 红色
        
        main_viewbox.addItem(self.left_y_label_main, ignoreBounds=True)
        
        # 主图x轴标签
        self.x_label_main = pg.TextItem("", anchor=(0.5, 1))  # X轴标签
        self.x_label_main.setZValue(1000)
        self.x_label_main.setFont(pg.QtGui.QFont("Arial", 9))
        self.x_label_main.setColor(pg.QtGui.QColor(0, 0, 0))  # 黑色
        
        main_viewbox.addItem(self.x_label_main, ignoreBounds=True)
        
        # 隐藏主图表的十字线和标签
        self.hide_all_labels()

        # 连接信号
        self.plot_widget.sigRangeChanged.connect(self.on_range_changed)
        self.plot_widget.scene().sigMouseMoved.connect(self.on_mouse_move)

    def hide_all_labels(self):
        self.v_line_main.hide()
        self.h_line_main.hide()
        self.label_main.hide()
        self.label_main_2.hide()
        self.left_y_label_main.hide()
        # self.right_y_label_main.hide()
        self.x_label_main.hide()

    def draw_chart(self, data, top=20, show_type=0):
        self.show_type = show_type
        # 正确获取数据中的日期信息
        if 'date' in data.columns and not data.empty:
            # 获取数据中的唯一日期
            self.data_dates = data['date'].unique().tolist()
            # 或者获取第一条数据的日期
            self.chart_date = data['date'].iloc[0]
            self.logger.info(f"获取唯一日期成功：{self.chart_date}")
        else:
            self.chart_date = None
            self.data_dates = []
            self.logger.error(f"未获取到唯一日期！")
            return False

        if self.board_type == 0:
            s_board_name = "industry_name"
            s_board_type = "行业板块"
            if show_type == 0:
                field_name = "change_percent"
                display_name = "涨跌幅"
                self.bottom_10 = data.nsmallest(top, field_name)
            elif show_type == 1:
                field_name = "total_amount"
                display_name = "成交额"
                self.bottom_10 = None

            self.top_10 = data.nlargest(top, field_name)
            
        else:
            s_board_name = "concept_name"
            s_board_type = "概念板块"

            if show_type == 0:
                field_name = "board_change_percent"
                display_name = "涨跌幅"
                self.bottom_10 = data.nsmallest(top, field_name)  
            elif show_type == 1:
                field_name = "turnover"
                display_name = "成交额"
                self.bottom_10 = None
            
                self.logger.info(f"data.columns: {data.columns}")

            self.top_10 = data.nlargest(top, field_name)
            

        if field_name not in data.columns:
            self.logger.error(f"{field_name}字段不存在于数据中！")
            return False
        
        self.data = data
        # 清除之前的绘图
        self.plot_widget.clear()
        # board_name = getattr(data, s_board_name, None)

        if show_type == 0:
            self.draw_change_percent_chart(s_board_type, s_board_name, top, field_name)
        elif show_type == 1:
            self.draw_amount_chart(s_board_type, s_board_name, top, field_name)


        return True
    
    def draw_change_percent_chart(self, s_board_type, s_board_name, top, field_name):
                
        self.plot_widget.setTitle(f"{s_board_type} 涨跌幅 Top {top}", color='#008080', size='12pt')

        # 创建x轴位置（共10个位置，每个位置绘制两个柱子）
        self.x_positions = list(range(top))
        self.bar_width = 0.6
        
        # 获取涨幅和跌幅数据
        top_values = self.top_10[field_name].values
        bottom_values = self.bottom_10[field_name].values
        
        top_bars = pg.BarGraphItem(
            x=self.x_positions, 
            height=top_values, 
            width=self.bar_width, 
            brush=pg.mkBrush(255, 0, 0, 150),  # 红色半透明
            pen=pg.mkPen('k', width=0.5)
        )
    
        bottom_bars = pg.BarGraphItem(
            x=self.x_positions,  # 相同的x位置
            height=bottom_values, 
            width=self.bar_width, 
            brush=pg.mkBrush(0, 255, 0, 150),  # 绿色半透明
            pen=pg.mkPen('k', width=0.5)
        )
        
        # 添加柱状图到绘图区域
        self.plot_widget.addItem(top_bars)
        self.plot_widget.addItem(bottom_bars)
        
        # 设置y轴范围
        all_values = np.concatenate([top_values, bottom_values])
        max_value = max(abs(all_values)) * 1.2  # 增加20%边距
        self.plot_widget.setYRange(-max_value, max_value)
        
        # 设置坐标轴标签
        self.plot_widget.setLabel('left', '涨跌幅 (%)')
        self.plot_widget.setLabel('bottom', '排名')


        # 添加行业名称标签
        self.top_names = self.top_10[s_board_name].tolist()  # 假设字段名为industry_name
        self.bottom_names = self.bottom_10[s_board_name].tolist()
        self.add_bar_value_labels(top_values, bottom_values, self.show_type)

    def draw_amount_chart(self, s_board_type, s_board_name, top, field_name):
        self.plot_widget.setTitle(f"{s_board_type} 成交额 Top {top}", color='#008080', size='12pt')

        # 创建x轴位置（共10个位置，每个位置绘制两个柱子）
        self.x_positions = list(range(top))
        self.bar_width = 0.6
        
        # 获取涨幅和跌幅数据
        top_values = self.top_10[field_name].values
        bottom_values = None
        
        top_bars = pg.BarGraphItem(
            x=self.x_positions, 
            height=top_values, 
            width=self.bar_width, 
            brush=pg.mkBrush(255, 0, 0, 150),  # 红色半透明
            pen=pg.mkPen('k', width=0.5)
        )
    
        # 添加柱状图到绘图区域
        self.plot_widget.addItem(top_bars)

        # 设置y轴范围
        all_values = np.concatenate([top_values])
        max_value = max(abs(all_values)) * 1.2  # 增加20%边距
        self.plot_widget.setYRange(-max_value, max_value)
        
        # 设置坐标轴标签
        self.plot_widget.setLabel('left', '成交额 (亿)')
        self.plot_widget.setLabel('bottom', '排名')


        # 添加行业名称标签
        self.top_names = self.top_10[s_board_name].tolist()  # 假设字段名为industry_name
        self.bottom_names = None
        self.add_bar_value_labels(top_values, bottom_values, self.show_type)

    # def add_bar_value_labels(self, top_values, bottom_values, show_type):
    #     y_range = self.plot_widget.viewRange()[1]  # 获取y轴范围
    #     y_span = y_range[1] - y_range[0]
    #     offset = y_span * 0.03
        
    #     # 处理顶部值的标签（如果存在）
    #     if self.top_names is not None and len(self.top_names) > 0:
    #         for i, top_name in enumerate(self.top_names):
    #             if i >= len(top_values):  # 防止索引越界
    #                 break
                    
    #             # 涨幅名称标签（上方）
    #             top_text = pg.TextItem(top_name[:8] + '...' if len(top_name) > 8 else top_name, anchor=(0.5, 1))
    #             top_text.setPos(i, top_values[i] + offset)
    #             top_text.setColor(pg.mkColor('k'))
    #             font = pg.QtGui.QFont()
    #             # font.setPointSize(7)
    #             top_text.setFont(font)
    #             self.plot_widget.addItem(top_text)
            
    #         # 添加顶部数值标签
    #         for i, top_val in enumerate(top_values):
    #             # 涨幅数值标签
    #             if top_val > 0:
    #                 if show_type == 0:
    #                     top_text = pg.TextItem(f"+{top_val:.2f}%", anchor=(0.5, 0))
    #                 elif show_type == 1:
    #                     top_text = pg.TextItem(f"{top_val:.2f}", anchor=(0.5, 0))

    #                 top_text.setPos(i, top_val + offset)
    #                 top_text.setColor(pg.mkColor('k'))
    #                 font = pg.QtGui.QFont()
    #                 # font.setPointSize(7)
    #                 top_text.setFont(font)
    #                 self.plot_widget.addItem(top_text)
        
    #     # 处理底部值的标签（如果存在）
    #     if self.bottom_names is not None and bottom_values is not None and len(self.bottom_names) > 0:
    #         for i, bottom_name in enumerate(self.bottom_names):
    #             if i >= len(bottom_values):  # 防止索引越界
    #                 break
                    
    #             # 跌幅名称标签（下方）
    #             bottom_text = pg.TextItem(bottom_name[:8] + '...' if len(bottom_name) > 8 else bottom_name, anchor=(0.5, 0))
    #             bottom_text.setPos(i, bottom_values[i] - offset)
    #             bottom_text.setColor(pg.mkColor('k'))
    #             bottom_text.setFont(pg.QtGui.QFont())
    #             bottom_text.setFont(pg.QtGui.QFont())
    #             self.plot_widget.addItem(bottom_text)
            
    #         # 添加底部数值标签
    #         for i, bottom_val in enumerate(bottom_values):
    #             # 跌幅数值标签
    #             if bottom_val < 0:
    #                 bottom_text = pg.TextItem(f"{bottom_val:.2f}%", anchor=(0.5, 1))
    #                 bottom_text.setPos(i, bottom_val - offset)
    #                 bottom_text.setColor(pg.mkColor('k'))
    #                 bottom_text.setFont(pg.QtGui.QFont())
    #                 self.plot_widget.addItem(bottom_text)

    def add_bar_value_labels(self, top_values, bottom_values, show_type):
        y_range = self.plot_widget.viewRange()[1]  # 获取y轴范围
        y_span = y_range[1] - y_range[0]
        offset = y_span * 0.03
        
        # 处理顶部值的标签（如果存在）
        if self.top_names is not None and len(self.top_names) > 0:
            for i, top_name in enumerate(self.top_names):
                if i >= len(top_values):  # 防止索引越界
                    break
                    
                # 涨幅名称标签（上方）
                top_text = pg.TextItem(top_name[:8] + '...' if len(top_name) > 8 else top_name, anchor=(0.5, 1))
                top_text.setPos(i, top_values[i] + offset)
                top_text.setColor(pg.mkColor('k'))
                font = pg.QtGui.QFont()
                top_text.setFont(font)
                self.plot_widget.addItem(top_text)
            
            # 添加顶部数值标签
            for i, top_val in enumerate(top_values):
                # 涨幅数值标签
                if top_val > 0:
                    if show_type == 0:
                        top_text = pg.TextItem(f"+{top_val:.2f}%", anchor=(0.5, 0))
                    elif show_type == 1:
                        top_text = pg.TextItem(f"{top_val:.2f}", anchor=(0.5, 0))
                    
                    top_text.setPos(i, top_val + offset)
                    top_text.setColor(pg.mkColor('k'))
                    font = pg.QtGui.QFont()
                    top_text.setFont(font)
                    self.plot_widget.addItem(top_text)
        
        # 处理底部值的标签（如果存在）
        if self.bottom_names is not None and bottom_values is not None and len(self.bottom_names) > 0:
            # 计算一个固定的底部位置，确保标签总是在0轴线下方
            min_bottom_position = min(0, min(bottom_values)) - offset if len(bottom_values) > 0 else -offset
            
            for i, bottom_name in enumerate(self.bottom_names):
                if i >= len(bottom_values):  # 防止索引越界
                    break
                
                # 底部数值标签（固定在名称上方）
                if bottom_values[i] < 0:
                    # 负值情况下显示在柱子下方
                    bottom_text = pg.TextItem(f"{bottom_values[i]:.2f}%", anchor=(0.5, 1))
                    bottom_text.setPos(i, bottom_values[i] - offset)
                    bottom_text.setColor(pg.mkColor('k'))
                    bottom_text.setFont(pg.QtGui.QFont())
                    self.plot_widget.addItem(bottom_text)
                elif bottom_values[i] >= 0:
                    # 正值情况下也显示在柱子下方
                    if show_type == 0:
                        bottom_text = pg.TextItem(f"+{bottom_values[i]:.2f}%", anchor=(0.5, 1))
                    elif show_type == 1:
                        bottom_text = pg.TextItem(f"{bottom_values[i]:.2f}", anchor=(0.5, 1))
                    
                    # 固定在底部区域，确保在0轴线下方
                    fixed_bottom_pos = 0    # min(min_bottom_position, bottom_values[i] - offset if bottom_values[i] < 0 else min_bottom_position)
                    bottom_text.setPos(i, fixed_bottom_pos - offset)
                    bottom_text.setColor(pg.mkColor('k'))
                    bottom_text.setFont(pg.QtGui.QFont())
                    self.plot_widget.addItem(bottom_text)
                
                # 底部名称标签（固定在数值标签下方）
                bottom_name_text = pg.TextItem(bottom_name[:8] + '...' if len(bottom_name) > 8 else bottom_name, anchor=(0.5, 0))
                
                # 根据数值标签的位置确定名称标签位置
                if bottom_values[i] < 0:
                    # 负值情况下名称标签在数值标签下方
                    name_pos_y = bottom_values[i] - offset
                else:
                    # 正值情况下名称标签在数值标签下方
                    name_pos_y = fixed_bottom_pos - offset
                
                bottom_name_text.setPos(i, name_pos_y)
                bottom_name_text.setColor(pg.mkColor('k'))
                bottom_name_text.setFont(pg.QtGui.QFont())
                self.plot_widget.addItem(bottom_name_text)

    def get_date_str(self, index):
        row = self.data.iloc[index]
        date_str = row['date']
        return date_str
    
    def get_row_by_board_and_date(self, board_name, date):
        """根据板块名称和日期获取对应的行数据"""
        if not hasattr(self, 'data') or self.data is None:
            return None
        
        try:
            # 查找同时匹配板块名称和日期的行
            if self.board_type == 0:
                # 行业板块
                matching_rows = self.data[
                    (self.data['industry_name'] == board_name) & 
                    (self.data['date'] == date)
                ]
            else:
                # 概念板块
                matching_rows = self.data[
                    (self.data['concept_name'] == board_name) & 
                    (self.data['date'] == date)
                ]
            
            if not matching_rows.empty:
                return matching_rows.iloc[0]  # 返回第一行匹配的数据
            else:
                # 如果没有精确匹配，尝试只按日期查找
                date_rows = self.data[self.data['date'] == date]
                if not date_rows.empty:
                    return date_rows.iloc[0]
        except Exception as e:
            self.logger.error(f"查找板块数据时发生错误: {e}")
        
        return None
    
    def get_industry_board_tip_text(self, row, board_name):
        date_str = row['date']
        change_percent = row['change_percent']
        total_volume = row['total_volume']
        total_amount = row['total_amount']
        net_inflow = row['net_inflow']
        rising_count = row['rising_count']
        falling_count = row['falling_count']
        avg_price = row['avg_price']
        leading_stock = row['leading_stock']
        leading_stock_price = row['leading_stock_price']
        leading_stock_change_percent = row['leading_stock_change_percent']

        label_text = f"板块：{board_name}<br>日期: {date_str}<br>涨跌幅：{change_percent}%<br>成交量：{total_volume} 万<br>成交额: {total_amount} 亿\
            <br>净流入: {net_inflow} 亿<br>上涨家数: {rising_count}<br>下跌家数: {falling_count}<br>均价: {avg_price}<br>领涨股：{leading_stock}<br>领涨股价格：{leading_stock_price}<br>领涨股涨跌幅：{leading_stock_change_percent}%"
    
        return label_text
    
    def get_concept_board_tip_text(self, row, board_name):
        open_price = row['open_price']
        previous_close_price = row['previous_close']
        low_price = row['low_price']
        high_price = row['high_price']

        date_str = row['date']
        change_percent = row['board_change_percent']
        total_volume = row['volume']
        total_amount = row['turnover']
        net_inflow = row['net_inflow']
        rising_count = row['rising_count']
        falling_count = row['falling_count']
        rank = row['rank']

        label_text = f"板块：{board_name}<br>日期: {date_str}<br>排名：{rank}<br>昨收：{previous_close_price}<br>今开：{open_price}<br>最高：{high_price}\
            <br>最低：{low_price}<br>涨跌幅：{change_percent}%<br>成交量：{total_volume} 万<br>成交额: {total_amount} 亿\
            <br>净流入: {net_inflow} 亿<br>上涨家数: {rising_count}<br>下跌家数: {falling_count}"
        
        return label_text


    def update_label(self, index):
        """更新标签显示"""
        if hasattr(self, 'data'):
            if self.board_type == 0:
                self.update_label_industry(index)
            else:
                self.update_label_concept(index)
            

    def update_label_industry(self, index):

        if self.top_names is not None:
            top_name = self.top_names[index]
            top_row = self.get_row_by_board_and_date(top_name, self.chart_date)

            if top_row is None:
                return
            else:
                top_tip = self.get_industry_board_tip_text(top_row, top_name)
                top_tip_with_style = '<div style="color: black; background-color: white; border: 3px solid black; padding: 2px;">{}</div>'.format(top_tip)
                self.label_main.setHtml(top_tip_with_style)
        
        if self.bottom_names is not None:
            bottom_name = self.bottom_names[index]
            bottom_row = self.get_row_by_board_and_date(bottom_name, self.chart_date)
            if bottom_row is None:
                return
            else:
                bottom_tip = self.get_industry_board_tip_text(bottom_row, bottom_name) 
                bottom_tip_with_style = '<div style="color: black; background-color: white; border: 3px solid black; padding: 2px;">{}</div>'.format(bottom_tip)
                self.label_main_2.setHtml(bottom_tip_with_style)
    def update_label_concept(self, index):

        if self.top_names is not None:
            top_name = self.top_names[index]
            top_row = self.get_row_by_board_and_date(top_name, self.chart_date)

            if top_row is None:
                return
            else:
                tip_text = self.get_concept_board_tip_text(top_row, top_name)
                text_with_style = '<div style="color: black; background-color: white; border: 3px solid black; padding: 2px;">{}</div>'.format(tip_text)
                self.label_main.setHtml(text_with_style)

        if self.bottom_names is not None:
            bottom_name = self.bottom_names[index]
            bottom_row = self.get_row_by_board_and_date(bottom_name, self.chart_date)
            if bottom_row is None:
                return
            else:
                bottom_tip = self.get_concept_board_tip_text(bottom_row, bottom_name) 
                bottom_tip_with_style = '<div style="color: black; background-color: white; border: 3px solid black; padding: 2px;">{}</div>'.format(bottom_tip)
                self.label_main_2.setHtml(bottom_tip_with_style)


    def on_range_changed(self):
        pass

    def on_mouse_move(self, pos):
        if self.x_positions is None or self.x_positions == []: return
        if self.plot_widget.sceneBoundingRect().contains(pos):
            mouse_point = self.plot_widget.getViewBox().mapSceneToView(pos)
            x_val = mouse_point.x()
            y_val = mouse_point.y()

            bar_centers = self.x_positions
            
            closest_index = None
            min_distance = float('inf')
            
            for i, center in enumerate(bar_centers):
                distance = abs(center - x_val)
                if distance <= self.bar_width / 2:
                    if distance < min_distance:
                        min_distance = distance
                        closest_index = i
            
            if closest_index is not None:
                view_range = self.plot_widget.getViewBox().viewRange()
                closest_x = bar_centers[closest_index]

                # 更新主图表垂直线位置
                self.v_line_main.setPos(closest_x)
                self.v_line_main.show()
                
                # 更新主图表水平线位置
                self.h_line_main.setPos(y_val)
                self.h_line_main.show()

                # 主图表左侧Y轴标签
                left_y_label_main_x = view_range[0][0]
                self.left_y_label_main.setPos(left_y_label_main_x, y_val)

                left_y_label_main_text = f"{y_val:.2f}"
                left_y_label_text_with_style = '<div style="color: black; background-color: white; border: 3px solid black; padding: 2px;">{}</div>'.format(left_y_label_main_text)
                self.left_y_label_main.setHtml(left_y_label_text_with_style)
                self.left_y_label_main.show() 


                # 主图X轴标签
                x_rank_str = f"Top {closest_index + 1}"
                label_x_main_x = closest_x
                
                
                label_main_x_text_with_style = '<div style="color: black; background-color: white; border: 3px solid black; padding: 2px;">{}</div>'.format(x_rank_str)
                self.x_label_main.setHtml(label_main_x_text_with_style)

                label_x_main_y = view_range[1][0]
                self.x_label_main.setPos(label_x_main_x, label_x_main_y)
                self.x_label_main.show()

                self.update_label(closest_index)
                y_center = (view_range[1][0]) * 3 / 4
                label_main_y = y_center
                # self.logger.info(f"view range: {view_range}")
                # self.logger.info(f"label_main_y: {label_main_y}, y_val: {y_val}")
                if closest_x >= len(bar_centers) - 5:
                    self.label_main.setPos(closest_x - 5, y_val)
                    self.label_main_2.setPos(closest_x - 2, y_val)
                else:
                    self.label_main.setPos(closest_x, y_val)
                    self.label_main_2.setPos(closest_x + 3, y_val)
                
                self.label_main.show()
                self.label_main_2.show()

            else:
                self.hide_all_labels()

        else:
            self.hide_all_labels()

    def enterEvent(self, event):
        """
        当鼠标进入控件时的处理
        """
        super().enterEvent(event)

    def leaveEvent(self, event):
        """
        当鼠标离开控件时，隐藏所有标签和十字线
        """
        self.hide_all_labels()
        super().leaveEvent(event)