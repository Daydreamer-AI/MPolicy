# base_chart_widget.py
from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg
import numpy as np

class BaseIndicatorWidget(QWidget):
    def __init__(self, data, parent=None):
        super(BaseIndicatorWidget, self).__init__(parent)
        self.item = None
        self.df_data = None
        self.logger = None
        self.plot_widget = None
        
        self.init_para(data)
        self.init_ui()
        self.init_connect()
    
    def init_ui(self):
        # 加载UI文件（子类需提供）
        uic.loadUi(self.get_ui_path(), self)
        
        layout = self.layout()
        if layout is None:
            self.logger.info("没有布局，创建一个")
            self.setLayout(QVBoxLayout())
            layout = self.layout()
            
        self.plot_widget = pg.PlotWidget()
        self.setup_plot_widget()
        layout.addWidget(self.plot_widget)
        self.draw()
    
    def setup_plot_widget(self):
        """设置plot widget的基本属性"""
        self.plot_widget.hideAxis('bottom')
        self.plot_widget.getAxis('left').setWidth(60)
        self.plot_widget.setBackground('w')
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setMouseEnabled(x=True, y=False)
        
        # 设置坐标轴颜色
        self.plot_widget.getAxis('left').setPen(QtGui.QColor(110, 110, 110))
        self.plot_widget.getAxis('bottom').setPen(QtGui.QColor(110, 110, 110))
        self.plot_widget.getAxis('left').setTextPen(QtGui.QColor(110, 110, 110))
        self.plot_widget.getAxis('bottom').setTextPen(QtGui.QColor(110, 110, 110))
    
    def update_data(self, data):
        self.df_data = data
        self.draw()
    
    def get_data(self):
        return self.df_data
    
    def get_plot_widget(self):
        return self.plot_widget
    
    def draw(self):
        self.plot_widget.clear()
        
        if self.df_data is None or self.df_data.empty:
            return
            
        if not self.validate_data():
            self.logger.warning(f"缺少必要的数据列来绘制{self.get_chart_name()}")
            return
            
        self.create_and_add_item()
        self.set_axis_ranges()

        # 调用钩子方法，允许子类添加额外绘制逻辑
        self.additional_draw()

    def additional_draw(self):
        """钩子方法：子类可以重写此方法添加额外的绘制逻辑"""
        pass
    
    def get_ui_path(self):
        """返回UI文件路径"""
        raise NotImplementedError("子类必须实现 get_ui_path 方法")
    
    def validate_data(self):
        """验证数据是否满足要求"""
        raise NotImplementedError("子类必须实现 validate_data 方法")
    
    def create_and_add_item(self):
        """创建并添加图表项"""
        raise NotImplementedError("子类必须实现 create_and_add_item 方法")
    
    def set_axis_ranges(self):
        """设置坐标轴范围"""
        raise NotImplementedError("子类必须实现 set_axis_ranges 方法")
    
    def get_chart_name(self):
        """返回图表名称"""
        raise NotImplementedError("子类必须实现 get_chart_name 方法")
    
    def init_para(self, data):
        """初始化参数"""
        raise NotImplementedError("子类必须实现 init_para 方法")
    
    def init_connect(self):
        """初始化信号连接"""
        pass