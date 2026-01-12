from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout
from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtGui import QIntValidator

import pandas as pd

from manager.logging_manager import get_logger

from gui.qt_widgets.board.industry_board_overview_widget import IndustryBoardOverviewWidget
from processor.ak_stock_data_processor import AKStockDataProcessor
from gui.qt_widgets.board.board_change_percent_chart_widget import BoardChangePercentChartWidget
from gui.qt_widgets.MComponents.MRangeValidator import MRangeValidator


class BoardOverviewWidget(QWidget):
    def __init__(self):
        super(BoardOverviewWidget, self).__init__()
        self.logger = get_logger(__name__)
        
        self.init_para()
        self.init_ui()
        self.init_connect()

    def init_ui(self):
        uic.loadUi('./src/gui/qt_widgets/board/BoardOverViewWidget.ui', self)

        validator = MRangeValidator(10, 30, self.lineEdit_top)
        self.lineEdit_top.setValidator(validator)
        self.lineEdit_top.setText('20')

        self.industry_change_percent_chart_widget = BoardChangePercentChartWidget(type=0)
        self.concept_change_percent_chart_widget = BoardChangePercentChartWidget(type=1)
        self.industry_change_percent_chart_widget.setMinimumHeight(768)
        self.concept_change_percent_chart_widget.setMinimumHeight(768)

        container_layout = self.widget.layout()
        if container_layout is None:
            self.setLayout(QVBoxLayout())

        container_layout.addWidget(self.industry_change_percent_chart_widget)
        container_layout.addWidget(self.concept_change_percent_chart_widget)
        self.widget.setMinimumHeight(
            self.industry_change_percent_chart_widget.sizeHint().height() +
            self.concept_change_percent_chart_widget.sizeHint().height() + 30
        )

        self.update_chart()

        
    def init_para(self):
        self.lastest_industry_data_date = None
        self.lastest_concept_data_date = None

        self.df_lastest_industry_data = AKStockDataProcessor().get_latest_ths_board_industry_data()
        self.df_lastest_concept_data = AKStockDataProcessor().get_latest_ths_board_concept_overview()
        self.df_lastest_concept_data = self.df_lastest_concept_data.dropna()

    def init_connect(self):
        self.lineEdit_top.returnPressed.connect(self.slot_lineEdit_top_returnPressed)

    def update_chart(self, top=20):
        if self.df_lastest_industry_data is None or self.df_lastest_concept_data is None:
            self.logger.warning("数据为空！")
            return

        if self.df_lastest_industry_data.empty or self.df_lastest_concept_data.empty:
            self.logger.warning("数据为空！")
            return
        

        # 判断日期是否匹配
        s_industry_date = self.df_lastest_industry_data['date'].iloc[-1]
        s_concept_date = self.df_lastest_concept_data['date'].iloc[-1]
        if s_industry_date != s_concept_date:
            self.logger.warning(f"行业板块数据日期和概念板块数据日期不一致，请检查数据！s_industry_date：{s_industry_date}，s_concept_date：{s_concept_date}")
            return
        
        self.lastest_industry_data_date = s_industry_date
        self.lastest_concept_data_date = s_concept_date

        
        self.label.setText(f"{s_industry_date} 板块概览")
        self.industry_change_percent_chart_widget.draw_chart(self.df_lastest_industry_data, top)

        # if 'board_change_percent' in df_lastest_concept_data.columns:
        #     df_lastest_concept_data = df_lastest_concept_data.rename(columns={'board_change_percent': 'change_percent'})
        # else:
        #     self.logger.warning("数据中不包含 board_change_percent 字段")
        # 预处理数据
        try:
            if 'change_rank' in self.df_lastest_concept_data.columns:
                # 检查 change_rank 是否有有效数据
                change_rank_series = self.df_lastest_concept_data['change_rank']
                
                # 提取排名数据
                extracted = change_rank_series.str.extract(r'(\d+)/\d+')
                
                # 检查提取结果，如果有无效数据，标记出来
                invalid_mask = extracted[0].isna()
                if invalid_mask.any():
                    self.logger.warning(f"发现 {invalid_mask.sum()} 个无效的 change_rank 格式")
                    
                # 转换为数值，无效的设为0
                self.df_lastest_concept_data['rank'] = pd.to_numeric(extracted[0], errors='coerce').fillna(0).astype(int)
            else:
                self.logger.warning("数据中不包含 change_rank 字段")
        except Exception as e:
            self.logger.warning(f"数据转换错误：{e}")

            
        if 'rise_fall_count' in self.df_lastest_concept_data.columns:
            # 使用正则表达式提取上涨家数和下跌家数（格式为：16/4，第一个数字是上涨家数，第二个是下跌家数）
            rise_fall_split = self.df_lastest_concept_data['rise_fall_count'].str.extract(r'(\d+)/(\d+)')
            self.df_lastest_concept_data['rising_count'] = rise_fall_split[0].astype(int)
            self.df_lastest_concept_data['falling_count'] = rise_fall_split[1].astype(int)
        else:
            self.logger.warning("数据中不包含 rise_fall_count 字段")

        self.concept_change_percent_chart_widget.draw_chart(self.df_lastest_concept_data, top)

    def slot_lineEdit_top_returnPressed(self):
        text = self.lineEdit_top.text()
        self.logger.info(f"输入的top值为：{text}")
        if not text:  # 空输入处理
            self.lineEdit_top.setText('20')
            self.update_chart(20)
            self.lineEdit_top.clearFocus()
            return
        
        try:
            top = int(text)
            # 虽然验证器已限制范围，但仍做一次检查
            if 10 <= top <= 30:
                self.update_chart(top)
            else:
                # 自动修正到有效范围
                corrected = max(10, min(30, top))
                self.lineEdit_top.setText(str(corrected))
                self.update_chart(corrected)
        except ValueError:
            # 异常情况恢复默认值
            self.lineEdit_top.setText('20')
            self.update_chart(20)

        self.lineEdit_top.clearFocus()

    def showEvent(self, event):
        """
        重写showEvent方法，在窗口显示时执行初始化操作
        """
        super().showEvent(event)

        if self.df_lastest_industry_data is None or self.df_lastest_concept_data is None:
            # self.logger.warning("数据为空！")
            return

        if self.df_lastest_industry_data.empty or self.df_lastest_concept_data.empty:
            # self.logger.warning("数据为空！")
            return
        

        # 判断日期是否匹配
        s_industry_date = self.df_lastest_industry_data['date'].iloc[-1]
        s_concept_date = self.df_lastest_concept_data['date'].iloc[-1]
        if s_industry_date != s_concept_date:
            self.logger.warning(f"行业板块数据日期和概念板块数据日期不一致，请检查数据！s_industry_date：{s_industry_date}，s_concept_date：{s_concept_date}")
            return
        
        if self.lastest_industry_data_date != s_industry_date or self.lastest_concept_data_date != s_concept_date:
            self.slot_lineEdit_top_returnPressed()
        else:
            self.logger.info("已是最新板块数据，无需更新！")

        



