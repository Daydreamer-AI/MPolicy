import pyqtgraph as pg
from pyqtgraph import DateAxisItem
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import QDateTime
import numpy as np
from datetime import datetime, timedelta
import sys

class CustomDateAxisItem(DateAxisItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def tickStrings(self, values, scale, spacing):
        """重写此方法来自定义日期显示格式为'YYYY-MM-DD'"""
        strings = []
        for value in values:
            # 关键修复：将浮点数转换为整数
            timestamp_ms = int(value * 1000)  # 转换为整数毫秒
            qdt = QDateTime.fromMSecsSinceEpoch(timestamp_ms)
            date_str = qdt.toString('yyyy-MM-dd')
            strings.append(date_str)
        return strings

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("日期轴柱状图示例")
        self.resize(1366, 768)
        
        # 创建中央部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 关键修改：使用自定义的日期轴类
        self.date_axis = CustomDateAxisItem(orientation='bottom')
        self.plot_widget = pg.PlotWidget(axisItems={'bottom': self.date_axis})
        layout.addWidget(self.plot_widget)

        self.plot_widget.setMouseEnabled(x=True, y=False)
        # 在初始化时启用自动范围调整，即使禁用y轴鼠标交互
        self.plot_widget.getViewBox().enableAutoRange(axis=pg.ViewBox.XAxis, enable=True)
        self.plot_widget.getViewBox().enableAutoRange(axis=pg.ViewBox.YAxis, enable=True)

        # 连接视图范围改变信号
        self.plot_widget.sigRangeChanged.connect(self.on_range_changed)

        # self.plot_widget.getViewBox().setContentsMargins(0, 0, 0, 0)
        # plot_item = self.plot_widget.getPlotItem()
        # plot_item.setDefaultPadding(0)          # 消除原点间距

        
        # 禁用自动调整
        # view_box = plot_item.getViewBox()
        # view_box.setAutoPan(False, False)
        # view_box.setMouseEnabled(False, False)
        
        # 设置图表样式
        self.setup_plot_style()
        # 创建示例数据并绘图
        self.plot_date_bar_chart()
    
    def setup_plot_style(self):
        """设置图表样式"""
        self.plot_widget.setBackground('w')
        self.plot_widget.setTitle("销售数据趋势", color='#008080', size='12pt')
        self.plot_widget.setLabel('left', '销售额', units='元')
        self.plot_widget.setLabel('bottom', '日期')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.addLegend()
    
    def plot_date_bar_chart(self):
        """绘制日期轴柱状图"""
        
        # 准备日期和数据
        base_date = datetime(2025, 10, 1)
        date_list = [base_date + timedelta(days=i) for i in range(10)]
        
        # 生成示例销售额数据
        self.sales_data = np.random.randint(1000, 5000, size=len(date_list))
        
        # 将日期转换为时间戳
        timestamps = [date.timestamp() for date in date_list]
        
        # 计算合适的柱子宽度
        day_seconds = 24 * 60 * 60
        bar_width = 0.8 * day_seconds

        # 关键修改：调整柱子的位置，使日期标签位于柱子中间
        # 将柱子的中心对准日期时间点，而不是起始位置
        self.adjusted_timestamps = [ts - bar_width/2 for ts in timestamps]
        
        # 创建柱状图
        bargraph = pg.BarGraphItem(
            x0=self.adjusted_timestamps,
            height=self.sales_data,
            width=bar_width,
            brush='#1f77b4',
            pen={'color': '#0f4d8f', 'width': 1},
            name="日销售额"
        )
        
        self.plot_widget.addItem(bargraph)
        
        # 调整视图范围
        # x_min = min(timestamps) - day_seconds
        # x_max = max(timestamps) + day_seconds
        # self.plot_widget.setXRange(x_min, x_max)
        
        # y_max = max(sales_data) * 1.1
        # self.plot_widget.setYRange(0, y_max)

        # 考虑柱子宽度，使柱子居中显示
        x_min = min(timestamps) - bar_width/2
        x_max = max(timestamps) + bar_width * 1.5
        self.plot_widget.setXRange(x_min, x_max)
        
        y_max = max(self.sales_data) * 1.1
        print(f"y_max: {y_max}")
        self.plot_widget.setYRange(0, y_max)
        
        # 可选：添加数据标签显示在柱子顶部
        self.add_value_labels(self.adjusted_timestamps, self.sales_data, bar_width)
        self.fix_y_axis_ticks(self.sales_data)

    def add_value_labels(self, timestamps, values, bar_width):
        """在柱子顶部添加数值标签"""
        for i, (ts, val) in enumerate(zip(timestamps, values)):
            # 计算标签位置（柱子中心顶部）
            x_pos = ts + bar_width/2
            y_pos = val + 0.05  # 稍微高于柱子顶部
            
            # 创建文本项
            text = pg.TextItem(text=f"{val}", color=(0, 0, 0), anchor=(0.5, 1))
            text.setPos(x_pos, y_pos)
            self.plot_widget.addItem(text)

    def get_visible_y_data(self):
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
            return [self.sales_data[i] for i in visible_indices]
        return []

    def fix_y_axis_ticks(self, sales_data):
        """修复Y轴刻度显示，确保显示为整数"""
        # 获取Y轴对象
        y_axis = self.plot_widget.getAxis('left')
        
        # if sales_data.empty:
        #     return
            
        # 计算合适的刻度间隔
        data_min, data_max = min(sales_data), max(sales_data)
        data_range = data_max - data_min

        # 确保最小显示范围
        # 设置最小显示范围
        # MIN_DISPLAY_RANGE = 100  # 最小显示范围设置为100
        # if data_range < MIN_DISPLAY_RANGE:
        #     center = (data_min + data_max) / 2
        #     data_min = max(0, center - MIN_DISPLAY_RANGE / 2)
        #     data_max = center + MIN_DISPLAY_RANGE / 2
        #     data_range = MIN_DISPLAY_RANGE
        
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
        # 根据当前可视范围调整Y轴
        self.adjust_y_range_to_visible_data()
        # 重新设置Y轴刻度
        visible_y_data = self.get_visible_y_data()
        if visible_y_data:
            self.fix_y_axis_ticks(visible_y_data)

    def adjust_y_range_to_visible_data(self):
        """根据X轴范围内可见数据调整Y轴范围"""
        vb = self.plot_widget.getViewBox()
        x_range = vb.viewRange()[0]  # 获取X轴范围
        
        # 找到在当前X轴范围内的数据点
        visible_indices = []
        for i, ts in enumerate(self.adjusted_timestamps):
            # 柱子的范围是从 ts 到 ts+bar_width
            bar_center = ts + 0.8 * 24 * 60 * 60 / 2  # bar_width/2
            if x_range[0] <= bar_center <= x_range[1]:
                visible_indices.append(i)
        
        if visible_indices:
            # 获取可见数据点的高度值
            visible_data = [self.sales_data[i] for i in visible_indices]
            if visible_data:
                y_min, y_max = min(visible_data), max(visible_data)
                # 设置Y轴范围，增加一些边距 (10%)
                vb.setYRange(0, y_max * 1.1)


    def get_x_zoom_ratio(self):
        """获取x轴当前缩放比例"""
        # 初始缩放比例：0.7851121287553338
        vb = self.plot_widget.getViewBox()
        # 获取当前视图范围 [min, max]
        x_range = vb.viewRange()[0]
        # 计算当前显示的范围宽度
        current_width = x_range[1] - x_range[0]
        
        # 如果需要相对于数据总范围的比例，需要保存原始数据范围
        # 假设你知道数据的总范围，比如：
        data_width = max(self.adjusted_timestamps) - min(self.adjusted_timestamps)
        zoom_ratio = data_width / current_width
        
        return zoom_ratio

    def get_x_zoom_ratio_from_transform(self):
        """通过坐标变换矩阵获取缩放比例"""
        # 无论怎么缩放，都是1
        vb = self.plot_widget.getViewBox()
        # 获取当前的变换矩阵
        transform = vb.transform()
        # 获取x轴的缩放因子 (m11元素)
        x_scale = transform.m11()
        return x_scale
    
    def get_x_scale_factor(self):
        """获取x轴每像素代表的数据单位数"""
        # 初始值：1642.507091121294
        vb = self.plot_widget.getViewBox()
        # 获取视图范围
        x_range = vb.viewRange()[0]
        # 获取视图的像素宽度
        view_width_px = vb.width()
        # 计算每像素代表的数据单位数
        if view_width_px > 0:
            scale_factor = (x_range[1] - x_range[0]) / view_width_px
            return scale_factor
        return 1.0

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()