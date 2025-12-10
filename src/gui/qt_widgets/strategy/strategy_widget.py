from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QWidget, QMessageBox, QVBoxLayout
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtCore import QRegExp
import re

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
        self.last_filter_date = ""
        self.last_strategy_btn_checked_id = 0
        self.last_select_comboBox_index = 0
    def init_ui(self):

        # 设置日期输入格式验证器 (YYYY-MM-DD)
        date_pattern = QRegExp(r'^\d{4}-\d{2}-\d{2}$')
        validator = QRegExpValidator(date_pattern, self.lineEdit_current_filter_date)
        self.lineEdit_current_filter_date.setValidator(validator)

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
        self.lineEdit_current_filter_date.editingFinished.connect(self.slot_lineEdit_current_filter_date_editingFinished)
        self.strategy_button_group.buttonClicked.connect(self.slot_strategy_button_clicked)

        self.btn_filter_setting.clicked.connect(self.slot_filter_setting_clicked)

        self.comboBox_level.currentTextChanged.connect(self.slot_comboBox_level_currentTextChanged)

    def restore_last_filter_date(self):
        if self.last_filter_date != "":
            self.lineEdit_current_filter_date.setText(self.last_filter_date)
        else:
            self.lineEdit_current_filter_date.setText("2025-12-01")
            self.last_filter_date = "2025-12-01"

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
        # 默认选中策略
        self.btn_zero_up_ma52.setChecked(True)
        checked_id = self.strategy_button_group.checkedId()
        self.last_strategy_btn_checked_id = checked_id

        # 默认选中级别
        self.comboBox_level.setCurrentIndex(0)
        self.last_select_comboBox_index = 0

        # 默认最新日期
        filter_result_data_manager = FilterResultDataManger(checked_id)
        select_period_text = self.comboBox_level.currentText()
        select_period = TimePeriod.from_label(select_period_text)

        lastest_filter_result_date = filter_result_data_manager.get_lastest_filter_result_date(select_period)
        if lastest_filter_result_date is not None:
            self.lineEdit_current_filter_date.setText(lastest_filter_result_date)
            self.last_filter_date = lastest_filter_result_date

        self.update_strategy_result_new(True)

    def update_date_and_count_labels(self, date, count, period=TimePeriod.DAY):
        self.lineEdit_current_filter_date.blockSignals(True)
        self.lineEdit_current_filter_date.setText(date)
        self.lineEdit_current_filter_date.blockSignals(False)

        self.label_filter_result_count.setText(str(count))

        self.comboBox_level.blockSignals(True)
        self.comboBox_level.setCurrentText(period.value)
        self.comboBox_level.blockSignals(False)

    def update_count_label(self, count):
        self.label_filter_result_count.setText(str(count))

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

            # 已是最新策略结果，直接加载不弹窗
            if b_ret and b_ret_2:
            #     msg = f"本地已存在【{TimePeriod.get_chinese_label(period)}】级别最新日期（{lastest_stock_data_date}）的筛选策略，是否重新筛选？\n\n注意：重新筛选结果将覆盖本地数据！"
            #     reply = QtWidgets.QMessageBox.question(self, '提示', msg,
            #                             QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            #                             QtWidgets.QMessageBox.No)
                
            #     if reply == QtWidgets.QMessageBox.Yes:
            #         if checked_id >= 9 and checked_id <= 12:
            #             self.logger.info(f"双底扩展策略默认加载本地数据")
            #             b_use_local_result = True
            #         else:
            #             b_use_local_result = False
            #     else:
            #         
                b_use_local_result = True
                    
            else:
                # 无最新策略结果，
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
    
    def update_strategy_result_new(self, load_local_result=False):
        s_target_date = self.lineEdit_current_filter_date.text()

        strategy_btn_checked_id = self.strategy_button_group.checkedId()
        checked_btn_text = self.strategy_button_group.button(strategy_btn_checked_id).text()

        select_period_text = self.comboBox_level.currentText()
        select_period = TimePeriod.from_label(select_period_text)

        filter_result = []

        filter_result_data_manager = FilterResultDataManger(strategy_btn_checked_id)
        df_local_filter_result = filter_result_data_manager.get_filter_result_with_params(s_target_date, select_period)

        if load_local_result:
            b_use_local_result = True
        else:
            lastest_stock_data_date = None
            lastest_stock_data_date = BaostockDataManager().get_lastest_stock_data_date('sh.600000', select_period)
            self.logger.info(f"最新股票数据日期：{lastest_stock_data_date}")
            
            # 人工确认弹窗
            if df_local_filter_result is not None and not df_local_filter_result.empty:
                lastest_filter_result_date = None
                lastest_filter_result_date = df_local_filter_result['date'].iloc[0]
                self.logger.info(f"最新筛选结果日期：{lastest_filter_result_date}")
                # self.logger.info(f"lastest_stock_data_date的类型：{type(lastest_stock_data_date)}， lastest_filter_result_date的类型：{type(lastest_filter_result_date)}")  # 都是<class 'str'>
                
                none_ret = lastest_filter_result_date is None or lastest_stock_data_date is None
                date_ret = lastest_filter_result_date >= lastest_stock_data_date
                self.logger.info(f"none_ret: {none_ret}, date_ret: {date_ret}")
                b_ret = True if none_ret else date_ret
                if b_ret:
                    msg = f"本地已存在最新【{select_period_text}】级别筛选结果\n筛选结果日期：{lastest_filter_result_date}\n目标股票日期：{s_target_date}\n是否重新执行【{checked_btn_text}】筛选策略？\n\n注意：重新筛选结果将覆盖本地数据！"
                else:
                    s_target_date = lastest_stock_data_date
                    msg = f"【{select_period_text}】级别的股票日期已更新至：{lastest_stock_data_date}\n筛选结果日期：{lastest_filter_result_date}\n是否更新执行【{checked_btn_text}】筛选策略？\n\n提示：执行策略较为耗时，请耐心等待！"

                reply = QtWidgets.QMessageBox.question(self, '提示', msg,
                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                        QtWidgets.QMessageBox.No)
                
                if reply == QtWidgets.QMessageBox.Yes:
                    if strategy_btn_checked_id >= 9 and strategy_btn_checked_id <= 12:
                        self.logger.info(f"双底扩展策略默认加载本地数据")
                        b_use_local_result = True
                    else:
                        b_use_local_result = False
                else:
                    b_use_local_result = True
            else:
                if strategy_btn_checked_id >= 9 and strategy_btn_checked_id <= 12:
                    QtWidgets.QMessageBox.information(self, '提示', "暂无最新筛选结果，请执行【零轴下方双底】策略！")
                    return False
                
                msg = f"即将执行【{select_period_text}】级别，目标股票日期（{s_target_date}）的【{checked_btn_text}】策略筛选\n请确认？\n\n提示：执行策略较为耗时，请耐心等待！"
                reply = QtWidgets.QMessageBox.question(self, '提示', msg,
                                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                        QtWidgets.QMessageBox.No)
                
                if reply == QtWidgets.QMessageBox.Yes:
                    b_use_local_result = False
                    s_target_date = lastest_stock_data_date
                else:
                    b_use_local_result = True
                    return False

        if b_use_local_result:
            # 本地存在指定日期、策略、时间级别的筛选结果
            # self.logger.info(f"本地策略结果：\n{df_local_filter_result.tail(3)}")
            filter_result = df_local_filter_result['code'].tolist()
        else:
            filter_result = self.process_filter_result(s_target_date, strategy_btn_checked_id, select_period)

        self.logger.info(f"策略结果：\n{filter_result[:3]}...{filter_result[-3:]}\n策略结果数量：{len(filter_result)}")
        
        # 展示最后日期的k线，而不是指定日期的k线
        new_dict_lastest_1d_stock_data = BaostockDataManager().get_lastest_row_data_dict_by_code_list_auto(filter_result)
        result_data_len = len(new_dict_lastest_1d_stock_data)
        self.logger.info(f"new_dict_lastest_1d_stock_data 长度: {result_data_len}")

        if new_dict_lastest_1d_stock_data is not None and result_data_len == 0:
            self.logger.info(f"无策略结果")
            return False
        
        if result_data_len > 0:
            self.strategy_result_show_widget.update_stock_data_dict(new_dict_lastest_1d_stock_data)
        else:
            self.logger.info(f"策略结果为空")

        self.update_date_and_count_labels(s_target_date, result_data_len, select_period)
        # 切换至指定级别K线显示
        
        return True
    
    def process_filter_result(self, target_date, checked_id, period):
        self.logger.info(f"执行筛选，目标日期：{target_date}，策略ID：{checked_id}，时间级别：{period.value}")
        filter_result = []
        if checked_id == 0:
            # 这里可以先检查本地数据是否存在，如果存在则直接从本地加载筛选结果列表，而无需重新调用筛选接口
            filter_result = BaoStockProcessor().daily_up_ma52_filter(AKStockDataProcessor().get_stocks_eastmoney(), period, end_date=target_date)
            
        elif checked_id == 1:
            filter_result = BaoStockProcessor().daily_up_ma24_filter(AKStockDataProcessor().get_stocks_eastmoney(), period, end_date=target_date)
            
        elif checked_id == 2:
            filter_result = BaoStockProcessor().daily_up_ma10_filter(AKStockDataProcessor().get_stocks_eastmoney(), period, end_date=target_date)
        elif checked_id == 3:
            # filter_result = BaoStockProcessor().daily_up_ma5_filter(AKStockDataProcessor().get_stocks_eastmoney())
            pass
        elif checked_id == 4:
            filter_result = BaoStockProcessor().daily_down_between_ma24_ma52_filter(AKStockDataProcessor().get_stocks_eastmoney(), period, end_date=target_date)
        elif checked_id == 5:
            filter_result = BaoStockProcessor().daily_down_between_ma5_ma52_filter(AKStockDataProcessor().get_stocks_eastmoney(), period, end_date=target_date)
        elif checked_id == 6:
            filter_result = BaoStockProcessor().daily_down_breakthrough_ma52_filter(AKStockDataProcessor().get_stocks_eastmoney(), period, end_date=target_date)
        elif checked_id == 7:
            filter_result = BaoStockProcessor().daily_down_breakthrough_ma24_filter(AKStockDataProcessor().get_stocks_eastmoney(), period, end_date=target_date)
        elif checked_id == 8:
            filter_result = BaoStockProcessor().daily_down_double_bottom_filter(AKStockDataProcessor().get_stocks_eastmoney(), period, end_date=target_date)
        else:
            filter_result = BaoStockProcessor().daily_up_ma52_filter(AKStockDataProcessor().get_stocks_eastmoney(), period, end_date=target_date)

        return filter_result

    # ------------槽函数-----------
    def slot_lineEdit_current_filter_date_editingFinished(self):
        text = self.lineEdit_current_filter_date.text()
        self.logger.info(f"输入的日期值为：{text}")

         # 定义日期格式正则表达式
        date_pattern = r'^\d{4}-\d{2}-\d{2}$'
        
        # 检查格式是否匹配
        if not re.match(date_pattern, text):
            QMessageBox.warning(self, '输入错误', '请输入正确日期格式: YYYY-MM-DD')
            # 恢复之前的有效值或者清空
            self.restore_last_filter_date()
            return
        
        # 可选：进一步验证日期有效性（例如月份1-12，日期1-31）
        try:
            year, month, day = map(int, text.split('-'))
            if not (1 <= month <= 12) or not (1 <= day <= 31):
                raise ValueError("无效日期")
            # 可以添加更多日期有效性检查
                
        except ValueError:
            QMessageBox.warning(self, '输入错误', '请输入有效的日期')
            self.restore_last_filter_date()
            return
            
        # 在这里可以添加其他处理逻辑
        BaoStockProcessor().set_filter_date(text)

        self.lineEdit_current_filter_date.blockSignals(True)
        self.lineEdit_current_filter_date.clearFocus()
        self.lineEdit_current_filter_date.blockSignals(False)
        b_ret = self.update_strategy_result_new()

        if not b_ret:
            self.restore_last_filter_date()
            BaoStockProcessor().set_filter_date(self.last_filter_date)
            return

        # 保存当前有效的日期
        self.last_filter_date = text

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
            # self.comboBox_level.blockSignals(True)
            # self.comboBox_level.setCurrentText(TimePeriod.get_chinese_label(TimePeriod.DAY))
            # # 恢复信号
            # self.comboBox_level.blockSignals(False)

            b_ret = self.update_strategy_result_new()

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
        checked_id = self.strategy_button_group.checkedId()
        # if checked_id >= 9 and checked_id <= 12:
        #     self.btn_zero_down_double_bottom.setChecked(True)
        #     self.last_strategy_btn_checked_id = 8
        #     checked_id = self.strategy_button_group.checkedId()
        #     self.logger.info(f"双底扩展策略默认执行双底策略接口,checked_id: {checked_id}")
            
        b_ret = self.update_strategy_result_new()
        if not b_ret:
            self.comboBox_level.blockSignals(True)
            self.restore_last_select_comboBox_index()
            self.comboBox_level.blockSignals(False)
            return
        
        self.last_select_comboBox_index = self.comboBox_level.currentIndex()
