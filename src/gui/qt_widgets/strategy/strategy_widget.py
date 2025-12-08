from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QWidget, QMessageBox, QVBoxLayout

# from controller.processor_controller import processor_controller_instance
from gui.qt_widgets.setting.policy_filter_setting_dialog import PolicyFilterSettingDialog
from processor.baostock_processor import BaoStockProcessor
from processor.ak_stock_data_processor import AKStockDataProcessor

from manager.logging_manager import get_logger

from gui.qt_widgets.market.market_widget import MarketWidget

from manager.filter_result_data_manager import FilterResultDataManger
from manager.bao_stock_data_manager import BaostockDataManager
from manager.period_manager import TimePeriod

class StrategyWidget(QWidget):
    def __init__(self, parent=None):
        super(StrategyWidget, self).__init__(parent)
        self.ui = uic.loadUi("./src/gui/qt_widgets/strategy/StrategyWidget.ui", self)

        self.init_para()
        self.init_ui()
        self.init_connect()

        # filter_result_data_manager = FilterResultDataManger(0)
        # filter_result_data_manager.save_old_filter_result_to_db()
        # df_result = filter_result_data_manager.get_filter_result_with_params('2025-11-28')
        # self.logger.info(f"策略结果：\n{df_result}")

        # for i in range(0, 13):
        #     if i == 3:
        #         continue
        #     filter_result_data_manager = FilterResultDataManger(i)
        #     filter_result_data_manager.save_filter_result_from_db_to_txt("2025-12-01")
        #     filter_result_data_manager.save_filter_result_from_db_to_txt("2025-12-02")
        #     filter_result_data_manager.save_filter_result_from_db_to_txt("2025-12-03")


    def init_para(self):
        self.logger = get_logger(__name__)
        self.last_strategy_btn_checked_id = 0
        self.last_select_comboBox_index = 0
    def init_ui(self):
        self.strategy_result_show_widget = MarketWidget()
        # self.strategy_result_show_widget.show_period_frame(False)

        main_layout = self.layout()
        if main_layout is None:
            self.setLayout(QVBoxLayout())
        
        self.layout().addWidget(self.strategy_result_show_widget)

        self.comboBox_level.addItems([TimePeriod.get_chinese_label(TimePeriod.DAY), TimePeriod.get_chinese_label(TimePeriod.WEEK), TimePeriod.get_chinese_label(TimePeriod.MINUTE_15), TimePeriod.get_chinese_label(TimePeriod.MINUTE_30), TimePeriod.get_chinese_label(TimePeriod.MINUTE_60)])
        self.comboBox_level.setCurrentIndex(0)

        self.strategy_button_group = QtWidgets.QButtonGroup(self)
        self.strategy_button_group.addButton(self.btn_zero_up_ma52, 0)
        self.strategy_button_group.addButton(self.btn_zero_up_ma24, 1)
        self.strategy_button_group.addButton(self.btn_zero_up_ma10, 2)
        self.strategy_button_group.addButton(self.btn_zero_up_ma5, 3)
        self.strategy_button_group.addButton(self.btn_zero_down_ma52, 4)
        self.strategy_button_group.addButton(self.btn_zero_down_ma5, 5)
        self.strategy_button_group.addButton(self.btn_zero_down_ma52_breakthrough, 6)
        self.strategy_button_group.addButton(self.btn_zero_down_ma24_breakthrough, 7)
        self.strategy_button_group.addButton(self.btn_zero_down_double_bottom, 8)       # 双底
        self.strategy_button_group.addButton(self.btn_zero_down_double_bottom_9, 9)       # 双底 - 背离
        self.strategy_button_group.addButton(self.btn_zero_down_double_bottom_10, 10)      # 双底 - 动能不足
        self.strategy_button_group.addButton(self.btn_zero_down_double_bottom_11, 11)      # 双底 - 隐形背离
        self.strategy_button_group.addButton(self.btn_zero_down_double_bottom_12, 12)      # 双底 - 隐形动能不足

    def init_connect(self):
        self.strategy_button_group.buttonClicked.connect(self.slot_strategy_button_clicked)

        self.btn_filter_setting.clicked.connect(self.slot_filter_setting_clicked)

        self.comboBox_level.currentTextChanged.connect(self.slot_comboBox_level_currentTextChanged)

    def restore_last_checked_strategy_button(self):
        checked_id = self.last_strategy_btn_checked_id
        if checked_id >= 0 and checked_id < self.strategy_button_group.buttons().__len__():
            last_checked_button = self.strategy_button_group.button(checked_id)
            if last_checked_button:
                last_checked_button.setChecked(True)
        else:
            self.last_strategy_btn_checked_id = 0
            self.btn_zero_up_ma52.setChecked(True)


    def restore_last_select_comboBox_index(self):
        select_index = self.last_select_comboBox_index
        if select_index >= 0 and select_index < self.comboBox_level.count():
            self.comboBox_level.setCurrentIndex(select_index)
        else:
            self.comboBox_level.setCurrentIndex(0)

    def show_default_strategy(self):
        self.btn_zero_up_ma52.setChecked(True)
        checked_id = self.strategy_button_group.checkedId()
        self.last_strategy_btn_checked_id = checked_id

        self.comboBox_level.setCurrentIndex(0)
        self.last_select_comboBox_index = 0

        self.update_strategy_result(checked_id, True)

    def update_date_and_count_labels(self, date, count, period=TimePeriod.DAY):
        self.lineEdit_current_filter_date.setText(date)
        self.label_filter_result_count.setText(str(count))
        self.comboBox_level.setCurrentText(period.value)

    def update_strategy_result(self, checked_id, load_local_result=False, period=TimePeriod.DAY):
        filter_result = []
        dict_daily_filter_result = {}
        dict_weekly_filter_result = {}


        lastest_stock_data_date = BaostockDataManager().get_lastest_stock_data_date('sh.600000', period)
        filter_result_data_manager = FilterResultDataManger(checked_id)
        lastest_filter_result_date = filter_result_data_manager.get_lastest_filter_result_date(period)
        self.logger.info(f"最新策略结果日期：{lastest_filter_result_date}")
        self.logger.info(f"最新股票数据日期：{lastest_stock_data_date}")

        b_use_local_result = False

        if load_local_result:
            b_use_local_result = True
        else:
            b_ret = lastest_filter_result_date is not None and lastest_stock_data_date != ""
            b_ret_2 = True if (lastest_filter_result_date is None or lastest_stock_data_date is None) else lastest_filter_result_date >= lastest_stock_data_date
            if b_ret and b_ret_2:
                msg = f"本地已存在【{TimePeriod.get_chinese_label(period)}】级别最新日期（{lastest_stock_data_date}）的筛选策略，是否重新筛选？\n\n注意：重新筛选结果将覆盖本地数据！"
                reply = QtWidgets.QMessageBox.question(self, '提示', msg,
                                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                        QtWidgets.QMessageBox.No)
                
                if reply == QtWidgets.QMessageBox.No:
                    b_use_local_result = True
                else:
                    b_use_local_result = False
            else:
                if checked_id >= 9 and checked_id <= 12:
                    QtWidgets.QMessageBox.information(self, '提示', "暂无最新筛选结果，请执行【零轴下方双底】策略！")
                    return
                
                msg = f"即将更新【{TimePeriod.get_chinese_label(period)}】级别至日期（{lastest_stock_data_date}）的筛选策略，确认执行？\n\n提示：执行策略较为耗时，请耐心等待！"
                reply = QtWidgets.QMessageBox.question(self, '提示', msg,
                                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                        QtWidgets.QMessageBox.No)
                
                if reply == QtWidgets.QMessageBox.No:
                    b_use_local_result = True
                    return False
                else:
                    b_use_local_result = False
                
                self.logger.info("开始策略筛选...") 
            
        if b_use_local_result:
            # 从本地加载筛选结果
            df_local_filter_result = filter_result_data_manager.get_lastest_filter_result_with_params(period)
            # self.logger.info(f"本地策略结果：\n{df_local_filter_result.tail(3)}")
            filter_result = df_local_filter_result['code'].tolist()
        else:
            if checked_id == 0:
                # 这里可以先检查本地数据是否存在，如果存在则直接从本地加载筛选结果列表，而无需重新调用筛选接口
                filter_result = BaoStockProcessor().daily_up_ma52_filter(AKStockDataProcessor().get_stocks_eastmoney(), period)
                
            elif checked_id == 1:
                filter_result = BaoStockProcessor().daily_up_ma24_filter(AKStockDataProcessor().get_stocks_eastmoney(), period)
                
            elif checked_id == 2:
                filter_result = BaoStockProcessor().daily_up_ma10_filter(AKStockDataProcessor().get_stocks_eastmoney(), period)
            elif checked_id == 3:
                # filter_result = BaoStockProcessor().daily_up_ma5_filter(AKStockDataProcessor().get_stocks_eastmoney())
                pass
            elif checked_id == 4:
                filter_result = BaoStockProcessor().daily_down_between_ma24_ma52_filter(AKStockDataProcessor().get_stocks_eastmoney(), period)
            elif checked_id == 5:
                filter_result = BaoStockProcessor().daily_down_between_ma5_ma52_filter(AKStockDataProcessor().get_stocks_eastmoney(), period)
            elif checked_id == 6:
                filter_result = BaoStockProcessor().daily_down_breakthrough_ma52_filter(AKStockDataProcessor().get_stocks_eastmoney(), period)
            elif checked_id == 7:
                filter_result = BaoStockProcessor().daily_down_breakthrough_ma24_filter(AKStockDataProcessor().get_stocks_eastmoney(), period)
            elif checked_id == 8:
                filter_result = BaoStockProcessor().daily_down_double_bottom_filter(AKStockDataProcessor().get_stocks_eastmoney(), period)
            else:
                filter_result = BaoStockProcessor().daily_up_ma52_filter(AKStockDataProcessor().get_stocks_eastmoney(), period)

        self.logger.info(f"策略结果：\n{filter_result[:3]}...{filter_result[-3:]}\n策略结果数量：{len(filter_result)}")
        self.update_date_and_count_labels(lastest_stock_data_date, len(filter_result), period)
        
        new_dict_lastest_1d_stock_data = BaostockDataManager().get_lastest_row_data_dict_by_code_list_auto(filter_result)
        result_data_len = len(new_dict_lastest_1d_stock_data)
        self.logger.info(f"new_dict_lastest_1d_stock_data 长度: {result_data_len}")
        if result_data_len == 0:
            self.logger.info(f"无策略结果")
            return False
        
        if new_dict_lastest_1d_stock_data is not None or result_data_len > 0:
            self.strategy_result_show_widget.update_stock_data_dict(new_dict_lastest_1d_stock_data)
        else:
            self.logger.info(f"策略结果为空")

        return True

    # ------------槽函数-----------
    def slot_strategy_button_clicked(self, btn):
        if btn.isChecked():
            checked_btn_text = btn.text()
            checked_id = self.strategy_button_group.checkedId()
            self.logger.info(f"slot_strategy_button_clicked--text: {checked_btn_text}, id: {checked_id}")

            if checked_id == 3:
                self.logger.info(f"暂不支持5日MA策略")
                QtWidgets.QMessageBox.warning(self, '警告', '暂不支持零轴上方5日MA策略！')
                self.restore_last_checked_strategy_button()
                return

            # text = self.comboBox_level.currentText()
            # period = TimePeriod.from_label(text)

            # 使用信号阻塞避免触发更新
            self.comboBox_level.blockSignals(True)
            self.comboBox_level.setCurrentText(TimePeriod.get_chinese_label(TimePeriod.DAY))
            # 恢复信号
            self.comboBox_level.blockSignals(False)

            b_ret = self.update_strategy_result(checked_id)

            # k线也默认显示日线级别

            if not b_ret:
                # 这里不用阻塞信号是因为设置Checked不会触发clicked信号
                self.restore_last_checked_strategy_button()
                return

            self.last_strategy_btn_checked_id = checked_id


            

    def slot_filter_setting_clicked(self):
        self.logger.info("点击筛选设置")
        dlg = PolicyFilterSettingDialog()
        dlg.exec()
        self.logger.info("完成筛选设置")

    def slot_comboBox_level_currentTextChanged(self, text):
        self.logger.info(f"slot_comboBox_level_currentTextChanged--text: {text}")
        b_ret = self.update_strategy_result(self.strategy_button_group.checkedId(), False, TimePeriod.from_label(text))
        if not b_ret:
            self.comboBox_level.blockSignals(True)
            self.restore_last_select_comboBox_index()
            self.comboBox_level.blockSignals(False)
            return
        
        self.last_select_comboBox_index = self.comboBox_level.currentIndex()
