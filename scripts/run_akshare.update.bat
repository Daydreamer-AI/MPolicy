@echo off
REM 自动检测并激活Python环境，然后运行AKShare数据更新脚本

SET SCRIPT_DIR=%~dp0
SET PROJECT_ROOT=%SCRIPT_DIR%..

REM 切换到项目根目录
cd /d "%PROJECT_ROOT%"

echo 检查MPolicy主程序是否正在运行...

REM 检查主程序是否正在运行
python scripts/check_process.py --quiet
if %ERRORLEVEL% EQU 1 (
    echo 错误: MPolicy主程序正在运行，无法执行更新任务!
    echo 请先关闭主程序再运行此脚本。
    if /I "%1" NEQ "--force" (
        pause
        exit /b 1
    ) else (
        echo 警告: 强制模式下继续执行...
    )
)

REM 检测conda环境
where conda >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo 检测到Conda环境...
    REM 激活默认conda环境（可以根据需要修改环境名）
    call conda activate base
    if ERRORLEVEL 1 (
        echo 警告: Conda环境激活失败，尝试使用系统Python
    ) else (
        echo Conda环境已激活
    )
) else (
    echo 未检测到Conda，检查虚拟环境...
    REM 检查venv环境
    if exist "%PROJECT_ROOT%\venv\Scripts\activate.bat" (
        echo 检测到venv虚拟环境...
        call "%PROJECT_ROOT%\venv\Scripts\activate.bat"
    ) else if exist "%PROJECT_ROOT%\env\Scripts\activate.bat" (
        echo 检测到env虚拟环境...
        call "%PROJECT_ROOT%\env\Scripts\activate.bat"
    ) else (
        echo 未检测到虚拟环境，使用系统Python
    )
)

REM 运行Python脚本
echo 开始执行AKShare板块数据更新...
python scripts/auto_update_akshare_board_data.py %*

REM 保持窗口打开以便查看结果（可选）
if %ERRORLEVEL% NEQ 0 (
    echo 脚本执行出现错误!
    pause
) else (
    echo 脚本执行完成!
)

exit /b %ERRORLEVEL%