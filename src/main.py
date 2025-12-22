import sys
import os
from PyQt5.QtCore import QFile, QCoreApplication, Qt
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

from resources import resources_rc

from gui.qt_widgets.main.main_widget import MainWidget
from manager.logging_manager import get_logger, setup_logging

# qml
from PyQt5.QtQml import QQmlApplicationEngine
from gui.qml.main.main_bridge import MainBridge 


# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    
# 确保能导入自定义组件
components_path = os.path.join(project_root, 'gui', 'qt_widgets', 'MComponents')
if components_path not in sys.path:
    sys.path.insert(0, components_path)

# os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'

def main():
    # 设置进程标识环境变量
    os.environ['MPOLICY_PROCESS'] = 'main'
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    # 初始化日志系统
    # 初始化日志系统
    setup_logging(
        log_dir="./data/logs",
        level="INFO",
        enable_file_log=True,
        max_bytes=10 * 1024 * 1024,
        backup_count=5,
        unique_log_file=True  # 启用唯一日志文件名
    )
    
    logger = get_logger(__name__)
    logger.info("应用程序启动")

    # PyQt5
    app = QApplication(sys.argv)  # 创建应用程序对象
    app.setWindowIcon(QIcon(":/app.svg"))

    qssFile = QFile(":/theme/default/main.qss")
    if qssFile.open(QFile.ReadOnly):
        # 使用 data() 方法获取字节数据并解码
        app.setStyleSheet(str(qssFile.readAll(), encoding='utf-8'))
        qssFile.close()
    else:
        logger.warning("无法打开整体样式表文件")
        qssFile.close()

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
    ret = -1
    try:
        ret = app.exec_()
        logger.info("应用程序正常退出")
        
    except Exception as e:
        logger.error(f"应用程序异常退出: {e}")

    # sys.exit(app.exec_())          # 进入主事件循环[1,7]
    # logger.info("应用程序正常退出")
    sys.exit(ret)

if __name__ == "__main__":
    main()
