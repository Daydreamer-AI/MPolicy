from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout
from PyQt5.QtCore import pyqtSlot

from common.logging_manager import get_logger
from processor.ak_stock_data_processor import AKStockDataProcessor
from gui.qt_widgets.MComponents.stock_card_widget import StockCardWidget

class IndustryBoardWidget(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('./gui/qt_widgets/board/IndustryBoardWidget.ui', self)

        self.init_para()
        self.init_ui()
        self.init_connect()

    def init_para(self):
        self.logger = get_logger(__name__)
        self.df_industry_board_data = AKStockDataProcessor().query_ths_board_industry_data()

    def init_ui(self):
        df_lastest_industry_data = AKStockDataProcessor().get_latest_ths_board_industry_data()
        self.logger.info(f"获取最新行业板块数据成功，数量: {len(df_lastest_industry_data)}")
        for row in df_lastest_industry_data.itertuples():
            # self.logger.info(row)

            # 创建 QListWidgetItem
            item = QtWidgets.QListWidgetItem()

            stock_card_widget = StockCardWidget()
            stock_card_widget.set_data(row)
            stock_card_widget.update_ui()

            stock_card_widget.clicked.connect(self.slot_stock_card_clicked)
            stock_card_widget.hovered.connect(self.slot_stock_card_hovered)
            stock_card_widget.hoverLeft.connect(self.slot_stock_card_hover_left)
            stock_card_widget.doubleClicked.connect(self.slot_stock_card_double_clicked)

            # 设置 item 的大小（可选）
            item.setSizeHint(stock_card_widget.sizeHint())
            
            # 将 item 添加到 list widget
            self.listWidget_card.addItem(item)
            
            # 将自定义 widget 设置为 item 的 widget
            self.listWidget_card.setItemWidget(item, stock_card_widget)

    def init_connect(self):
        pass

    @pyqtSlot()
    def slot_stock_card_clicked(self):
        self.logger.info("slot_stock_card_clicked")

    @pyqtSlot()
    def slot_stock_card_hovered(self):
        # self.logger.info("slot_stock_card_hovered")
        pass

    @pyqtSlot()
    def slot_stock_card_hover_left(self):
        # self.logger.info("slot_stock_card_hover_left")
        pass

    @pyqtSlot()
    def slot_stock_card_double_clicked(self):
        self.logger.info("slot_stock_card_double_clicked")
