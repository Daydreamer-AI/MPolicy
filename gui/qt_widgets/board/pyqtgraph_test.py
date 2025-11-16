import pyqtgraph as pg
from pyqtgraph import DateAxisItem, AxisItem
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QGraphicsItem
from PyQt5.QtCore import QDateTime, Qt
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
        
        # 使用自定义的日期轴类
        self.date_axis = CustomDateAxisItem(orientation='bottom')
        self.plot_widget = pg.PlotWidget(axisItems={'bottom': self.date_axis})
        layout.addWidget(self.plot_widget)

        self.plot_widget.setMouseEnabled(x=True, y=False)
        # 在初始化时启用自动范围调整，即使禁用y轴鼠标交互
        # self.plot_widget.getViewBox().enableAutoRange(axis=pg.ViewBox.XAxis, enable=True)
        # self.plot_widget.getViewBox().enableAutoRange(axis=pg.ViewBox.YAxis, enable=True)

        # 连接视图范围改变信号
        self.plot_widget.sigRangeChanged.connect(self.on_range_changed)
        
        # 连接鼠标移动信号
        self.plot_widget.scene().sigMouseMoved.connect(self.on_mouse_move)

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

        # 初始化十字线
        self.v_line = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('r', width=1, style=Qt.DashLine))
        self.h_line = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('r', width=1, style=Qt.DashLine))
        self.plot_widget.addItem(self.v_line, ignoreBounds=True)
        self.plot_widget.addItem(self.h_line, ignoreBounds=True)
        
        # 初始化标签
        self.label = pg.TextItem("", anchor=(0, 1))
        self.plot_widget.addItem(self.label, ignoreBounds=True)
        
        # 初始隐藏十字线
        self.v_line.hide()
        self.h_line.hide()
        self.label.hide()
    
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
        date_list = [base_date + timedelta(days=i) for i in range(100)]
        
        # 生成示例销售额数据
        self.sales_data = np.random.randint(1000, 5000, size=len(date_list))

        # 生成折线图数据（例如7日移动平均线）
        self.line_data = self.calculate_moving_average(self.sales_data, window=7)
        
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

        # 创建右侧Y轴用于显示折线图
        self.right_viewbox = pg.ViewBox()
        self.right_axis = self.plot_widget.getAxis('right')

        # 链接右侧Y轴到主视图
        self.plot_widget.scene().addItem(self.right_viewbox)
        self.plot_widget.getAxis('right').linkToView(self.right_viewbox)
        self.right_viewbox.setXLink(self.plot_widget)
        
        # 设置右侧Y轴标签
        self.plot_widget.setLabel('right', '移动平均', units='元')
        self.plot_widget.showAxis('right')

        # 创建折线图（移动平均线）
        # 使用柱子的中心位置作为x坐标
        line_x_positions = [ts + bar_width/2 for ts in self.adjusted_timestamps]

        # 创建折线图
        self.line_plot = self.plot_widget.plot(
            x=line_x_positions,
            y=self.line_data,
            pen=pg.mkPen(color='#ff7f0e', width=3),
            symbol='o',
            symbolSize=6,
            symbolBrush='#ff7f0e',
            name="7日移动平均"
        )

        self.right_viewbox.addItem(self.line_plot)

        # 同步两个ViewBox的视图范围
        def update_views():
            self.right_viewbox.setGeometry(self.plot_widget.getViewBox().sceneBoundingRect())
            self.right_viewbox.linkedViewChanged(self.plot_widget.getViewBox(), self.right_viewbox.XAxis)
        
        update_views()
        self.plot_widget.getViewBox().sigResized.connect(update_views)
        
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
        
        # 设置左右两侧Y轴的范围
        y_max_bar = max(self.sales_data) * 1.1
        y_max_line = max(self.line_data) * 1.1
        self.plot_widget.setYRange(0, y_max_bar)
        self.right_viewbox.setYRange(0, y_max_line)
        
        # 可选：添加数据标签显示在柱子顶部
        # self.add_value_labels(self.adjusted_timestamps, self.sales_data, bar_width)
        self.fix_y_axis_ticks(self.sales_data)
        # self.fix_right_y_axis_ticks(self.line_data)

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

    def calculate_moving_average(self, data, window=7):
        """计算移动平均线"""
        if len(data) < window:
            return data
        
        moving_avg = []
        for i in range(len(data)):
            if i < window - 1:
                # 对于前几个数据点，使用可用数据的平均值
                avg = np.mean(data[:i+1])
            else:
                # 计算window天的移动平均
                avg = np.mean(data[i-window+1:i+1])
            moving_avg.append(avg)
        
        return moving_avg

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

    def on_mouse_move(self, pos):
        """处理鼠标移动事件，限制只能在x轴节点上移动"""
        # 检查鼠标是否在绘图区域内
        if self.plot_widget.sceneBoundingRect().contains(pos):
            # 确保有数据存在
            if (hasattr(self, 'adjusted_timestamps') and hasattr(self, 'sales_data') and 
                len(self.adjusted_timestamps) > 0 and len(self.sales_data) > 0):
                
                # 将场景坐标转换为视图坐标
                mouse_point = self.plot_widget.getViewBox().mapSceneToView(pos)
                x_val = mouse_point.x()
                
                # 计算柱子中心位置
                bar_width = 0.8 * 24 * 60 * 60  # 一天的秒数 * 0.8
                bar_centers = [ts + bar_width / 2 for ts in self.adjusted_timestamps]
                
                # 找到鼠标位置附近的柱子
                closest_index = None
                min_distance = float('inf')
                
                for i, center in enumerate(bar_centers):
                    distance = abs(center - x_val)
                    # 只有当鼠标在柱子宽度范围内时才考虑该柱子
                    if distance <= bar_width / 2:
                        if distance < min_distance:
                            min_distance = distance
                            closest_index = i
                
                # 如果找到有效的柱子
                if closest_index is not None:
                    closest_x = bar_centers[closest_index]
                    closest_y = self.sales_data[closest_index]
                    
                    # 更新垂直线位置（对齐到最近的数据节点）
                    self.v_line.setPos(closest_x)
                    # 水平线仍然跟随鼠标y坐标
                    self.h_line.setPos(mouse_point.y())
                    
                    # 显示十字线和标签
                    self.v_line.show()
                    self.h_line.show()
                    self.label.show()
                    
                    # 转换x轴时间戳为日期字符串
                    try:
                        timestamp_ms = int(closest_x * 1000)
                        qdt = QDateTime.fromMSecsSinceEpoch(timestamp_ms)
                        date_str = qdt.toString('yyyy-MM-dd')
                        
                        # 获取对应的移动平均值
                        line_y_value = self.line_data[closest_index] if hasattr(self, 'line_data') else 0
                        
                        # 格式化标签文本
                        label_text = f"日期: {date_str}\n销售额: {closest_y}\n移动平均: {line_y_value:.2f}\n鼠标Y: {mouse_point.y():.2f}"
                        self.label.setText(label_text)
                        
                        # 将标签定位在图表上部，避免遮挡
                        # y_range = self.plot_widget.getViewBox().viewRange()[1]
                        # label_y = y_range[1] * 0.95
                        # self.label.setPos(closest_x, label_y)
                        self.label.setPos(closest_x, mouse_point.y())

                    except Exception as e:
                        print(f"Error in mouse move: {e}")
                        pass
                else:
                    # 没有靠近任何柱子时隐藏十字线
                    self.v_line.hide()
                    self.h_line.hide()
                    self.label.hide()
            else:
                # 没有数据时隐藏十字线
                self.v_line.hide()
                self.h_line.hide()
                self.label.hide()
        else:
            # 鼠标移出绘图区域时隐藏十字线
            self.v_line.hide()
            self.h_line.hide()
            self.label.hide()


