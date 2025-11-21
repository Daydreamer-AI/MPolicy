# base_chart_widget.py
from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg
import numpy as np

class BaseIndicatorWidget(QWidget):
    # 类变量，用于存储所有实例的垂直线引用
    _shared_v_lines = {}
    _shared_h_lines = {}
    def __init__(self, data, parent=None):
        super(BaseIndicatorWidget, self).__init__(parent)
        self.item = None
        self.df_data = None
        self.logger = None
        self.plot_widget = None
        
        self.init_para(data)
        self.init_ui()
        self.init_connect()

    # 清理资源
    def __del__(self):
        # 从共享字典中移除
        chart_name = self.get_chart_name()
        self.logger.info(f"开始清理{chart_name}及其资源")
        if chart_name in BaseIndicatorWidget._shared_v_lines:
            del BaseIndicatorWidget._shared_v_lines[chart_name]
        if chart_name in BaseIndicatorWidget._shared_h_lines:
            del BaseIndicatorWidget._shared_h_lines[chart_name]
    
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

        self.v_line = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('#808286', width=2, style=Qt.DashLine))
        self.h_line = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('#808286', width=2, style=Qt.DashLine))
        self.v_line.setZValue(1000)
        self.h_line.setZValue(1000)

        # 将垂直线添加到共享列表
        BaseIndicatorWidget._shared_v_lines[self.get_chart_name()] = self.v_line
        BaseIndicatorWidget._shared_h_lines[self.get_chart_name()] = self.h_line

        main_viewbox = self.plot_widget.getViewBox()
        main_viewbox.addItem(self.v_line, ignoreBounds=True)
        main_viewbox.addItem(self.h_line, ignoreBounds=True)

        self.hide_all_labels()

        # self.plot_widget.scene().sigMouseMoved.connect(self.slot_mouse_moved)

    
    def update_data(self, data):
        self.logger.info(f"更新数据{self.get_chart_name()}, data长度：{len(data)}")
        self.df_data = data
        self.draw()
        self.update()
    
    def get_data(self):
        return self.df_data
    
    def get_plot_widget(self):
        return self.plot_widget
    
    def draw(self):
        if self.df_data is None or self.df_data.empty:
            self.logger.info(f"数据为空，无法绘制{self.get_chart_name()}")
            return
            
        if not self.validate_data():
            self.logger.warning(f"缺少必要的数据列来绘制{self.get_chart_name()}")
            return
        
        self.plot_widget.clear()
        
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

    def slot_mouse_moved(self, pos, widget_source=None):
        """鼠标移动事件处理"""
        if widget_source is not None:
            # self.logger.info(f"正在处理{self.get_chart_name()}鼠标移动响应，来源：{widget_source.get_chart_name()}")
            pass
        else:
            # self.logger.info(f"widget_source is not None")
            return

        if self.plot_widget.sceneBoundingRect().contains(pos):
            mouse_point = self.plot_widget.getViewBox().mapSceneToView(pos)
            x_val = mouse_point.x()
            y_val = mouse_point.y()

            # self.logger.info(f"鼠标位置：x={x_val}, y={y_val}")

            # 同步更新所有视图中的十字线
            # self.logger.info(f"当前存储的垂直线：\n{BaseIndicatorWidget._shared_v_lines.keys()}")
            # for chart_name, v_line in BaseIndicatorWidget._shared_v_lines.items():
            #     # self.logger.info(f"正在显示{chart_name}的垂直线")
            #     v_line.setPos(x_val)
            #     v_line.show()

            # self.logger.info(f"当前存储的水平线：\n{BaseIndicatorWidget._shared_h_lines.keys()}")
            for chart_name, h_line in BaseIndicatorWidget._shared_h_lines.items():
                if chart_name == widget_source.get_chart_name():
                    h_line.setPos(y_val)
                    h_line.show()
                # else:
                #     h_line.hide()

            bar_centers = list(range(len(self.df_data)))
            
            closest_index = None
            min_distance = float('inf')
            
            for i, center in enumerate(bar_centers):
                distance = abs(center - x_val)
                if distance <= 0.25 / 2:
                    if distance < min_distance:
                        min_distance = distance
                        closest_index = i
            
            if closest_index is not None:
                view_range = self.plot_widget.getViewBox().viewRange()
                closest_x = bar_centers[closest_index]
                for chart_name, v_line in BaseIndicatorWidget._shared_v_lines.items():
                    v_line.setPos(closest_x)
                    v_line.show()


            # else:
            #     self.hide_all_labels()
        # else:
            # self.logger.info(f"鼠标位置超出图表范围")
            # self.hide_all_labels()

    def additional_mouse_moved(self, closest_x):
        """钩子方法：子类可以重写此方法添加鼠标移动处理"""
        pass

    def hide_all_labels(self):
        self.v_line.hide()
        self.h_line.hide()
        pass

    def enterEvent(self, event):
        """
        当鼠标进入控件时的处理
        """
        super().enterEvent(event)

    def leaveEvent(self, event):
        """
        当鼠标离开控件时，隐藏所有标签和十字线
        """
        self.hide_all_labels()
        super().leaveEvent(event)


