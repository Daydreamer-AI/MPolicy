from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene
from PyQt5.QtCore import pyqtSlot, QRectF, Qt
from PyQt5.QtGui import QColor, QPen, QBrush, QPainter, QFont

import pyqtgraph as pg
import numpy as np

from common.logging_manager import get_logger
from processor.ak_stock_data_processor import AKStockDataProcessor
from gui.qt_widgets.MComponents.MPieChartItem import MPieChartItem, InteractiveMPieChartItem
from gui.qt_widgets.MComponents.custom_date_axisItem import NoLabelAxis
from gui.qt_widgets.board.board_change_percent_chart_widget import BoardChangePercentChartWidget


class IndustryBoardOverviewWidget(QWidget):
    def __init__(self):
        super(IndustryBoardOverviewWidget, self).__init__()
        self.logger = get_logger(__name__)

        self.init_ui()
        self.init_para()
        self.init_connect()

    def init_connect(self):
        pass

    def init_para(self):
        self.df_industry_board_data = AKStockDataProcessor().query_ths_board_industry_data()

    def init_ui(self):
        uic.loadUi('gui/qt_widgets/board/IndustryBoardOverviewWidget.ui', self)

        layout = self.layout()
        if layout is None:
            self.setLayout(QVBoxLayout())

        # self.graph_widget = pg.GraphicsLayoutWidget()
        # self.graph_widget.setBackground(pg.QtGui.QColor('white'))
        

        # layout.addWidget(self.graph_widget)

        # self.draw_pie_chart()

        self.industry_change_percent_chart_widget = BoardChangePercentChartWidget(type=0)
        layout.addWidget(self.industry_change_percent_chart_widget)
        df = AKStockDataProcessor().get_latest_ths_board_industry_data()
        self.industry_change_percent_chart_widget.draw_chart(df)

    # ----------------------------------------------------------
    def draw_pie_chart(self):
        """
        使用 PyQtGraph 绘制行业板块成交额饼图，突出前10大成交额行业
        """
        try:
            # 获取最新行业板块数据
            df_lastest_industry_data = AKStockDataProcessor().get_latest_ths_board_industry_data()
            if df_lastest_industry_data is None or df_lastest_industry_data.empty:
                self.logger.warning("行业板块数据为空，无法绘制饼图")
                return
                
            # 按成交额排序并获取前10
            top_10 = df_lastest_industry_data.nlargest(10, 'total_amount')
            others = df_lastest_industry_data.iloc[10:]
            
            # 准备绘图数据
            labels = list(top_10['industry_name'])
            sizes = list(top_10['total_amount'])
            
            # 添加"其他"类别
            if not others.empty:
                labels.append('其他')
                sizes.append(others['total_amount'].sum())
            
            # 清除之前的图形
            self.graph_widget.clear()
            
            # 添加绘图区域
            plot_item = self.graph_widget.addPlot()
            plot_item.setAspectLocked(True)

            # 设置背景颜色为白色
            # plot_item.setBackground(pg.QtGui.QColor('white'))
            
            # 创建饼图项
            # pie_item = MPieChartItem(sizes, labels)
            pie_item = InteractiveMPieChartItem(sizes, labels)
            
            # 添加到场景
            plot_item.addItem(pie_item)
            
            # 设置标题
            plot_item.setTitle('行业板块成交额分布图（前10名突出显示）')
            
            # 隐藏坐标轴
            plot_item.hideAxis('left')
            plot_item.hideAxis('bottom')
            
            # 添加图例
            self.add_legend(plot_item, labels, len(sizes))

            # 保存引用以便后续访问
            self.plot_item = plot_item
            self.pie_item = pie_item

            # 将提示框添加到绘图项中
            if hasattr(pie_item, 'tooltip') and pie_item.tooltip:
                plot_item.addItem(pie_item.tooltip)
            
        except Exception as e:
            self.logger.error(f"使用 PyQtGraph 绘制行业板块成交额饼图时发生错误: {e}")

    def add_legend(self, plot_item, labels, count):
        """添加图例"""
        # 创建图例
        legend = plot_item.addLegend(offset=(10, 10))
        
        # 定义颜色
        colors = [
            (255, 170, 170),  # 浅红
            (170, 255, 170),  # 浅绿
            (170, 170, 255),  # 浅蓝
            (255, 255, 170),  # 浅黄
            (255, 170, 255),  # 浅紫
            (170, 255, 255),  # 浅青
            (255, 210, 170),  # 浅橙
            (210, 170, 255),  # 浅紫红
            (170, 255, 210),  # 浅绿蓝
            (255, 170, 210),  # 浅粉
            (200, 200, 200)   # 灰色（其他）
        ]
        
        # 为每个标签创建一个简单的图例项
        for i, label in enumerate(labels[:min(count, 11)]):
            # 创建一个不可见的散点图项用于图例
            color = colors[i % len(colors)] if i < 10 else (200, 200, 200)
            scatter = pg.ScatterPlotItem([0], [0], brush=color, size=10)
            legend.addItem(scatter, label)

    # def draw_pie_chart(self):
    #     """
    #     使用 PyQtGraph 绘制行业板块成交额饼图，突出前10大成交额行业
    #     """
    #     try:
    #         # 获取最新行业板块数据
    #         df_lastest_industry_data = AKStockDataProcessor().get_latest_ths_board_industry_data()
    #         if df_lastest_industry_data is None or df_lastest_industry_data.empty:
    #             self.logger.warning("行业板块数据为空，无法绘制饼图")
    #             return
                
    #         # 按成交额排序并获取前10
    #         top_10 = df_lastest_industry_data.nlargest(10, 'total_amount')
    #         others = df_lastest_industry_data.iloc[10:]
            
    #         # 准备绘图数据
    #         labels = list(top_10['industry_name'])
    #         sizes = list(top_10['total_amount'])
            
    #         # 添加"其他"类别
    #         if not others.empty:
    #             labels.append('其他')
    #             sizes.append(others['total_amount'].sum())
            
    #         # 清除之前的图形
    #         self.scene.clear()
            
    #         # 创建饼图项
    #         pie_item = MPieChartItem(sizes, labels)
            
    #         # 添加到场景
    #         self.scene.addItem(pie_item)
            
    #         # 居中显示
    #         self.graphics_view.centerOn(pie_item)
            
    #         # 添加标题
    #         title = pg.TextItem('行业板块成交额分布图（前10名突出显示）', anchor=(0.5, 0.5))
    #         title.setPos(0, -150)
    #         font = QFont()
    #         font.setPointSize(12)
    #         font.setBold(True)
    #         title.setFont(font)
    #         self.scene.addItem(title)
            
    #         # 添加图例
    #         self.add_legend(labels, len(sizes))
            
    #     except Exception as e:
    #         self.logger.error(f"使用 PyQtGraph 绘制行业板块成交额饼图时发生错误: {e}")

    # def add_legend(self, labels, count):
        """添加图例"""
        # 创建图例背景
        legend_bg = pg.QtGui.QGraphicsRectItem(-120, 120, 240, 120)
        legend_bg.setBrush(QBrush(QColor(240, 240, 240, 200)))
        legend_bg.setPen(QPen(Qt.gray, 1))
        self.scene.addItem(legend_bg)
        
        # 定义颜色
        colors = [
            QColor(255, 170, 170),  # 浅红
            QColor(170, 255, 170),  # 浅绿
            QColor(170, 170, 255),  # 浅蓝
            QColor(255, 255, 170),  # 浅黄
            QColor(255, 170, 255),  # 浅紫
            QColor(170, 255, 255),  # 浅青
            QColor(255, 210, 170),  # 浅橙
            QColor(210, 170, 255),  # 浅紫红
            QColor(170, 255, 210),  # 浅绿蓝
            QColor(255, 170, 210),  # 浅粉
            QColor(200, 200, 200)   # 灰色（其他）
        ]
        
        # 添加图例项
        for i, label in enumerate(labels[:min(count, 11)]):  # 最多显示11项（包括"其他"）
            y_pos = 130 + i * 10
            
            # 颜色方块
            color_rect = pg.QtGui.QGraphicsRectItem(-115, y_pos, 8, 8)
            color = colors[i % len(colors)] if i < 10 else QColor(200, 200, 200)
            color_rect.setBrush(QBrush(color))
            color_rect.setPen(QPen(Qt.black, 1))
            self.scene.addItem(color_rect)
            
            # 标签文本
            text = pg.TextItem(label, anchor=(0, 0.5))
            text.setPos(-105, y_pos + 4)
            font = QFont()
            font.setPointSize(8)
            text.setFont(font)
            self.scene.addItem(text)