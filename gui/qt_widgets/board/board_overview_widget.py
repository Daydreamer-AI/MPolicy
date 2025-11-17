from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout
from PyQt5.QtCore import pyqtSlot

from common.logging_manager import get_logger

from gui.qt_widgets.board.industry_board_overview_widget import IndustryBoardOverviewWidget

class BoardOverviewWidget(QWidget):
    def __init__(self):
        super(BoardOverviewWidget, self).__init__()
        self.logger = get_logger(__name__)
        
        self.init_para()
        self.init_ui()
        self.init_connect()

    def init_ui(self):
        uic.loadUi('gui/qt_widgets/board/BoardOverViewWidget.ui', self)

        self.industry_board_overview_widget = IndustryBoardOverviewWidget()
        # item = QtWidgets.QListWidgetItem()
        # item.setSizeHint(self.industry_board_overview_widget.sizeHint())
        # self.listWidget.addItem(item) 
        # self.listWidget.setItemWidget(item, self.industry_board_overview_widget)
        
        layout = self.layout()
        if layout is None:
            self.setLayout(QVBoxLayout())
        layout.addWidget(self.industry_board_overview_widget)

    def init_para(self):
        pass

    def init_connect(self):
        pass
