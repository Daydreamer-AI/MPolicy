from abc import ABC, abstractmethod
from enum import Enum
from datetime import datetime
from typing import Any, Optional
import traceback
import threading

from PyQt5.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool, pyqtSlot

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class BaseTask(QObject):
    """Qt集成的任务基类"""
    
    # Qt信号
    task_started = pyqtSignal(str)  # task_id
    task_progress = pyqtSignal(str, int)  # task_id, progress
    task_completed = pyqtSignal(str, object)  # task_id, result
    task_error = pyqtSignal(str, str)  # task_id, error_message
    task_cancelled = pyqtSignal(str)  # task_id
    
    def __init__(self, task_id: Optional[str] = None, priority: int = 0, timeout: Optional[int] = None):
        super().__init__()
        self.task_id = task_id
        self.priority = priority
        self.timeout = timeout
        self.status = TaskStatus.PENDING
        self.created_time = datetime.now()
        self.start_time = None
        self.end_time = None
        self.result = None
        self.error = None
        self._cancelled = False
        self._lock = threading.Lock()
        
    @abstractmethod
    def execute(self) -> Any:
        """执行任务的主要方法，子类必须实现"""
        pass
    
    def run(self):
        """任务执行方法"""
        with self._lock:
            if self._cancelled:
                self.status = TaskStatus.CANCELLED
                self.task_cancelled.emit(self.task_id)
                return
            
            self.status = TaskStatus.RUNNING
            self.start_time = datetime.now()
        
        # 发送开始信号
        self.task_started.emit(self.task_id)
        
        try:
            # 执行任务
            self.result = self.execute()
            
            # 发送完成信号
            with self._lock:
                self.status = TaskStatus.COMPLETED
                self.end_time = datetime.now()
            
            self.task_completed.emit(self.task_id, self.result)
            
        except Exception as e:
            # 发送错误信号
            with self._lock:
                self.status = TaskStatus.FAILED
                self.error = str(e)
                self.end_time = datetime.now()
            
            self.task_error.emit(self.task_id, str(e))
    
    def cancel(self):
        """取消任务"""
        with self._lock:
            if self.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                self._cancelled = True
                self.status = TaskStatus.CANCELLED
                self.task_cancelled.emit(self.task_id)
    
    def is_cancelled(self) -> bool:
        with self._lock:
            return self._cancelled
    
    def set_progress(self, progress: int):
        """设置任务进度"""
        self.task_progress.emit(self.task_id, progress)