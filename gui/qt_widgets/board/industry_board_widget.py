from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QListWidget
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
        self.options_list_widget = QListWidget(self)
        self.options_list_widget.setMinimumSize(500, 200)
        # self.options_list_widget.move(self.listWidget_card.x(), self.listWidget_card.y())
        self.options_list_widget.hide()

        df_lastest_industry_data = AKStockDataProcessor().get_latest_ths_board_industry_data()
        
        # 获取更详细的统计信息
        if 'total_amount' in df_lastest_industry_data.columns and 'industry_name' in df_lastest_industry_data.columns:
            # 按总成交额排序
            df_sorted = df_lastest_industry_data.sort_values('total_amount', ascending=False)
            
            # 获取前10个行业
            top_10_industries = df_sorted.head(10)
            
            # 获取后10个行业
            bottom_10_industries = df_sorted.tail(10)
            
            total_amount_sum = df_lastest_industry_data['total_amount'].sum()
            total_amount_mean = df_lastest_industry_data['total_amount'].mean()
            total_amount_max = df_lastest_industry_data['total_amount'].max()
            total_amount_min = df_lastest_industry_data['total_amount'].min()
            
            self.logger.info(f"获取最新行业板块数据成功，数量: {len(df_lastest_industry_data)}")
            self.logger.info(f"总成交额统计 - 总和: {total_amount_sum:.2f} 亿, 平均: {total_amount_mean:.2f} 亿, 最大: {total_amount_max:.2f} 亿, 最小: {total_amount_min:.2f} 亿")
            
            # 输出前10个行业
            self.logger.info("=== 总成交额前10行业 ===")
            for i, (index, row) in enumerate(top_10_industries.iterrows(), 1):
                self.logger.info(f"  {i:2d}. {row['industry_name']:<20} {row['total_amount']:>8.2f} 亿")
            
            # 输出后10个行业
            self.logger.info("=== 总成交额后10行业 ===")
            for i, (index, row) in enumerate(bottom_10_industries.iterrows(), 1):
                self.logger.info(f"  {i:2d}. {row['industry_name']:<20} {row['total_amount']:>8.2f} 亿")
        else:
            self.logger.warning("数据中不包含 total_amount 或 industry_name 字段")
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



        self.all_industries = df_lastest_industry_data['industry_name'].tolist()

        # 如果有数据，自动选择第一个item（使用定时器延迟执行）
        if first_item_data is not None:
            # 使用单次定时器确保UI完全初始化后再执行
            QTimer.singleShot(100, lambda: self.select_first_item(first_item_data))

    def init_connect(self):
        self.comboBox_bar_type.currentTextChanged.connect(self.update_chart)
        self.lineEdit_search.textChanged.connect(self.slot_search_text_changed)

        self.options_list_widget.itemClicked.connect(self.slot_search_item_clicked)

        self.lineEdit_search.editingFinished.connect(self.hide_options_list)

    def select_first_item(self, first_item_data):
        """选择第一个item的独立方法"""
        # 设置列表选中第一个
        self.listWidget_card.setCurrentRow(0)
        # 调用槽函数
        self.slot_stock_card_clicked(first_item_data)

    def update_options_list_widget(self, options):
        """
        更新选项列表显示
        """
        # 清空现有选项
        self.options_list_widget.clear()
        
        # 添加新选项
        for option in options:
            self.options_list_widget.addItem(option)

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
            industry_history_data = industry_history_data.sort_values('date')
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

        # 净流入方副图展示
        # if hasattr(data, 'net_inflow'):
        #     self.comboBox_bar_type.addItem('净流入')

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


    def slot_search_text_changed(self, text):
        """
        处理搜索文本变化
        """
        self.logger.info(f"输入的搜索值为：{text}")
        if not text:
            # 显示所有行业
            filtered_industries = self.all_industries
        else:
            # 根据输入过滤行业
            filtered_industries = [industry for industry in self.all_industries 
                                if text.lower() in industry.lower()]
        
        # 更新搜索结果列表
        self.options_list_widget.clear()
        for industry in filtered_industries:  # 限制显示数量
            self.options_list_widget.addItem(industry)

        # 动态定位和显示控制
        if filtered_industries and self.options_list_widget.isHidden():
            self.position_options_list()
            self.options_list_widget.show()
        else:
            self.options_list_widget.hide()

    def slot_search_item_clicked(self, item):
        """
        处理搜索项点击事件
        """
        selected_industry = item.text()
        self.logger.info(f"点击的搜索项为：{selected_industry}")
        # 找到对应行业并选中
        for i in range(self.listWidget_card.count()):
            card_widget = self.listWidget_card.itemWidget(self.listWidget_card.item(i))
            if card_widget and getattr(card_widget.data, 'industry_name', '') == selected_industry:
                self.listWidget_card.setCurrentRow(i)
                self.slot_stock_card_clicked(card_widget.data)
                break

        # 点击后隐藏选项列表并清空搜索框
        self.options_list_widget.hide()
        self.lineEdit_search.textChanged.disconnect(self.slot_search_text_changed)
        self.lineEdit_search.clear()
        self.lineEdit_search.textChanged.connect(self.slot_search_text_changed)
        self.lineEdit_search.clearFocus()
        
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
    
    def position_options_list(self):
        """
        动态计算并设置选项列表的位置，确保其在搜索框下方
        """
        # 获取搜索框的全局坐标
        search_global_pos = self.lineEdit_search.mapToGlobal(self.lineEdit_search.pos())
        
        # 计算搜索框在父窗口中的位置
        search_pos_in_parent = self.lineEdit_search.pos()
        
        # 设置选项列表的位置在搜索框正下方
        # X坐标与搜索框对齐，Y坐标在搜索框下方
        x_pos = search_pos_in_parent.x()
        y_pos = search_pos_in_parent.y() + self.lineEdit_search.height()
        
        self.options_list_widget.move(x_pos, y_pos)
        
        # 可选：设置宽度与搜索框一致
        self.options_list_widget.setFixedWidth(self.lineEdit_search.width())
    def hide_options_list(self):
        """
        隐藏选项列表
        """
        # 使用定时器延迟隐藏，以便处理点击事件
        QTimer.singleShot(100, self.options_list_widget.hide)