#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境检查脚本
检查Python版本和依赖包是否满足要求
"""

import sys
import subprocess
import importlib
from typing import List, Tuple


def check_python_version() -> bool:
    """检查Python版本"""
    required_version = (3, 6)
    current_version = sys.version_info[:2]
    
    print(f"当前Python版本: {sys.version}")
    print(f"要求Python版本: {required_version[0]}.{required_version[1]}+")
    
    if current_version >= required_version:
        print("✓ Python版本检查通过")
        return True
    else:
        print("✗ Python版本不满足要求")
        return False


def check_package(package_name: str, import_name: str = None) -> bool:
    """检查单个包是否已安装"""
    if import_name is None:
        import_name = package_name
    
    try:
        importlib.import_module(import_name)
        print(f"✓ {package_name} 已安装")
        return True
    except ImportError:
        print(f"✗ {package_name} 未安装")
        return False


def install_package(package_name: str) -> bool:
    """安装包"""
    try:
        print(f"正在安装 {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"✓ {package_name} 安装成功")
        return True
    except subprocess.CalledProcessError:
        print(f"✗ {package_name} 安装失败")
        return False


def check_and_install_packages() -> bool:
    """检查并安装所需的包"""
    required_packages = [
        ("requests", "requests"),
        ("urllib3", "urllib3"),
        ("PyYAML", "yaml"),
        ("pymysql", "pymysql"),
        ("schedule", "schedule")
    ]
    
    print("\n检查依赖包...")
    missing_packages = []
    
    for package_name, import_name in required_packages:
        if not check_package(package_name, import_name):
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"\n发现 {len(missing_packages)} 个缺失的包:")
        for package in missing_packages:
            print(f"  - {package}")
        
        response = input("\n是否自动安装缺失的包? (y/n): ").lower().strip()
        if response in ['y', 'yes', '是']:
            for package in missing_packages:
                if not install_package(package):
                    return False
        else:
            print("请手动安装缺失的包:")
            print("pip install -r requirements.txt")
            return False
    else:
        print("✓ 所有依赖包检查通过")
    
    return True


def check_config_file() -> bool:
    """检查配置文件是否存在"""
    import os
    
    config_file = "config.yaml"
    if os.path.exists(config_file):
        print(f"✓ 配置文件 {config_file} 存在")
        return True
    else:
        print(f"✗ 配置文件 {config_file} 不存在")
        print("请确保 config.yaml 文件在当前目录下")
        return False


def main():
    """主函数"""
    print("=" * 50)
    print("TDH自动登录脚本 - 环境检查")
    print("=" * 50)
    
    all_passed = True
    
    # 检查Python版本
    if not check_python_version():
        all_passed = False
    
    # 检查依赖包
    if not check_and_install_packages():
        all_passed = False
    
    # 检查配置文件
    if not check_config_file():
        all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✓ 环境检查全部通过！可以运行脚本了")
        print("\n使用方法:")
        print("1. 修改 config.yaml 中的配置")
        print("2. 运行: python config.py")
    else:
        print("✗ 环境检查未通过，请解决上述问题后重试")
    print("=" * 50)


if __name__ == "__main__":
    main() 