class NoLabelAxis(AxisItem):
    def tickStrings(self, values, scale, spacing):
        # 返回空字符串列表，隐藏所有刻度值
        return [""] * len(values)

class MWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("日期轴柱状图示例")
        self.resize(1366, 768)

        layout = QVBoxLayout(self)

        # self.plot_widget = pg.PlotWidget()      # 默认自带X、Y轴，默认x、y轴鼠标交互。
        # 使用自定义的无标签轴
        x_axis = NoLabelAxis(orientation='bottom')
        self.plot_widget = pg.PlotWidget(axisItems={'bottom': x_axis})
        self.plot_widget.setMouseEnabled(x=True, y=False)

        # self.plot_widget.showAxis('bottom', show=False)   # 隐藏X轴，效果不好

        layout.addWidget(self.plot_widget)

        # 初始化十字线
        self.v_line = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('r', width=1, style=Qt.DashLine))
        self.h_line = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('r', width=1, style=Qt.DashLine))
        self.v_line.setZValue(1000)
        self.h_line.setZValue(1000)
        self.plot_widget.addItem(self.v_line, ignoreBounds=True)
        self.plot_widget.addItem(self.h_line, ignoreBounds=True)

        # 初始化标签
        self.label = pg.TextItem("", anchor=(0, 1))
        self.label.setZValue(1000)
        self.plot_widget.addItem(self.label, ignoreBounds=True)

        # 主图x轴标签
        self.x_label_main = pg.TextItem("", anchor=(0.5, 0.5))
        self.x_label_main.setFont(pg.QtGui.QFont("Arial", 9))
        self.x_label_main.setColor(pg.QtGui.QColor(255, 0, 0))  # 红色
        self.x_label_main.setZValue(1000)
        self.plot_widget.addItem(self.x_label_main, ignoreBounds=True)

        # 主图表左y轴标签
        self.left_y_label_main = pg.TextItem("", anchor=(1, 0.5))  # 左侧Y轴标签
        self.left_y_label_main.setFont(pg.QtGui.QFont("Arial", 9))
        self.left_y_label_main.setColor(pg.QtGui.QColor(255, 0, 0))  # 红色
        self.left_y_label_main.setZValue(1000)
        self.plot_widget.addItem(self.left_y_label_main, ignoreBounds=True)

        # 主图右y轴标签
        self.right_y_label_main = pg.TextItem("", anchor=(0, 0.5))  # 左侧Y轴标签
        self.right_y_label_main.setFont(pg.QtGui.QFont("Arial", 9))
        self.right_y_label_main.setColor(pg.QtGui.QColor(255, 0, 0))  # 红色
        self.right_y_label_main.setZValue(1000)
        self.plot_widget.addItem(self.right_y_label_main, ignoreBounds=True)

        # 初始隐藏十字线及标签
        self.hide_all_labels()

        self.plot_chart()

        self.plot_widget.sigRangeChanged.connect(self.on_range_changed)
        
        # 连接鼠标移动信号
        self.plot_widget.scene().sigMouseMoved.connect(self.on_mouse_move)


    def plot_chart(self):
        """绘制图表"""
        x_list = [0+i for i in range(500)]
        self.bar_width = 0.8
        self.adjusted_x_list = [ts - self.bar_width/2 for ts in x_list]

        self.data = np.random.randint(100, 5000, size=len(self.adjusted_x_list))

        self.line_data = np.random.randint(100, 500, size=len(self.adjusted_x_list))

        # 创建柱状图
        bargraph = pg.BarGraphItem(
            x0=self.adjusted_x_list,
            height=self.data,
            width=self.bar_width,
            brush='#1f77b4',
            pen={'color': '#0f4d8f', 'width': 1},
            name="股价"
        )
        
        self.plot_widget.addItem(bargraph)

        # ==============================绘制折线图===============================
        # 创建右侧Y轴用于显示折线图
        self.right_viewbox = pg.ViewBox()
        self.right_axis = self.plot_widget.getAxis('right')

        # 链接右侧Y轴到主视图
        self.plot_widget.scene().addItem(self.right_viewbox)
        self.plot_widget.getAxis('right').linkToView(self.right_viewbox)
        self.right_viewbox.setXLink(self.plot_widget)
        
        # 设置右侧Y轴标签
        self.plot_widget.setLabel('right', "涨跌幅")
        self.plot_widget.showAxis('right')

        # 创建折线图（移动平均线）
        line_x_positions = [ts + self.bar_width / 2 for ts in self.adjusted_x_list]
        self.line_plot = self.plot_widget.plot(
            x=line_x_positions,
            y=self.line_data,
            pen=pg.mkPen(color='#0f4d8f', width=3),
            symbol='o',
            symbolSize=12,
            symbolBrush='#ff7f0e',
            name="涨跌幅"
        )
        self.line_plot.setZValue(1000)
        self.right_viewbox.addItem(self.line_plot)

        # 同步两个ViewBox的视图范围
        def update_views():
            self.right_viewbox.setGeometry(self.plot_widget.getViewBox().sceneBoundingRect())
            self.right_viewbox.linkedViewChanged(self.plot_widget.getViewBox(), self.right_viewbox.XAxis)
        
        update_views()
        self.plot_widget.getViewBox().sigResized.connect(update_views)


        # 设置坐标轴范围
        # 考虑柱子宽度，使柱子居中显示
        x_min = min(self.adjusted_x_list) - self.bar_width / 2
        x_max = max(self.adjusted_x_list) + self.bar_width * 1.5
        self.plot_widget.setXRange(x_min, x_max)
        
        # 设置左右两侧Y轴的范围
        y_max_bar = max(self.data) * 1.1
        y_min_bar = min(self.data) * 1.1
        if y_min_bar >=0:
            y_min_bar = 0
        self.plot_widget.setYRange(y_min_bar, y_max_bar)


        y_max_line = max(self.line_data) * 1.1
        direct = 0 if y_min_bar >= 0 else -1
        y_min_line = min(self.line_data)  * direct * 1.1
        # self.logger.info(f"board_type: {self.board_type}, y_min_line: {y_min_line}, y_max_line: {y_max_line}")
        self.right_viewbox.setYRange(y_min_line, y_max_line)

    def on_range_changed(self):
        """图表范围改变时触发"""
        # x_range = view_range[0]
        # x_min, x_max = x_range
        # print(f"X Range Changed: {x_min:.2f} - {x_max:.2f}")

        # # 获取图表数据范围
        # data_range = self.plot_widget.getViewBox().viewRange()[0]

    def on_mouse_move(self, pos):
        """鼠标移动时触发"""
        # mouse_point = pos
        # vb = self.plot_widget.getViewBox()
        # x_range = vb.viewRange()[0]  # 获取X轴范围
        
        # # 找到鼠标位置最接近的柱子
        # closest_index = np.argmin(np.abs(self.x_list - mouse_point.x()))

        if self.plot_widget.sceneBoundingRect().contains(pos):
            # 确保有数据存在
            if (hasattr(self, 'adjusted_x_list') and hasattr(self, 'data') and 
                len(self.adjusted_x_list) > 0 and len(self.data) > 0):

                # 主视图：将场景坐标转换为视图坐标
                mouse_point = self.plot_widget.getViewBox().mapSceneToView(pos)
                x_val = mouse_point.x()

                # 右视图：将场景坐标转换为视图坐标
                mouse_point_right = self.right_viewbox.mapSceneToView(pos)
                
                # 计算柱子中心位置
                bar_centers = [ts + self.bar_width / 2 for ts in self.adjusted_x_list]
                
                # 找到鼠标位置附近的柱子
                closest_index = None
                min_distance = float('inf')
                
                for i, center in enumerate(bar_centers):
                    distance = abs(center - x_val)
                    # 只有当鼠标在柱子宽度范围内时才考虑该柱子
                    if distance <= self.bar_width / 2:
                        if distance < min_distance:
                            min_distance = distance
                            closest_index = i

                if closest_index is not None:
                    closest_x = bar_centers[closest_index]
                    closest_y = self.data[closest_index]

                    view_range = self.plot_widget.getViewBox().viewRange()
                    right_view_range = self.right_viewbox.viewRange()
                    
                    # 更新垂直线位置（对齐到最近的数据节点）
                    self.v_line.setPos(closest_x)
                    # 水平线仍然跟随鼠标y坐标
                    self.h_line.setPos(mouse_point.y())
                    
                    # 显示十字线和标签
                    self.v_line.show()
                    self.h_line.show()
                    self.label.show()

                    self.x_label_main.show()
                    self.left_y_label_main.show()
                    self.right_y_label_main.show()

                    try:
                        # 获取对应的移动平均值
                        line_left_y_value = self.data[closest_index] if hasattr(self, 'data') else 0
                        line_right_y_value = self.line_data[closest_index] if hasattr(self, 'line_data') else 0
                        
                        # 格式化标签文本
                        label_text = f"索引: {closest_index}\n股价: {line_left_y_value}，涨跌幅：{line_right_y_value}\n鼠标Y: {mouse_point.y():.2f}"
                        self.label.setText(label_text)
                        
                        # 将标签定位在图表上部，避免遮挡
                        # y_range = self.plot_widget.getViewBox().viewRange()[1]
                        # label_y = y_range[1] * 0.95
                        # self.label.setPos(closest_x, label_y)
                        self.label.setPos(closest_x, mouse_point.y())

                        label_x_main_y = view_range[1][0] + (view_range[1][1] - view_range[1][0]) * 0.01    # 下侧3%位置

                        # 无用
                        # x_axis_height = self.plot_widget.getAxis('bottom').height()  # 获取X轴高度
                        # label_x_main_y = view_range[1][0] - x_axis_height - 20  # 在X轴下方20像素处
                        
                        # 无用
                        # x_axis = self.plot_widget.getAxis('bottom')
                        # axis_rect = x_axis.boundingRect()
                        # # 获取X轴的底部Y坐标
                        # x_axis_bottom = axis_rect.bottom()
                        # # 设置标签位置
                        # label_x_main_y = x_axis_bottom + 10  # 在X轴下方10像素

                        self.x_label_main.setPos(closest_x, label_x_main_y)
                        label_main_x_text = "2025-11-16"
                        label_main_x_text_with_style = '<div style="color: black; background-color: white; border: 3px solid black; padding: 2px;">{}</div>'.format(label_main_x_text)
                        self.x_label_main.setHtml(label_main_x_text_with_style)

                        left_y_label_main_x = view_range[0][0] + (view_range[0][1] - view_range[0][0]) * 0.03  # 左侧3%位置
                        self.left_y_label_main.setPos(left_y_label_main_x, mouse_point.y())

                        left_y_label_main_text = f"{mouse_point.y():.2f}"
                        left_y_label_text_with_style = '<div style="color: black; background-color: white; border: 3px solid black; padding: 2px;">{}</div>'.format(left_y_label_main_text)
                        self.left_y_label_main.setHtml(left_y_label_text_with_style)

                        right_y_label_main_x = view_range[0][1] - (view_range[0][1] - view_range[0][0]) * 0.03
                        self.right_y_label_main.setPos(right_y_label_main_x, mouse_point.y())

                        right_y_label_main_text = f"{mouse_point_right.y():.2f}"
                        right_y_label_text_with_style = '<div style="color: black; background-color: white; border: 3px solid black; padding: 2px;">{}</div>'.format(right_y_label_main_text)
                        self.right_y_label_main.setHtml(right_y_label_text_with_style)

                    except Exception as e:
                        print(f"Error in mouse move: {e}")
                        pass
                else:
                    # 没有靠近任何柱子时隐藏十字线
                    self.hide_all_labels()
            else:
                # 没有数据时隐藏十字线
                self.hide_all_labels()
        else:
            # 鼠标移出绘图区域时隐藏十字线
            self.hide_all_labels()

    def hide_all_labels(self):
        """隐藏所有标签和十字线"""
        self.v_line.hide()
        self.h_line.hide()
        self.label.hide()

        self.x_label_main.hide()
        self.left_y_label_main.hide()
        self.right_y_label_main.hide()


def main():
    app = QApplication(sys.argv)
    # window = MainWindow()
    # window.show()

    widget = MWidget(None)
    widget.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()