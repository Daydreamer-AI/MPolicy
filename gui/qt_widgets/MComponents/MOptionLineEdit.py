# gui/qt_widgets/MComponents/m_option_line_edit.py

from PyQt5.QtWidgets import QLineEdit, QListWidget, QWidget
from PyQt5.QtCore import pyqtSignal, QTimer, Qt
import logging

class MOptionLineEdit(QLineEdit):
    """
    带有选项列表的LineEdit控件
    """
    # 自定义信号
    optionSelected = pyqtSignal(str)  # 当选项被选中时发出信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 初始化选项列表
        self.options_list_widget = QListWidget()
        self.options_list_widget.setParent(self.parent() if self.parent() else None)
        self.options_list_widget.hide()
        self.options_list_widget.setMinimumSize(300, 150)
        
        # 数据属性
        self.all_options = []
        self.filtered_options = []
        
        # 连接信号
        self.textChanged.connect(self.on_text_changed)
        self.options_list_widget.itemClicked.connect(self.on_option_selected)
        self.editingFinished.connect(self.hide_options_list)
        
        # 安装事件过滤器
        self.installEventFilter(self)
        self.options_list_widget.installEventFilter(self)
        
    def set_options(self, options):
        """
        设置所有选项
        :param options: 选项列表
        """
        self.all_options = list(options) if options else []
        self.filtered_options = self.all_options[:]
        
    def on_text_changed(self, text):
        """
        处理文本变化
        """
        self.logger.debug(f"输入的搜索值为：{text}")
        if not text:
            # 显示所有选项
            self.filtered_options = self.all_options[:]
        else:
            # 根据输入过滤选项
            self.filtered_options = [option for option in self.all_options 
                                   if text.lower() in option.lower()]
        
        # 更新选项列表显示
        self.update_options_list()
        
        # 动态定位和显示控制
        if self.filtered_options:
            self.position_options_list()
            self.options_list_widget.show()
        elif text:  # 如果有输入文本但没有匹配项，则隐藏
            self.options_list_widget.hide()
            
    def update_options_list(self):
        """
        更新选项列表显示
        """
        # 清空现有选项
        self.options_list_widget.clear()
        
        # 添加过滤后的选项
        for option in self.filtered_options:
            self.options_list_widget.addItem(option)
            
    def position_options_list(self):
        """
        动态计算并设置选项列表的位置，确保其在输入框下方
        """
        if not self.parent():
            return
            
        # 获取输入框在父窗口中的位置
        line_edit_pos = self.pos()
        
        # 设置选项列表的位置在输入框正下方
        x_pos = line_edit_pos.x()
        y_pos = line_edit_pos.y() + self.height()
        
        self.options_list_widget.move(x_pos, y_pos)
        
        # 设置宽度与输入框一致
        self.options_list_widget.setFixedWidth(self.width())
        
    def on_option_selected(self, item):
        """
        处理选项被点击
        """
        selected_text = item.text()
        self.logger.debug(f"选中的选项为：{selected_text}")
        
        # 发出信号
        self.optionSelected.emit(selected_text)
        
        # 设置文本并隐藏选项列表
        self.setText(selected_text)
        self.options_list_widget.hide()
        self.clearFocus()
        
    def hide_options_list(self):
        """
        隐藏选项列表
        """
        # 使用定时器延迟隐藏，以便处理点击事件
        QTimer.singleShot(100, self.options_list_widget.hide)
        
    def eventFilter(self, obj, event):
        """
        事件过滤器
        """
        if obj == self:
            if event.type() == event.FocusIn:
                # 当输入框获得焦点时
                self.on_focus_in()
            elif event.type() == event.FocusOut:
                # 当输入框失去焦点时
                QTimer.singleShot(150, self.check_focus_and_hide)
        elif obj == self.options_list_widget:
            if event.type() == event.FocusOut:
                # 当选项列表失去焦点时
                QTimer.singleShot(100, self.check_focus_and_hide)
                
        return super().eventFilter(obj, event)
        
    def on_focus_in(self):
        """
        当输入框获得焦点时的处理
        """
        current_text = self.text()
        if current_text:
            # 如果有文本，重新显示匹配的选项
            self.on_text_changed(current_text)
        else:
            # 如果没有文本，显示所有选项
            self.filtered_options = self.all_options[:]
            self.update_options_list()
            if self.filtered_options:
                self.position_options_list()
                self.options_list_widget.show()
                
    def check_focus_and_hide(self):
        """
        检查焦点状态并决定是否隐藏选项列表
        """
        # 如果输入框和选项列表都不拥有焦点，则隐藏选项列表
        if not (self.hasFocus() or self.options_list_widget.hasFocus()):
            self.options_list_widget.hide()
            
    def show_options(self):
        """
        显示选项列表
        """
        if self.filtered_options:
            self.position_options_list()
            self.options_list_widget.show()
            
    def hide_options(self):
        """
        隐藏选项列表
        """
        self.options_list_widget.hide()
        
    def get_selected_option(self):
        """
        获取当前选中的选项
        """
        return self.text()
        
    def clear_selection(self):
        """
        清除选择
        """
        self.clear()
        self.options_list_widget.hide()
        
    def resizeEvent(self, event):
        """
        处理大小变化事件
        """
        super().resizeEvent(event)
        # 当输入框大小变化时，重新定位选项列表
        if self.options_list_widget.isVisible():
            self.position_options_list()