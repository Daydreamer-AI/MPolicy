import pyqtgraph as pg
from PyQt5 import QtGui, QtCore
import numpy as np

from manager.indicators_config_manager import *


class CandlestickItem(pg.GraphicsObject):
    # "."蜡烛图绘制类…·
    def __init__(self, data):
        pg.GraphicsObject.__init__(self)

        # 数据验证
        required_columns = ['open', 'close', 'high', 'low'] # , 'ma5', 'ma10', 'ma20', 'ma24', 'ma30', 'ma52', 'ma60'
        if not all(col in data.columns for col in required_columns):
            raise ValueError(f"缺少必要的数据列，需要: {required_columns}")

        self.data = data            # data should be a list or Pandas.DataFrame (date, code, open, high, low, close...)
        self.ma_visible = True
        self.generatePicture()

    def get_data(self):
        return self.data
    
    def update_data(self, data):
        # 数据验证
        required_columns = ['open', 'close', 'high', 'low'] # , 'ma5', 'ma10', 'ma20', 'ma24', 'ma30', 'ma52', 'ma60'
        if not all(col in data.columns for col in required_columns):
            raise ValueError(f"缺少必要的数据列，需要: {required_columns}")

        self.data = data
        self.generatePicture()
        self.prepareGeometryChange()  # 通知框架几何形状可能发生了变化
        self.update()  # 触发重绘

    def is_ma_show(self):
        return self.ma_visible
    
    def show_ma(self, b_show=True):
        if self.ma_visible == b_show:
            return
        
        self.ma_visible = b_show
        self.generatePicture()
        self.prepareGeometryChange()
        self.update()

    def generatePicture(self):
        # 生成蜡烛图
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        pg.setConfigOptions(leftButtonPan=False, antialias=False)
        w = 0.25

        # 长度检查
        if len(self.data) == 0:
            p.end()
            return

        #绘制移动平均线
        if self.ma_visible:
            
            if 'ma5' in self.data.columns and len(self.data) > 5:
                ma5 = self.data['ma5']
                ma5_lines = self._get_quota_lines(ma5)
                if ma5_lines:  # 确保有线段可绘制
                    p.setPen(pg.mkPen(dict_ma_color['ma5'], width=2))
                    p.drawLines(*tuple(ma5_lines))

            if 'ma10' in self.data.columns and len(self.data) > 10:
                ma10 = self.data['ma10']
                ma10_lines = self._get_quota_lines(ma10)
                if ma10_lines:
                    p.setPen(pg.mkPen(dict_ma_color['ma10'], width=2))
                    p.drawLines(*tuple(ma10_lines))

            # if 'ma20' in self.data.columns and len(self.data) > 20:
            #     ma20 = self.data['ma20']
            #     ma20_lines = self._get_quota_lines(ma20)
            #     if ma20_lines:
            #         p.setPen(pg.mkPen(dict_ma_color['ma20'], width=1))
            #         p.drawLines(*tuple(ma20_lines))

            if 'ma24' in self.data.columns and len(self.data) > 24:
                ma24 = self.data['ma24']
                ma24_lines = self._get_quota_lines(ma24)
                if ma24_lines:
                    p.setPen(pg.mkPen(dict_ma_color['ma24'], width=2))
                    p.drawLines(*tuple(ma24_lines))

            
            # if 'ma30' in self.data.columns and len(self.data) > 30:
            #     ma30 = self.data['ma30']
            #     ma30_lines = self._get_quota_lines(ma30)
            #     if ma30_lines:
            #         p.setPen(pg.mkPen(dict_ma_color['30'], width=1))
            #         p.drawLines(*tuple(ma30_lines))

            if 'ma52' in self.data.columns and len(self.data) > 52:
                ma52 = self.data['ma52']
                ma52_lines = self._get_quota_lines(ma52)
                if ma52_lines:
                    p.setPen(pg.mkPen(dict_ma_color['ma52'], width=2))
                    p.drawLines(*tuple(ma52_lines))
        

        #绘制蜡烛图
        for i in range(len(self.data)):
            open_price = self.data['open' ][i]
            close_price = self.data['close'][i]
            high_price = self.data['high'][i]
            low_price = self.data['low'][i]

            if close_price < open_price:
                #下跌－绿色
                p.setPen(pg.mkPen(dict_kline_color['desc']))
                p.setBrush(pg.mkBrush(dict_kline_color['desc']))
                p.drawLine(QtCore.QPointF(i, low_price), QtCore.QPointF(i, high_price))
                p.drawRect(QtCore.QRectF(i - w, open_price, w * 2, close_price - open_price))
                
            else:
                #上涨－红色 空心蜡烛
                p.setPen(pg.mkPen(dict_kline_color['asc']))
                p.setBrush(QtGui.QBrush(QtCore.Qt.NoBrush))  # 设置为空画刷，绘制空心矩形
                
                # 绘制上下影线
                if high_price != close_price:
                    p.drawLine(QtCore.QPointF(i, high_price), QtCore.QPointF(i, close_price))
                    
                if low_price != open_price:
                    p.drawLine(QtCore.QPointF(i, open_price), QtCore.QPointF(i, low_price))
                
                #绘制实体（空心）
                if close_price == open_price:
                    p.drawLine(QtCore.QPointF(i - w, open_price), QtCore.QPointF(i + w, open_price))
                else:
                    p.drawRect(QtCore.QRectF(i - w, open_price, w * 2, close_price - open_price))
                    
        p.end()

    def _get_quota_lines(self, data):
        #…获取指标线段的坐标点·
        lines = []
        for i in range(1, len(data)):
            if not np.isnan(data[i-1]) and not np.isnan(data[i]):
                lines.append(QtCore.QLineF(QtCore.QPointF(i-1, data[i-1]),
                QtCore.QPointF(i, data[i])))
        return lines
    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)
    def boundingRect(self) :
        return QtCore.QRectF(self.picture.boundingRect())

