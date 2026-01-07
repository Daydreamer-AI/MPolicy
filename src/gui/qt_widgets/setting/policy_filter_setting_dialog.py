import sys
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QDialog, QPushButton, QLabel, QLineEdit, QVBoxLayout
from PyQt5.QtQuickWidgets import QQuickWidget
from PyQt5.QtCore import QUrl, QObject, pyqtSignal, pyqtSlot
from gui.qml.setting.policy_filter_setting_bridge import PolicyFilterSettingBridge
from processor.baostock_processor import BaoStockProcessor
from manager.config_manager import ConfigManager
from manager.logging_manager import get_logger

class PolicyFilterSettingDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi('./src/gui/qt_widgets/setting/policy_filter_setting_dialog.ui', self)

        self.logger = get_logger(__name__)

        # qt_widget控件初始化
        self.ui_init()

        # 初始化qml控件
        self.qml_init()

        self.connect_init()

    def ui_init(self):
        policy_filter_turn_config = BaoStockProcessor().get_policy_filter_turn()
        policy_filter_lb_config = BaoStockProcessor().get_policy_filter_lb()
        b_weekly_condition = BaoStockProcessor().get_weekly_condition()
        s_filter_date = BaoStockProcessor().get_filter_date()
        s_target_code = BaoStockProcessor().get_target_code()

        b_less_than_ma5 = BaoStockProcessor().get_b_less_than_ma5()
        b_filter_log = BaoStockProcessor().get_b_filter_log()


        self.logger.info(f"Config from config.ini: {policy_filter_turn_config}, {policy_filter_lb_config}, {b_weekly_condition}, {s_filter_date}, {s_target_code}, {b_less_than_ma5}, {b_filter_log}")

        self.lineEdit_turn.setText(str(policy_filter_turn_config))
        self.lineEdit_lb.setText(str(policy_filter_lb_config))
        self.checkBox_weekly_condition.setChecked(b_weekly_condition)
        self.lineEdit_filter_date.setText(s_filter_date)
        self.lineEdit_target_code.setText(s_target_code)
        self.checkBox_less_than_ma5.setChecked(b_less_than_ma5)
        self.checkBox_log.setChecked(b_filter_log)

        self.label_filter_date.hide()
        self.lineEdit_filter_date.hide()

    def connect_init(self):
        self.btn_cancel.clicked.connect(self.solt_btn_cancel_clicked)
        self.btn_ok.clicked.connect(self.solt_btn_ok_clicked)

    def qml_init(self):
        self.quickWidget.setSource(QUrl.fromLocalFile("./src/gui/qml/setting/policy_filter_setting.qml")) # 加载QML文件

        # 检查QML是否加载成功
        if self.quickWidget.status() == QQuickWidget.Error:
            self.logger.info("Error loading QML file!")
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
        self.logger.info("solt_cancel_clicked!")
        if self.qml_root:
            # 通过设置QML根对象的属性来更新QML界面
            self.qml_root.setMessage("Message from Qt Widgets Button!")

    def solt_btn_ok_clicked(self):
        turn_str = self.lineEdit_turn.text()
        lb_str = self.lineEdit_lb.text()
        b_weekly_condition = self.checkBox_weekly_condition.isChecked()
        s_filter_date = self.lineEdit_filter_date.text()
        s_target_code = self.lineEdit_target_code.text()

        b_less_than_ma5 = self.checkBox_less_than_ma5.isChecked()
        b_filter_log = self.checkBox_log.isChecked()


        self.logger.info(f"策略筛选配置--换手率：{float(turn_str)}")
        self.logger.info(f"策略筛选配置--量比：{float(lb_str)}")
        self.logger.info(f"策略筛选配置--启用周线筛选条件：{b_weekly_condition}")
        self.logger.info("策略筛选配置--指定筛选日期：{s_filter_date}")
        self.logger.info("策略筛选配置--指定股票代码：{s_target_code}")

        self.logger.info(f"策略筛选配置--启用筛选价格小于MA5：{b_less_than_ma5}")
        self.logger.info(f"策略筛选配置--启用筛选日志：{b_filter_log}")


        BaoStockProcessor().set_policy_filter_turn(float(turn_str))
        BaoStockProcessor().set_policy_filter_lb(float(lb_str))
        BaoStockProcessor().set_weekly_condition(b_weekly_condition)
        BaoStockProcessor().set_filter_date(s_filter_date)
        BaoStockProcessor().set_target_code(s_target_code)

        BaoStockProcessor().set_b_less_than_ma5(b_less_than_ma5)
        BaoStockProcessor().set_b_filter_log(b_filter_log)


        config_manager = ConfigManager()
        config_manager.set_config_path("config.ini")
        config_manager.set('PolicyFilter', 'turn', turn_str)
        config_manager.set('PolicyFilter', 'lb', lb_str)
        config_manager.set('PolicyFilter', 'weekly_condition', '1' if b_weekly_condition else '0')
        config_manager.set('PolicyFilter', 'filter_date', s_filter_date)
        config_manager.set('PolicyFilter', 'target_code', s_target_code)

        config_manager.set('PolicyFilter', 'less_than_ma5', '1' if b_less_than_ma5 else '0')
        config_manager.set('PolicyFilter', 'filter_log', '1' if b_filter_log else '0')

        config_manager.save()
        
        self.accept()