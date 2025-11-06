# 安装: pip install pyqtgraph
import os
# os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'

import pyqtgraph as pg
from pyqtgraph import DateAxisItem
from PyQt5.QtWidgets import QWidget, QVBoxLayout
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from PyQt5.QtCore import QDateTime

from gui.qt_widgets.MComponents.custom_date_axisItem import CustomDateAxisItem

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
        self.plot_widget.sigRangeChanged.connect(self.slot_range_changed)
        
        # 连接鼠标移动信号
        self.plot_widget.scene().sigMouseMoved.connect(self.slot_mouse_move)

        
        self.plot_widget.setBackground('w')
        self.plot_widget.setLabel('left', '总成交量')
        self.plot_widget.setLabel('bottom', '交易日期')

        # 显示网格
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        
        # 添加图例
        self.plot_widget.addLegend()
        
    def plot_chart(self, industry_name, data):
        # 清除之前的绘图
        self.plot_widget.clear()

        self.plot_widget.setTitle(f"{industry_name}趋势", color='#008080', size='12pt')
        
        # 处理数据
        if 'data_date' in data.columns:
            data = data.copy()
            data['date'] = pd.to_datetime(data['data_date'])
            data = data.sort_values('date')
            timestamps = [d.timestamp() for d in data['date']]
            dates = data['date'].tolist()
        else:
            timestamps = list(range(len(data)))
            dates = [datetime.fromtimestamp(ts) for ts in timestamps]

        # 计算合适的柱子宽度
        day_seconds = 24 * 60 * 60
        bar_width = 0.8 * day_seconds
        # 动态计算柱子宽度
        # if len(timestamps) > 1:
        #     # 计算相邻时间点的最小间隔
        #     time_intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
        #     min_interval = min(time_intervals)
        #     bar_width = 0.8 * min_interval  # 柱子占80%的最小时间间隔
        # else:
        #     # 只有一个数据点时使用默认一天宽度
        #     day_seconds = 24 * 60 * 60
        #     bar_width = 0.8 * day_seconds

        # 将柱子的中心对准日期时间点，而不是起始位置
        self.adjusted_timestamps = [ts - bar_width*0.92 for ts in timestamps]

        # 创建柱状图
        total_volume = data['total_volume'].values
        bargraph = pg.BarGraphItem(
            x0=self.adjusted_timestamps,
            height=total_volume,
            width=bar_width,
            brush='#1f77b4',
            pen={'color': '#0f4d8f', 'width': 1},
            name="总成交量"
        )

        self.plot_widget.addItem(bargraph)

        # 考虑柱子宽度，使柱子居中显示
        x_min = min(timestamps) - bar_width/2
        x_max = max(timestamps) + bar_width * 1.5
        self.plot_widget.setXRange(x_min, x_max)
        
        # 设置左右两侧Y轴的范围
        y_max_bar = max(total_volume) * 1.1
        self.plot_widget.setYRange(0, y_max_bar)

        # y_max_line = max(self.line_data) * 1.1
        # self.right_viewbox.setYRange(0, y_max_line)

        self.add_bar_value_labels(self.adjusted_timestamps, total_volume, bar_width)
            
        # 绘制价格线
        # count = list(range(len(data)))
        # if 'avg_price' in data.columns:
        #     price_line = self.plot_widget.plot(
        #         count, 
        #         count,
        #         pen=pg.mkPen(color='r', width=2),
        #         name='价格',
        #         symbol='o', 
        #         symbolSize=6,
        #         symbolBrush='b'
        #     )
            
        # 设置X轴标签格式
        # axis = self.plot_widget.getAxis('bottom')
        # 自定义刻度标签
        # ticks = []
        # 选择一些关键日期作为标签
        # step = max(1, len(timestamps) // 10)  # 大约显示10个标签
        # for i in range(0, len(timestamps), step):
        #     ticks.append((timestamps[i], dates[i].strftime('%Y-%m-%d')))
        
        # axis.setTicks([ticks])
            
        # 绘制成交量柱状图
        # if 'total_volume' in data.columns:
        #     # 创建第二个Y轴
        #     volume_plot = pg.ViewBox()
        #     self.plot_widget.scene().addItem(volume_plot)
        #     self.plot_widget.getAxis('right').linkToView(volume_plot)
        #     volume_plot.setXLink(self.plot_widget)
            
        #     # 绘制柱状图
        #     bars = pg.BarGraphItem(
        #         x=timestamps,
        #         height=data['total_volume'].values,
        #         width=(timestamps[1] - timestamps[0]) * 0.8 if len(timestamps) > 1 else 1,
        #         brush='b'
        #     )
        #     volume_plot.addItem(bars)

        # self.plot_date_bar_chart()

        return True
    
    def plot_date_bar_chart(self):
        """绘制日期轴柱状图"""
        
        # 关键步骤2：准备日期和数据
        # 生成示例日期（例如：2025-10-01 到 2025-10-10）
        base_date = datetime(2025, 10, 1)
        date_list = [base_date + timedelta(days=i) for i in range(10)]
        
        # 生成示例销售额数据
        sales_data = np.random.randint(1000, 5000, size=len(date_list))
        
        # 关键步骤3：将日期转换为时间戳（PyQtGraph内部使用）
        # DateAxisItem需要数值型的时间戳作为X轴数据[2,4](@ref)
        timestamps = [date.timestamp() for date in date_list]
        
        # 关键步骤4：计算合适的柱子宽度
        # 一天的秒数，确保柱子宽度与日期间隔匹配[4](@ref)
        day_seconds = 24 * 60 * 60
        # 柱子宽度设置为0.8天，使柱子间有间隙
        bar_width = 0.8 * day_seconds
        
        # 关键步骤5：创建柱状图
        bargraph = pg.BarGraphItem(
            x0=timestamps, # 使用时间戳作为X轴数据
            height=sales_data,
            width=bar_width, # 设置柱子宽度
            brush='#1f77b4', # 设置柱子颜色
            pen={'color': '#0f4d8f', 'width': 1}, # 设置边框
            name="日销售额"
        )
        
        self.plot_widget.addItem(bargraph)
        
        # 关键步骤6：调整视图范围，确保所有柱子可见
        # 设置X轴范围，包含所有日期并留有一些边距
        x_min = min(timestamps) - day_seconds
        x_max = max(timestamps) + day_seconds
        self.plot_widget.setXRange(x_min, x_max)
        
        # 设置Y轴范围，留出一些顶部空间
        y_max = max(sales_data) * 1.1
        self.plot_widget.setYRange(0, y_max)
    
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
    def slot_range_changed(self):
        # 根据当前可视范围调整Y轴
        # 重新设置Y轴刻度
        pass

    def slot_mouse_move(self, pos):
        pass