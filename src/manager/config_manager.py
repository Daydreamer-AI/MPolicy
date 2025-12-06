import os
import configparser
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from manager.logging_manager import get_logger

class ConfigManager:
    """
    增强版配置管理器。
    支持动态修改配置文件路径，并自动管理配置数据的加载与同步。
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.__initialized = False # 标记未初始化
            return cls._instance

    def __init__(self):
        """初始化管理器。真正的初始化在 set_config_path 中完成。"""
        if getattr(self, '__initialized', False):
            return
        
        self.logger = get_logger(__name__)
            
        self._config_path = Path.home() / 'AppData' / 'Roaming' / 'MPolicy' / 'config.ini' # 当前管理的配置文件路径
        self.logger.info(f"正在使用配置文件 '{self._config_path}'")
        self._config_data = configparser.ConfigParser() # 内存中的配置数据
        self._file_mtime = 0 # 记录文件最后修改时间，用于判断是否需重载
        self._lock = threading.RLock() # 实例级别的可重入锁，用于线程安全
        self.__initialized = True # 标记已初始化

    def set_config_path(self, config_path: Union[str, Path]) -> bool:
        """
        设置或更改配置文件路径，并自动加载该文件。

        参数:
            config_path: 新的配置文件路径。

        返回:
            成功加载返回 True，否则返回 False（但会初始化空配置）。
        """
        config_path = Path(config_path)
        with self._lock:
            self._config_path = config_path
            return self._load_config()

    def get_config_path(self) -> Optional[Path]:
        """获取当前管理的配置文件路径。"""
        return self._config_path

    def _load_config(self) -> bool:
        """内部方法：从当前路径加载配置到内存。"""
        if self._config_path is None:
            self._config_data = configparser.ConfigParser()
            self._file_mtime = 0
            return False

        if self._config_path.exists():
            try:
                # 读取并更新修改时间
                new_mtime = self._config_path.stat().st_mtime
                # 如果文件被修改过，才重新加载
                if new_mtime != self._file_mtime:
                    self._config_data.read(self._config_path, encoding='utf-8')
                    self._file_mtime = new_mtime
                return True
            except (OSError, configparser.Error) as e:
                self.logger.info(f"加载配置文件失败: {e}")
                # 加载失败，使用空配置，但不改变原有记忆的mtime，防止覆盖
                self._config_data = configparser.ConfigParser()
                return False
        else:
            # 文件不存在，初始化一个空配置
            self._config_data = configparser.ConfigParser()
            self._file_mtime = 0
            self.logger.info(f"配置文件 '{self._config_path}' 不存在，已初始化空配置。")
            return False

    def _ensure_loaded(self) -> None:
        """内部方法：确保内存中的数据是最新的。"""
        if self._config_path is not None:
            self._load_config() # 简单重载，内部会判断是否需更新

    def save(self, save_path: Union[str, Path, None] = None) -> bool:
        """
        将当前内存中的配置保存到文件。

        参数:
            save_path: 指定的保存路径。如果为 None，则使用当前管理的路径。

        返回:
            成功保存返回 True，否则返回 False。
        """
        with self._lock:
            target_path = Path(save_path) if save_path is not None else self._config_path
            if target_path is None:
                self.logger.info("错误：未指定保存路径且当前无管理路径。")
                return False

            try:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with open(target_path, 'w', encoding='utf-8') as configfile:
                    self._config_data.write(configfile)
                # 更新内存中记录的文件修改时间
                self._file_mtime = target_path.stat().st_mtime if target_path.exists() else 0
                return True
            except (OSError, configparser.Error) as e:
                self.logger.info(f"保存配置文件失败: {e}")
                return False

    def get(self, section: str, key: str, default: Any = None) -> Optional[str]:
        """获取字符串配置值。"""
        with self._lock:
            self._ensure_loaded()
            try:
                return self._config_data[section][key]
            except KeyError:
                return default

    def getint(self, section: str, key: str, default: int = None) -> Optional[int]:
        """获取整数配置值。"""
        # ... 实现与之前类似，但在开头调用 self._ensure_loaded()
        with self._lock:
            self._ensure_loaded()
            try:
                return self._config_data.getint(section, key)
            except (ValueError, configparser.NoSectionError, configparser.NoOptionError):
                return default

    def set(self, section: str, key: str, value: Any) -> None:
        """设置配置值。"""
        with self._lock:
            self._ensure_loaded() # 确保操作的是最新配置
            if not self._config_data.has_section(section):
                self._config_data.add_section(section)
            self._config_data[section][key] = str(value)

    def remove_key(self, section: str, key: str) -> bool:
        """删除配置项。"""
        with self._lock:
            self._ensure_loaded()
            return self._config_data.remove_option(section, key)

    def remove_section(self, section: str) -> bool:
        """删除整个配置块。"""
        with self._lock:
            self._ensure_loaded()
            return self._config_data.remove_section(section)

    def has_section(self, section: str) -> bool:
        """检查配置块是否存在。"""
        with self._lock:
            self._ensure_loaded()
            return self._config_data.has_section(section)

    def has_key(self, section: str, key: str) -> bool:
        """检查配置项是否存在。"""
        with self._lock:
            self._ensure_loaded()
            return self._config_data.has_option(section, key)

    def reload(self) -> bool:
        """强制从当前配置文件重新加载，丢弃未保存的更改。"""
        with self._lock:
            return self._load_config()

    def clear_in_memory(self) -> None:
        """清空内存中的配置数据（不删除文件）。"""
        with self._lock:
            self._config_data = configparser.ConfigParser()
            self._file_mtime = 0

# 使用示例
if __name__ == "__main__":
    manager = ConfigManager()

    # 1. 设置路径并操作 config_a.ini
    manager.set_config_path('config_a.ini')
    manager.set('Database', 'host', 'host_a.com')
    manager.save() # 保存到 config_a.ini

    # 2. 动态切换到 config_b.ini 并操作
    manager.set_config_path('config_b.ini') # 自动加载 config_b.ini (如果存在)
    manager.set('App', 'name', 'MyApp_B')
    manager.save() # 保存到 config_b.ini

    # 3. 再切回 config_a.ini，内存中的数据会自动更新回 config_a.ini 的内容
    manager.set_config_path('config_a.ini')
    db_host = manager.get('Database', 'host')