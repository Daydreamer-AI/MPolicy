from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal, Qt

import os
from pathlib import Path
import pandas as pd

class StockCardWidget(QWidget):

    # 定义自定义信号
    clicked = pyqtSignal(object)  # 点击信号
    hovered = pyqtSignal()  # 悬浮进入信号
    hoverLeft = pyqtSignal()  # 悬浮离开信号
    doubleClicked = pyqtSignal()  # 双击信号

    def __init__(self, type=0):
        super().__init__()
        # uic.loadUi('.gui/qt_widgets/MComponents/StockCardWidget.ui', self)
        # 使用 pathlib 确保跨平台兼容性
        ui_file = Path(__file__).parent / "StockCardWidget.ui"
        
        # 检查文件是否存在
        if not ui_file.exists():
            raise FileNotFoundError(
                f"找不到UI文件: {ui_file.absolute()}\n"
                f"当前工作目录: {Path.cwd()}"
            )
        
        uic.loadUi(str(ui_file), self)

        self.board_type = type  # 0: 行业板块，1: 概念板块
        
        self.init_para()
        self.init_ui()
        self.init_connect()

    def init_para(self):
        self._is_hovered = False  # 跟踪悬浮状态

    def init_ui(self):
        # 启用鼠标跟踪以检测悬浮事件
        self.setMouseTracking(True)
        # 设置焦点策略以便接收键盘事件（可选）
        self.setFocusPolicy(Qt.StrongFocus)

        self.label_stock_code.hide()

    def init_connect(self):
        pass

    def update_ui(self):
        if self.data:
            if self.board_type == 0:
                self.label_stock_name.setText(self.data.industry_name)
                # 设置均价，保留2位小数
                avg_price = getattr(self.data, 'avg_price', None)
                if avg_price is not None and not (isinstance(avg_price, float) and pd.isna(avg_price)):
                    self.label_price.setText(f"{float(avg_price):.2f}")
                else:
                    self.label_price.setText("N/A")
            else:
                self.label_stock_name.setText(self.data.concept_name)
                self.label_price.hide()

            
            
            # 设置涨跌幅，保留2位小数并添加百分号
            change_percent = getattr(self.data, 'change_percent', None)
            if change_percent is not None and not (isinstance(change_percent, float) and pd.isna(change_percent)):
                self.label_change_percent.setText(f"{float(change_percent):.2f}%")
            else:
                self.label_change_percent.setText("N/A")


    def mousePressEvent(self, event):
        """重写鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.data)  # 发射点击信号
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """重写鼠标释放事件（可选）"""
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        """重写鼠标双击事件"""
        if event.button() == Qt.LeftButton:
            self.doubleClicked.emit()  # 发射双击信号
        super().mouseDoubleClickEvent(event)

    def enterEvent(self, event):
        """重写鼠标进入事件（悬浮开始）"""
        self._is_hovered = True
        self.hovered.emit()  # 发射悬浮信号
        self.update()  # 触发重绘
        super().enterEvent(event)

    def leaveEvent(self, event):
        """重写鼠标离开事件（悬浮结束）"""
        self._is_hovered = False
        self.hoverLeft.emit()  # 发射悬浮离开信号
        self.update()  # 触发重绘
        super().leaveEvent(event)

    def mouseMoveEvent(self, event):
        """重写鼠标移动事件（需要启用mouseTracking）"""
        # 可以在这里处理鼠标在控件内移动的逻辑
        super().mouseMoveEvent(event)


    def set_data(self, data):
        self.data = data