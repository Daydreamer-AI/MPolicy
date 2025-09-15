import argparse
import os
import subprocess
import sys
from pathlib import Path

def compile_qrc_file(qrc_file_path, output_file_path=None, compiler_type="auto"):
    """
    手动编译指定的 .qrc 文件
    
    :param qrc_file_path: .qrc 文件的路径
    :param output_file_path: 输出的 _rc.py 文件路径，默认为 None（自动生成）
    :param compiler_type: 编译器类型，'auto'（自动检测）, 'pyqt5', 'pyside6'
    :return: 布尔值，表示编译是否成功
    """
    # 检查 .qrc 文件是否存在
    if not os.path.exists(qrc_file_path):
        print(f"错误：未找到文件 {qrc_file_path}")
        return False
    
    # 确定输出文件路径
    if output_file_path is None:
        output_file_path = str(Path(qrc_file_path).with_name(Path(qrc_file_path).stem + "_rc.py"))
    
    # 确定编译器
    compiler = None
    if compiler_type == "auto":
        # 尝试自动检测可用的编译器
        for candidate in ["pyrcc5", "pyside6-rcc"]:
            try:
                subprocess.run([candidate, "--version"], capture_output=True, check=True)
                compiler = candidate
                break
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        
        if compiler is None:
            print("错误：未找到可用的资源编译器。请确保已安装 PyQt5 或 PySide6。")
            return False
    else:
        compiler_map = {
            "pyqt5": "pyrcc5",
            "pyside6": "pyside6-rcc"
        }
        compiler = compiler_map.get(compiler_type)
        if compiler is None:
            print(f"错误：不支持的编译器类型 '{compiler_type}'")
            return False
    
    # 执行编译命令
    compile_command = [compiler, qrc_file_path, "-o", output_file_path]
    
    try:
        print(f"正在编译 {qrc_file_path} -> {output_file_path}")
        print(f"执行命令: {' '.join(compile_command)}")
        
        result = subprocess.run(compile_command, check=True, capture_output=True, text=True)
        
        print("编译成功！")
        if result.stderr:
            print(f"编译器输出: {result.stderr}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"编译失败！退出码: {e.returncode}")
        if e.stderr:
            print(f"错误信息: {e.stderr}")
        return False
    except Exception as e:
        print(f"编译过程中发生未知错误: {e}")
        return False

def main():
    """命令行入口点"""
    parser = argparse.ArgumentParser(description="手动编译 Qt 资源文件 (.qrc)")
    parser.add_argument("qrc_file", help="要编译的 .qrc 文件路径")
    parser.add_argument("-o", "--output", help="输出的 _rc.py 文件路径")
    parser.add_argument("-c", "--compiler", choices=["auto", "pyqt5", "pyside6"], 
                       default="auto", help="编译器类型 (默认: auto)")
    
    args = parser.parse_args()
    
    success = compile_qrc_file(args.qrc_file, args.output, args.compiler)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()