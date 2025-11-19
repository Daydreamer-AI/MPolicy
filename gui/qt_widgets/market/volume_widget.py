from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout
from PyQt5.QtCore import pyqtSlot

class VolumeWidget(QWidget):
    def __init__(self, parent=None):
        super(VolumeWidget, self).__init__(parent)

        self.init_para()
        self.init_ui()
        self.init_connect()

    def init_ui(self):
        pass

    def init_para(self):
        pass

    def init_connect(self):
        pass
