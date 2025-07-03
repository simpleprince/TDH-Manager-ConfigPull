@echo off
chcp 65001 >nul
echo ========================================
echo TDH自动登录脚本 - 快速安装
echo ========================================

echo 正在检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.6+
    echo 下载地址: https://www.python.org/downloads/
    echo.
    echo 安装完成后请重新运行此脚本
    pause
    exit /b 1
)

echo Python环境检查通过
echo.

echo 正在安装依赖包...
pip install -r requirements.txt
if errorlevel 1 (
    echo 依赖包安装失败，请检查网络连接
    pause
    exit /b 1
)

echo 依赖包安装完成
echo.

echo 正在检查配置文件...
if not exist "config.yaml" (
    echo 配置文件不存在，正在创建示例配置...
    copy "config_example.yaml" "config.yaml" >nul
    echo 已创建 config.yaml 文件，请编辑此文件配置您的环境
) else (
    echo 配置文件已存在
)

echo.
echo ========================================
echo 安装完成！
echo ========================================
echo.
echo 下一步操作：
echo 1. 编辑 config.yaml 文件，配置您的TDH系统信息
echo 2. 运行 run.bat 启动脚本
echo.
pause 