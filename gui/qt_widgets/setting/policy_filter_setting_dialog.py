import sys
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QDialog, QPushButton, QLabel, QLineEdit, QVBoxLayout
from PyQt5.QtQuickWidgets import QQuickWidget
from PyQt5.QtCore import QUrl, QObject, pyqtSignal, pyqtSlot
from gui.qml.setting.policy_filter_setting_bridge import PolicyFilterSettingBridge
from processor.baostock_processor import BaoStockProcessor
from common.config_manager import ConfigManager

class PolicyFilterSettingDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi('./gui/qt_widgets/setting/policy_filter_setting_dialog.ui', self)

        # qt_widget控件初始化
        self.ui_init()

        # 初始化qml控件
        self.qml_init()

        self.connect_init()

    def ui_init(self):
        policy_filter_turn_config = BaoStockProcessor().get_policy_filter_turn()
        policy_filter_lb_config = BaoStockProcessor().get_policy_filter_lb()
        self.lineEdit_turn.setText(str(policy_filter_turn_config))
        self.lineEdit_lb.setText(str(policy_filter_lb_config))

    def connect_init(self):
        self.btn_cancel.clicked.connect(self.solt_btn_cancel_clicked)
        self.btn_ok.clicked.connect(self.solt_btn_ok_clicked)

    def qml_init(self):
        self.quickWidget.setSource(QUrl.fromLocalFile("./gui/qml/setting/policy_filter_setting.qml")) # 加载QML文件

        # 检查QML是否加载成功
        if self.quickWidget.status() == QQuickWidget.Error:
            print("Error loading QML file!")
            sys.exit(-1)

        self.policy_filter_setting_bridge = PolicyFilterSettingBridge()
        # 将Python对象暴露给QML的根上下文，在QML中通过别名 "policyFilterSettingBridge" 访问
        self.quickWidget.rootContext().setContextProperty("policyFilterSettingBridge", self.policy_filter_setting_bridge)

        # 连接信号：当Python发送消息时，更新QML中的文本显示
        # 首先获取QML根对象的引用
        self.qml_root = self.quickWidget.rootObject()
        if self.qml_root:
            self.policy_filter_setting_bridge.messageToQml.connect(self.qml_root.setMessage)

    @pyqtSlot()
    def solt_btn_cancel_clicked(self):
        print("solt_cancel_clicked!")
        if self.qml_root:
            # 通过设置QML根对象的属性来更新QML界面
            self.qml_root.setMessage("Message from Qt Widgets Button!")

    def solt_btn_ok_clicked(self):
        turn_str = self.lineEdit_turn.text()
        lb_str = self.lineEdit_lb.text()
        print("策略筛选配置--换手率：", float(turn_str))
        print("策略筛选配置--量比：", float(lb_str))
        BaoStockProcessor().set_policy_filter_turn(float(turn_str))
        BaoStockProcessor().set_policy_filter_lb(float(lb_str))
        config_manager = ConfigManager()
        config_manager.set_config_path("./resources/config/config.ini")
        config_manager.set('PolicyFilter', 'turn', turn_str)
        config_manager.set('PolicyFilter', 'lb', lb_str)
        config_manager.save()
        
        self.accept()