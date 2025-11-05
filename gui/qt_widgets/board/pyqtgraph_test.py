import os
os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow
import numpy as np

class ChartWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQtGraph Chart")
        self.setGeometry(100, 100, 1000, 600)

        self.plot_widget = pg.PlotWidget()
        self.setCentralWidget(self.plot_widget)

        x = np.linspace(0, 10, 100)
        y1 = np.sin(x) * 10000
        y2 = np.cos(x) * 10 + 8
        y3 = np.random.randn(100) * 500

        self.plot_widget.plot(x, y1, pen='b', name='Line 1')
        self.plot_widget.plot(x, y2, pen='orange', name='Line 2')

        bars = pg.BarGraphItem(x=x, height=y3, width=0.1, brush='g')
        self.plot_widget.addItem(bars)

        text = pg.TextItem("103564.92", anchor=(0, 0), color='blue')
        text.setPos(x[50], y1[50] + 1000)
        self.plot_widget.addItem(text)

        # 关键：强制原点在左下角
        # self.plot_widget.setRange(xRange=(0, 10), yRange=(-10000, 10000))
        # self.plot_widget.showGrid(True, True, 0.5)

if __name__ == '__main__':
    app = QApplication([])
    window = ChartWindow()
    window.show()
    app.exec_()