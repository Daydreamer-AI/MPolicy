from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout
from PyQt5.QtCore import pyqtSlot

from common.logging_manager import get_logger

from gui.qt_widgets.main.home_widget import HomeWidget
from gui.qt_widgets.board.board_home_widget import BoardHomeWidget
from gui.qt_widgets.market.market_widget import MarketWidget

class MainWidget(QWidget):
    def __init__(self):
        super().__init__()

        # 加载 UI 文件，第二个参数 self 表示将控件加载到当前窗口
        # 注意：PyQt5 在加载 .ui文件时，如果发现槽函数名称符合 on_对象名_信号名的格式，​​会自动连接​​信号和槽
        uic.loadUi('./gui/qt_widgets/main/MainWidget.ui', self)  # 确保路径正确

        self.init_para()
        self.init_ui()
        self.init_connect()


    def init_para(self):
        self.logger = get_logger(__name__)

    def init_ui(self):
        self.home_page = HomeWidget()
        self.market_page = MarketWidget()
        self.board_home_page = BoardHomeWidget()

        self.stackedWidget.addWidget(self.home_page)
        self.stackedWidget.addWidget(self.market_page)
        self.stackedWidget.addWidget(self.board_home_page)
        self.stackedWidget.setCurrentWidget(self.home_page)

    def init_connect(self):
        self.btn_home.clicked.connect(self.slot_btn_home_clicked)
        self.btn_market.clicked.connect(self.slot_btn_market_clicked)
        self.btn_board.clicked.connect(self.slot_btn_board_clicked)
        self.btn_setting.clicked.connect(self.slot_btn_setting_clicked)

    @pyqtSlot()
    def slot_btn_home_clicked(self):
        self.stackedWidget.setCurrentWidget(self.home_page)


    @pyqtSlot()
    def slot_btn_market_clicked(self):
        self.stackedWidget.setCurrentWidget(self.market_page)

    @pyqtSlot()
    def slot_btn_board_clicked(self):
        self.stackedWidget.setCurrentWidget(self.board_home_page)

    @pyqtSlot()
    def slot_btn_setting_clicked(self):
        # self.stackedWidget.setCurrentWidget(self.setting_page)
        self.logger.info("slot_btn_setting_clicked")
