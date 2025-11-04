from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout
from PyQt5.QtCore import pyqtSlot

class ConceptBoardWidget(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('./gui/qt_widgets/board/ConceptBoardWidget.ui', self)

        self.init_para()
        self.init_ui()
        self.init_connect()

    def init_para(self):
        pass

    def init_ui(self):
        pass

    def init_connect(self):
        pass