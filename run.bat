@echo off
chcp 65001 >nul
echo ========================================
echo TDH自动登录脚本 - Windows启动器
echo ========================================

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.6+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查配置文件是否存在
if not exist "config.yaml" (
    echo 错误: 未找到配置文件 config.yaml
    echo 请确保配置文件在当前目录下
    pause
    exit /b 1
)

REM 运行环境检查
echo 正在检查环境...
python check_environment.py
if errorlevel 1 (
    echo 环境检查失败，请解决上述问题后重试
    pause
    exit /b 1
)

REM 运行主脚本
echo.
echo 开始运行TDH自动登录脚本...
python config.py

echo.
echo 脚本执行完成
pause 