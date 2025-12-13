from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtWidgets import QDialog, QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import pyqtSlot

from manager.logging_manager import get_logger
# from gui.qt_widgets.MComponents.indicators.indicators_view_widget import IndicatorsViewWidget

from processor.baostock_processor import BaoStockProcessor
from manager.bao_stock_data_manager import BaostockDataManager

class ReviewDialog(QDialog):
    def __init__(self, parent=None):
        super(ReviewDialog, self).__init__(parent) 
        uic.loadUi('./src/gui/qt_widgets/review/ReviewDialog.ui', self)

        self.init_para()
        self.init_ui()
        self.init_connect()

        self.load_data_test()

    def init_para(self):
        self.logger = get_logger(__name__)
        self.dict_progress_data = {}

    def init_ui(self):
        from gui.qt_widgets.MComponents.indicators.indicators_view_widget import IndicatorsViewWidget
        self.indicators_view_widget = IndicatorsViewWidget(self)
        self.indicators_view_widget.setProperty("review", True)
        self.indicators_view_widget.show_review_btn(False)

        self.verticalLayout_indicators_view.addWidget(self.indicators_view_widget)

        self.btn_play.setProperty("is_play", False)

    def init_connect(self):
        self.indicators_view_widget.sig_current_animation_index_changed.connect(self.slot_current_animation_index_changed)
        self.indicators_view_widget.sig_min_and_max_animation_index_changed.connect(self.slot_min_and_max_animation_index_changed)

        self.btn_play.clicked.connect(self.slot_btn_play_clicked)

        self.btn_back_to_front.clicked.connect(self.slot_btn_back_to_front_clicked)
        self.btn_back_ten.clicked.connect(self.slot_btn_back_ten_clicked)
        self.btn_back.clicked.connect(self.slot_btn_back_clicked)
        self.btn_move_on.clicked.connect(self.slot_btn_move_on_clicked)
        self.btn_move_on_10.clicked.connect(self.slot_btn_move_on_10_clicked)
        self.btn_move_to_last.clicked.connect(self.slot_btn_move_to_last_clicked)

        self.horizontalSlider_progress.valueChanged.connect(self.slot_horizontalSlider_progress_valueChanged)

    def update_progress_label(self, current_index):
        if self.dict_progress_data is not None and self.dict_progress_data != {}:
            s_current_progress = f"{current_index}/{self.dict_progress_data['max_index']}"
            self.label_progress.setText(s_current_progress)
        else:
            self.logger.info("进度数据为空")
            self.label_progress.setText("")

    def load_data_test(self):
        filter_result = ['sh.600000']
        bao_stock_data_manager = BaostockDataManager()
        new_dict_lastest_1d_stock_data = bao_stock_data_manager.get_lastest_row_data_dict_by_code_list_auto(filter_result)
        self.logger.info(f"new_dict_lastest_1d_stock_data: {new_dict_lastest_1d_stock_data}")

        if new_dict_lastest_1d_stock_data:
            self.indicators_view_widget.update_stock_data_dict('sh.600000')
            data = new_dict_lastest_1d_stock_data['sh.600000'].iloc[-1]
            # self.indicators_view_widget.update_chart(data, '2025-12-08')
            self.dict_progress_data = self.indicators_view_widget.init_animation(data, "2025-12-01")
            if self.dict_progress_data is not None and self.dict_progress_data != {}:
                self.horizontalSlider_progress.setMinimum(self.dict_progress_data['min_index'])
                self.horizontalSlider_progress.setMaximum(self.dict_progress_data['max_index'])

                self.horizontalSlider_progress.blockSignals(True)
                self.horizontalSlider_progress.setSliderPosition(self.dict_progress_data['start_date_index'])
                self.horizontalSlider_progress.blockSignals(False)

                self.update_progress_label(self.dict_progress_data['start_date_index'])
            else:
                self.logger.info(f"初始化返回的进度数据为空")
        else:
            self.logger.info(f"结果为空")

    # -----------------槽函数----------------
    def slot_current_animation_index_changed(self, index):
        self.logger.info(f"收到k线图进度: {index}")

        self.horizontalSlider_progress.blockSignals(True)
        self.horizontalSlider_progress.setSliderPosition(index)
        self.horizontalSlider_progress.blockSignals(False)

        self.update_progress_label(index)

    def slot_min_and_max_animation_index_changed(self, min_index, max_index):
        pass

    def slot_btn_play_clicked(self):
        if self.btn_play.property("is_play"):
            self.logger.info("暂停播放")
            self.indicators_view_widget.pause_animation()
            self.btn_play.setProperty("is_play", False)
            # self.btn_play.setIcon(QtGui.QIcon("./src/gui/qt_widgets/images/pause.png"))
        else:
            self.logger.info("开始播放")
            self.indicators_view_widget.start_animation()
            self.btn_play.setProperty("is_play", True)

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
        


