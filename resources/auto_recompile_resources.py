import os
import time
import logging
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 设置日志格式，方便查看监控状态和编译结果
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

# 定义需要监控的文件和输出文件路径
QRC_FILE = "./resources/resources.qrc"  # 你的 .qrc 文件路径
OUTPUT_PY_FILE = "./resources/resources_rc.py"  # 输出的 .py 文件路径

# 根据你的项目环境选择编译命令（二选一）
# 如果你使用 PyQt5，使用 pyrcc5
COMPILE_COMMAND = ["pyrcc5", QRC_FILE, "-o", OUTPUT_PY_FILE]
# 如果你使用 PySide6，取消下面一行的注释并使用 pyside6-rcc
# COMPILE_COMMAND = ["pyside6-rcc", QRC_FILE, "-o", OUTPUT_PY_FILE]

class ResourceChangeHandler(FileSystemEventHandler):
    """处理文件系统事件，当 .qrc 文件改变时执行编译"""
    
    def __init__(self):
        self.last_triggered = 0  # 用于防抖，防止短时间內多次触发
        self.debounce_interval = 1  # 防抖时间间隔（秒）

    def on_modified(self, event):
        # 只关心文件修改事件，且路径匹配我们监控的 .qrc 文件
        if not event.is_directory and event.src_path.endswith('.qrc') and os.path.abspath(event.src_path) == os.path.abspath(QRC_FILE):
            current_time = time.time()
            # 防抖检查：避免因编辑器多次保存等操作导致短时间內重复编译
            if current_time - self.last_triggered > self.debounce_interval:
                self.last_triggered = current_time
                logger.info(f"检测到 {QRC_FILE} 被修改，开始重新编译...")
                self.compile_resource()

    def on_created(self, event):
        # 有时某些编辑器保存文件时可能会先创建临时文件，也触发编译
        if not event.is_directory and event.src_path.endswith('.qrc') and os.path.abspath(event.src_path) == os.path.abspath(QRC_FILE):
            self.on_modified(event)  # 直接调用 on_modified 处理

    def compile_resource(self):
        """执行实际的资源编译命令"""
        try:
            # 运行编译命令
            result = subprocess.run(COMPILE_COMMAND, check=True, capture_output=True, text=True)
            logger.info("资源文件编译成功！")
            if result.stderr:
                logger.debug(f"编译输出: {result.stderr}")
        except subprocess.CalledProcessError as e:
            logger.error(f"编译失败！返回值: {e.returncode}, 错误信息: {e.stderr}")
        except FileNotFoundError:
            logger.error("未能找到编译工具 (pyrcc5 或 pyside6-rcc)。请确保 PyQt5 或 PySide6 已正确安装并配置在PATH中。")
        except Exception as e:
            logger.error(f"编译过程中发生未知错误: {e}")

def start_monitoring():
    """启动文件监控"""
    # 获取需要监控的目录（.qrc 文件所在的目录）
    watch_directory = os.path.dirname(QRC_FILE) if os.path.dirname(QRC_FILE) else '.'

    event_handler = ResourceChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path=watch_directory, recursive=False) # recursive=False 表示不监控子目录

    observer.start()
    logger.info(f"开始监控目录 {os.path.abspath(watch_directory)} 下的 {QRC_FILE}...")
    logger.info("每当该文件被修改并保存，脚本将自动重新编译。")
    logger.info("按 Ctrl+C 停止监控。")

    try:
        while True:
            time.sleep(1)  # 保持主线程运行
    except KeyboardInterrupt:
        observer.stop()
        logger.info("监控已停止。")
    finally:
        observer.join()

if __name__ == "__main__":
    # 脚本启动时先检查并编译一次，确保资源文件是最新的
    if os.path.exists(QRC_FILE):
        logger.info("启动时检测到资源文件，执行首次编译...")
        handler = ResourceChangeHandler()
        handler.compile_resource()
    else:
        logger.warning(f"未找到资源文件 {QRC_FILE}，请确保路径正确。监控将继续，一旦该文件被创建即会触发编译。")

    start_monitoring()