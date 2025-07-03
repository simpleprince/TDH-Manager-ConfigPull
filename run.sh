#!/bin/bash

echo "========================================"
echo "TDH自动登录脚本 - Linux/Mac启动器"
echo "========================================"

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python 3.6+"
    echo "Ubuntu/Debian: sudo apt-get install python3 python3-pip"
    echo "CentOS/RHEL: sudo yum install python3 python3-pip"
    echo "macOS: brew install python3"
    exit 1
fi

# 检查配置文件是否存在
if [ ! -f "config.yaml" ]; then
    echo "错误: 未找到配置文件 config.yaml"
    echo "请确保配置文件在当前目录下"
    exit 1
fi

# 运行环境检查
echo "正在检查环境..."
python3 check_environment.py
if [ $? -ne 0 ]; then
    echo "环境检查失败，请解决上述问题后重试"
    exit 1
fi

# 运行主脚本
echo ""
echo "开始运行TDH自动登录脚本..."
python3 config.py

echo ""
echo "脚本执行完成" 