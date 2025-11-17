from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene
from PyQt5.QtCore import pyqtSlot, QRectF, Qt
from PyQt5.QtGui import QColor, QPen, QBrush, QPainter, QFont

import pyqtgraph as pg
import numpy as np

class MPieChartItem(pg.GraphicsObject):
    """自定义饼图项"""
    def __init__(self, data, labels, parent=None):
        pg.GraphicsObject.__init__(self, parent)
        self.data = data
        self.labels = labels
        self.generate_picture()
    
    def generate_picture(self):
        """生成饼图"""
        self.picture = pg.QtGui.QPicture()
        painter = pg.QtGui.QPainter(self.picture)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 计算总量
        total = sum(self.data)
        if total == 0:
            return
            
        # 定义颜色
        colors = [
            QColor(255, 170, 170),  # 浅红
            QColor(170, 255, 170),  # 浅绿
            QColor(170, 170, 255),  # 浅蓝
            QColor(255, 255, 170),  # 浅黄
            QColor(255, 170, 255),  # 浅紫
            QColor(170, 255, 255),  # 浅青
            QColor(255, 210, 170),  # 浅橙
            QColor(210, 170, 255),  # 浅紫红
            QColor(170, 255, 210),  # 浅绿蓝
            QColor(255, 170, 210),  # 浅粉
            QColor(200, 200, 200)   # 灰色（其他）
        ]
        
        rect = QRectF(-100, -100, 200, 200)
        start_angle = 0
        
        for i, value in enumerate(self.data):
            span_angle = (value / total) * 360 * 16  # Qt角度单位是1/16度
            
            # 设置颜色和画笔
            color = colors[i % len(colors)] if i < 10 else QColor(200, 200, 200)
            painter.setBrush(QBrush(color))
            
            # 对前10名设置更粗的边框以突出显示
            pen_width = 2 if i < 10 else 1
            painter.setPen(QPen(Qt.black, pen_width))
            
            # 绘制扇形
            painter.drawPie(rect, int(start_angle), int(span_angle))
            
            start_angle += span_angle
        
        painter.end()
    
    def paint(self, painter, option, widget=None):
        painter.drawPicture(0, 0, self.picture)
    
    def boundingRect(self):
        return QRectF(-110, -110, 220, 220)