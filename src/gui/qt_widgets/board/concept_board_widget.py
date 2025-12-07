from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout, QMessageBox
from PyQt5.QtCore import pyqtSlot, QTimer

from manager.logging_manager import get_logger
from processor.ak_stock_data_processor import AKStockDataProcessor
from gui.qt_widgets.MComponents.stock_card_widget import StockCardWidget
from gui.qt_widgets.board.board_chart_widget import BoardChartWidget

class ConceptBoardWidget(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('./src/gui/qt_widgets/board/ConceptBoardWidget.ui', self)

        self.init_para()
        self.init_ui()
        self.init_connect()

    def init_para(self):
        self.logger = get_logger(__name__)

        self.df_concept_board_data = AKStockDataProcessor().query_ths_board_concept_overview()
        self.data_clean()
        self.last_board_data_date = self.df_concept_board_data['date'].iloc[0]
        self.logger.info(f"当前概念板块最新数据日期：{self.last_board_data_date}")

    def init_ui(self):
        self.init_card_list()

    def init_connect(self):
        self.comboBox_bar_type.currentTextChanged.connect(self.update_chart)

        self.lineEdit_search.optionSelected.connect(self.slot_concept_selected)

    def data_clean(self):
        if self.df_concept_board_data is None or self.df_concept_board_data.empty:
            return

        if 'board_change_percent' in self.df_concept_board_data.columns:
            self.df_concept_board_data = self.df_concept_board_data.rename(columns={'board_change_percent': 'change_percent'})
        else:
            self.logger.warning("数据中不包含 board_change_percent 字段")

        # 预处理数据
        if 'change_rank' in self.df_concept_board_data.columns:
            # 使用正则表达式提取排名（格式为：10/389，提取第一个数字作为排名）
            self.df_concept_board_data['rank'] = self.df_concept_board_data['change_rank'].str.extract(r'(\d+)/\d+').astype(int)
        else:
            self.logger.warning("数据中不包含 change_rank 字段")
            
        if 'rise_fall_count' in self.df_concept_board_data.columns:
            # 使用正则表达式提取上涨家数和下跌家数（格式为：16/4，第一个数字是上涨家数，第二个是下跌家数）
            rise_fall_split = self.df_concept_board_data['rise_fall_count'].str.extract(r'(\d+)/(\d+)')
            self.df_concept_board_data['rising_count'] = rise_fall_split[0].astype(int)
            self.df_concept_board_data['falling_count'] = rise_fall_split[1].astype(int)
        else:
            self.logger.warning("数据中不包含 rise_fall_count 字段")

    def init_card_list(self):
        df_lastest_concept_data = AKStockDataProcessor().get_latest_ths_board_concept_overview()

        if df_lastest_concept_data is None or df_lastest_concept_data.empty:
            self.logger.warning("没有获取到最新概念板块数据")
            return

        if 'board_change_percent' in df_lastest_concept_data.columns:
            df_lastest_concept_data = df_lastest_concept_data.rename(columns={'board_change_percent': 'change_percent'})
        else:
            self.logger.warning("数据中不包含 board_change_percent 字段")

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
        
        # 获取更详细的统计信息
        # if 'turnover' in df_lastest_concept_data.columns and 'concept_name' in df_lastest_concept_data.columns:
        #     # 按总成交额排序
        #     df_sorted = df_lastest_concept_data.sort_values('turnover', ascending=False)
            
        #     # 获取前10个行业
        #     top_10_industries = df_sorted.head(10)
            
        #     # 获取后10个行业
        #     bottom_10_industries = df_sorted.tail(10)
            
        #     total_amount_sum = df_lastest_concept_data['turnover'].sum()
        #     total_amount_mean = df_lastest_concept_data['turnover'].mean()
        #     total_amount_max = df_lastest_concept_data['turnover'].max()
        #     total_amount_min = df_lastest_concept_data['turnover'].min()
            
        #     self.logger.info(f"获取最新概念板块数据成功，数量: {len(df_lastest_concept_data)}")
        #     self.logger.info(f"总成交额统计 - 总和: {total_amount_sum:.2f} 亿, 平均: {total_amount_mean:.2f} 亿, 最大: {total_amount_max:.2f} 亿, 最小: {total_amount_min:.2f} 亿")
            
        #     # 输出前10个行业
        #     self.logger.info("=== 总成交额前10行业 ===")
        #     for i, (index, row) in enumerate(top_10_industries.iterrows(), 1):
        #         self.logger.info(f"  {i:2d}. {row['concept_name']:<20} {row['turnover']:>8.2f} 亿")
            
        #     # 输出后10个行业
        #     self.logger.info("=== 总成交额后10行业 ===")
        #     for i, (index, row) in enumerate(bottom_10_industries.iterrows(), 1):
        #         self.logger.info(f"  {i:2d}. {row['concept_name']:<20} {row['turnover']:>8.2f} 亿")
        # else:
        #     self.logger.warning("数据中不包含 turnover 或 concept_name 字段")
        #     self.logger.info(f"获取最新行业板块数据成功，数量: {len(df_lastest_concept_data)}")
        
        self.listWidget_card.clear()
        first_item_data = None  # 保存第一个item的数据
        for index, row in enumerate(df_lastest_concept_data.itertuples()):
            # self.logger.info(row)

            # 创建 QListWidgetItem
            item = QtWidgets.QListWidgetItem()

            stock_card_widget = StockCardWidget(1)
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


        self.all_concepts = df_lastest_concept_data['concept_name'].tolist()
        self.lineEdit_search.set_options(self.all_concepts)

        # 如果有数据，自动选择第一个item（使用定时器延迟执行）
        if first_item_data is not None:
            # 使用单次定时器确保UI完全初始化后再执行
            QTimer.singleShot(100, lambda: self.select_first_item(first_item_data))

    def select_first_item(self, first_item_data):
        """选择第一个item的独立方法"""
        # 设置列表选中第一个
        self.listWidget_card.setCurrentRow(0)
        # 调用槽函数
        self.slot_stock_card_clicked(first_item_data)


    # ==============槽函数==============
    @pyqtSlot(object)
    def slot_stock_card_clicked(self, data):
        # self.logger.info("slot_stock_card_clicked")
        # self.logger.info(data)

        self.current_concept_name = getattr(data, 'concept_name', None)
        # self.current_data = data

        # 使用信号阻塞避免触发更新
        self.comboBox_bar_type.blockSignals(True)
        self.comboBox_bar_type.clear()
        if hasattr(data, 'turnover'):
            self.comboBox_bar_type.addItem('总成交额')

        if hasattr(data, 'volume'):
            self.comboBox_bar_type.addItem('总成交量')

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

    def slot_concept_selected(self, concept_name):
        self.logger.info(f"选中的行业为：{concept_name}")
        # 找到对应行业并选中
        for i in range(self.listWidget_card.count()):
            card_widget = self.listWidget_card.itemWidget(self.listWidget_card.item(i))
            if card_widget and getattr(card_widget.data, 'concept_name', '') == concept_name:
                self.listWidget_card.setCurrentRow(i)
                self.slot_stock_card_clicked(card_widget.data)
                break

    # ================其他成员函数===============
    def update_chart(self, bar_type='总成交额'):
        # 1. 从传递的data中获取板块名称
        # 注意：具体的属性名需要根据实际的data结构确定
        self.logger.info(f"当前选择的概念板块名称为：{self.current_concept_name}")
        
        if self.current_concept_name:
            # 2. 从历史数据中筛选该行业的所有交易日数据
            # 假设df_industry_board_data中有'industry_name'列
            concept_history_data = self.df_concept_board_data[
                self.df_concept_board_data['concept_name'] == self.current_concept_name
            ]
            
            # 3. 对数据进行排序（按日期）
            # 假设有一个'date'列表示交易日期
            concept_history_data = concept_history_data.sort_values('date')
            self.logger.info(f"获取行业 {self.current_concept_name} 的历史数据成功，数量: {len(concept_history_data)}")
            
            # 4. 调用绘图函数
            default_field = "总成交额"  # 或从ComboBox获取当前选中项
            if hasattr(self, 'comboBox_bar_type'):
                default_field = self.comboBox_bar_type.currentText()

            self.plot_industry_chart(self.current_concept_name, concept_history_data, default_field)

    def plot_industry_chart(self, concept_name, data, bar_type):
        """
        使用封装的图表控件绘制行业数据图表
        :param concept_name: 概念名称
        :param data: 该行业的历史数据
        """
        try:
            # 检查数据是否为空
            if data.empty:
                self.logger.warning(f"没有找到 {concept_name} 的历史数据")
                return
            
            # 创建图表控件实例
            chart_widget = BoardChartWidget(1)
            # chart_widget.resize(1366, 768)
            
            # 绘制图表
            success = chart_widget.plot_chart(concept_name, data, bar_type)
            
            if success:
                # 清除之前的图表（如果有）
                layout = self.widget_view.layout()
                if layout is None:
                    self.widget_view.setLayout(QVBoxLayout())
                for i in reversed(range(layout.count())): 
                    layout.itemAt(i).widget().setParent(None)

                # 添加到布局
                layout.addWidget(chart_widget)
                self.logger.info(f"成功绘制 {concept_name} 图表，数据量: {len(data)}")
            else:
                self.logger.error(f"绘制 {concept_name} 图表失败")

        except Exception as e:
            self.logger.error(f"绘制图表时出错: {e}")
            QMessageBox.warning(self, "绘图错误", f"绘制图表时出现错误:\n{str(e)}")

    def showEvent(self, event):
        """
        重写showEvent方法，在窗口显示时执行初始化操作
        """
        super().showEvent(event)

        new_df_data = AKStockDataProcessor().query_ths_board_concept_overview()
        new_data_date = new_df_data['date'].iloc[0]

        self.logger.info(f"初始化保存的概念板块数据日期：{self.last_board_data_date}")
        self.logger.info(f"最新获取的概念板块数据日期：{new_data_date}")

        if self.last_board_data_date != new_data_date:
            self.logger.info(f"概念板块数据已更新，重新加载")

            self.df_concept_board_data = new_df_data
            self.data_clean()
            self.last_board_data_date = new_data_date

            self.init_card_list()
        else:
            self.logger.info(f"已是最新概念板块数据")
    