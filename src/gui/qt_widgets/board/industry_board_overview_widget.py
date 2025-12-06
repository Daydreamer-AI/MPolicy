from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene
from PyQt5.QtCore import pyqtSlot, QRectF, Qt
from PyQt5.QtGui import QColor, QPen, QBrush, QPainter, QFont

import pyqtgraph as pg
import numpy as np

from manager.logging_manager import get_logger
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
        # self.df_industry_board_data = AKStockDataProcessor().query_ths_board_industry_data()
        pass

    def init_ui(self):
        uic.loadUi('gui/qt_widgets/board/IndustryBoardOverviewWidget.ui', self)

        container_layout = self.widget_container.layout()
        if container_layout is None:
            self.setLayout(QVBoxLayout())


        df_lastest_industry_data = AKStockDataProcessor().get_latest_ths_board_industry_data()
        df_lastest_concept_data = AKStockDataProcessor().get_latest_ths_board_concept_overview()

        self.industry_change_percent_chart_widget = BoardChangePercentChartWidget(type=0)
    
        self.concept_change_percent_chart_widget = BoardChangePercentChartWidget(type=1)
        self.industry_change_percent_chart_widget.draw_chart(df_lastest_industry_data)

        # if 'board_change_percent' in df_lastest_concept_data.columns:
        #     df_lastest_concept_data = df_lastest_concept_data.rename(columns={'board_change_percent': 'change_percent'})
        # else:
        #     self.logger.warning("数据中不包含 board_change_percent 字段")
        # 预处理数据
        if 'change_rank' in df_lastest_concept_data.columns:
            # 使用正则表达式提取排名（格式为：10/389，提取第一个数字作为排名）
            df_lastest_concept_data['rank'] = df_lastest_concept_data['change_rank'].str.extract(r'(\d+)/\d+').astype(int)
        else:
            self.logger.warning("数据中不包含 change_rank 字段")
            
        if 'rise_fall_count' in df_lastest_concept_data.columns:
            # 使用正则表达式提取上涨家数和下跌家数（格式为：16/4，第一个数字是上涨家数，第二个是下跌家数）
            rise_fall_split = df_lastest_concept_data['rise_fall_count'].str.extract(r'(\d+)/(\d+)')
            df_lastest_concept_data['rising_count'] = rise_fall_split[0].astype(int)
            df_lastest_concept_data['falling_count'] = rise_fall_split[1].astype(int)
        else:
            self.logger.warning("数据中不包含 rise_fall_count 字段")

        self.concept_change_percent_chart_widget.draw_chart(df_lastest_concept_data)

        self.industry_change_percent_chart_widget.setMinimumHeight(768)
        self.concept_change_percent_chart_widget.setMinimumHeight(768)
        container_layout.addWidget(self.industry_change_percent_chart_widget)
        container_layout.addWidget(self.concept_change_percent_chart_widget)
        self.widget_container.setMinimumHeight(
            self.industry_change_percent_chart_widget.sizeHint().height() +
            self.concept_change_percent_chart_widget.sizeHint().height() + 30
        )