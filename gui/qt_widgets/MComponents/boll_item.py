# file: gui/qt_widgets/MComponents/boll_item.py
import pyqtgraph as pg
from PyQt5 import QtGui, QtCore
import numpy as np

# 颜色配置
color_table = {
    'boll_up': (222, 42, 38),      # 上轨线 - 红色
    'boll_mb': (25, 160, 255),      # 中轨线 - 蓝色
    'boll_dn': (10, 204, 90),      # 下轨线 - 绿色
    'close': (128, 128, 128)       # 收盘价 - 灰色
}

class BOLLItem(pg.GraphicsObject):
    """BOLL指标绘制类"""
    def __init__(self, data):
        pg.GraphicsObject.__init__(self)

        # 数据验证
        required_columns = ['close', 'boll_up', 'boll_mb', 'boll_dn']
        if not all(col in data.columns for col in required_columns):
            raise ValueError(f"缺少必要的数据列，需要: {required_columns}")
        
        self.data = data
        self.generatePicture()

    def generatePicture(self):
        """生成BOLL图"""
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        pg.setConfigOptions(leftButtonPan=False, antialias=False)

        # 绘制收盘价线
        close_points = []
        for i in range(len(self.data)):
            close_value = self.data['close'].iloc[i]
            if not np.isnan(close_value):
                close_points.append(QtCore.QPointF(i, close_value))
        
        if len(close_points) > 1:
            p.setPen(pg.mkPen(color_table['close'], width=2))
            for i in range(len(close_points) - 1):
                p.drawLine(close_points[i], close_points[i + 1])

        # 绘制上轨线
        up_points = []
        for i in range(len(self.data)):
            up_value = self.data['boll_up'].iloc[i]
            if not np.isnan(up_value):
                up_points.append(QtCore.QPointF(i, up_value))
        
        if len(up_points) > 1:
            p.setPen(pg.mkPen(color_table['boll_up'], width=2))
            for i in range(len(up_points) - 1):
                p.drawLine(up_points[i], up_points[i + 1])

        # 绘制中轨线
        mb_points = []
        for i in range(len(self.data)):
            mb_value = self.data['boll_mb'].iloc[i]
            if not np.isnan(mb_value):
                mb_points.append(QtCore.QPointF(i, mb_value))
        
        if len(mb_points) > 1:
            p.setPen(pg.mkPen(color_table['boll_mb'], width=2))
            for i in range(len(mb_points) - 1):
                p.drawLine(mb_points[i], mb_points[i + 1])

        # 绘制下轨线
        dn_points = []
        for i in range(len(self.data)):
            dn_value = self.data['boll_dn'].iloc[i]
            if not np.isnan(dn_value):
                dn_points.append(QtCore.QPointF(i, dn_value))
        
        if len(dn_points) > 1:
            p.setPen(pg.mkPen(color_table['boll_dn'], width=2))
            for i in range(len(dn_points) - 1):
                p.drawLine(dn_points[i], dn_points[i + 1])

        # 绘制布林带填充区域（上轨和下轨之间）
        if len(up_points) > 1 and len(dn_points) > 1:
            p.setPen(QtGui.QPen(QtCore.Qt.NoPen))
            p.setBrush(QtGui.QBrush(QtGui.QColor(255, 61, 61, 30)))  # 半透明红色
            
            # 创建填充区域的点
            fill_points = up_points + dn_points[::-1]  # 上轨点 + 反转的下轨点
            if len(fill_points) > 2:
                polygon = QtGui.QPolygonF(fill_points)
                p.drawPolygon(polygon)

        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())