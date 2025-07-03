# TDH自动登录脚本

一个用于自动登录TDH系统、爬取服务配置并更新数据库的Python脚本。

## 功能特性

- 自动登录TDH系统
- 爬取健康状态服务的配置信息
- 支持CSV和JSON格式输出
- 数据库配置更新
- 定时任务支持
- 配置文件驱动
- 环境检查和自动依赖安装
- 跨平台支持（Windows/Linux/Mac）

## 快速开始

### 1. 环境要求

- Python 3.6+
- 网络连接到TDH系统
- 数据库访问权限（可选）

### 2. 下载和安装

1. 下载项目文件到本地目录
2. 运行环境安装脚本：

**Windows:**
```bash
install.bat
```

**Linux/Mac:**
```bash
./install.sh
```

### 3. 配置

编辑 `config.yaml` 文件，根据您的环境修改配置：

```yaml
# TDH系统配置
tdh:
  base_url: "https://your-tdh-server:8180"  # 修改为您的TDH服务器地址
  username: "your-username"                 # 修改为您的用户名
  password: "your-password"                 # 修改为您的密码
  cluster_id: 1                             # 集群ID

# 数据库配置（可选）
database:
  host: "your-db-host"                      # 数据库主机
  port: 3306                                # 数据库端口
  database: "config"                        # 数据库名
  username: "your-db-user"                  # 数据库用户名
  password: "your-db-password"              # 数据库密码
```

### 4. 运行

**方法一：使用启动脚本（推荐）**

**Windows:**
```bash
run.bat
```

**Linux/Mac:**
```bash
./run.sh
```

**方法二：直接运行Python脚本**
```bash
python config.py
```

## 输出文件说明

### CSV文件
主要输出格式，包含所有配置信息的表格文件：
- `tdh_configs_YYYYMMDD_HHMMSS.csv`

### JSON文件
单个服务的详细配置信息：
- `{service_name}_YYYYMMDD_HHMMSS.json`

### 摘要文件
爬取结果统计信息：
- `crawl_summary_YYYYMMDD_HHMMSS.json`

## 定时任务

启用定时任务后，脚本会按照配置的时间间隔自动执行：

1. 修改 `config.yaml` 中的定时任务配置：
```yaml
scheduler:
  enabled: true                           # 启用定时任务
  interval_minutes: 5                     # 每5分钟执行一次
```

2. 运行脚本，它会持续运行并定时执行任务

3. 按 `Ctrl+C` 停止定时任务