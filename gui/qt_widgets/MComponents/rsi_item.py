# file: gui/qt_widgets/MComponents/rsi_item.py
import pyqtgraph as pg
from PyQt5 import QtGui, QtCore
import numpy as np

# 颜色配置
color_table = {
    'rsi6_line': (255, 208, 0),     # RSI6线 - 黄色
    'rsi12_line': (10, 204, 90),    # RSI12线 - 绿色
    'rsi24_line': (25, 160, 255),    # RSI24线 - 蓝色
    'overbought': (255, 0, 0),      # 超买线 - 红色
    'oversold': (0, 255, 0),        # 超卖线 - 绿色
    'mid_line': (128, 128, 128)     # 中轴线 - 灰色
}

class RSIItem(pg.GraphicsObject):
    """RSI指标绘制类"""
    def __init__(self, data):
        pg.GraphicsObject.__init__(self)

        # 数据验证
        required_columns = []
        # 检查至少有一个RSI列存在
        rsi_columns = ['rsi6', 'rsi12', 'rsi24']
        has_rsi = any(col in data.columns for col in rsi_columns)
        if not has_rsi:
            raise ValueError(f"缺少必要的RSI数据列，至少需要: {rsi_columns}")
        
        self.data = data
        self.generatePicture()

    def generatePicture(self):
        """生成RSI图"""
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        pg.setConfigOptions(leftButtonPan=False, antialias=False)

        # 绘制RSI6线
        if 'rsi6' in self.data.columns:
            rsi6_points = []
            for i in range(len(self.data)):
                rsi6_value = self.data['rsi6'].iloc[i]
                if not np.isnan(rsi6_value):
                    rsi6_points.append(QtCore.QPointF(i, rsi6_value))
            
            if len(rsi6_points) > 1:
                p.setPen(pg.mkPen(color_table['rsi6_line'], width=2))
                for i in range(len(rsi6_points) - 1):
                    p.drawLine(rsi6_points[i], rsi6_points[i + 1])

        # 绘制RSI12线
        if 'rsi12' in self.data.columns:
            rsi12_points = []
            for i in range(len(self.data)):
                rsi12_value = self.data['rsi12'].iloc[i]
                if not np.isnan(rsi12_value):
                    rsi12_points.append(QtCore.QPointF(i, rsi12_value))
            
            if len(rsi12_points) > 1:
                p.setPen(pg.mkPen(color_table['rsi12_line'], width=2))
                for i in range(len(rsi12_points) - 1):
                    p.drawLine(rsi12_points[i], rsi12_points[i + 1])

        # 绘制RSI24线
        if 'rsi24' in self.data.columns:
            rsi24_points = []
            for i in range(len(self.data)):
                rsi24_value = self.data['rsi24'].iloc[i]
                if not np.isnan(rsi24_value):
                    rsi24_points.append(QtCore.QPointF(i, rsi24_value))
            
            if len(rsi24_points) > 1:
                p.setPen(pg.mkPen(color_table['rsi24_line'], width=2))
                for i in range(len(rsi24_points) - 1):
                    p.drawLine(rsi24_points[i], rsi24_points[i + 1])

        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())