# 安装: pip install pyqtgraph
import os
# os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'

import pyqtgraph as pg
from pyqtgraph import DateAxisItem
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from PyQt5.QtCore import QDateTime, Qt, pyqtSlot, QPointF, QTimer

from gui.qt_widgets.MComponents.custom_date_axisItem import CustomDateAxisItem, NoLabelAxis

from manager.logging_manager import get_logger

class BoardChartWidget(QWidget):
    def __init__(self, type=0):
        super().__init__()
        self.logger = get_logger(__name__)

        self.board_type = type
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 创建使用日期轴的绘图窗口
        # 使用自定义的日期轴类
        # self.date_axis_main = CustomDateAxisItem(orientation='bottom')
        # self.plot_widget = pg.PlotWidget(axisItems={'bottom': self.date_axis_main})

        # self.plot_widget = pg.PlotWidget()

        self.date_axis_main = NoLabelAxis(orientation='bottom')
        self.plot_widget = pg.PlotWidget(axisItems={'bottom': self.date_axis_main})
        layout.addWidget(self.plot_widget)

        # 添加底部坐标系容器
        # self.date_axis_bottom = CustomDateAxisItem(orientation='bottom')
        # self.bottom_plot_widget = pg.PlotWidget(axisItems={'bottom': self.date_axis_bottom})
        # self.bottom_plot_widget = pg.PlotWidget()

        self.date_axis_bottom = NoLabelAxis(orientation='bottom')
        self.bottom_plot_widget = pg.PlotWidget(axisItems={'bottom': self.date_axis_bottom})

        #self.bottom_plot_widget = pg.PlotWidget()

        layout.addWidget(self.bottom_plot_widget)
        
        layout.setStretchFactor(self.plot_widget, 2)
        layout.setStretchFactor(self.bottom_plot_widget, 1)
        
        self.setup_plot_style()

    def setup_plot_style(self):
        # 主图表样式设置
        self.plot_widget.setBackground('w')
        # self.plot_widget.setLabel('left', '总成交额')
        # self.plot_widget.setLabel('bottom', '日期')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.addLegend()
        self.plot_widget.setMouseEnabled(x=True, y=False)
        self.plot_widget.getViewBox().setMouseMode(pg.ViewBox.PanMode)  # 平移模式
        
        # 初始化主图表十字线
        self.v_line_main = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('#808286', width=2, style=Qt.DashLine))
        self.h_line_main = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('#808286', width=2, style=Qt.DashLine))
        self.v_line_main.setZValue(1000)
        self.h_line_main.setZValue(1000)
        
        main_viewbox = self.plot_widget.getViewBox()
        # 明确添加到主视图
        main_viewbox.addItem(self.v_line_main, ignoreBounds=True)
        main_viewbox.addItem(self.h_line_main, ignoreBounds=True)
        # self.plot_widget.addItem(self.v_line_main, ignoreBounds=True)
        # self.plot_widget.addItem(self.h_line_main, ignoreBounds=True)
        
        
        # 初始化主图表标签（优化样式）
        self.label_main = pg.TextItem("", anchor=(0, 1))
        self.label_main.setZValue(1000)
        
        # 预设标签样式
        font = pg.QtGui.QFont("Arial", 10, pg.QtGui.QFont.Bold)
        self.label_main.setFont(font)
        
        main_viewbox.addItem(self.label_main, ignoreBounds=True)
        
        # 主图表左y轴标签
        self.left_y_label_main = pg.TextItem("", anchor=(0, 0.5))  # 左侧Y轴标签
        self.left_y_label_main.setZValue(1000)
        self.left_y_label_main.setFont(pg.QtGui.QFont("Arial", 9))
        self.left_y_label_main.setColor(pg.QtGui.QColor(255, 0, 0))  # 红色
        
        main_viewbox.addItem(self.left_y_label_main, ignoreBounds=True)
        
        # 主图右y轴标签
        self.right_y_label_main = pg.TextItem("", anchor=(1, 0.5))  # 右侧Y轴标签
        self.right_y_label_main.setZValue(1000)

        self.right_y_label_main.setFont(pg.QtGui.QFont("Arial", 9))
        self.right_y_label_main.setColor(pg.QtGui.QColor(0, 0, 255))  # 蓝色
        
        main_viewbox.addItem(self.right_y_label_main, ignoreBounds=True)
        
        # 主图x轴标签
        self.x_label_main = pg.TextItem("", anchor=(0.5, 1))  # X轴标签
        self.x_label_main.setZValue(1000)
        self.x_label_main.setFont(pg.QtGui.QFont("Arial", 9))
        self.x_label_main.setColor(pg.QtGui.QColor(0, 0, 0))  # 黑色
        
        main_viewbox.addItem(self.x_label_main, ignoreBounds=True)
        
        # 隐藏主图表的十字线和标签
        self.v_line_main.hide()
        self.h_line_main.hide()
        self.label_main.hide()
        self.left_y_label_main.hide()
        self.right_y_label_main.hide()
        self.x_label_main.hide()
        
        # 底部图表样式设置
        self.bottom_plot_widget.setBackground('w')
        # self.bottom_plot_widget.setLabel('left', '净流入')
        # self.bottom_plot_widget.setLabel('bottom', '日期')
        self.bottom_plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.bottom_plot_widget.setMouseEnabled(x=True, y=False)
        self.bottom_plot_widget.getViewBox().setMouseMode(pg.ViewBox.PanMode)  # 平移模式
        
        # 初始化底部图表十字线
        self.v_line_bottom = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('#808286', width=2, style=Qt.DashLine))
        self.h_line_bottom = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('#808286', width=2, style=Qt.DashLine))
        self.v_line_bottom.setZValue(1000)
        self.h_line_bottom.setZValue(1000)
        
        bottom_viewbox = self.bottom_plot_widget.getViewBox()
        bottom_viewbox.addItem(self.v_line_bottom, ignoreBounds=True)
        bottom_viewbox.addItem(self.h_line_bottom, ignoreBounds=True)
        
        # 底部图表左y轴标签
        self.left_y_label_bottom = pg.TextItem("", anchor=(0, 0.5))  # 左侧Y轴标签
        self.left_y_label_bottom.setZValue(1000)
        self.left_y_label_bottom.setFont(pg.QtGui.QFont("Arial", 9))
        self.left_y_label_bottom.setColor(pg.QtGui.QColor(0, 128, 0))  # 绿色
        
        bottom_viewbox.addItem(self.left_y_label_bottom, ignoreBounds=True)
        
        # 底部图表x轴标签
        self.x_label_bottom = pg.TextItem("", anchor=(0.5, 1))  # X轴标签
        self.x_label_bottom.setZValue(1000)
        self.x_label_bottom.setFont(pg.QtGui.QFont("Arial", 9))
        self.x_label_bottom.setColor(pg.QtGui.QColor(0, 0, 0))  # 黑色
        
        bottom_viewbox.addItem(self.x_label_bottom, ignoreBounds=True)
        
        # 隐藏底部图表的十字线和标签
        self.v_line_bottom.hide()
        self.h_line_bottom.hide()
        self.left_y_label_bottom.hide()
        self.x_label_bottom.hide()
        
        # 设置底部图表十字线与主图表同步
        self.v_line_main.sigPositionChanged.connect(self.sync_v_line_position)
        self.v_line_bottom.sigPositionChanged.connect(self.sync_v_line_position)
        
        # 连接信号
        self.bottom_plot_widget.setXLink(self.plot_widget)
        self.plot_widget.sigRangeChanged.connect(self.on_range_changed)
        

        self.plot_widget.scene().sigMouseMoved.connect(self.on_mouse_move)
        self.bottom_plot_widget.scene().sigMouseMoved.connect(self.on_mouse_move_bottom)
    def sync_v_line_position(self):
        """同步两个坐标系的垂直线位置"""
        if hasattr(self, 'v_line_main') and hasattr(self, 'v_line_bottom'):
            pos = self.v_line_main.pos()
            self.v_line_bottom.setPos(pos)
            
            # 同步X轴标签位置
            if self.x_label_main.isVisible():
                self.x_label_main.setPos(pos.x(), self.plot_widget.getViewBox().viewRange()[1][0])
            if self.x_label_bottom.isVisible():
                self.x_label_bottom.setPos(pos.x(), self.bottom_plot_widget.getViewBox().viewRange()[1][0])

    def plot_chart(self, board_name, data, field_name="总成交额"):
        if self.board_type == 0:
            # 字段映射字典
            field_mapping = {
                '总成交量': 'total_volume',
                '总成交额': 'total_amount',
                '净流入': 'net_inflow',
                '上涨家数': 'rising_count',
                '下跌家数': 'falling_count'
            }
            
            # 获取实际字段名
            actual_field = field_mapping.get(field_name, 'total_amount')  # 默认使用总成交额
            display_name = field_name  # 显示名称

            right_y_field = 'avg_price'
            right_y_name = '均价'
            right_y_unit = '元'
        else:
            field_mapping = {
                '总成交量': 'volume',
                '总成交额': 'turnover',
                '净流入': 'net_inflow',
                '上涨家数': 'rising_count',
                '下跌家数': 'falling_count'
            }
            
            # 获取实际字段名
            actual_field = field_mapping.get(field_name, 'turnover')  # 默认使用总成交额
            display_name = field_name  # 显示名称

            right_y_field = 'open_price'
            right_y_name = '今开'
            right_y_unit = '元'

        # 检查字段是否存在（修复错误的检查方式）
        if actual_field not in data.columns:
            self.logger.error(f"{field_name}字段不存在于数据中！")
            return False

        self.data = data
        # 清除之前的绘图
        self.plot_widget.clear()

        self.plot_widget.setTitle(f"{board_name}趋势", color='#008080', size='12pt')
        
        # 处理数据
        if 'date' in data.columns:
            date_list = []
            for row in data.itertuples():
                date_object = datetime.strptime(row.date, "%Y-%m-%d")
                date_list.append(date_object)
        else:
            timestamps = list(range(len(data)))

        
        # 将日期转换为时间戳
        # timestamps = [date.timestamp() for date in date_list]
        x_list = list(range(len(date_list)))

        # 计算合适的柱子宽度
        self.bar_width = 0.8

        # 将柱子的中心对准日期时间点，而不是起始位置
        self.adjusted_timestamps = x_list   # [ts - self.bar_width / 2 for ts in x_list]

        # 创建柱状图（根据传入的字段名）
        if actual_field in data.columns:
            self.field_data = data[actual_field].values
        else:
            return False


        # =================================绘制主图柱状图=================================
        # 获取涨跌幅数据
        change_percent_data = data['change_percent'].values

        # 分别创建不同样式的柱子，根据field_name决定显示方式
        up_indices = []
        down_indices = []

        if field_name in ['总成交量', '总成交额']:
            # 按涨跌区分：上涨为红色边框空心柱，下跌为绿色实心柱
            up_indices = [i for i, pct in enumerate(change_percent_data) if pct >= 0]
            down_indices = [i for i, pct in enumerate(change_percent_data) if pct < 0]
        elif field_name == '上涨家数':
            # 上涨家数全部显示为红色边框空心柱
            up_indices = list(range(len(self.field_data)))
            down_indices = []
        elif field_name == '下跌家数':
            # 下跌家数全部显示为绿色实心柱
            up_indices = []
            down_indices = list(range(len(self.field_data)))
        else:
            # 默认按涨跌区分
            up_indices = [i for i, pct in enumerate(change_percent_data) if pct >= 0]
            down_indices = [i for i, pct in enumerate(change_percent_data) if pct < 0]

        # 绘制上涨柱子（红色边框空心柱）
        if up_indices:
            up_timestamps = [self.adjusted_timestamps[i] for i in up_indices]
            up_values = [self.field_data[i] for i in up_indices]
            
            up_bargraph = pg.BarGraphItem(
                x=up_timestamps,
                height=up_values,
                width=self.bar_width,
                pen={'color': 'r', 'width': 2},  # 红色边框
                brush=pg.mkColor(255, 255, 255, 0),  # 透明填充
                name=display_name
            )
            self.plot_widget.addItem(up_bargraph)

        # 绘制下跌柱子（绿色实心柱）
        if down_indices:
            down_timestamps = [self.adjusted_timestamps[i] for i in down_indices]
            down_values = [self.field_data[i] for i in down_indices]
            
            down_bargraph = pg.BarGraphItem(
                x=down_timestamps,
                height=down_values,
                width=self.bar_width,
                pen={'color': '#0ACC5A', 'width': 1}, # 绿色边框
                brush=pg.mkColor(10, 204, 90),  # 绿色实心填充
                name=display_name
            )
            self.plot_widget.addItem(down_bargraph)

        # ==============================绘制折线图===============================
        # 先创建右侧Y轴和折线图（确保在柱状图之前添加）
        # 创建右侧Y轴用于显示折线图
        self.right_viewbox = pg.ViewBox()
        self.right_axis = self.plot_widget.getAxis('right')

        # 链接右侧Y轴到主视图
        self.plot_widget.scene().addItem(self.right_viewbox)
        self.plot_widget.getAxis('right').linkToView(self.right_viewbox)
        self.right_viewbox.setXLink(self.plot_widget)
        
        # 设置右侧Y轴标签
        self.plot_widget.setLabel('right', right_y_name, units=right_y_unit)
        self.plot_widget.showAxis('right')

        # 创建折线图（移动平均线）
        line_x_positions = [ts for ts in self.adjusted_timestamps]
        self.right_line_data = data[right_y_field].values
        self.line_plot = self.plot_widget.plot(
            x=line_x_positions,
            y=self.right_line_data,
            pen=pg.mkPen(color='#0f4d8f', width=2),
            symbol='o',
            symbolSize=8,
            symbolBrush='#ff7f0e',
            name=right_y_name, unit=right_y_unit
        )
        self.right_viewbox.addItem(self.line_plot)

        # 同步两个ViewBox的视图范围
        def update_views():
            self.right_viewbox.setGeometry(self.plot_widget.getViewBox().sceneBoundingRect())
            self.right_viewbox.linkedViewChanged(self.plot_widget.getViewBox(), self.right_viewbox.XAxis)
        
        update_views()
        self.plot_widget.getViewBox().sigResized.connect(update_views)

        # 考虑柱子宽度，使柱子居中显示
        x_min = min(self.adjusted_timestamps) 
        x_max = max(self.adjusted_timestamps) 
        self.plot_widget.setXRange(x_min, x_max)
        
        # 设置左右两侧Y轴的范围
        y_max_bar = max(self.field_data) * 1.1
        y_min_bar = min(self.field_data) * 1.1
        if y_min_bar >=0:
            y_min_bar = 0
        self.plot_widget.setYRange(y_min_bar, y_max_bar)

        # 右y
        y_max_line = max(self.right_line_data) * 1.1
        direct = 0 if y_min_bar >= 0 else -1
        y_min_line = min(self.right_line_data)  * direct * 1.1
        self.logger.info(f"board_type: {self.board_type}, y_min_line: {y_min_line}, y_max_line: {y_max_line}")
        self.right_viewbox.setYRange(y_min_line, y_max_line)

        self.add_bar_value_labels(self.adjusted_timestamps, self.field_data, self.bar_width)

        # =====================绘制底部图表数据（示例：添加另一个指标）===============
        self.plot_bottom_chart(data)

        return True

    def plot_bottom_chart(self, data):
        """绘制底部图表的数据"""
        # 示例：绘制净流入数据
        if 'net_inflow' in data.columns:
            net_inflow_data = data['net_inflow'].values
            # change_percent_data = data['change_percent'].values
            
            # 分别创建上涨和下跌的柱子
            up_indices = [i for i, pct in enumerate(net_inflow_data) if pct >= 0]
            down_indices = [i for i, pct in enumerate(net_inflow_data) if pct < 0]

            # 绘制上涨柱子（#FF5656实心柱）
            if up_indices:
                up_timestamps = [self.adjusted_timestamps[i] for i in up_indices]
                up_values = [net_inflow_data[i] for i in up_indices]
                
                up_bargraph = pg.BarGraphItem(
                    x=up_timestamps,
                    height=up_values,
                    width=self.bar_width,
                    pen={'color': '#FF5656', 'width': 1},
                    brush=pg.mkColor(255, 86, 86, 180),  # #FF5656半透明填充
                    name="净流入"
                )
                self.bottom_plot_widget.addItem(up_bargraph)

            # 绘制下跌柱子（#2AD672实心柱）
            if down_indices:
                down_timestamps = [self.adjusted_timestamps[i] for i in down_indices]
                down_values = [net_inflow_data[i] for i in down_indices]
                
                down_bargraph = pg.BarGraphItem(
                    x=down_timestamps,
                    height=down_values,
                    width=self.bar_width,
                    pen={'color': '#2AD672', 'width': 1},
                    brush=pg.mkColor(42, 214, 114, 180),  # #2AD672半透明填充
                    name="净流入"
                )
                self.bottom_plot_widget.addItem(down_bargraph)
            
            # 设置Y轴范围
            y_max = max(net_inflow_data) * 1.1
            y_min = min(net_inflow_data) * 1.1
            if y_min >= 0:
                y_min = 0
            self.bottom_plot_widget.setYRange(y_min, y_max)

        # -----------------------------------------------------------------------
        bottom_right_y_name_2 = '涨跌家数'
        bottom_right_y_unit_2 = '家'
        bottom_right_y_rasing_field = 'rising_count'
        bottom_right_y_falling_field = 'falling_count'
        # 底部右y折线图
        self.bottom_right_viewbox = pg.ViewBox()

        # 链接右侧Y轴到主视图
        self.bottom_plot_widget.scene().addItem(self.bottom_right_viewbox)
        self.bottom_plot_widget.getAxis('right').linkToView(self.bottom_right_viewbox)
        self.bottom_right_viewbox.setXLink(self.bottom_plot_widget)
        # 设置右侧Y轴标签
        self.bottom_plot_widget.setLabel('right', bottom_right_y_name_2, units=bottom_right_y_unit_2)
        self.bottom_plot_widget.showAxis('right')

        line_x_positions = [ts for ts in self.adjusted_timestamps]
        self.bottom_right_line_rasing_data = data[bottom_right_y_rasing_field].values

        self.right_rasing_line_plot = self.bottom_plot_widget.plot(
            x=line_x_positions,
            y=self.bottom_right_line_rasing_data,
            pen=pg.mkPen(color='#FF0000', width=2),
            symbol='o',
            symbolSize=8,
            symbolBrush='#FF6666',
            name=bottom_right_y_name_2, unit=bottom_right_y_unit_2
        )
        self.bottom_right_viewbox.addItem(self.right_rasing_line_plot)

        self.bottom_right_line_falling_data = data[bottom_right_y_falling_field].values
        self.right_falling_line_plot = self.bottom_plot_widget.plot(
            x=line_x_positions,
            y=self.bottom_right_line_falling_data,
            pen=pg.mkPen(color='#00AA00', width=2),
            symbol='o',
            symbolSize=8,
            symbolBrush='#66AA66'
        )
        self.bottom_right_viewbox.addItem(self.right_falling_line_plot)

        # ---
        right_y_min_rasing = min(self.bottom_right_line_rasing_data) 
        right_y_max_rasing = max(self.bottom_right_line_rasing_data)

        right_y_min_falling = min(self.bottom_right_line_falling_data)
        right_y_max_falling = max(self.bottom_right_line_falling_data)

        bottom_right_y_min = min(right_y_min_rasing, right_y_min_falling) * 1.1
        bottom_right_y_max = max(right_y_max_rasing, right_y_max_falling) * 1.1

        self.logger.info(f"bottom_right_y_min: {bottom_right_y_min}, bottom_right_y_max: {bottom_right_y_max}")

        if bottom_right_y_min >=0:
            bottom_right_y_min = 0

        self.bottom_right_viewbox.setYRange(bottom_right_y_min, bottom_right_y_max)

        def update_bottom_views():
            self.bottom_right_viewbox.setGeometry(self.bottom_plot_widget.getViewBox().sceneBoundingRect())
            self.bottom_right_viewbox.linkedViewChanged(self.bottom_plot_widget.getViewBox(), self.bottom_right_viewbox.XAxis)
        
        update_bottom_views()
        self.bottom_plot_widget.getViewBox().sigResized.connect(update_bottom_views)

    def add_bar_value_labels(self, timestamps, values, bar_width):
        """在柱子顶部添加数值标签"""
        for i, (ts, val) in enumerate(zip(timestamps, values)):
            # 计算标签位置（柱子中心顶部）
            x_pos = ts
            y_pos = val + 0.05  # 稍微高于柱子顶部
            
            # 创建文本项
            text = pg.TextItem(text=f"{val}", color=(0, 0, 0), anchor=(0.5, 1))
            text.setPos(x_pos, y_pos)
            self.plot_widget.addItem(text)

    def adjust_left_y_range_to_visible_data(self):
        """根据X轴范围内可见数据调整Y轴范围"""
        vb = self.plot_widget.getViewBox()
        x_range = vb.viewRange()[0]  # 获取X轴范围
        
        # 找到在当前X轴范围内的数据点
        visible_indices = []
        
        for i, ts in enumerate(self.adjusted_timestamps):
            # 柱子的范围是从 ts 到 ts+bar_width
            bar_center = ts
            if x_range[0] <= bar_center <= x_range[1]:
                visible_indices.append(i)
        
        if visible_indices:
            # 获取可见数据点的高度值 - 使用 iloc 按位置访问
            visible_data = [self.field_data[i] for i in visible_indices]
            if visible_data:
                y_min, y_max = min(visible_data), max(visible_data)
                # 设置Y轴范围，增加一些边距 (10%)
                vb.setYRange(0, y_max * 1.1)

    def get_left_visible_y_data(self):
        """获取当前可视范围内的Y轴数据"""
        vb = self.plot_widget.getViewBox()
        x_range = vb.viewRange()[0]  # 获取X轴范围
        
        # 找到在当前X轴范围内的数据点
        visible_indices = []
        
        for i, ts in enumerate(self.adjusted_timestamps):
            bar_center = ts
            if x_range[0] <= bar_center <= x_range[1]:
                visible_indices.append(i)
        
        if visible_indices:
            # 使用 iloc 按位置访问数据
            return [self.field_data[i] for i in visible_indices]
        return []

    def fix_left_y_axis_ticks(self, data):
        """修复Y轴刻度显示，确保显示为整数"""
        # 获取Y轴对象
        y_axis = self.plot_widget.getAxis('left')
        
        if not data:
            return

        # 计算合适的刻度间隔
        data_min, data_max = min(data), max(data)
        data_range = data_max - data_min

        if data_range > 0:
            # 根据数据范围动态设置刻度间隔
            if data_range > 5000:
                tick_interval = 1000
            elif data_range > 1000:
                tick_interval = 500
            elif data_range > 500:
                tick_interval = 100
            elif data_range > 100:
                tick_interval = 50
            else:
                tick_interval = 10
                
            # 设置Y轴刻度
            y_max = data_max * 1.1
            ticks = [(i, str(i)) for i in range(0, int(y_max) + tick_interval, tick_interval)]
            y_axis.setTicks([ticks])
        else:
            # 如果数据范围为0，设置默认刻度
            y_max = data_max * 1.1 if data_max > 0 else 100
            ticks = [(i, str(i)) for i in range(0, int(y_max) + 50, 50)]
        y_axis.setTicks([ticks])

    def adjust_bottom_y_range_to_visible_data(self):
        """根据X轴范围内可见数据调整底部图表Y轴范围"""
        # 检查底部图表是否有数据
        if not hasattr(self, 'data') or self.data is None:
            return
            
        vb = self.bottom_plot_widget.getViewBox()
        x_range = vb.viewRange()[0]  # 获取X轴范围
        
        # 找到在当前X轴范围内的数据点
        visible_indices = []
        
        for i, ts in enumerate(self.adjusted_timestamps):
            # 柱子的范围是从 ts 到 ts+bar_width
            bar_center = ts
            if x_range[0] <= bar_center <= x_range[1]:
                visible_indices.append(i)
        
        if visible_indices:
            # 检查底部图表是否有净流入数据
            if 'net_inflow' in self.data.columns:
                # 获取可见数据点的高度值
                visible_data = [self.data['net_inflow'].iloc[i] for i in visible_indices]
                if visible_data:
                    y_min, y_max = min(visible_data), max(visible_data)
                    # 设置Y轴范围，增加一些边距 (10%)
                    y_range = y_max - y_min
                    margin = y_range * 0.1 if y_range > 0 else 0.1
                    vb.setYRange(y_min - margin, y_max + margin)

    def get_bottom_visible_y_data(self):
        """获取底部图表当前可视范围内的Y轴数据"""
        # 检查底部图表是否有数据
        if not hasattr(self, 'data') or self.data is None:
            return []
            
        vb = self.bottom_plot_widget.getViewBox()
        x_range = vb.viewRange()[0]  # 获取X轴范围
        
        # 找到在当前X轴范围内的数据点
        visible_indices = []
        
        for i, ts in enumerate(self.adjusted_timestamps):
            bar_center = ts
            if x_range[0] <= bar_center <= x_range[1]:
                visible_indices.append(i)
        
        if visible_indices:
            # 检查底部图表是否有净流入数据
            if 'net_inflow' in self.data.columns:
                # 使用 iloc 按位置访问数据
                return [self.data['net_inflow'].iloc[i] for i in visible_indices]
        return []

    def fix_bottom_y_axis_ticks(self, data):
        """修复底部图表Y轴刻度显示，确保显示为整数"""
        # 获取Y轴对象
        y_axis = self.bottom_plot_widget.getAxis('left')
        
        if not data:
            return

        # 计算合适的刻度间隔
        data_min, data_max = min(data), max(data)
        data_range = data_max - data_min

        if data_range > 0:
            # 根据数据范围动态设置刻度间隔
            if data_range > 5000:
                tick_interval = 1000
            elif data_range > 1000:
                tick_interval = 500
            elif data_range > 500:
                tick_interval = 100
            elif data_range > 100:
                tick_interval = 50
            elif data_range > 50:
                tick_interval = 10
            else:
                tick_interval = 5
                
            # 设置Y轴刻度
            y_max = data_max * 1.1
            y_min = data_min * 1.1
            if y_min >= 0:
                y_min = 0
                
            # 计算刻度范围
            min_tick = int(y_min // tick_interval) * tick_interval
            max_tick = int(y_max // tick_interval + 1) * tick_interval
            
            ticks = [(i, str(i)) for i in range(int(min_tick), int(max_tick) + int(tick_interval), int(tick_interval))]
            y_axis.setTicks([ticks])
        else:
            # 如果数据范围为0，设置默认刻度
            y_max = data_max * 1.1 if data_max > 0 else 100
            y_min = data_min * 1.1 if data_min < 0 else 0
            ticks = [(i, str(i)) for i in range(int(y_min), int(y_max) + 50, 50)]
            y_axis.setTicks([ticks])

    def on_range_changed(self):
        """当视图范围改变时调用"""
        # 根据当前可视范围调整Y轴
        self.adjust_left_y_range_to_visible_data()
        # 重新设置Y轴刻度
        visible_y_data = self.get_left_visible_y_data()
        if visible_y_data:
            self.fix_left_y_axis_ticks(visible_y_data)

        # 根据当前可视范围调整底部图表Y轴
        self.adjust_bottom_y_range_to_visible_data()
        # 重新设置底部图表Y轴刻度
        visible_bottom_y_data = self.get_bottom_visible_y_data()
        if visible_bottom_y_data:
            self.fix_bottom_y_axis_ticks(visible_bottom_y_data)
    def on_mouse_move(self, pos):
        """处理主图表鼠标移动事件"""
        if self.plot_widget.sceneBoundingRect().contains(pos):
            mouse_point = self.plot_widget.getViewBox().mapSceneToView(pos)
            x_val = mouse_point.x()
            y_val = mouse_point.y()

            # 右视图：将场景坐标转换为视图坐标
            mouse_point_right = self.right_viewbox.mapSceneToView(pos)
            x_val_right = mouse_point_right.x()
            y_val_right = mouse_point_right.y()

            # self.logger.info(f"鼠标位置: x={x_val:.2f}, y={y_val:.2f}")
            
            # 找到最近的数据点
            bar_centers = [ts for ts in self.adjusted_timestamps]
            # self.logger.info(f"柱子宽度: {self.bar_width:.2f}")
            
            closest_index = None
            min_distance = float('inf')
            
            for i, center in enumerate(bar_centers):
                distance = abs(center - x_val)

                # if i == 0:
                #     self.logger.info(f"索引：{i}，中心：{center}，距离: {distance:.2f}")

                if distance <= self.bar_width / 2:
                    if distance < min_distance:
                        min_distance = distance
                        closest_index = i
            
            if closest_index is not None:
                view_range = self.plot_widget.getViewBox().viewRange()
                bottom_view_range = self.bottom_plot_widget.getViewBox().viewRange()
                closest_x = bar_centers[closest_index]

                # self.logger.info(f"最接近的索引: {closest_index}")
                
                # 更新主图表垂直线位置
                self.v_line_main.setPos(closest_x)
                self.v_line_main.show()
                
                # 更新主图表水平线位置
                self.h_line_main.setPos(y_val)
                self.h_line_main.show()
                
                # 同步到底部坐标系（只显示垂直线）
                self.v_line_bottom.setPos(closest_x)
                self.v_line_bottom.show()
                self.h_line_bottom.hide()  # 隐藏底部水平线
                
                # 显示轴外标签
                # 主图表左侧Y轴标签
                left_y_label_main_x = view_range[0][0]  # + (view_range[0][1] - view_range[0][0]) * 0.03  # 左侧3%位置
                self.left_y_label_main.setPos(left_y_label_main_x, y_val)

                left_y_label_main_text = f"{y_val:.2f}"
                left_y_label_text_with_style = '<div style="color: black; background-color: white; border: 3px solid black; padding: 2px;">{}</div>'.format(left_y_label_main_text)
                self.left_y_label_main.setHtml(left_y_label_text_with_style)
                self.left_y_label_main.show() 

                # 右侧Y轴标签（主图）（需要转换到右侧坐标系）
                if hasattr(self, 'right_viewbox'):
                    right_y_label_main_x = view_range[0][1] # - (view_range[0][1] - view_range[0][0]) * 0.03
                    self.right_y_label_main.setPos(right_y_label_main_x, mouse_point.y())

                    right_y_label_main_text = f"{mouse_point_right.y():.2f}"
                    right_y_label_text_with_style = '<div style="color: black; background-color: white; border: 3px solid black; padding: 2px;">{}</div>'.format(right_y_label_main_text)
                    self.right_y_label_main.setHtml(right_y_label_text_with_style)
                    self.right_y_label_main.show()
                
                # X轴标签（两个图表都显示）
                x_date_str = self.get_date_str(closest_index)
                label_x_main_x = closest_x
                
                # X轴标签（主图）
                label_main_x_text_with_style = '<div style="color: black; background-color: white; border: 3px solid black; padding: 2px;">{}</div>'.format(x_date_str)
                self.x_label_main.setHtml(label_main_x_text_with_style)

                label_x_main_y = view_range[1][0]    # (view_range[1][1] - view_range[1][0]) * 0.03
                self.x_label_main.setPos(label_x_main_x, label_x_main_y)
                self.x_label_main.show()
                
                # X轴标签（底部图）
                label_x_bottom_x = closest_x
                label_x_bottom_y = bottom_view_range[1][0]  #  + (bottom_view_range[1][1] - bottom_view_range[1][0]) * 0.03 
                self.x_label_bottom.setPos(label_x_bottom_x, label_x_bottom_y)

                label_bottom_x_text_with_style = '<div style="color: black; background-color: white; border: 3px solid black; padding: 2px;">{}</div>'.format(x_date_str)
                self.x_label_bottom.setHtml(label_bottom_x_text_with_style)
                self.x_label_bottom.show()
                                
                # 更新数据标签
                self.update_label(closest_index)
            else:
                # self.logger.info("closest_index is None")
                self.hide_all_labels()
        else:
            self.hide_all_labels()

    def on_mouse_move_bottom(self, pos):
        """处理底部图表鼠标移动事件"""
        if self.bottom_plot_widget.sceneBoundingRect().contains(pos):
            mouse_point = self.bottom_plot_widget.getViewBox().mapSceneToView(pos)
            x_val = mouse_point.x()
            y_val = mouse_point.y()
            
            # 找到最近的数据点
            bar_centers = [ts for ts in self.adjusted_timestamps]
            
            closest_index = None
            min_distance = float('inf')
            
            for i, center in enumerate(bar_centers):
                distance = abs(center - x_val)
                if distance <= self.bar_width / 2:
                    if distance < min_distance:
                        min_distance = distance
                        closest_index = i
            
            if closest_index is not None:
                closest_x = bar_centers[closest_index]
                
                # 更新底部图表垂直线位置
                self.v_line_bottom.setPos(closest_x)
                self.v_line_bottom.show()
                
                # 更新底部图表水平线位置
                self.h_line_bottom.setPos(y_val)
                self.h_line_bottom.show()
                
                # 同步到主图表（只显示垂直线）
                self.v_line_main.setPos(closest_x)
                self.v_line_main.show()
                self.h_line_main.hide()  # 隐藏主图表水平线
                
                # 显示轴外标签
                # 底部图表左侧Y轴标签
                left_y_label_bottom_text = f"{y_val:.2f}"
                left_y_label_text_with_style = '<div style="color: black; background-color: white; border: 3px solid black; padding: 2px;">{}</div>'.format(left_y_label_bottom_text)
                self.left_y_label_bottom.setHtml(left_y_label_text_with_style)
                self.left_y_label_bottom.setPos(self.bottom_plot_widget.getViewBox().viewRange()[0][0], y_val)
                self.left_y_label_bottom.show()
                
                # X轴标签（两个图表都显示）
                x_date_str = self.get_date_str(closest_index)
                x_pos = closest_x
                
                # 主图表X轴标签
                self.x_label_main.setText(x_date_str)
                self.x_label_main.setPos(x_pos, self.plot_widget.getViewBox().viewRange()[1][0])
                self.x_label_main.show()
                
                # 底部图表X轴标签
                self.x_label_bottom.setText(x_date_str)
                self.x_label_bottom.setPos(x_pos, self.bottom_plot_widget.getViewBox().viewRange()[1][0])
                self.x_label_bottom.show()
                
                # 更新数据标签
                self.update_label(closest_index)
            else:
                self.hide_all_labels()
        else:
            self.hide_all_labels()

    def hide_all_labels(self):
        """隐藏所有标签和十字线"""
        self.v_line_main.hide()
        self.h_line_main.hide()
        self.v_line_bottom.hide()
        self.h_line_bottom.hide()
        self.label_main.hide()
        self.left_y_label_main.hide()
        self.right_y_label_main.hide()
        self.x_label_main.hide()
        self.left_y_label_bottom.hide()
        self.x_label_bottom.hide()

    def timestamp_to_date_str(self, timestamp):
        """将时间戳转换为日期字符串"""
        try:
            from PyQt5.QtCore import QDateTime
            qdt = QDateTime.fromMSecsSinceEpoch(int(timestamp * 1000))
            return qdt.toString('yyyy-MM-dd')
        except:
            return ""

    def get_date_str(self, index):
        row = self.data.iloc[index]
        date_str = row['date']
        return date_str

    def convert_y_to_right_axis(self, y_val):
        """将左侧Y轴值转换为右侧Y轴值"""
        try:
            # 获取左侧Y轴范围
            left_range = self.plot_widget.getViewBox().viewRange()[1]
            # 获取右侧Y轴范围
            right_range = self.right_viewbox.viewRange()[1]
            
            # 计算比例
            left_span = left_range[1] - left_range[0]
            right_span = right_range[1] - right_range[0]
            
            # 转换
            ratio = (y_val - left_range[0]) / left_span if left_span != 0 else 0
            right_y_val = right_range[0] + ratio * right_span
            
            return right_y_val
        except:
            return y_val
    
    def update_label(self, index):
        """更新标签显示"""
        if hasattr(self, 'data') and len(self.data) > index:

            if self.board_type == 0:
                self.update_label_industry(index)
            else:
                self.update_label_concept(index)
            

    def update_label_industry(self, index):
        row = self.data.iloc[index]
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

        # label_text = f"日期: {date_str}\n涨跌幅：{change_percent}%\n成交量：{total_volume} 万\n成交额: {total_amount} 亿\n净流入: {net_inflow} 亿\n上涨家数: {rising_count}\n下跌家数: {falling_count}\n均价: {avg_price}"
        # self.label_main.setText(label_text)

        label_text = f"日期: {date_str}<br>涨跌幅：{change_percent}%<br>成交量：{total_volume} 万<br>成交额: {total_amount} 亿\
            <br>净流入: {net_inflow} 亿<br>上涨家数: {rising_count}<br>下跌家数: {falling_count}<br>均价: {avg_price}<br>领涨股：{leading_stock}<br>领涨股价格：{leading_stock_price}<br>领涨股涨跌幅：{leading_stock_change_percent}%"
        text_with_style = '<div style="color: black; background-color: white; border: 3px solid black; padding: 2px;">{}</div>'.format(label_text)
        self.label_main.setHtml(text_with_style)

        self.label_main.setPos(self.adjusted_timestamps[index] + self.bar_width, 0)
        self.label_main.show()

    def update_label_concept(self, index):
        row = self.data.iloc[index]

        open_price = row['open_price']
        previous_close_price = row['previous_close']
        low_price = row['low_price']
        high_price = row['high_price']

        date_str = row['date']
        change_percent = row['change_percent']
        total_volume = row['volume']
        total_amount = row['turnover']
        net_inflow = row['net_inflow']
        rising_count = row['rising_count']
        falling_count = row['falling_count']
        rank = row['rank']

        label_text = f"日期: {date_str}<br>排名：{rank}<br>昨收：{previous_close_price}<br>今开：{open_price}<br>最高：{high_price}\
            <br>最低：{low_price}<br>涨跌幅：{change_percent}%<br>成交量：{total_volume} 万<br>成交额: {total_amount} 亿\
            <br>净流入: {net_inflow} 亿<br>上涨家数: {rising_count}<br>下跌家数: {falling_count}"
        text_with_style = '<div style="color: black; background-color: white; border: 3px solid black; padding: 2px;">{}</div>'.format(label_text)
        self.label_main.setHtml(text_with_style)

        self.label_main.setPos(self.adjusted_timestamps[index] + self.bar_width, 0)
        self.label_main.show()

    def get_row_by_date(self, date_str):
        """根据日期字符串获取对应的行数据"""
        if not hasattr(self, 'data') or self.data is None:
            return None
        
        try:
            # 确保日期列存在
            if 'date' in self.data.columns:
                # 查找匹配的行
                matching_rows = self.data[self.data['date'] == date_str]
                if not matching_rows.empty:
                    return matching_rows.iloc[0]  # 返回第一行匹配的数据
            elif 'date' in self.data.columns:
                # 如果使用的是'date'列
                matching_rows = self.data[self.data['date'].dt.strftime('%Y-%m-%d') == date_str]
                if not matching_rows.empty:
                    return matching_rows.iloc[0]
        except Exception as e:
            print(f"Error finding row by date: {e}")
        
        return None
    

    def add_time_markers(self, timestamps):
        """在X轴上添加时间节点标记但不影响数据点位置"""
        if not timestamps:
            return
            
        # 获取X轴范围
        x_range = self.plot_widget.getViewBox().viewRange()[0]
        
        # 在X轴上添加标记点（仅作视觉参考）
        for ts in timestamps:
            if x_range[0] <= ts <= x_range[1]:  # 只显示可见范围内的标记
                # 创建一个小的标记点
                marker = pg.ScatterPlotItem(
                    x=[ts], 
                    y=[0], 
                    pen=pg.mkPen('gray', width=1), 
                    brush=pg.mkBrush('gray'), 
                    size=3
                )
                self.plot_widget.addItem(marker)