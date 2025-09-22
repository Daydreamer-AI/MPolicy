from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout
from PyQt5.QtCore import pyqtSlot
# from controller.processor_controller import processor_controller_instance
from gui.qt_widgets.setting.policy_filter_setting_dialog import PolicyFilterSettingDialog
from processor.baostock_processor import BaoStockProcessor
from processor.ak_stock_data_processor import AKStockDataProcessor
from common.common_api import *
import datetime

class MainWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        # 加载 UI 文件，第二个参数 self 表示将控件加载到当前窗口
        # 注意：PyQt5 在加载 .ui文件时，如果发现槽函数名称符合 on_对象名_信号名的格式，​​会自动连接​​信号和槽
        uic.loadUi('./gui/qt_widgets/main/MainWidget.ui', self)  # 确保路径正确

        # 连接信号槽 (示例：假设UI文件中有一个名为 pushButton 的按钮)
        # Baostock
        self.btn_get_all_stocks.clicked.connect(self.slot_btn_get_all_stocks_clicked)
        self.btn_query_sh_main.clicked.connect(self.slot_btn_query_sh_main_clicked)
        self.btn_query_sz_main.clicked.connect(self.slot_btn_query_sz_main_clicked)
        self.btn_query_gem.clicked.connect(self.slot_btn_query_gem_clicked)
        self.btn_query_star.clicked.connect(self.slot_btn_query_star_clicked)

        # AKShare
        self.btn_get_akshare_stocks_info.clicked.connect(self.slot_btn_get_akshare_stocks_info_clicked)
        self.btn_update_ths_board_industry_data.clicked.connect(self.slot_btn_update_ths_board_industry_data_clicked)
        self.btn_update_sh_main_data.clicked.connect(self.slot_btn_update_sh_main_data_clicked)
        self.btn_update_sz_main_data.clicked.connect(self.slot_btn_update_sz_main_data_clicked)
        self.btn_update_gem_data.clicked.connect(self.slot_btn_update_gem_data_clicked)

        # 策略筛选
        self.btn_daily_up_ma52_filter.clicked.connect(self.slot_btn_daily_up_ma52_filter_clicked)
        self.btn_daily_up_ma24_filter.clicked.connect(self.slot_btn_daily_up_ma24_filter_clicked)
        self.btn_daily_up_ma10_filter.clicked.connect(self.slot_btn_daily_up_ma10_filter_clicked)
        self.btn_daily_down_ma52_filter.clicked.connect(self.slot_btn_daily_down_ma52_filter_clicked)
        self.btn_daily_down_ma5_filter.clicked.connect(self.slot_btn_daily_down_ma5_filter_clicked)

        self.btn_stop.clicked.connect(self.slot_btn_stop_clicked)

        self.btn_policy_filter_setting.clicked.connect(self.slot_btn_policy_filter_setting_clicked)
        self.init_processors()
    
    def init_processors(self):
        """初始化所有处理器（如Baostock）"""
        try:
            ak_success = AKStockDataProcessor().initialize()
            success = BaoStockProcessor().initialize()
            if ak_success and success:
                print("所有处理器初始化成功")
            else:
                print("处理器初始化失败")
                # 可以进行一些UI提示，例如设置label的文本为红色警告
                quit()
        except Exception as e:
            print(f"初始化过程中发生错误: {e}")

    def closeEvent(self, event):
        """
        重写 closeEvent，当窗口请求关闭时调用。
        这是执行清理操作的理想位置。
        """
        print("开始执行清理操作...")
        try:
            BaoStockProcessor().cleanup() # 清理所有处理器
        except Exception as e:
            print(f"清理过程中发生错误: {e}")
        finally:
            # 确保事件继续传递，允许窗口关闭
            event.accept()
            print("清理完成，窗口关闭。")

    # 槽函数
    # Baostock
    @pyqtSlot()
    def slot_btn_get_all_stocks_clicked(self):
        self.plainTextEdit_log.appendPlainText("slot_btn_get_all_stocks_clicked")
        BaoStockProcessor().get_and_save_all_stocks_from_bao()
        BaoStockProcessor().get_all_stocks_from_db()

    @pyqtSlot()
    def slot_btn_query_sh_main_clicked(self):
        self.plainTextEdit_log.appendPlainText("slot_btn_query_sh_main_clicked...")
        BaoStockProcessor().process_sh_main_stock_daily_data()
        BaoStockProcessor().process_sh_main_stock_weekly_data()
        print("done")

    @pyqtSlot()
    def slot_btn_query_sz_main_clicked(self):
        self.plainTextEdit_log.appendPlainText("slot_btn_query_sz_main_clicked...")
        BaoStockProcessor().process_sz_main_stock_daily_data()
        BaoStockProcessor().process_sz_main_stock_weekly_data()
        print("done")

    @pyqtSlot()
    def slot_btn_query_gem_clicked(self):
        self.plainTextEdit_log.appendPlainText("slot_btn_query_gem_clicked...")
        BaoStockProcessor().process_gem_stock_daily_data()
        BaoStockProcessor().process_gem_stock_weekly_data()
        print("done")

    @pyqtSlot()
    def slot_btn_query_star_clicked(self):
        self.plainTextEdit_log.appendPlainText("slot_btn_query_star_clicked...")
        BaoStockProcessor().process_star_stock_daily_data()
        BaoStockProcessor().process_star_stock_weekly_data()
        print("done")

    # AKShare
    @pyqtSlot()
    def slot_btn_get_akshare_stocks_info_clicked(self):
        self.plainTextEdit_log.appendPlainText("slot_btn_get_akshare_stocks_info_clicked...")
        AKStockDataProcessor().get_stocks_info_and_save_to_db()
    @pyqtSlot()
    def slot_btn_update_ths_board_industry_data_clicked(self):
        self.plainTextEdit_log.appendPlainText("slot_btn_update_ths_board_industry_data_clicked...")
        AKStockDataProcessor().process_and_save_board_industry_ths()

    @pyqtSlot()
    def slot_btn_update_sh_main_data_clicked(self):
        self.plainTextEdit_log.appendPlainText("slot_btn_update_sh_main_data_clicked...")
        result = AKStockDataProcessor().query_board_industry_data()
        print("slot_btn_update_sh_main_data_clicked done.")
        print(result)

    @pyqtSlot()
    def slot_btn_update_sz_main_data_clicked(self):
        self.plainTextEdit_log.appendPlainText("slot_btn_update_sz_main_data_clicked...")
        result = AKStockDataProcessor().get_latest_board_industry_data()
        print("slot_btn_update_sz_main_data_clicked done.")
        print(result)

    @pyqtSlot()
    def slot_btn_update_gem_data_clicked(self):
        self.plainTextEdit_log.appendPlainText("slot_btn_update_gem_data_clicked...")
        AKStockDataProcessor().process_and_save_stock_fund_flow_industry()
        print("slot_btn_update_gem_data_clicked done.")

    # 策略筛选
    @pyqtSlot()
    def slot_btn_daily_up_ma52_filter_clicked(self):
        self.plainTextEdit_log.appendPlainText("slot_btn_daily_up_ma52_filter_clicked...")
        result = BaoStockProcessor().daily_up_ma52_filter()
        today_str = datetime.datetime.now().strftime('%m%d')
        save_list_to_txt(result, f"./policy_filter/filter_result/daily_up_ma52/{today_str}.txt", ', ', "零轴上方MA52筛选结果：\n")
        print("daily_up_ma52_filter done.")
        print(result)

    @pyqtSlot()
    def slot_btn_daily_up_ma24_filter_clicked(self):
        self.plainTextEdit_log.appendPlainText("slot_btn_daily_up_ma24_filter_clicked...")
        result = BaoStockProcessor().daily_up_ma24_filter()
        today_str = datetime.datetime.now().strftime('%m%d')
        save_list_to_txt(result, f"./policy_filter/filter_result/daily_up_ma24/{today_str}.txt", ', ', "零轴上方MA24筛选结果：\n")
        print("daily_up_ma24_filter done.")
        print(result)

    @pyqtSlot()
    def slot_btn_daily_up_ma10_filter_clicked(self):
        self.plainTextEdit_log.appendPlainText("slot_btn_daily_up_ma10_filter_clicked...")
        result = BaoStockProcessor().daily_up_ma10_filter()
        today_str = datetime.datetime.now().strftime('%m%d')
        save_list_to_txt(result, f"./policy_filter/filter_result/daily_up_ma10/{today_str}.txt", ', ', "零轴上方MA10筛选结果：\n")
        print("daily_up_ma10_filter done.")
        print(result)

    @pyqtSlot()
    def slot_btn_daily_down_ma52_filter_clicked(self):
        self.plainTextEdit_log.appendPlainText("slot_btn_daily_down_ma52_filter_clicked...")
        result = BaoStockProcessor().daily_down_between_ma24_ma52_filter()
        today_str = datetime.datetime.now().strftime('%m%d')
        save_list_to_txt(result, f"./policy_filter/filter_result/daily_down_ma52/{today_str}.txt", ', ', "零轴下方MA52筛选结果：\n")
        print("daily_down_between_ma24_ma52_filter done.")
        print(result)

    @pyqtSlot()
    def slot_btn_daily_down_ma5_filter_clicked(self):
        self.plainTextEdit_log.appendPlainText("slot_btn_daily_down_ma5_filter_clicked...")
        result = BaoStockProcessor().daily_down_between_ma5_ma52_filter()
        today_str = datetime.datetime.now().strftime('%m%d')
        save_list_to_txt(result, f"./policy_filter/filter_result/daily_down_ma5/{today_str}.txt", ', ', "零轴下方MA5筛选结果：\n")
        print("daily_down_between_ma5_ma52_filter done.")
        print(result)

    @pyqtSlot()
    def slot_btn_stop_clicked(self):
        self.plainTextEdit_log.appendPlainText("slot_btn_stop_clicked...")
        BaoStockProcessor().stop_process()

    @pyqtSlot()
    def slot_btn_policy_filter_setting_clicked(self):
        dlg = PolicyFilterSettingDialog()
        dlg.exec()