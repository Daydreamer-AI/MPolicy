import pyqtgraph as pg
from pyqtgraph import DateAxisItem
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from PyQt5.QtCore import QDateTime, Qt, pyqtSlot, QPointF, QTimer

from gui.qt_widgets.MComponents.custom_date_axisItem import CustomDateAxisItem, NoLabelAxis

from common.logging_manager import get_logger


class BoardChangePercentChartWidget(QWidget):
    def __init__(self, type=0):
        super().__init__()
        self.logger = get_logger(__name__)

        self.board_type = type
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # self.date_axis_main = NoLabelAxis(orientation='bottom')
        # self.plot_widget = pg.PlotWidget(axisItems={'bottom': self.date_axis_main})
        self.plot_widget = pg.PlotWidget()
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
        self.left_y_label_main.hide()
        # self.right_y_label_main.hide()
        self.x_label_main.hide()

    def draw_chart(self, data):
        if self.board_type == 0:
            s_board_name = "industry_name"
            field_name = "change_percent"
            display_name = "涨跌幅"
            self.top_10 = data.nlargest(10, 'change_percent')      # 涨幅前十
            self.bottom_10 = data.nsmallest(10, 'change_percent')  # 跌幅前十
        else:
            s_board_name = "concept_name"
            field_name = "board_change_percent"
            display_name = "涨跌幅"
            self.top_10 = data.nlargest(10, 'board_change_percent')      # 涨幅前十
            self.bottom_10 = data.nsmallest(10, 'board_change_percent')  # 跌幅前十

        if field_name not in data.columns:
            self.logger.error(f"{field_name}字段不存在于数据中！")
            return False
        
        self.data = data
        # 清除之前的绘图
        self.plot_widget.clear()
        # board_name = getattr(data, s_board_name, None)
        self.plot_widget.setTitle(f"涨跌幅Top 10", color='#008080', size='12pt')

        # 创建x轴位置（共10个位置，每个位置绘制两个柱子）
        self.x_positions = list(range(10))
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
        top_names = self.top_10[s_board_name].tolist()  # 假设字段名为industry_name
        bottom_names = self.bottom_10[s_board_name].tolist()
        self.add_bar_value_labels(top_names, top_values, bottom_names, bottom_values)

    def add_bar_value_labels(self, top_names, top_values, bottom_names, bottom_values):
        y_range = self.plot_widget.viewRange()[1]  # 获取y轴范围
        y_span = y_range[1] - y_range[0]
        offset = y_span * 0.03
        
        for i, (top_name, bottom_name) in enumerate(zip(top_names, bottom_names)):
            # 涨幅行业名称（上方）
            top_text = pg.TextItem(top_name[:8] + '...' if len(top_name) > 8 else top_name, anchor=(0.5, 1))
            top_text.setPos(i, top_values[i] + offset)
            top_text.setColor(pg.mkColor('k'))
            font = pg.QtGui.QFont()
            font.setPointSize(7)
            top_text.setFont(font)
            self.plot_widget.addItem(top_text)
            
            # 跌幅行业名称（下方）
            bottom_text = pg.TextItem(bottom_name[:8] + '...' if len(bottom_name) > 8 else bottom_name, anchor=(0.5, 0))
            bottom_text.setPos(i, bottom_values[i] - offset)
            bottom_text.setColor(pg.mkColor('k'))
            bottom_text.setFont(font)
            self.plot_widget.addItem(bottom_text)
        
        # 添加数值标签
        for i, (top_val, bottom_val) in enumerate(zip(top_values, bottom_values)):
            # 涨幅数值标签
            if top_val > 0:
                top_text = pg.TextItem(f"+{top_val:.2f}%", anchor=(0.5, 0))
                top_text.setPos(i, top_val + offset)
                top_text.setColor(pg.mkColor('k'))
                font = pg.QtGui.QFont()
                font.setPointSize(7)
                top_text.setFont(font)
                self.plot_widget.addItem(top_text)
            
            # 跌幅数值标签
            if bottom_val < 0:
                bottom_text = pg.TextItem(f"{bottom_val:.2f}%", anchor=(0.5, 1))
                bottom_text.setPos(i, bottom_val - offset)
                bottom_text.setColor(pg.mkColor('k'))
                bottom_text.setFont(font)
                self.plot_widget.addItem(bottom_text)


    def on_range_changed(self):
        pass

    def on_mouse_move(self, pos):
        return
        if self.plot_widget.sceneBoundingRect().contains(pos):
            mouse_point = self.plot_widget.getViewBox().mapSceneToView(pos)
            x_val = mouse_point.x()
            y_val = mouse_point.y()

            bar_centers = [ts + self.bar_width / 2 for ts in self.x_positions]
            
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
                bottom_view_range = self.bottom_plot_widget.getViewBox().viewRange()
                closest_x = bar_centers[closest_index]