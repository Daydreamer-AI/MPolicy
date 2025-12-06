from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout
from PyQt5.QtCore import pyqtSlot, QFile

from gui.qt_widgets.board.board_overview_widget import BoardOverviewWidget
from gui.qt_widgets.board.industry_board_widget import IndustryBoardWidget
from gui.qt_widgets.board.concept_board_widget import ConceptBoardWidget


class BoardHomeWidget(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('./src/gui/qt_widgets/board/BoardHomeWidget.ui', self)

        self.init_para()
        self.init_ui()
        self.init_connect()

    def init_para(self):
        pass

    def init_ui(self):

        self.home_button_group = QtWidgets.QButtonGroup(self)
        self.home_button_group.addButton(self.btn_board_overview, 0)
        self.home_button_group.addButton(self.btn_industry_board, 1)
        self.home_button_group.addButton(self.btn_concept_board, 2)

        self.board_overview_widget = BoardOverviewWidget()
        self.industry_board_widget = IndustryBoardWidget()
        self.concept_board_widget = ConceptBoardWidget()

        self.stackedWidget.addWidget(self.board_overview_widget)
        self.stackedWidget.addWidget(self.industry_board_widget)
        self.stackedWidget.addWidget(self.concept_board_widget)
        self.stackedWidget.setCurrentWidget(self.board_overview_widget)

        self.load_qss()

    def init_connect(self):
        self.btn_board_overview.clicked.connect(self.slot_btn_board_overview_clicked)
        self.btn_industry_board.clicked.connect(self.slot_btn_industry_board_clicked)
        self.btn_concept_board.clicked.connect(self.slot_btn_concept_board_clicked)

    def load_qss(self, theme="default"):
        qss_file_name = f":/theme/{theme}/board/board.qss"
        qssFile = QFile(qss_file_name)
        if qssFile.open(QFile.ReadOnly):
            self.setStyleSheet(str(qssFile.readAll(), encoding='utf-8'))
        else:
            self.logger.warning("无法打开板块模块样式表文件")
        qssFile.close()

    @pyqtSlot()
    def slot_btn_board_overview_clicked(self):
        self.stackedWidget.setCurrentWidget(self.board_overview_widget)

    @pyqtSlot()
    def slot_btn_industry_board_clicked(self):
        self.stackedWidget.setCurrentWidget(self.industry_board_widget)

    @pyqtSlot()
    def slot_btn_concept_board_clicked(self):
        self.stackedWidget.setCurrentWidget(self.concept_board_widget)


