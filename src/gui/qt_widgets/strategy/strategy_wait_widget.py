from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtWidgets import QWidget

class StrategyWaitWidget(QWidget):
    def __init__(self, parent = None):
        super(StrategyWaitWidget, self).__init__(parent)

        uic.loadUi("./src/gui/qt_widgets/strategy/StrategyWaitWidget.ui", self)

        self.init_para()
        self.init_ui()
        self.init_connect()
        

    def init_para(self):
        pass

    def init_ui(self):
        pass

    def init_connect(self):
        pass

