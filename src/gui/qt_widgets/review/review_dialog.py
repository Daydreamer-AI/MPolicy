from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtWidgets import QDialog, QMessageBox
from PyQt5.QtCore import QDate

from manager.logging_manager import get_logger
# from gui.qt_widgets.MComponents.indicators.indicators_view_widget import IndicatorsViewWidget

from processor.baostock_processor import BaoStockProcessor
from manager.bao_stock_data_manager import BaostockDataManager
from manager.period_manager import TimePeriod

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

    def init_ui(self):
        from gui.qt_widgets.MComponents.indicators.indicators_view_widget import IndicatorsViewWidget
        self.indicators_view_widget = IndicatorsViewWidget(self)
        self.indicators_view_widget.setProperty("review", True)
        self.indicators_view_widget.show_review_btn(False)

        self.verticalLayout_indicators_view.addWidget(self.indicators_view_widget)

        self.btn_play.setProperty("is_play", False)

        self.comboBox_period.addItems([TimePeriod.get_chinese_label(TimePeriod.DAY), TimePeriod.get_chinese_label(TimePeriod.WEEK), TimePeriod.get_chinese_label(TimePeriod.MINUTE_15), TimePeriod.get_chinese_label(TimePeriod.MINUTE_30), TimePeriod.get_chinese_label(TimePeriod.MINUTE_60)])
        self.comboBox_period.setCurrentIndex(0)

    def init_connect(self):
        self.indicators_view_widget.sig_current_animation_index_changed.connect(self.slot_current_animation_index_changed)
        self.indicators_view_widget.sig_init_review_animation_finished.connect(self.slot_init_review_animation_finished)

        self.lineEdit_code.editingFinished.connect(self.slot_lineEdit_code_editingFinished)
        self.dateEdit.dateChanged.connect(self.slot_dateEdit_dateChanged)
        self.comboBox_period.currentIndexChanged.connect(self.slot_comboBox_period_currentIndexChanged)
        self.btn_load_data.clicked.connect(self.slot_btn_load_data_clicked)

        self.btn_play.clicked.connect(self.slot_btn_play_clicked)

        self.btn_back_to_front.clicked.connect(self.slot_btn_back_to_front_clicked)
        self.btn_back_ten.clicked.connect(self.slot_btn_back_ten_clicked)
        self.btn_back.clicked.connect(self.slot_btn_back_clicked)
        self.btn_move_on.clicked.connect(self.slot_btn_move_on_clicked)
        self.btn_move_on_10.clicked.connect(self.slot_btn_move_on_10_clicked)
        self.btn_move_to_last.clicked.connect(self.slot_btn_move_to_last_clicked)

        self.horizontalSlider_progress.valueChanged.connect(self.slot_horizontalSlider_progress_valueChanged)

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


    def update_progress_label(self, current_index):
        if self.dict_progress_data is not None and self.dict_progress_data != {}:
            s_current_progress = f"{current_index}/{self.dict_progress_data['max_index']}"
            self.label_progress.setText(s_current_progress)
        else:
            self.logger.info("进度数据为空")
            self.label_progress.setText("")

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
        else:
            self.logger.info(f"结果为空")

    # -----------------槽函数----------------
    def slot_current_animation_index_changed(self, index):
        # self.logger.info(f"收到k线图进度: {index}")

        self.horizontalSlider_progress.blockSignals(True)
        self.horizontalSlider_progress.setSliderPosition(index)
        self.horizontalSlider_progress.blockSignals(False)

        self.update_progress_label(index)

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

                start_date = self.dict_progress_data['start_date']
                self.logger.info(f"实际开始日期--start_date: {start_date}")

                self.dateEdit.blockSignals(True)
                self.dateEdit.setDate(QDate.fromString(start_date, "yyyy-MM-dd"))
                self.dateEdit.blockSignals(False)

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

    def slot_btn_load_data_clicked(self):
        code = self.lineEdit_code.text()
        date = self.dateEdit.date().toString("yyyy-MM-dd")
        period = self.comboBox_period.currentText()
        self.logger.info(f"点击加载数据: {code}, {date}, {period}")

        if self.current_load_code == code:
            self.logger.info("当前股票数据已加载，无需重复加载")
            return
        
        self.load_data(code, date)

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
        


