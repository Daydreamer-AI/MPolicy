from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout
from PyQt5.QtCore import pyqtSlot
from controller.processor_controller import processor_controller_instance

class MainWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        # 加载 UI 文件，第二个参数 self 表示将控件加载到当前窗口
        # 注意：PyQt5 在加载 .ui文件时，如果发现槽函数名称符合 on_对象名_信号名的格式，​​会自动连接​​信号和槽
        uic.loadUi('./gui/main/MainWidget.ui', self)  # 确保路径正确

        # 连接信号槽 (示例：假设UI文件中有一个名为 pushButton 的按钮)
        self.btn_get_all_stocks.clicked.connect(self.slot_btn_get_all_stocks_clicked)
        self.btn_query_gem.clicked.connect(self.slot_btn_query_gem_clicked)

    @pyqtSlot()
    def slot_btn_get_all_stocks_clicked(self):
        self.plainTextEdit_log.appendPlainText("slot_btn_get_all_stocks_clicked")
        processor_controller_instance.test()

    @pyqtSlot()
    def slot_btn_query_gem_clicked(self):
        processor_controller_instance.process_gem_stock_data()