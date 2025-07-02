# TDH Manager Config Pull

一个用于自动登录TDH Manager并拉取服务配置的Python脚本。

## 功能特性

- **自动登录**: 支持用户名密码登录TDH管理系统
- **配置拉取**: 自动获取健康状态服务的配置信息
- **多格式输出**: 支持CSV和JSON格式保存配置
- **数据库同步**: 可选择性将配置同步到MySQL数据库
- **定时任务**: 支持定时执行配置拉取任务
- **SSL支持**: 自动处理SSL证书验证问题

## 主要功能

### 1. 服务配置拉取
- 获取集群中所有健康状态的服务
- 拉取每个服务的详细配置信息
- 支持集群服务和全局服务

### 2. 数据输出
- **CSV格式**: 主要输出格式，包含所有配置信息
- **JSON格式**: 备用格式，按服务分别保存
- **数据库**: 可选择同步到MySQL数据库

### 3. 定时执行
- 支持定时任务调度
- 可配置执行间隔时间
- 自动重试和错误处理

## 环境要求

- Python 3.6+
- 网络连接到TDH管理系统
- MySQL数据库（可选）

## 依赖安装

```bash
pip install requests pymysql schedule
```

## 配置说明

在 `config.py` 中修改以下配置：

```python
# TDH系统配置
BASE_URL = "https://172.18.135.37:8180"
USERNAME = "admin"  # 替换为实际用户名
PASSWORD = "admin"  # 替换为实际密码

# 数据库配置（可选）
DB_HOST = "172.18.128.83"
DB_PORT = 3327
DB_NAME = "config"
DB_USER = "lmt"
DB_PASSWORD = "lmt@123"
```

## 运行方式

### 1. 单次执行

```bash
python config.py
```

### 2. 定时执行

脚本默认会启动定时调度器，每1分钟执行一次：

```python
# 在main()函数中已配置
run_scheduler(USERNAME, PASSWORD, update_database=True, interval_minutes=1)
```

### 3. 自定义执行

```python
from config import TDHAutoLogin

# 创建实例
tdh = TDHAutoLogin(save_config_file=True)

# 运行完整流程
tdh.run_full_process(
    username="admin",
    password="admin",
    update_database=True,    # 是否更新数据库
    save_config_file=True    # 是否保存配置文件
)
```

## 输出文件

### CSV文件
- 位置: `tdh_configs/crawl_YYYYMMDD_HHMMSS/tdh_configs_YYYYMMDD_HHMMSS.csv`
- 包含所有服务的配置信息，便于分析

### JSON文件
- 位置: `tdh_configs/crawl_YYYYMMDD_HHMMSS/`
- 按服务分别保存，包含详细的服务信息

### 数据库表
- `services`: 存储服务基本信息
- `pull_config`: 存储配置详细信息

## 日志输出

脚本会输出详细的执行日志，包括：
- 登录状态
- 服务发现过程
- 配置拉取进度
- 数据库操作结果
- 错误信息