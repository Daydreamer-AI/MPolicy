import sys
from PyQt5.QtCore import QObject, QT_VERSION_STR, PYQT_VERSION_STR
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from gui.qt_widgets.main.main_widget import MainWidget
from resources import resources_rc

# qml
from PyQt5.QtQml import QQmlApplicationEngine
from gui.qml.main.main_bridge import MainBridge 

def main():
    # PyQt5
    app = QApplication(sys.argv)  # 创建应用程序对象
    app.setWindowIcon(QIcon(":/app.svg"))

    # qt widgets实现
    # widget = QWidget()           # 创建窗口实例
    widget = MainWidget()
    widget.setWindowTitle("MPolicy")
    widget.show()                  # 显示窗口

    # -----------------------------------------------------------------

    # qml实现
    # 创建QML引擎，用于加载和运行QML文件
    # engine = QQmlApplicationEngine()
    
    # 实例化我们的后端对象
    # main_bridge = MainBridge()
    
    # 获取引擎的根上下文，将后端对象暴露给QML
    # 设置上下文属性后，在QML中可以通过变量名 "main_bridge" 访问这个Python对象
    # engine.rootContext().setContextProperty("main_bridge", main_bridge)
    
    # 加载我们编写的QML文件
    # engine.load('./gui/qml/main/main.qml')
    
    # 检查QML文件是否加载成功
    # if not engine.rootObjects():
    #     print("错误：未能加载QML文件。")
    #     sys.exit(-1)
    
    # 获取QML文件的根对象（即ApplicationWindow）
    # root = engine.rootObjects()[0]
    
    # 连接QML中定义的信号到Python后端对象的槽函数
    # root.sendToPython.connect(main_bridge.receiveFromQML)
    
    # 演示：从Python端主动调用QML中的方法（这里设置Label的文本）
    # 首先找到QML中的Label对象，可以通过其id 'messageFromPython' 来查找
    # label_object = root.findChild(QObject, "messageFromPython")
    # if label_object:
    #     label_object.setProperty("text", "你好，这是Python设置的消息！")

    # -----------------------------------------------------------------

    sys.exit(app.exec_())          # 进入主事件循环[1,7]

if __name__ == "__main__":
    main()
