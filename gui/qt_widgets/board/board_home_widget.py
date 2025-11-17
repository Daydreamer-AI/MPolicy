from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout
from PyQt5.QtCore import pyqtSlot

from gui.qt_widgets.board.board_overview_widget import BoardOverviewWidget
from gui.qt_widgets.board.industry_board_widget import IndustryBoardWidget
from gui.qt_widgets.board.concept_board_widget import ConceptBoardWidget


class BoardHomeWidget(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('./gui/qt_widgets/board/BoardHomeWidget.ui', self)

        self.init_para()
        self.init_ui()
        self.init_connect()

    def init_para(self):
        pass

    def init_ui(self):
        self.board_overview_widget = BoardOverviewWidget()
        self.industry_board_widget = IndustryBoardWidget()
        self.concept_board_widget = ConceptBoardWidget()

        self.stackedWidget.addWidget(self.board_overview_widget)
        self.stackedWidget.addWidget(self.industry_board_widget)
        self.stackedWidget.addWidget(self.concept_board_widget)
        self.stackedWidget.setCurrentWidget(self.board_overview_widget)

    def init_connect(self):
        self.btn_board_overview.clicked.connect(self.slot_btn_board_overview_clicked)
        self.btn_industry_board.clicked.connect(self.slot_btn_industry_board_clicked)
        self.btn_concept_board.clicked.connect(self.slot_btn_concept_board_clicked)

    @pyqtSlot()
    def slot_btn_board_overview_clicked(self):
        self.stackedWidget.setCurrentWidget(self.board_overview_widget)

    @pyqtSlot()
    def slot_btn_industry_board_clicked(self):
        self.stackedWidget.setCurrentWidget(self.industry_board_widget)

    @pyqtSlot()
    def slot_btn_concept_board_clicked(self):
        self.stackedWidget.setCurrentWidget(self.concept_board_widget)


