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

    def get_visible_data_range(self):
        '''
        获取当前视图范围内X轴对应的数据索引范围和数据
        返回: (visible_data, x_min, x_max) 或 (None, None, None) 如果无效
        '''
        if self.plot_widget is None or self.df_data is None or self.df_data.empty:
            return None, None, None
        
        # 获取当前X轴的视图范围
        view_range = self.plot_widget.viewRange()
        x_range = view_range[0]  # X轴范围 [min, max]
        
        # 确定可视范围内的数据索引
        x_min, x_max = int(max(0, x_range[0])), int(min(len(self.df_data), x_range[1]))
        
        # 确保范围有效
        if x_min >= len(self.df_data) or x_max <= 0 or x_min >= x_max:
            return None, None, None
            
        # 获取可视范围内的数据
        visible_data = self.df_data.iloc[x_min:x_max]
        
        if visible_data.empty:
            return None, None, None
            
        return visible_data, x_min, x_max

    def slot_range_changed(self):
        '''当视图范围改变时调用'''
        # y轴坐标值同步
        # 获取当前x轴视图范围内的数据


        # 根据当前可视范围内的数据的最大、最小值调整Y轴坐标值范围

        # 重新设置Y轴刻度
        pass

    def set_default_view_range(self, visible_days=120):
        """
        设置默认视图范围，显示最新的数据
        :param visible_days: 默认显示的天数
        """
        if self.plot_widget is None or self.df_data is None or self.df_data.empty:
            return
        
        total_days = len(self.df_data)
        if total_days <= visible_days:
            # 数据量小于等于默认显示天数，显示所有数据
            self.plot_widget.setXRange(-1, total_days + 1, padding=0)
        else:
            # 显示最新的visible_days天数据
            start_index = total_days - visible_days
            end_index = total_days
            self.plot_widget.setXRange(start_index, end_index, padding=0)

    def auto_scale_to_latest(self, visible_days=120):
        """
        自动缩放到最新数据并触发Y轴自适应
        :param visible_days: 默认显示的天数
        """
        self.set_default_view_range(visible_days)
        # 触发Y轴范围调整
        self.slot_range_changed()


