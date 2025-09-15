from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout
from PyQt5.QtCore import pyqtSlot
from controller.processor_controller import processor_controller_instance
from gui.qt_widgets.setting.policy_filter_setting_dialog import PolicyFilterSettingDialog

class MainWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        # 加载 UI 文件，第二个参数 self 表示将控件加载到当前窗口
        # 注意：PyQt5 在加载 .ui文件时，如果发现槽函数名称符合 on_对象名_信号名的格式，​​会自动连接​​信号和槽
        uic.loadUi('./gui/qt_widgets/main/MainWidget.ui', self)  # 确保路径正确

        # 连接信号槽 (示例：假设UI文件中有一个名为 pushButton 的按钮)
        # 全量获取
        self.btn_get_all_stocks.clicked.connect(self.slot_btn_get_all_stocks_clicked)
        self.btn_query_sh_main.clicked.connect(self.slot_btn_query_sh_main_clicked)
        self.btn_query_sz_main.clicked.connect(self.slot_btn_query_sz_main_clicked)
        self.btn_query_gem.clicked.connect(self.slot_btn_query_gem_clicked)
        self.btn_query_star.clicked.connect(self.slot_btn_query_star_clicked)

        # 增量更新
        self.btn_update_sh_main_data.clicked.connect(self.slot_btn_update_sh_main_data_clicked)

        # 策略筛选
        self.btn_daily_up_ma52_filter.clicked.connect(self.slot_btn_daily_up_ma52_filter_clicked)
        self.btn_daily_up_ma24_filter.clicked.connect(self.slot_btn_daily_up_ma24_filter_clicked)
        self.btn_daily_up_ma10_filter.clicked.connect(self.slot_btn_daily_up_ma10_filter_clicked)
        self.btn_daily_down_ma52_filter.clicked.connect(self.slot_btn_daily_down_ma52_filter_clicked)
        self.btn_daily_down_ma5_filter.clicked.connect(self.slot_btn_daily_down_ma5_filter_clicked)

        self.btn_stop.clicked.connect(self.slot_btn_stop_clicked)

        self.btn_policy_filter_setting.clicked.connect(self.slot_btn_policy_filter_setting_clicked)

    # 槽函数
    # 全量获取
    @pyqtSlot()
    def slot_btn_get_all_stocks_clicked(self):
        self.plainTextEdit_log.appendPlainText("slot_btn_get_all_stocks_clicked")
        processor_controller_instance.test()

    @pyqtSlot()
    def slot_btn_query_sh_main_clicked(self):
        self.plainTextEdit_log.appendPlainText("slot_btn_query_sh_main_clicked...")
        processor_controller_instance.process_sh_main_stock_data()

    @pyqtSlot()
    def slot_btn_query_sz_main_clicked(self):
        self.plainTextEdit_log.appendPlainText("slot_btn_query_sz_main_clicked...")
        processor_controller_instance.process_sz_main_stock_data()

    @pyqtSlot()
    def slot_btn_query_gem_clicked(self):
        self.plainTextEdit_log.appendPlainText("slot_btn_query_gem_clicked...")
        processor_controller_instance.process_gem_stock_data()

    @pyqtSlot()
    def slot_btn_query_star_clicked(self):
        self.plainTextEdit_log.appendPlainText("slot_btn_query_star_clicked...")
        processor_controller_instance.process_star_stock_data()

    # 增量更新
    @pyqtSlot()
    def slot_btn_update_sh_main_data_clicked(self):
        self.plainTextEdit_log.appendPlainText("slot_btn_update_sh_main_data_clicked...")
        processor_controller_instance.update_sh_main_daily_data()

    # 策略筛选
    @pyqtSlot()
    def slot_btn_daily_up_ma52_filter_clicked(self):
        self.plainTextEdit_log.appendPlainText("slot_btn_daily_up_ma52_filter_clicked...")
        processor_controller_instance.process_daily_up_ma52_filter()

    @pyqtSlot()
    def slot_btn_daily_up_ma24_filter_clicked(self):
        self.plainTextEdit_log.appendPlainText("slot_btn_daily_up_ma24_filter_clicked...")
        processor_controller_instance.process_daily_up_ma24_filter()

    @pyqtSlot()
    def slot_btn_daily_up_ma10_filter_clicked(self):
        self.plainTextEdit_log.appendPlainText("slot_btn_daily_up_ma10_filter_clicked...")
        processor_controller_instance.process_daily_up_ma10_filter()

    @pyqtSlot()
    def slot_btn_daily_down_ma52_filter_clicked(self):
        self.plainTextEdit_log.appendPlainText("slot_btn_daily_down_ma52_filter_clicked...")
        processor_controller_instance.process_daily_down_between_ma24_ma52_filter()

    @pyqtSlot()
    def slot_btn_daily_down_ma5_filter_clicked(self):
        self.plainTextEdit_log.appendPlainText("slot_btn_daily_down_ma5_filter_clicked...")
        processor_controller_instance.process_daily_down_between_ma5_ma52_filter()

    @pyqtSlot()
    def slot_btn_stop_clicked(self):
        self.plainTextEdit_log.appendPlainText("slot_btn_stop_clicked...")
        processor_controller_instance.stop_process()

    @pyqtSlot()
    def slot_btn_policy_filter_setting_clicked(self):
        dlg = PolicyFilterSettingDialog()
        dlg.exec()