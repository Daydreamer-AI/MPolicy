from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QGraphicsLineItem, QGraphicsRectItem, QGraphicsTextItem
from PyQt5.QtCore import pyqtSlot, QTimer
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QBarSeries, QBarSet, QDateTimeAxis, QValueAxis
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QBrush

# 导入pyqtgraph
import pyqtgraph as pg
import pandas as pd
import numpy as np

from common.logging_manager import get_logger
from processor.ak_stock_data_processor import AKStockDataProcessor
from gui.qt_widgets.MComponents.stock_card_widget import StockCardWidget
from gui.qt_widgets.board.board_chart_widget import BoardChartWidget

class IndustryBoardWidget(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('./gui/qt_widgets/board/IndustryBoardWidget.ui', self)

        self.init_para()
        self.init_ui()
        self.init_connect()

    def init_para(self):
        self.logger = get_logger(__name__)
        self.df_industry_board_data = AKStockDataProcessor().query_ths_board_industry_data()

    def init_ui(self):
        df_lastest_industry_data = AKStockDataProcessor().get_latest_ths_board_industry_data()
        self.logger.info(f"获取最新行业板块数据成功，数量: {len(df_lastest_industry_data)}")
        
        first_item_data = None  # 保存第一个item的数据
        for index, row in enumerate(df_lastest_industry_data.itertuples()):
            # self.logger.info(row)

            # 创建 QListWidgetItem
            item = QtWidgets.QListWidgetItem()

            stock_card_widget = StockCardWidget()
            stock_card_widget.set_data(row)
            stock_card_widget.update_ui()

            stock_card_widget.clicked.connect(self.slot_stock_card_clicked)
            stock_card_widget.hovered.connect(self.slot_stock_card_hovered)
            stock_card_widget.hoverLeft.connect(self.slot_stock_card_hover_left)
            stock_card_widget.doubleClicked.connect(self.slot_stock_card_double_clicked)

            # 设置 item 的大小（可选）
            item.setSizeHint(stock_card_widget.sizeHint())
            
            # 将 item 添加到 list widget
            self.listWidget_card.addItem(item)
            
            # 将自定义 widget 设置为 item 的 widget
            self.listWidget_card.setItemWidget(item, stock_card_widget)

            # 保存第一个item的数据
            if index == 0:
                first_item_data = row


        # 如果有数据，自动选择第一个item（使用定时器延迟执行）
        if first_item_data is not None:
            # 使用单次定时器确保UI完全初始化后再执行
            QTimer.singleShot(100, lambda: self.select_first_item(first_item_data))

    def init_connect(self):
        self.comboBox_bar_type.currentTextChanged.connect(self.update_chart)

    def select_first_item(self, first_item_data):
        """选择第一个item的独立方法"""
        # 设置列表选中第一个
        self.listWidget_card.setCurrentRow(0)
        # 调用槽函数
        self.slot_stock_card_clicked(first_item_data)

    def update_chart(self, bar_type='总成交额'):
        # 1. 从传递的data中获取板块名称
        # 注意：具体的属性名需要根据实际的data结构确定
        # industry_name = getattr(self.current_data, 'industry_name', None)  # 假设属性名为industry_name
        self.logger.info(f"当前选择的板块名称为：{self.current_industry_name}")
        
        if self.current_industry_name:
            # 2. 从历史数据中筛选该行业的所有交易日数据
            # 假设df_industry_board_data中有'industry_name'列
            industry_history_data = self.df_industry_board_data[
                self.df_industry_board_data['industry_name'] == self.current_industry_name
            ]
            
            # 3. 对数据进行排序（按日期）
            # 假设有一个'date'列表示交易日期
            industry_history_data = industry_history_data.sort_values('data_date')
            self.logger.info(f"获取行业 {self.current_industry_name} 的历史数据成功，数量: {len(industry_history_data)}")
            
            # 4. 调用绘图函数
            default_field = "总成交额"  # 或从ComboBox获取当前选中项
            if hasattr(self, 'comboBox_bar_type'):
                default_field = self.comboBox_bar_type.currentText()

            self.plot_industry_chart(self.current_industry_name, industry_history_data, default_field)

    # ==============槽函数==============
    @pyqtSlot(object)
    def slot_stock_card_clicked(self, data):
        self.logger.info("slot_stock_card_clicked")
        self.logger.info(data)

        self.current_industry_name = getattr(data, 'industry_name', None)
        # self.current_data = data

        # 使用信号阻塞避免触发更新
        self.comboBox_bar_type.blockSignals(True)
        self.comboBox_bar_type.clear()
        if hasattr(data, 'total_amount'):
            self.comboBox_bar_type.addItem('总成交额')

        if hasattr(data, 'total_volume'):
            self.comboBox_bar_type.addItem('总成交量')

        if hasattr(data, 'net_inflow'):
            self.comboBox_bar_type.addItem('净流入')

        if hasattr(data, 'rising_count'):
            self.comboBox_bar_type.addItem('上涨家数')

        if hasattr(data, 'falling_count'):
            self.comboBox_bar_type.addItem('下跌家数')
        
        # 恢复信号
        self.comboBox_bar_type.blockSignals(False)

        self.update_chart()

    @pyqtSlot()
    def slot_stock_card_hovered(self):
        # self.logger.info("slot_stock_card_hovered")
        pass

    @pyqtSlot()
    def slot_stock_card_hover_left(self):
        # self.logger.info("slot_stock_card_hover_left")
        pass

    @pyqtSlot()
    def slot_stock_card_double_clicked(self):
        self.logger.info("slot_stock_card_double_clicked")


    # =================其他成员函数===============
    # QtChart 绘图
    def plot_industry_chart(self, industry_name, data, bar_type):
        """
        使用封装的图表控件绘制行业数据图表
        :param industry_name: 行业名称
        :param data: 该行业的历史数据
        """
        try:
            # 检查数据是否为空
            if data.empty:
                self.logger.warning(f"没有找到 {industry_name} 的历史数据")
                return
            
            # 创建图表控件实例
            chart_widget = BoardChartWidget()
            # chart_widget.resize(1366, 768)
            
            # 绘制图表
            success = chart_widget.plot_chart(industry_name, data, bar_type)
            
            if success:
                # 清除之前的图表（如果有）
                layout = self.widget_view.layout()
                if layout is None:
                    self.widget_view.setLayout(QVBoxLayout())
                for i in reversed(range(layout.count())): 
                    layout.itemAt(i).widget().setParent(None)

                # 添加到布局
                layout.addWidget(chart_widget)
                self.logger.info(f"成功绘制 {industry_name} 图表，数据量: {len(data)}")
            else:
                self.logger.error(f"绘制 {industry_name} 图表失败")

        except Exception as e:
            self.logger.error(f"绘制图表时出错: {e}")
            QMessageBox.warning(self, "绘图错误", f"绘制图表时出现错误:\n{str(e)}")
    
    # pyqtgraph 绘图
    # def plot_industry_chart(self, industry_name, data):
    #     """
    #     使用pyqtgraph绘制行业数据图表（柱状图和折线图在同一图表中）
    #     :param industry_name: 行业名称
    #     :param data: 该行业的历史数据
    #     """
    #     try:
    #         # 检查数据是否为空
    #         if data.empty:
    #             self.logger.warning(f"没有找到 {industry_name} 的历史数据")
    #             return
            
    #         layout = self.widget_view.layout()
    #         if layout is None:
    #             self.widget_view.setLayout(QVBoxLayout())

    #         # 清除之前的图表（如果有）
    #         for i in reversed(range(layout.count())): 
    #             layout.itemAt(i).widget().setParent(None)

    #         # 创建GraphicsLayoutWidget
    #         graphics_layout = pg.GraphicsLayoutWidget()
    #         layout.addWidget(graphics_layout)
            
    #         # 创建图表
    #         plot_item = graphics_layout.addPlot(title=f"{industry_name} 数据")
            
    #         # 启用网格
    #         plot_item.showGrid(x=True, y=True, alpha=0.3)
            
    #         # 处理日期数据
    #         if 'data_date' in data.columns:
    #             data = data.copy()
    #             data['date'] = pd.to_datetime(data['data_date'])
    #             data = data.sort_values('date')
    #             # 转换为时间戳用于绘图
    #             timestamps = [d.timestamp() for d in data['date']]
    #         else:
    #             timestamps = list(range(len(data)))
            
    #         # 创建第二个Y轴用于不同的数据类型
    #         price_plot = plot_item
    #         volume_plot = pg.ViewBox()
    #         price_plot.showAxis('right')
    #         price_plot.scene().addItem(volume_plot)
    #         price_plot.getAxis('right').linkToView(volume_plot)
    #         volume_plot.setXLink(price_plot)
            
    #         # 更新视图链接
    #         def update_views():
    #             volume_plot.setGeometry(price_plot.getViewBox().sceneBoundingRect())
    #             volume_plot.linkedViewChanged(price_plot.getViewBox(), volume_plot.XAxis)
            
    #         update_views()
    #         price_plot.getViewBox().sigResized.connect(update_views)
            
    #         # 绘制成交量柱状图（使用柱状图）
    #         if 'total_volume' in data.columns:
    #             if len(timestamps) > 1:
    #                 # 计算柱状图宽度
    #                 bar_width = (timestamps[1] - timestamps[0]) * 0.8
    #             else:
    #                 bar_width = 1
                
    #             # 创建柱状图项目
    #             bar_graph_item = pg.BarGraphItem(
    #                 x=timestamps, 
    #                 height=data['total_volume'].values, 
    #                 width=bar_width,
    #                 brush=pg.mkBrush(100, 150, 255, 150),  # 半透明蓝色
    #                 pen=pg.mkPen('b')
    #             )
    #             volume_plot.addItem(bar_graph_item)
    #             price_plot.getAxis('right').setLabel('成交量', color='blue')
            
    #         # 绘制价格折线图
    #         price_columns = ['avg_price']
    #         price_column = None
    #         for col in price_columns:
    #             if col in data.columns:
    #                 price_column = col
    #                 break
                    
    #         if price_column:
    #             # 绘制价格折线图
    #             price_curve = price_plot.plot(
    #                 timestamps, 
    #                 data[price_column].values, 
    #                 pen=pg.mkPen(color='r', width=2), 
    #                 name='价格',
    #                 symbol='o',
    #                 symbolSize=4,
    #                 symbolBrush='r'
    #             )
    #             price_plot.setLabel('left', '价格', color='red')
            
    #         # 设置X轴为日期
    #         axis = price_plot.getAxis('bottom')
    #         if len(timestamps) > 0:
    #             # 计算合适的日期标签间隔
    #             tick_step = max(1, len(timestamps)//10)
    #             axis.setTicks([[(timestamps[i], pd.to_datetime(timestamps[i], unit='s').strftime('%Y-%m-%d')) 
    #                         for i in range(0, len(timestamps), tick_step)]])
            
    #         # 设置X轴标签
    #         price_plot.setLabel('bottom', '日期')
            
    #         self.logger.info(f"成功绘制 {industry_name} 图表，数据量: {len(data)}")

    #     except Exception as e:
    #         self.logger.error(f"绘制图表时出错: {e}")
    #         QMessageBox.warning(self, "绘图错误", f"绘制图表时出现错误:\n{str(e)}")

    # matplotlib 绘图
    # def plot_industry_chart(self, industry_name, data):
    #     """
    #     绘制行业数据图表
    #     :param industry_name: 行业名称
    #     :param data: 该行业的历史数据
    #     """
    #     try:
    #         # 检查数据是否为空
    #         if data.empty:
    #             self.logger.warning(f"没有找到 {industry_name} 的历史数据")
    #             return
                
    #         # 导入绘图相关库
    #         import matplotlib.pyplot as plt
    #         from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    #         from matplotlib.figure import Figure
    #         from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QLabel
    #         import pandas as pd
            
    #         # 创建一个新的窗口来显示图表
    #         chart_window = QMainWindow()
    #         chart_window.setWindowTitle(f'{industry_name} 历史数据图表')
    #         chart_window.resize(1000, 600)
            
    #         # 创建中央widget
    #         central_widget = QWidget()
    #         chart_window.setCentralWidget(central_widget)
            
    #         # 创建布局
    #         layout = QVBoxLayout(central_widget)
            
    #         # 添加标题
    #         title_label = QLabel(f'{industry_name} 行业数据趋势')
    #         title_label.setAlignment(Qt.AlignCenter)
    #         layout.addWidget(title_label)
            
    #         # 创建matplotlib图形
    #         fig = Figure(figsize=(10, 6), dpi=100)
    #         canvas = FigureCanvas(fig)
    #         layout.addWidget(canvas)
            
    #         # 创建子图
    #         ax1 = fig.add_subplot(111)
            
    #         # 确保日期列是datetime类型
    #         if 'date' in data.columns:
    #             data = data.copy()  # 避免修改原始数据
    #             data['date'] = pd.to_datetime(data['date'])
    #             data = data.sort_values('date')
            
    #         # 绘制成交量柱状图
    #         if 'volume' in data.columns:
    #             ax1.bar(data['date'], data['volume'], 
    #                 alpha=0.7, color='lightblue', label='成交量')
    #             ax1.set_ylabel('成交量', color='blue')
    #             ax1.tick_params(axis='y', labelcolor='blue')
            
    #         # 创建第二个y轴绘制价格折线图
    #         ax2 = ax1.twinx()
            
    #         # 绘制价格折线图（根据实际数据字段调整）
    #         price_columns = ['price', 'close', 'avg_price']
    #         price_column = None
    #         for col in price_columns:
    #             if col in data.columns:
    #                 price_column = col
    #                 break
                    
    #         if price_column:
    #             ax2.plot(data['date'], data[price_column], 
    #                     color='red', linewidth=2, marker='o', markersize=3, label='价格')
    #             ax2.set_ylabel('价格', color='red')
    #             ax2.tick_params(axis='y', labelcolor='red')
            
    #         # 设置x轴日期格式
    #         import matplotlib.dates as mdates
    #         ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    #         fig.autofmt_xdate()  # 自动旋转日期标签
            
    #         # 添加图例
    #         ax1.legend(loc='upper left')
    #         if price_column:
    #             ax2.legend(loc='upper right')
            
    #         # 添加网格
    #         ax1.grid(True, alpha=0.3)
            
    #         # 刷新画布
    #         canvas.draw()
            
    #         # 显示窗口
    #         chart_window.show()
            
    #         # 保存窗口引用防止被垃圾回收
    #         self.chart_window = chart_window
            
    #         self.logger.info(f"成功绘制 {industry_name} 图表，数据量: {len(data)}")
            
    #     except Exception as e:
    #         self.logger.error(f"绘制图表时出错: {e}")
    #         # 可以在这里添加错误提示对话框
    #         from PyQt5.QtWidgets import QMessageBox
    #         QMessageBox.warning(self, "绘图错误", f"绘制图表时出现错误:\n{str(e)}")


