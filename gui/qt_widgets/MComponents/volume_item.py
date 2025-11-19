import pyqtgraph as pg
from PyQt5 import QtGui, QtCore
import numpy as np

#颜色配置
color_table = {
'line_desc': (0, 169, 178), #绿色－下跌
'line_asc': (255, 61, 61), #红色 -上涨
'klines': (110, 110, 110)
}

class VolumeItem(pg.GraphicsObject):
    # …"交易量柱状图绘制类……
    def __init__(self, data):
        pg.GraphicsObject.__init__(self)

        # 数据验证
        required_columns = ['open', 'close', 'volume'] # , 'low', 'ma5', 'ma10', 'ma20', 'ma24', 'ma30', 'ma52', 'ma60'
        if not all(col in data.columns for col in required_columns):
            raise ValueError(f"缺少必要的数据列，需要: {required_columns}")
        
        self.data = data
        self.generatePicture()

    def generatePicture(self):
        # …生成交易量柱状图?…
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        pg.setConfigOptions(leftButtonPan=False, antialias=False)
        w = 0.25

        for i in range(len(self.data['volume'])):
            open_price = self.data['open'][i]
            close_price = self.data['close'][i]
            volume = self.data['volume'][i]
            
            if close_price < open_price:
                #下跌－ 绿色填充
                p.setPen(pg.mkPen(color_table['line_desc']))
                p.drawRect(QtCore.QRectF(i - w, 0, w * 2, volume))
                p.setBrush(pg.mkBrush(color_table['line_desc']))
            else:
                #上涨－ 红色空心
                p.setPen(pg.mkPen(color_table['line_asc']))
                p.drawLines(
                    QtCore.QLineF(QtCore.QPointF(i - w, 0), QtCore.QPointF(i - w, volume)),
                    QtCore.QLineF(QtCore.QPointF(i - w, volume), QtCore.QPointF(i + w, volume)),
                    QtCore.QLineF(QtCore.QPointF(i + w, volume), QtCore.QPointF(i + w, 0)),
                    QtCore.QLineF(QtCore.QPointF(i + w, 0), QtCore.QPointF(i - w, 0))
                )
        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())