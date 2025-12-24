from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtWidgets import QDialog, QMessageBox
from PyQt5.QtCore import QDate

import random
from datetime import date

from manager.logging_manager import get_logger
# from gui.qt_widgets.MComponents.indicators.indicators_view_widget import IndicatorsViewWidget

from processor.baostock_processor import BaoStockProcessor
from manager.bao_stock_data_manager import BaostockDataManager
from manager.period_manager import TimePeriod
from manager.review_demo_trading_manager import ReviewDemoTradingManager

class ReviewDialog(QDialog):
    def __init__(self, parent=None):
        super(ReviewDialog, self).__init__(parent) 
        uic.loadUi('./src/gui/qt_widgets/review/ReviewDialog.ui', self)

        self.init_para()
        self.init_ui()
        self.init_connect()

        # self.load_data('sh.600000', "2025-12-08")

    def init_para(self):
        self.logger = get_logger(__name__)
        self.dict_progress_data = {}

        self.current_load_code = ""

        self.demo_trading_manager = ReviewDemoTradingManager()

    def init_ui(self):
        from gui.qt_widgets.MComponents.indicators.indicators_view_widget import IndicatorsViewWidget
        self.indicators_view_widget = IndicatorsViewWidget(self)
        self.indicators_view_widget.setProperty("review", True)
        self.indicators_view_widget.show_review_btn(False)

        self.verticalLayout_indicators_view.addWidget(self.indicators_view_widget)

        self.btn_play.setProperty("is_play", False)

        self.comboBox_period.addItems([TimePeriod.get_chinese_label(TimePeriod.DAY), TimePeriod.get_chinese_label(TimePeriod.WEEK), TimePeriod.get_chinese_label(TimePeriod.MINUTE_15), TimePeriod.get_chinese_label(TimePeriod.MINUTE_30), TimePeriod.get_chinese_label(TimePeriod.MINUTE_60)])
        self.comboBox_period.setCurrentIndex(0)

        self.btn_load_data_random.setAutoDefault(False)
        self.btn_load_data_random.setDefault(False)

        self.btn_load_data.setAutoDefault(False)
        self.btn_load_data.setDefault(False)

        self.playing_enabled(True)

        self.label_total_assets.setText(str(self.demo_trading_manager.get_total_assets()))
        self.label_available_balance.setText(str(self.demo_trading_manager.get_available_balance()))

    def init_connect(self):
        self.indicators_view_widget.sig_current_animation_index_changed.connect(self.slot_current_animation_index_changed)
        self.indicators_view_widget.sig_init_review_animation_finished.connect(self.slot_init_review_animation_finished)

        self.lineEdit_code.editingFinished.connect(self.slot_lineEdit_code_editingFinished)
        self.dateEdit.dateChanged.connect(self.slot_dateEdit_dateChanged)
        self.comboBox_period.currentIndexChanged.connect(self.slot_comboBox_period_currentIndexChanged)

        self.btn_load_data_random.clicked.connect(self.slot_btn_load_data_random_clicked)
        self.btn_load_data.clicked.connect(self.slot_btn_load_data_clicked)

        self.btn_play.clicked.connect(self.slot_btn_play_clicked)

        self.btn_back_to_front.clicked.connect(self.slot_btn_back_to_front_clicked)
        self.btn_back_ten.clicked.connect(self.slot_btn_back_ten_clicked)
        self.btn_back.clicked.connect(self.slot_btn_back_clicked)
        self.btn_move_on.clicked.connect(self.slot_btn_move_on_clicked)
        self.btn_move_on_10.clicked.connect(self.slot_btn_move_on_10_clicked)
        self.btn_move_to_last.clicked.connect(self.slot_btn_move_to_last_clicked)

        self.horizontalSlider_progress.valueChanged.connect(self.slot_horizontalSlider_progress_valueChanged)

        # 模拟交易
        self.lineEdit_price.editingFinished.connect(self.slot_lineEdit_price_editingFinished)
        self.btn_all.clicked.connect(self.slot_btn_all_clicked)
        self.btn_one_half.clicked.connect(self.slot_btn_one_half_clicked)
        self.btn_one_third.clicked.connect(self.slot_btn_one_third_clicked)
        self.btn_a_quarter.clicked.connect(self.slot_btn_a_quarter_clicked)
        self.btn_one_in_five.clicked.connect(self.slot_btn_one_in_five_clicked)

        self.btn_buy.clicked.connect(self.slot_btn_buy_clicked)
        self.btn_sell.clicked.connect(self.slot_btn_sell_clicked)
        self.btn_pending_order_cancel.clicked.connect(self.slot_btn_pending_order_cancel_clicked)

    def update_count_and_amount_labels(self, price, count):
        self.lineEdit_count.setText(str(count))
        self.lineEdit_amount.setText(str(count * price))

    def playing_enabled(self, is_playing):
        self.lineEdit_code.setEnabled(not is_playing)
        self.dateEdit.setEnabled(not is_playing)

        self.btn_back_to_front.setEnabled(not is_playing)
        self.btn_back_ten.setEnabled(not is_playing)
        self.btn_back.setEnabled(not is_playing)
        self.btn_move_on.setEnabled(not is_playing)
        self.btn_move_on_10.setEnabled(not is_playing)
        self.btn_move_to_last.setEnabled(not is_playing)

        self.horizontalSlider_progress.setEnabled(not is_playing)

        self.btn_buy.setEnabled(not is_playing)
        self.btn_sell.setEnabled(not is_playing)
        self.btn_pending_order_cancel.setEnabled(not is_playing)

        self.btn_all.setEnabled(not is_playing)
        self.btn_one_half.setEnabled(not is_playing)
        self.btn_one_third.setEnabled(not is_playing)
        self.btn_a_quarter.setEnabled(not is_playing)
        self.btn_one_in_five.setEnabled(not is_playing)


    def update_progress_label(self, current_index):
        if self.dict_progress_data is not None and self.dict_progress_data != {}:
            s_current_progress = f"{current_index}/{self.dict_progress_data['max_index']}"
            self.label_progress.setText(s_current_progress)
        else:
            self.logger.info("进度数据为空")
            self.label_progress.setText("")

    def update_trading_widgets_status(self):
        trading_status = self.demo_trading_manager.get_trading_status()

        if trading_status == 1 or trading_status == 3:
            self.btn_all.setEnabled(False)
            self.btn_one_half.setEnabled(False)
            self.btn_one_third.setEnabled(False)
            self.btn_a_quarter.setEnabled(False)
            self.btn_one_in_five.setEnabled(False)
            self.btn_buy.setEnabled(False)
            self.btn_sell.setEnabled(False)
            self.btn_pending_order_cancel.setEnabled(True)
        elif trading_status == 5:
            self.btn_all.setEnabled(False)
            self.btn_one_half.setEnabled(False)
            self.btn_one_third.setEnabled(False)
            self.btn_a_quarter.setEnabled(False)
            self.btn_one_in_five.setEnabled(False)
            self.btn_buy.setEnabled(False)
            self.btn_sell.setEnabled(True)
            self.btn_pending_order_cancel.setEnabled(False)
        else:
            self.btn_all.setEnabled(True)
            self.btn_one_half.setEnabled(True)
            self.btn_one_third.setEnabled(True)
            self.btn_a_quarter.setEnabled(True)
            self.btn_one_in_five.setEnabled(True)
            self.btn_buy.setEnabled(True)
            self.btn_sell.setEnabled(False)
            self.btn_pending_order_cancel.setEnabled(False)

    def reset_trading_record(self):
        self.lineEdit_price.blockSignals(True)
        self.lineEdit_price.clear()
        self.lineEdit_price.blockSignals(False)

        self.lineEdit_count.clear()
        self.lineEdit_amount.clear()

        # 清空收益率曲线

        # 清空交易记录列表

    def load_data(self, code, date):
        stock_codes = [code]
        bao_stock_data_manager = BaostockDataManager()
        new_dict_lastest_1d_stock_data = bao_stock_data_manager.get_lastest_row_data_dict_by_code_list_auto(stock_codes)
        self.logger.info(f"new_dict_lastest_1d_stock_data: {new_dict_lastest_1d_stock_data}")

        if new_dict_lastest_1d_stock_data:
            self.indicators_view_widget.update_stock_data_dict(code)
            data = new_dict_lastest_1d_stock_data[code].iloc[-1]
            # self.indicators_view_widget.update_chart(data, '2025-12-08')
            self.dict_progress_data = self.indicators_view_widget.init_animation(data, date)
            # if self.dict_progress_data is not None and self.dict_progress_data != {}:
            #     self.horizontalSlider_progress.setMinimum(self.dict_progress_data['min_index'])
            #     self.horizontalSlider_progress.setMaximum(self.dict_progress_data['max_index'])

            #     self.horizontalSlider_progress.blockSignals(True)
            #     self.horizontalSlider_progress.setSliderPosition(self.dict_progress_data['start_date_index'])
            #     self.horizontalSlider_progress.blockSignals(False)

            #     self.update_progress_label(self.dict_progress_data['start_date_index'])
            # else:
            #     self.logger.info(f"初始化返回的进度数据为空")

            self.current_load_code = code

            self.demo_trading_manager.reset_trading_record()
            self.playing_enabled(False)
            self.update_trading_widgets_status()
            self.reset_trading_record()

        else:
            self.logger.info(f"结果为空")

    def get_random_date(self):
        '''    
        # 使用示例
        random_date = get_random_date()
        print(random_date)  # 输出类似: 2025-08-08
    '''
        current_year = date.today().year
        # 生成3-8月之间的随机月份
        month = random.randint(3, 8)
        
        # 根据月份设置随机日期范围
        if month in [1, 3, 5, 7, 8, 10, 12]:
            day = random.randint(1, 31)
        elif month in [4, 6, 9, 11]:
            day = random.randint(1, 30)
        else:  # 2月
            # 判断闰年
            if (current_year % 4 == 0 and current_year % 100 != 0) or (current_year % 400 == 0):
                day = random.randint(1, 29)
            else:
                day = random.randint(1, 28)
        
        return f"{current_year}-{month:02d}-{day:02d}"



    # -----------------槽函数----------------
    def slot_current_animation_index_changed(self, index):
        # self.logger.info(f"收到k线图进度: {index}")

        self.horizontalSlider_progress.blockSignals(True)
        self.horizontalSlider_progress.setSliderPosition(index)
        self.horizontalSlider_progress.blockSignals(False)

        self.update_progress_label(index)

        date_time = self.indicators_view_widget.get_current_date_time_by_index(index)
        min_price, max_price = self.indicators_view_widget.get_min_and_max_price_by_index(index)

        trading_status = self.demo_trading_manager.get_trading_status()

        target_status = 0
        if trading_status == 1:
            target_status = 1
        elif trading_status == 3:
            target_status = 2
        elif trading_status == 5:
            target_status = 5
        
        self.demo_trading_manager.update_trading_record(target_status, min_price, max_price, date_time)
        self.update_trading_widgets_status()

    def slot_init_review_animation_finished(self, success, dict_progress_data):
        if success:
            self.logger.info("回放动画初始化成功")
            self.dict_progress_data = dict_progress_data
            if self.dict_progress_data is not None and self.dict_progress_data != {}:
                self.horizontalSlider_progress.setMinimum(self.dict_progress_data['min_index'])
                self.horizontalSlider_progress.setMaximum(self.dict_progress_data['max_index'])

                self.horizontalSlider_progress.blockSignals(True)
                self.horizontalSlider_progress.setSliderPosition(self.dict_progress_data['start_date_index'])
                self.horizontalSlider_progress.blockSignals(False)

                self.update_progress_label(self.dict_progress_data['start_date_index'])

                # start_date = self.dict_progress_data['start_date']
                # self.logger.info(f"实际开始日期--start_date: {start_date}")

                # self.dateEdit.blockSignals(True)
                # self.dateEdit.setDate(QDate.fromString(start_date, "yyyy-MM-dd"))
                # self.dateEdit.blockSignals(False)

            else:
                self.logger.info(f"初始化返回的进度数据为空")

    def slot_lineEdit_code_editingFinished(self):
        code = self.lineEdit_code.text()
        dict_lastest_1d_data = BaostockDataManager().get_lastest_1d_stock_data_dict_from_cache()
        if code not in dict_lastest_1d_data:
            QMessageBox.warning(self, "提示", "请输入正确的股票代码")
            return
        
        self.label_name.setText(str(dict_lastest_1d_data[code]['name'].iloc[0]))

        self.lineEdit_code.blockSignals(True)
        self.lineEdit_code.clearFocus()
        self.lineEdit_code.blockSignals(False)

    def slot_dateEdit_dateChanged(self, date):
        self.logger.info(f"收到日期选择: {date}")
        s_date = date.toString("yyyy-MM-dd")
        self.logger.info(f"收到日期选择--s_date: {s_date}")

    def slot_comboBox_period_currentIndexChanged(self, index):
        text = self.comboBox_period.currentText()
        self.logger.info(f"收到周期选择: {text}, index: {index}")

    def slot_btn_load_data_random_clicked(self):
        # 从 dict_lastest_1d_data 中获取一个随机的 code 和对应的 name
        dict_lastest_1d_data = BaostockDataManager().get_lastest_1d_stock_data_dict_from_cache()
        if dict_lastest_1d_data:
            # 随机选择一个 code
            code = random.choice(list(dict_lastest_1d_data.keys()))
            
            # 获取对应的 name
            name = dict_lastest_1d_data[code]['name'].iloc[0]
            
            print(f"随机股票代码: {code}, 对应名称: {name}")
        else:
            print("没有可用的股票数据")
            return
        
        date = self.get_random_date()

        period = self.comboBox_period.currentText()
        self.logger.info(f"点击随机加载数据: {code}, {date}, {period}")

        if self.current_load_code == code:
            self.logger.info("当前股票数据已加载，无需重复加载")
            return
        
        self.load_data(code, date)

        start_date = self.dict_progress_data['start_date']
        self.logger.info(f"实际开始日期--start_date: {start_date}")

        self.label_name.setText(str(dict_lastest_1d_data[code]['name'].iloc[0]))

        self.lineEdit_code.blockSignals(True)
        self.lineEdit_code.setText(code)
        self.lineEdit_code.blockSignals(False)

        self.dateEdit.blockSignals(True)
        self.dateEdit.setDate(QDate.fromString(start_date, "yyyy-MM-dd"))
        self.dateEdit.blockSignals(False)

        self.btn_buy.setDefault(True)


    def slot_btn_load_data_clicked(self):
        code = self.lineEdit_code.text()
        date = self.dateEdit.date().toString("yyyy-MM-dd")
        period = self.comboBox_period.currentText()
        self.logger.info(f"点击加载数据: {code}, {date}, {period}")

        if self.current_load_code == code:
            self.logger.info("当前股票数据已加载，无需重复加载")
            return
        
        self.load_data(code, date)

        start_date = self.dict_progress_data['start_date']
        self.logger.info(f"实际开始日期--start_date: {start_date}")

        self.dateEdit.blockSignals(True)
        self.dateEdit.setDate(QDate.fromString(start_date, "yyyy-MM-dd"))
        self.dateEdit.blockSignals(False)

        self.btn_buy.setDefault(True)

    def slot_btn_play_clicked(self):
        if self.btn_play.property("is_play"):
            self.logger.info("暂停播放")
            self.indicators_view_widget.pause_animation()
            self.btn_play.setProperty("is_play", False)
            # self.btn_play.setIcon(QtGui.QIcon("./src/gui/qt_widgets/images/pause.png"))
            self.playing_enabled(False)
        else:
            self.logger.info("开始播放")
            self.indicators_view_widget.start_animation()
            self.btn_play.setProperty("is_play", True)
            self.playing_enabled(True)

    def slot_btn_back_to_front_clicked(self):
        self.indicators_view_widget.back_to_front()

    def slot_btn_back_ten_clicked(self):
        self.indicators_view_widget.step_backward(10)

    def slot_btn_back_clicked(self):
        self.indicators_view_widget.step_backward()

    def slot_btn_move_on_clicked(self):
        self.indicators_view_widget.step_forward()

    def slot_btn_move_on_10_clicked(self):
        self.indicators_view_widget.step_forward(10)

    def slot_btn_move_to_last_clicked(self):
        self.indicators_view_widget.back_to_end()

    def slot_horizontalSlider_progress_valueChanged(self, value):
        self.logger.info(f"进度条值改变: {value}")
        self.indicators_view_widget.go_to_target_index(value)

    def slot_lineEdit_price_editingFinished(self):
        str_price = self.lineEdit_price.text()
        str_count = self.lineEdit_count.text()
        self.lineEdit_amount.setText(str(float(str_price) * int(str_count)))

    def slot_btn_all_clicked(self):
        str_price = self.lineEdit_price.text()
        max_count = self.demo_trading_manager.get_buy_count(float(str_price))

        self.logger.info(f"最大可买数量: {max_count}")
        self.lineEdit_count.setText(str(max_count))
        self.lineEdit_amount.setText(str(max_count * float(str_price)))

    def slot_btn_one_half_clicked(self):
        str_price = self.lineEdit_price.text()
        max_count = self.demo_trading_manager.get_buy_count(float(str_price), 1)

        self.logger.info(f"最大可买数量: {max_count}")
        self.lineEdit_count.setText(str(max_count))
        self.lineEdit_amount.setText(str(max_count * float(str_price)))

    def slot_btn_one_third_clicked(self):
        str_price = self.lineEdit_price.text()
        max_count = self.demo_trading_manager.get_buy_count(float(str_price), 2)
        self.logger.info(f"最大可买数量: {max_count}")
        self.lineEdit_count.setText(str(max_count))
        self.lineEdit_amount.setText(str(max_count * float(str_price)))

    def slot_btn_a_quarter_clicked(self):
        str_price = self.lineEdit_price.text()
        max_count = self.demo_trading_manager.get_buy_count(float(str_price), 3)
        self.logger.info(f"最大可买数量: {max_count}")
        self.lineEdit_count.setText(str(max_count))
        self.lineEdit_amount.setText(str(max_count * float(str_price)))

    def slot_btn_one_in_five_clicked(self):
        str_price = self.lineEdit_price.text()
        max_count = self.demo_trading_manager.get_buy_count(float(str_price), 4)

        self.logger.info(f"最大可买数量: {max_count}")
        self.lineEdit_count.setText(str(max_count))
        self.lineEdit_amount.setText(str(max_count * float(str_price)))

    def slot_btn_buy_clicked(self):
        if self.current_load_code == "":
            self.logger.info("请先加载股票数据")
            return

        str_code = self.lineEdit_code.text()
        str_name = self.label_name.text()
        str_price = self.lineEdit_price.text()
        str_count = self.lineEdit_count.text()

        current_index = self.horizontalSlider_progress.value()
        str_date_time = self.indicators_view_widget.get_current_date_time_by_index(current_index)
        self.logger.info(f"点击买入: {str_code}, {str_name}, {str_price}, {str_count}, {str_date_time}")
        self.demo_trading_manager.pending_order_buy(str_code, str_name, float(str_price), int(str_count), str_date_time)

        self.update_trading_widgets_status()

    def slot_btn_sell_clicked(self):
        if self.current_load_code == "":
            self.logger.info("请先加载股票数据")
            return
        str_price = self.lineEdit_price.text()
        str_count = self.lineEdit_count.text()

        current_index = self.horizontalSlider_progress.value()
        str_date_time = self.indicators_view_widget.get_current_date_time_by_index(current_index)

        self.logger.info(f"点击卖出: {str_price}, {str_count}, {str_date_time}")
        self.demo_trading_manager.pending_order_sell(float(str_price), int(str_count), str_date_time)

        self.update_trading_widgets_status()

    def slot_btn_pending_order_cancel_clicked(self):
        if self.current_load_code == "":
            self.logger.info("请先加载股票数据")
            return
        
        current_index = self.horizontalSlider_progress.value()
        str_date_time = self.indicators_view_widget.get_current_date_time_by_index(current_index)

        self.logger.info(f"点击取消挂单: {str_date_time}")
        self.demo_trading_manager.update_trading_record(0, None, None, str_date_time)

        self.update_trading_widgets_status()


