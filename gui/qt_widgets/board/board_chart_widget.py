# 安装: pip install pyqtgraph
import os
# os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'

import pyqtgraph as pg
from pyqtgraph import DateAxisItem
from PyQt5.QtWidgets import QWidget, QVBoxLayout
import pandas as pd
import numpy as np
from datetime import datetime

class BoardChartWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 创建使用日期轴的绘图窗口
        self.plot_widget = pg.PlotWidget()
        layout.addWidget(self.plot_widget)
        
        self.setup_plot_style()

    def setup_plot_style(self):
        self.plot_widget.setBackground('w')

        # 设置坐标轴标签
        # 完全禁用坐标轴
        # self.plot_widget.getAxis('bottom').hide()
        # self.plot_widget.getAxis('left').hide()
        self.plot_widget.setLabel('left', '平均价格')
        self.plot_widget.setLabel('bottom', '交易日期')

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
        # self.plot_widget.setMouseEnabled(x=False, y=False)
        
        # 启用缩放和拖拽，默认开启
        # self.plot_widget.setMenuEnabled(False)

        
        # 显示网格
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        
        # 添加图例
        self.plot_widget.addLegend()
        
    def plot_chart(self, industry_name, data):
        # 清除之前的绘图
        self.plot_widget.clear()

        self.plot_widget.setTitle(f"{industry_name}趋势", color='#008080', size='12pt')
        
        # 处理数据
        # if 'data_date' in data.columns:
        #     data = data.copy()
        #     data['date'] = pd.to_datetime(data['data_date'])
        #     data = data.sort_values('date')
        #     timestamps = [d.timestamp() for d in data['date']]
        #     dates = data['date'].tolist()
        # else:
        #     timestamps = list(range(len(data)))
        #     dates = [datetime.fromtimestamp(ts) for ts in timestamps]
            
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



        return True
        