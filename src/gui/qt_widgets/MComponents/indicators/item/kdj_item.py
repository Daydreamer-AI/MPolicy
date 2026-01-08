# file: gui/qt_widgets/MComponents/kdj_item.py
import pyqtgraph as pg
from PyQt5 import QtGui, QtCore
import numpy as np

from manager.indicators_config_manager import *

class KDJItem(pg.GraphicsObject):
    """KDJ指标绘制类"""
    def __init__(self, data):
        pg.GraphicsObject.__init__(self)

        # 数据验证
        required_columns = ['K', 'D', 'J']
        if not all(col in data.columns for col in required_columns):
            raise ValueError(f"缺少必要的数据列，需要: {required_columns}")
        
        self.data = data
        self.generatePicture()

    def get_data(self):
        return self.data
    
    def update_data(self, data):
        # 数据验证
        required_columns = ['K', 'D', 'J'] 
        if not all(col in data.columns for col in required_columns):
            raise ValueError(f"缺少必要的数据列，需要: {required_columns}")

        self.data = data
        self.generatePicture()
        self.prepareGeometryChange()  # 通知框架几何形状可能发生了变化
        self.update()  # 触发重绘

    def generatePicture(self):
        """生成KDJ图"""
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        pg.setConfigOptions(leftButtonPan=False, antialias=False)

        # 绘制K线
        k_points = []
        for i in range(len(self.data)):
            k_value = self.data['K'].iloc[i]
            if not np.isnan(k_value):
                k_points.append(QtCore.QPointF(i, k_value))
        
        if len(k_points) > 1:
            p.setPen(pg.mkPen(dict_kdj_color[IndicatrosEnum.KDJ_K.value], width=2))
            for i in range(len(k_points) - 1):
                p.drawLine(k_points[i], k_points[i + 1])

        # 绘制D线
        d_points = []
        for i in range(len(self.data)):
            d_value = self.data['D'].iloc[i]
            if not np.isnan(d_value):
                d_points.append(QtCore.QPointF(i, d_value))
        
        if len(d_points) > 1:
            p.setPen(pg.mkPen(dict_kdj_color[IndicatrosEnum.KDJ_D.value], width=2))
            for i in range(len(d_points) - 1):
                p.drawLine(d_points[i], d_points[i + 1])

        # 绘制J线
        j_points = []
        for i in range(len(self.data)):
            j_value = self.data['J'].iloc[i]
            if not np.isnan(j_value):
                j_points.append(QtCore.QPointF(i, j_value))
        
        if len(j_points) > 1:
            p.setPen(pg.mkPen(dict_kdj_color[IndicatrosEnum.KDJ_J.value], width=2))
            for i in range(len(j_points) - 1):
                p.drawLine(j_points[i], j_points[i + 1])

        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())