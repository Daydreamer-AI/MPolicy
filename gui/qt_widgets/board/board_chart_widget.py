# 安装: pip install pyqtgraph
import os
# os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'

import pyqtgraph as pg
from pyqtgraph import DateAxisItem
from PyQt5.QtWidgets import QWidget, QVBoxLayout
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from PyQt5.QtCore import QDateTime, Qt, pyqtSlot, QPointF

from gui.qt_widgets.MComponents.custom_date_axisItem import CustomDateAxisItem

from common.logging_manager import get_logger

# class CustomDateAxisItem(DateAxisItem):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
    
#     def tickStrings(self, values, scale, spacing):
#         """重写此方法来自定义日期显示格式为'YYYY-MM-DD'"""
#         strings = []
#         for value in values:
#             # 将时间戳转换为QDateTime对象
#             qdt = QDateTime.fromMSecsSinceEpoch(value * 1000)
#             # 格式化为'2025-10-10'这样的字符串
#             date_str = qdt.toString('yyyy-MM-dd')
#             strings.append(date_str)
#         return strings

class BoardChartWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.logger = get_logger(__name__)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 创建使用日期轴的绘图窗口
        # 使用自定义的日期轴类
        self.date_axis = CustomDateAxisItem(orientation='bottom')
        self.plot_widget = pg.PlotWidget(axisItems={'bottom': self.date_axis})
        layout.addWidget(self.plot_widget)
        
        self.setup_plot_style()

    def setup_plot_style(self):
        # 设置坐标轴标签
        # 完全禁用坐标轴
        # self.plot_widget.getAxis('bottom').hide()
        # self.plot_widget.getAxis('left').hide()

        # 设置坐标轴从0开始并强制对齐
        # self.plot_widget.setXRange(0, 1)  # 设置X轴范围
        # self.plot_widget.setYRange(0, 1)  # 设置Y轴范围

        # 关键修复：禁用自动边距，手动设置边距
        # self.plot_widget.getViewBox().setContentsMargins(0, 0, 0, 0)
        
        # 设置坐标轴范围时考虑边距
        # self.plot_widget.setXRange(0, 1, padding=0)  # padding=0 消除边距
        # self.plot_widget.setYRange(0, 1, padding=0)

        # 设置坐标轴从0开始
        # self.plot_widget.setLimits(xMin=0, yMin=0)

        # 启用鼠标交互，默认开启
        self.plot_widget.setMouseEnabled(x=True, y=False)
        
        # 启用缩放和拖拽，默认开启
        # self.plot_widget.setMenuEnabled(False)

        # 连接视图范围改变信号
        self.plot_widget.sigRangeChanged.connect(self.on_range_changed)
        
        # 连接鼠标移动信号
        self.plot_widget.scene().sigMouseMoved.connect(self.on_mouse_move)

        
        self.plot_widget.setBackground('w')
        self.plot_widget.setLabel('left', '总成交量')
        self.plot_widget.setLabel('bottom', '日期')

        # 显示网格
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        
        # 添加图例
        self.plot_widget.addLegend()

        # 初始化十字线
        self.v_line = pg.InfiniteLine(angle=90, movable=True, pen=pg.mkPen('r', width=2, style=Qt.DashLine))
        self.h_line = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('r', width=2, style=Qt.DashLine))
        # self.plot_widget.addItem(self.v_line, ignoreBounds=True)
        # self.plot_widget.addItem(self.h_line, ignoreBounds=True)

        # 设置高Z值确保在最上层
        self.v_line.setZValue(1000)
        self.h_line.setZValue(1000)

        # # 确保添加到主ViewBox而不是场景
        main_viewbox = self.plot_widget.getViewBox()
        main_viewbox.addItem(self.v_line, ignoreBounds=True)
        main_viewbox.addItem(self.h_line, ignoreBounds=True)
        
        # 初始化标签
        self.label = pg.TextItem("", anchor=(0, 1))
        self.label.setZValue(1001)  # 标签也在最上层
        # self.plot_widget.addItem(self.label, ignoreBounds=True)
        main_viewbox.addItem(self.label, ignoreBounds=True)
        
        
        # 初始隐藏十字线
        self.v_line.hide()
        self.h_line.hide()
        self.label.hide()
        
    def plot_chart(self, industry_name, data):
        self.data = data
        # 清除之前的绘图
        self.plot_widget.clear()

        self.plot_widget.setTitle(f"{industry_name}趋势", color='#008080', size='12pt')
        
        # 处理数据
        if 'data_date' in data.columns:
            self.logger.info(f"data_date类型：{type(data['data_date'][0])}")

            date_list = []
            for row in data.itertuples():
                date_object = datetime.strptime(row.data_date, "%Y-%m-%d")
                date_list.append(date_object)
        else:
            timestamps = list(range(len(data)))

        
        # 将日期转换为时间戳
        timestamps = [date.timestamp() for date in date_list]

        # 计算合适的柱子宽度
        day_seconds = 24 * 60 * 60
        bar_width = 0.8 * day_seconds

        # 将柱子的中心对准日期时间点，而不是起始位置
        self.adjusted_timestamps = [ts - bar_width / 2 for ts in timestamps]


        # 再创建柱状图（后添加的会显示在上层）
        total_volume = data['total_volume'].values
        bargraph = pg.BarGraphItem(
            x0=self.adjusted_timestamps,
            height=total_volume,
            width=bar_width,
            brush=pg.mkColor(31, 119, 180, 180),  # 添加alpha通道实现半透明
            pen={'color': '#0f4d8f', 'width': 1},
            name="总成交量"
        )
        self.plot_widget.addItem(bargraph)

        # 先创建右侧Y轴和折线图（确保在柱状图之前添加）
        # 创建右侧Y轴用于显示折线图
        self.right_viewbox = pg.ViewBox()
        self.right_axis = self.plot_widget.getAxis('right')

        # 链接右侧Y轴到主视图
        self.plot_widget.scene().addItem(self.right_viewbox)
        self.plot_widget.getAxis('right').linkToView(self.right_viewbox)
        self.right_viewbox.setXLink(self.plot_widget)
        
        # 设置右侧Y轴标签
        self.plot_widget.setLabel('right', '均价', units='元')
        self.plot_widget.showAxis('right')

        # 创建折线图（移动平均线）
        # 使用柱子的中心位置作为x坐标
        line_x_positions = [ts + bar_width / 2 for ts in self.adjusted_timestamps]
        # 创建折线图
        line_data = data['avg_price'].values
        self.line_plot = self.plot_widget.plot(
            x=line_x_positions,
            y=line_data,
            pen=pg.mkPen(color='#ff7f0e', width=3),
            symbol='o',
            symbolSize=6,
            symbolBrush='#ff7f0e',
            name="均价"
        )
        # self.line_plot.setZValue(2)  # 设置较高的Z值，显示在上层
        self.right_viewbox.addItem(self.line_plot)

        # 同步两个ViewBox的视图范围
        def update_views():
            self.right_viewbox.setGeometry(self.plot_widget.getViewBox().sceneBoundingRect())
            self.right_viewbox.linkedViewChanged(self.plot_widget.getViewBox(), self.right_viewbox.XAxis)
        
        update_views()
        self.plot_widget.getViewBox().sigResized.connect(update_views)

        # 考虑柱子宽度，使柱子居中显示
        x_min = min(timestamps) - bar_width / 2
        x_max = max(timestamps) + bar_width * 1.5
        self.plot_widget.setXRange(x_min, x_max)
        
        # 设置左右两侧Y轴的范围
        y_max_bar = max(total_volume) * 1.1
        self.plot_widget.setYRange(0, y_max_bar)

        y_max_line = max(line_data) * 1.1
        self.right_viewbox.setYRange(0, y_max_line)

        self.add_bar_value_labels(self.adjusted_timestamps, total_volume, bar_width)

        return True

    def add_bar_value_labels(self, timestamps, values, bar_width):
        """在柱子顶部添加数值标签"""
        for i, (ts, val) in enumerate(zip(timestamps, values)):
            # 计算标签位置（柱子中心顶部）
            x_pos = ts + bar_width/2
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
        bar_width = 0.8 * 24 * 60 * 60  # 一天的秒数 * 0.8
        
        for i, ts in enumerate(self.adjusted_timestamps):
            # 柱子的范围是从 ts 到 ts+bar_width
            bar_center = ts + bar_width / 2  # bar_width/2
            if x_range[0] <= bar_center <= x_range[1]:
                visible_indices.append(i)
        
        if visible_indices:
            # 获取可见数据点的高度值 - 使用 iloc 按位置访问
            visible_data = [self.data['total_volume'].iloc[i] for i in visible_indices]
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
        bar_width = 0.8 * 24 * 60 * 60  # 一天的秒数 * 0.8
        
        for i, ts in enumerate(self.adjusted_timestamps):
            bar_center = ts + bar_width / 2
            if x_range[0] <= bar_center <= x_range[1]:
                visible_indices.append(i)
        
        if visible_indices:
            # 使用 iloc 按位置访问数据
            return [self.data['total_volume'].iloc[i] for i in visible_indices]
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
            else:
                tick_interval = 50
                
            # 设置Y轴刻度
            y_max = data_max * 1.1
            ticks = [(i, str(i)) for i in range(0, int(y_max) + tick_interval, tick_interval)]
            y_axis.setTicks([ticks])
        else:
            # 如果数据范围为0，设置默认刻度
            y_max = data_max * 1.1 if data_max > 0 else 100
            ticks = [(i, str(i)) for i in range(0, int(y_max) + 50, 50)]
        y_axis.setTicks([ticks])

    def on_range_changed(self):
        """当视图范围改变时调用"""
        # 根据当前可视范围调整Y轴
        self.adjust_left_y_range_to_visible_data()
        # 重新设置Y轴刻度
        visible_y_data = self.get_left_visible_y_data()
        if visible_y_data:
            self.fix_left_y_axis_ticks(visible_y_data)

    # def on_mouse_move(self, pos):
    #     """处理鼠标移动事件，限制只能在x轴节点上移动"""
    #     # self.logger.info("on_mouse_move...")
    #     # 检查鼠标是否在绘图区域内
    #     if self.plot_widget.sceneBoundingRect().contains(pos):
    #         # 显示十字线
    #         self.v_line.show()
    #         self.h_line.show()
    #         self.label.show()
            
    #         # 将场景坐标转换为视图坐标
    #         mouse_point = self.plot_widget.getViewBox().mapSceneToView(pos)
    #         x_val = mouse_point.x()
    #         y_val = mouse_point.y()
            
    #         # 更新垂直线位置（跟随鼠标x坐标）
    #         self.v_line.setPos(x_val)
            
    #         # 更新水平线位置（跟随鼠标y坐标）
    #         self.h_line.setPos(y_val)

    #         # 确保有数据存在
    #         if (hasattr(self, 'adjusted_timestamps') and hasattr(self, 'data') and 
    #             len(self.adjusted_timestamps) > 0 and len(self.data) > 0):
                
    #             # # 将场景坐标转换为视图坐标
    #             # mouse_point = self.plot_widget.getViewBox().mapSceneToView(pos)
    #             # x_val = mouse_point.x()
                
    #             # # 计算柱子中心位置
    #             # bar_width = 0.8 * 24 * 60 * 60  # 一天的秒数 * 0.8
    #             # bar_centers = [ts + bar_width / 2 for ts in self.adjusted_timestamps]
                
    #             # # 找到鼠标位置附近的柱子
    #             # closest_index = None
    #             # min_distance = float('inf')
                
    #             # for i, center in enumerate(bar_centers):
    #             #     distance = abs(center - x_val)
    #             #     # 只有当鼠标在柱子宽度范围内时才考虑该柱子
    #             #     if distance <= bar_width / 2:
    #             #         if distance < min_distance:
    #             #             min_distance = distance
    #             #             closest_index = i

    #             # # 调试信息
    #             # # self.logger.info(f"Mouse X: {x_val}, Bar centers: {bar_centers[:3]}..., Distances checked: {len(bar_centers)}")
    #             # # self.logger.info(f"Closest index: {closest_index}")
                
    #             # # 如果找到有效的柱子
    #             # if closest_index is not None:
    #             #     closest_x = bar_centers[closest_index]

    #             #     # self.logger.info(f"closest_x: {closest_x}")
                    
    #             #     # 更新垂直线位置（对齐到最近的数据节点）
    #             #     self.v_line.setPos(closest_x)
    #             #     # 水平线仍然跟随鼠标y坐标
    #             #     self.h_line.setPos(mouse_point.y())
                    
    #             #     # 显示十字线和标签
    #             #     self.v_line.show()
    #             #     self.h_line.show()
    #             #     self.label.show()
                    
    #             #     # 转换x轴时间戳为日期字符串
    #             #     try:
    #             #         timestamp_ms = int(closest_x * 1000)
    #             #         qdt = QDateTime.fromMSecsSinceEpoch(timestamp_ms)
    #             #         date_str = qdt.toString('yyyy-MM-dd')
                        
    #             #         # 获取该日期对应的完整数据行
    #             #         row_data = self.get_row_by_date(date_str)
    #             #         if row_data is not None:
    #             #             total_volume = row_data['total_volume']
    #             #             avg_price = row_data['avg_price'] if 'avg_price' in row_data else 0
                            
    #             #             # 格式化标签文本
    #             #             label_text = f"日期: {date_str}\n成交量: {total_volume}\n均价: {avg_price:.2f}\n鼠标Y: {mouse_point.y():.2f}"
    #             #             self.label.setText(label_text)
    #             #         else:
    #             #             # 如果找不到对应数据，只显示基本坐标信息
    #             #             label_text = f"日期: {date_str}\n鼠标Y: {mouse_point.y():.2f}"
    #             #             self.label.setText(label_text)

    #             #         # 将标签定位在图表上部，避免遮挡
    #             #         # y_range = self.plot_widget.getViewBox().viewRange()[1]
    #             #         # label_y = y_range[1] * 0.95
    #             #         # self.label.setPos(closest_x, label_y)
    #             #         self.label.setPos(closest_x, mouse_point.y())

    #             #     except Exception as e:
    #             #         print(f"Error in mouse move: {e}")
    #             #         pass
    #             # 将场景坐标转换为视图坐标
    #             mouse_point = self.plot_widget.getViewBox().mapSceneToView(pos)
    #             x_val = mouse_point.x()
                
    #             # 找到最接近的x坐标数据点
    #             bar_width = 0.8 * 24 * 60 * 60  # 一天的秒数 * 0.8
    #             bar_centers = [ts + bar_width / 2 for ts in self.adjusted_timestamps]  # 柱子中心位置
    #             distances = [abs(center - x_val) for center in bar_centers]

    #             # self.logger.info(f"Mouse X: {x_val}, Bar centers: {bar_centers[:3]}..., Distances checked: {len(bar_centers)}")
    #             # self.logger.info(f"distances: {distances}")

    #             if distances:
    #                 closest_index = distances.index(min(distances))
    #                 closest_x = bar_centers[closest_index]
                    
    #                 # 更新垂直线位置（对齐到最近的数据节点）
    #                 self.v_line.setPos(closest_x)
    #                 # 水平线仍然跟随鼠标y坐标
    #                 self.h_line.setPos(mouse_point.y())
                    
    #                 # 转换x轴时间戳为日期字符串
    #                 try:
    #                     # timestamp_ms = int(closest_x * 1000)
    #                     # qdt = QDateTime.fromMSecsSinceEpoch(timestamp_ms)
    #                     # date_str = qdt.toString('yyyy-MM-dd')
                        
    #                     # 获取对应的移动平均值
    #                     # line_y_value = self.line_data[closest_index] if hasattr(self, 'line_data') else 0
                        
    #                     # 格式化标签文本
    #                     # label_text = f"日期: {date_str}\n销售额: {closest_y}\n移动平均: {line_y_value:.2f}\n鼠标Y: {mouse_point.y():.2f}"
    #                     # self.label.setText(label_text)
                        
    #                     # 将标签定位在数据节点附近
    #                     y_range = self.plot_widget.getViewBox().viewRange()[1]
    #                     label_y = y_range[1] * 0.95  # 放在图表上部
    #                     self.label.setPos(closest_x, label_y)
    #                 except Exception as e:
    #                     print(f"Error in mouse move: {e}")
    #                     pass
    #             else:
    #                 self.logger.warning("No closest bar found.")
    #                 # 没有靠近任何柱子时隐藏十字线
    #                 self.v_line.hide()
    #                 self.h_line.hide()
    #                 self.label.hide()
    #         else:
    #             self.logger.warning("No data available.")
    #             # 没有数据时隐藏十字线
    #             self.v_line.hide()
    #             self.h_line.hide()
    #             self.label.hide()
    #     else:
    #         # 鼠标移出绘图区域时隐藏十字线
    #         self.v_line.hide()
    #         self.h_line.hide()
    #         self.label.hide()

    def on_mouse_move(self, pos):
        """处理鼠标移动事件，显示十字线"""
        # 检查鼠标是否在绘图区域内
        if self.plot_widget.sceneBoundingRect().contains(pos):
            # self.logger.info(f"Mouse move: {pos}")
            # 显示十字线
            self.v_line.show()
            self.h_line.show()
            self.label.show()

            # 添加调试信息确认十字线状态
            # self.logger.info(f"Crosshair visibility - V line: {self.v_line.isVisible()}, H line: {self.h_line.isVisible()}")
            # self.logger.info(f"Crosshair Z values - V line: {self.v_line.zValue()}, H line: {self.h_line.zValue()}")
        
            
            # 将场景坐标转换为视图坐标
            mouse_point = self.plot_widget.getViewBox().mapSceneToView(pos)
            x_val = mouse_point.x()
            y_val = mouse_point.y()

            # self.logger.info(f"Mouse X: {x_val}, Mouse Y: {y_val}")
            
            # 更新垂直线位置（跟随鼠标x坐标）
            self.v_line.setPos(x_val)
            # self.logger.info(f"V line position set to: {x_val}")
            
            # 更新水平线位置（跟随鼠标y坐标）
            self.h_line.setPos(y_val)
            # self.logger.info(f"H line position set to: {y_val}")
            
            # 更新标签文本和位置
            try:
                # 转换x轴时间戳为日期字符串
                timestamp_ms = int(x_val * 1000)
                qdt = QDateTime.fromMSecsSinceEpoch(timestamp_ms)
                date_str = qdt.toString('yyyy-MM-dd')
                
                # 格式化标签文本
                label_text = f"日期: {date_str}\nX: {x_val:.2f}\nY: {y_val:.2f}"
                self.label.setText(label_text)
                
                # 将标签定位在鼠标附近
                self.label.setPos(x_val, y_val)
            except Exception as e:
                self.logger.error(f"Error updating crosshair label: {e}")
                pass
                
        else:
            # 鼠标移出绘图区域时隐藏十字线
            self.v_line.hide()
            self.h_line.hide()
            self.label.hide()

    def get_row_by_date(self, date_str):
        """根据日期字符串获取对应的行数据"""
        if not hasattr(self, 'data') or self.data is None:
            return None
        
        try:
            # 确保日期列存在
            if 'data_date' in self.data.columns:
                # 查找匹配的行
                matching_rows = self.data[self.data['data_date'] == date_str]
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