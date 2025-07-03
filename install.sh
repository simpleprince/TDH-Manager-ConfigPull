#!/bin/bash

echo "========================================"
echo "TDH自动登录脚本 - 快速安装"
echo "========================================"

# 检查Python环境
echo "正在检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python 3.6+"
    echo "Ubuntu/Debian: sudo apt-get install python3 python3-pip"
    echo "CentOS/RHEL: sudo yum install python3 python3-pip"
    echo "macOS: brew install python3"
    exit 1
fi

echo "Python环境检查通过"
echo

# 安装依赖包
echo "正在安装依赖包..."
python3 -m pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "依赖包安装失败，请检查网络连接"
    exit 1
fi

echo "依赖包安装完成"
echo

# 检查配置文件
echo "正在检查配置文件..."
if [ ! -f "config.yaml" ]; then
    echo "配置文件不存在，正在创建示例配置..."
    cp "config_example.yaml" "config.yaml"
    echo "已创建 config.yaml 文件，请编辑此文件配置您的环境"
else
    echo "配置文件已存在"
fi

echo
echo "========================================"
echo "安装完成！"
echo "========================================"
echo
echo "下一步操作："
echo "1. 编辑 config.yaml 文件，配置您的TDH系统信息"
echo "2. 运行 ./run.sh 启动脚本"
echo 