# file: gui/qt_widgets/MComponents/macd_item.py
import pyqtgraph as pg
from PyQt5 import QtGui, QtCore
import numpy as np

# 颜色配置
color_table = {
    'line_asc': (255, 61, 61),      # 红色 - 上涨
    'line_desc': (0, 169, 178),     # 绿色 - 下跌
    'macd_line': (255, 61, 61),     # MACD线 - 红色
    'signal_line': (0, 169, 178),   # 信号线 - 绿色
    'histogram_positive': (255, 61, 61),  # 柱状图正数 - 红色
    'histogram_negative': (0, 169, 178),  # 柱状图负数 - 绿色
    'klines': (110, 110, 110)
}

class MACDItem(pg.GraphicsObject):
    """MACD指标绘制类"""
    def __init__(self, data):
        pg.GraphicsObject.__init__(self)

        # 数据验证
        required_columns = ['diff', 'dea', 'macd']
        if not all(col in data.columns for col in required_columns):
            raise ValueError(f"缺少必要的数据列，需要: {required_columns}")
        
        self.data = data
        self.generatePicture()

    def generatePicture(self):
        """生成MACD图"""
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        pg.setConfigOptions(leftButtonPan=False, antialias=False)
        w = 0.3

        # 绘制MACD柱状图
        for i in range(len(self.data)):
            macd_value = self.data['macd'].iloc[i]
            
            if not np.isnan(macd_value):
                if macd_value >= 0:
                    # 正数 - 红色
                    p.setPen(pg.mkPen(color_table['histogram_positive']))
                    p.setBrush(pg.mkBrush(color_table['histogram_positive']))
                else:
                    # 负数 - 绿色
                    p.setPen(pg.mkPen(color_table['histogram_negative']))
                    p.setBrush(pg.mkBrush(color_table['histogram_negative']))
                
                # 绘制柱状图
                p.drawRect(QtCore.QRectF(i - w, 0, w * 2, macd_value))

        # 绘制DIFF线 (MACD线)
        diff_points = []
        for i in range(len(self.data)):
            diff_value = self.data['diff'].iloc[i]
            if not np.isnan(diff_value):
                diff_points.append(QtCore.QPointF(i, diff_value))
        
        if len(diff_points) > 1:
            p.setPen(pg.mkPen(color_table['macd_line'], width=1))
            for i in range(len(diff_points) - 1):
                p.drawLine(diff_points[i], diff_points[i + 1])

        # 绘制DEA线 (信号线)
        dea_points = []
        for i in range(len(self.data)):
            dea_value = self.data['dea'].iloc[i]
            if not np.isnan(dea_value):
                dea_points.append(QtCore.QPointF(i, dea_value))
        
        if len(dea_points) > 1:
            p.setPen(pg.mkPen(color_table['signal_line'], width=1))
            for i in range(len(dea_points) - 1):
                p.drawLine(dea_points[i], dea_points[i + 1])

        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())