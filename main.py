import sys
from PyQt5.QtCore import QT_VERSION_STR, PYQT_VERSION_STR
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from gui.qt_widgets.main.main_widget import MainWidget
from resources import resources_rc

def main():
    # PyQt5
    app = QApplication(sys.argv)  # 创建应用程序对象[1,7]
    app.setWindowIcon(QIcon(":/app.svg"))
    # widget = QWidget()           # 创建窗口实例
    widget = MainWidget()
    widget.setWindowTitle("MPolicy")
    widget.show()                  # 显示窗口[1,7]
    sys.exit(app.exec_())          # 进入主事件循环[1,7]

if __name__ == "__main__":
    main()
