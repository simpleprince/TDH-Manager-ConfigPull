#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TDH自动登录脚本
实现与Java项目相同的登录功能和API调用
增强版：包含爬取正在运行服务的配置功能，主要输出为CSV格式
新增：数据库连接和配置更新功能
支持配置文件，开箱即用
"""

import requests
import json
import urllib3
import ssl
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context
import logging
from typing import Dict, List, Optional, Any
import time
import os
import yaml
from datetime import datetime
import csv
import pymysql
from pymysql.cursors import DictCursor
import threading
import schedule

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理类"""
    
    def __init__(self, config_file: str = "config.yaml"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """加载配置文件"""
        try:
            if not os.path.exists(self.config_file):
                logger.error(f"配置文件 {self.config_file} 不存在")
                raise FileNotFoundError(f"配置文件 {self.config_file} 不存在")
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            logger.info(f"配置文件 {self.config_file} 加载成功")
            return config
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
            raise
    
    def get_tdh_config(self) -> Dict:
        """获取TDH配置"""
        return self.config.get('tdh', {})
    
    def get_database_config(self) -> Dict:
        """获取数据库配置"""
        return self.config.get('database', {})
    
    def get_output_config(self) -> Dict:
        """获取输出配置"""
        return self.config.get('output', {})
    
    def get_scheduler_config(self) -> Dict:
        """获取定时任务配置"""
        return self.config.get('scheduler', {})
    
    def get_request_config(self) -> Dict:
        """获取请求配置"""
        return self.config.get('request', {})
    
    def get_features_config(self) -> Dict:
        """获取功能开关配置"""
        return self.config.get('features', {})


class SSLAdapter(HTTPAdapter):
    """自定义SSL适配器，跳过SSL证书验证"""
    
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        kwargs['ssl_context'] = context
        return super(SSLAdapter, self).init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        context = create_urllib3_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        kwargs['ssl_context'] = context
        return super(SSLAdapter, self).proxy_manager_for(*args, **kwargs)


class DatabaseManager:
    """数据库管理类，实现与Java项目相同的数据库操作"""
    
    def __init__(self, config_manager: ConfigManager):
        db_config = config_manager.get_database_config()
        self.host = db_config.get('host', 'localhost')
        self.port = db_config.get('port', 3306)
        self.database = db_config.get('database', 'config')
        self.username = db_config.get('username', 'root')
        self.password = db_config.get('password', '')
        self.connection = None
    
    def connect(self) -> bool:
        """连接数据库"""
        try:
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.username,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                cursorclass=DictCursor,
                autocommit=True
            )
            logger.info("数据库连接成功")
            return True
        except Exception as e:
            logger.error(f"数据库连接失败: {str(e)}")
            return False
    
    def disconnect(self):
        """断开数据库连接"""
        if self.connection:
            self.connection.close()
            logger.info("数据库连接已断开")
    
    def save_service(self, service_version: str, service_type: str) -> Optional[int]:
        """
        保存服务信息到数据库
        
        Args:
            service_version: 服务版本
            service_type: 服务类型
            
        Returns:
            int: 服务ID，失败返回None
        """
        try:
            if not self.connection:
                logger.error("数据库未连接")
                return None
            
            with self.connection.cursor() as cursor:
                # 先尝试插入
                sql = """
                INSERT INTO services (service_version, service_type) 
                VALUES (%s, %s)
                """
                cursor.execute(sql, (service_version, service_type))
                service_id = cursor.lastrowid
                logger.info(f"服务保存成功，ID: {service_id}")
                return service_id
                
        except Exception as e:
            # 检查是否是唯一约束冲突
            if "Duplicate entry" in str(e) and "services.services_pk" in str(e):
                logger.info(f"服务已存在，完全忽略: {service_version}, {service_type}")
                return None  # 返回None，表示不处理此服务
            else:
                logger.error(f"保存服务信息失败: {str(e)}")
                return None
    
    def save_pull_config(self, service_id: int, config_data: Dict) -> bool:
        """
        保存配置信息到数据库
        
        Args:
            service_id: 服务ID
            config_data: 配置数据
            
        Returns:
            bool: 保存是否成功
        """
        try:
            if not self.connection:
                logger.error("数据库未连接")
                return False
            
            with self.connection.cursor() as cursor:
                sql = """
                INSERT INTO pull_config 
                (service_id, is_support_multi_instances, name, visibility, config_file, 
                 description, recommended_value, value, `values`) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                # 处理values字段，如果是列表则转换为JSON字符串，否则存[]
                values = config_data.get('values', [])
                if not values:
                    values_str = '[]'
                elif isinstance(values, list):
                    values_str = json.dumps(values, ensure_ascii=False)
                else:
                    values_str = str(values)

                cursor.execute(sql, (
                    service_id,
                    config_data.get('isSupportedMultiInstances', False),
                    config_data.get('name', ''),
                    config_data.get('visibility', ''),
                    config_data.get('configFile', ''),
                    config_data.get('description', ''),
                    config_data.get('recommendedValue', ''),
                    config_data.get('value', ''),
                    values_str,
                ))
                
                logger.info(f"配置保存成功: {config_data.get('name', 'Unknown')}")
                return True
                
        except Exception as e:
            # 检查是否是唯一约束冲突（如果pull_config表有唯一约束）
            if "Duplicate entry" in str(e):
                logger.info(f"配置已存在，忽略: {config_data.get('name', 'Unknown')} (service_id: {service_id})")
                return True  # 返回True表示"处理成功"，只是忽略而已
            else:
                logger.error(f"保存配置信息失败: {str(e)}")
                return False
    
    def clear_old_data(self):
        """清空旧数据（可选，用于完全重新同步）"""
        try:
            if not self.connection:
                logger.error("数据库未连接")
                return
            
            with self.connection.cursor() as cursor:
                cursor.execute("DELETE FROM pull_config")
                cursor.execute("DELETE FROM services")
                logger.info("旧数据已清空")
                
        except Exception as e:
            logger.error(f"清空旧数据失败: {str(e)}")


class TDHAutoLogin:
    """TDH自动登录类"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        
        # 获取配置
        tdh_config = config_manager.get_tdh_config()
        output_config = config_manager.get_output_config()
        request_config = config_manager.get_request_config()
        
        self.base_url = tdh_config.get('base_url', 'https://localhost:8180')
        self.username = tdh_config.get('username', 'admin')
        self.password = tdh_config.get('password', 'admin')
        self.cluster_id = tdh_config.get('cluster_id', 1)
        
        self.session = requests.Session()
        
        # 配置SSL适配器
        adapter = SSLAdapter()
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        # 设置请求头
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        self.is_logged_in = False
        
        # 创建输出目录
        self.output_dir = output_config.get('output_dir', 'tdh_configs')
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # 为每次爬取创建独立的时间戳文件夹
        self.session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_output_dir = os.path.join(self.output_dir, f"crawl_{self.session_timestamp}")
        if not os.path.exists(self.session_output_dir):
            os.makedirs(self.session_output_dir)
        
        # 初始化数据库管理器
        self.db_manager = DatabaseManager(config_manager)
        
        # 配置参数
        self.save_config_file = output_config.get('save_config_file', True)
        self.verbose_logging = output_config.get('verbose_logging', True)
        self.timeout = request_config.get('timeout', 30)
        self.delay = request_config.get('delay', 0.5)
        self.max_retries = request_config.get('max_retries', 3)
        
        # 设置日志级别
        if self.verbose_logging:
            logging.getLogger().setLevel(logging.INFO)
        else:
            logging.getLogger().setLevel(logging.WARNING)
    
    def login(self, username: str = None, password: str = None) -> bool:
        """
        登录TDH系统
        
        Args:
            username: 用户名（可选，默认使用配置文件中的用户名）
            password: 密码（可选，默认使用配置文件中的密码）
            
        Returns:
            bool: 登录是否成功
        """
        # 使用配置文件中的用户名和密码作为默认值
        if username is None:
            username = self.username
        if password is None:
            password = self.password
            
        try:
            login_url = f"{self.base_url}/api/users/login"
            
            login_data = {
                "userName": username,
                "userPassword": password,
                "captcha": "",
                "twoStepCode": ""
            }
            
            logger.info(f"正在登录用户: {username}")
            response = self.session.post(
                login_url,
                json=login_data,
                verify=False,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                logger.info("登录成功！")
                self.is_logged_in = True
                
                # 打印cookie信息
                cookies = self.session.cookies
                logger.info(f"获取到的cookies: {dict(cookies)}")
                
                return True
            else:
                logger.error(f"登录失败，状态码: {response.status_code}")
                logger.error(f"响应内容: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"登录过程中发生错误: {str(e)}")
            return False
    
    def get_endpoint(self) -> Optional[str]:
        """
        获取endpoint信息
        
        Returns:
            str: endpoint信息
        """
        try:
            endpoint_url = f"{self.base_url}/api/manager/aquila/endPoint"
            
            if not self.is_logged_in:
                logger.warning("未登录，无法获取endpoint")
                return None
            
            response = self.session.get(endpoint_url, verify=False, timeout=30)
            
            if response.status_code == 200:
                logger.info("成功获取endpoint信息")
                return response.text
            else:
                logger.error(f"获取endpoint失败，状态码: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"获取endpoint过程中发生错误: {str(e)}")
            return None
    
    def get_services(self, cluster_id: int = None) -> Optional[List[Dict]]:
        """
        获取服务列表
        
        Args:
            cluster_id: 集群ID（可选，默认使用配置文件中的集群ID）
            
        Returns:
            List[Dict]: 服务列表
        """
        if cluster_id is None:
            cluster_id = self.cluster_id
            
        try:
            services_url = f"{self.base_url}/api/services?clusterId={cluster_id}"
            
            if not self.is_logged_in:
                logger.warning("未登录，无法获取服务列表")
                return None
            
            response = self.session.get(services_url, verify=False, timeout=self.timeout)
            
            if response.status_code == 200:
                services = response.json()
                logger.info(f"成功获取到 {len(services)} 个服务")
                return services
            else:
                logger.error(f"获取服务列表失败，状态码: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"获取服务列表过程中发生错误: {str(e)}")
            return None
    
    def get_global_services(self) -> Optional[List[Dict]]:
        """
        获取全局服务列表
        
        Returns:
            List[Dict]: 全局服务列表
        """
        try:
            global_services_url = f"{self.base_url}/api/services?global=true"
            
            if not self.is_logged_in:
                logger.warning("未登录，无法获取全局服务列表")
                return None
            
            response = self.session.get(global_services_url, verify=False, timeout=30)
            
            if response.status_code == 200:
                services = response.json()
                logger.info(f"成功获取到 {len(services)} 个全局服务")
                return services
            else:
                logger.error(f"获取全局服务列表失败，状态码: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"获取全局服务列表过程中发生错误: {str(e)}")
            return None
    
    def get_service_configs(self, service_id: str) -> Optional[List[Dict]]:
        """
        获取服务配置
        
        Args:
            service_id: 服务ID
            
        Returns:
            List[Dict]: 服务配置列表
        """
        try:
            configs_url = f"{self.base_url}/api/services/{service_id}/configs?showPredefined=true&showCustom=false"
            
            if not self.is_logged_in:
                logger.warning("未登录，无法获取服务配置")
                return None
            
            response = self.session.get(configs_url, verify=False, timeout=30)
            
            if response.status_code == 200:
                configs = response.json()
                logger.info(f"成功获取到服务 {service_id} 的 {len(configs)} 个配置")
                return configs
            else:
                logger.error(f"获取服务配置失败，状态码: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"获取服务配置过程中发生错误: {str(e)}")
            return None
    
    def save_configs_to_csv(self, all_configs: List[Dict], filename: str = None) -> str:
        """
        将所有配置保存到CSV文件（主要输出格式）
        
        Args:
            all_configs: 所有配置列表
            filename: 文件名
            
        Returns:
            str: 保存的文件路径
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tdh_configs_{timestamp}.csv"
        
        filepath = os.path.join(self.session_output_dir, filename)
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:  # 使用utf-8-sig支持中文
                if all_configs:
                    # 定义CSV字段，确保包含所有可能的配置信息
                    fieldnames = [
                        'service_id', 'service_name', 'service_type', 'service_version',
                        'config_name', 'config_value', 'config_description', 'config_isSupportedMultiInstances',
                        'config_visibility', 'config_configFile',
                        'config_recommendedValue', 'config_values',
                        'timestamp', 'cluster_id'
                    ]
                    
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for config in all_configs:
                        # 确保所有字段都存在，不存在则设为空字符串
                        row = {}
                        for field in fieldnames:
                            row[field] = config.get(field, '')
                        writer.writerow(row)
            
            logger.info(f"配置已保存到CSV文件: {filepath}")
            logger.info(f"共保存 {len(all_configs)} 条配置记录")
            return filepath
            
        except Exception as e:
            logger.error(f"保存CSV文件时发生错误: {str(e)}")
            return ""
    
    def save_service_configs_to_file(self, service_name: str, configs: List[Dict], 
                                   service_info: Dict = None) -> str:
        """
        保存服务配置到JSON文件（备用格式）
        
        Args:
            service_name: 服务名称
            configs: 配置列表
            service_info: 服务信息
            
        Returns:
            str: 保存的文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{service_name}_{timestamp}.json"
        filepath = os.path.join(self.session_output_dir, filename)
        
        # 构建保存的数据结构
        save_data = {
            "service_name": service_name,
            "timestamp": timestamp,
            "configs_count": len(configs),
            "service_info": service_info,
            "configs": configs
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"配置已保存到JSON文件: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"保存配置到JSON文件时发生错误: {str(e)}")
            return ""
    
    def get_healthy_services(self, cluster_id: int = None) -> Optional[List[Dict]]:
        """
        获取健康状态的服务列表（包括运行中和已停止但健康的服务）
        
        Args:
            cluster_id: 集群ID（可选，默认使用配置文件中的集群ID）
            
        Returns:
            List[Dict]: 健康状态的服务列表
        """
        if cluster_id is None:
            cluster_id = self.cluster_id
            
        try:
            services = self.get_services(cluster_id)
            if not services:
                return None
            
            healthy_services = []
            for service in services:
                # 检查服务健康状态
                health = service.get('health', '')
                state = service.get('state', '')
                
                # 判断服务是否健康（包括运行中和已停止但健康的服务）
                if health == 'HEALTHY':
                    healthy_services.append(service)
                    logger.info(f"发现健康服务: {service.get('name', 'Unknown')} (状态: {state}, 健康: {health})")
            
            logger.info(f"总共发现 {len(healthy_services)} 个健康服务")
            return healthy_services
            
        except Exception as e:
            logger.error(f"获取健康服务列表时发生错误: {str(e)}")
            return None

    def crawl_healthy_services_configs(self, cluster_id: int = None) -> Dict[str, Any]:
        """
        爬取健康状态服务的配置，主要输出为CSV格式
        
        Args:
            cluster_id: 集群ID（可选，默认使用配置文件中的集群ID）
            
        Returns:
            Dict: 爬取结果
        """
        if cluster_id is None:
            cluster_id = self.cluster_id
            
        logger.info("开始爬取健康状态服务的配置...")
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "cluster_id": cluster_id,
            "healthy_services_count": 0,
            "total_configs": 0,
            "csv_file": "",
            "json_files": []
        }
        
        # 获取健康状态的服务
        healthy_services = self.get_healthy_services(cluster_id)
        if not healthy_services:
            logger.warning("没有找到健康状态的服务")
            return result
        
        result["healthy_services_count"] = len(healthy_services)
        all_configs = []
        
        for service in healthy_services:
            service_id = service.get('id')
            service_name = service.get('name', 'Unknown')
            service_type = service.get('type', 'Unknown')
            service_version = service.get('version', 'Unknown')
            
            logger.info(f"正在处理健康服务: {service_name}")
            
            # 获取服务配置
            configs = self.get_service_configs(service_id)
            if configs:
                result["total_configs"] += len(configs)
                
                # 为每个配置添加服务信息和时间戳
                for config in configs:
                    config_with_service = config.copy()
                    config_with_service.update({
                        "service_id": service_id,
                        "service_name": service_name,
                        "service_type": service_type,
                        "service_version": service_version,
                        "timestamp": datetime.now().isoformat(),
                        "cluster_id": cluster_id,
                        # 确保用户选中的配置字段被正确映射
                        "config_name": config.get('name', ''),
                        "config_value": config.get('value', ''),
                        "config_description": config.get('description', ''),
                        "config_isSupportedMultiInstances": config.get('isSupportedMultiInstances', 0) if config.get('isSupportedMultiInstances') is not None else 0,
                        "config_visibility": config.get('visibility', ''),
                        "config_configFile": config.get('configFile', ''),
                        "config_recommendedValue": config.get('recommendedValue', ''),
                        "config_values": str(config.get('values', '')) if config.get('values') else ''
                    })
                    all_configs.append(config_with_service)
                
                # 保存单个服务的配置到JSON文件（备用）
                if self.save_config_file:
                    saved_file = self.save_service_configs_to_file(
                        service_name, configs, service
                    )
                    if saved_file:
                        result["json_files"].append(saved_file)
            
            # 添加延迟避免请求过快
            time.sleep(self.delay)
        
        # 主要输出：保存所有配置到CSV文件
        if self.save_config_file and all_configs:
            csv_file = self.save_configs_to_csv(all_configs)
            if csv_file:
                result["csv_file"] = csv_file
                logger.info(f"主要输出：所有配置已保存到CSV文件: {csv_file}")
        
        logger.info(f"爬取完成！共处理 {len(healthy_services)} 个健康服务，获取 {result['total_configs']} 个配置")
        return result
    
    def update_database_with_configs(self, cluster_id: int = None, clear_old_data: bool = None) -> Dict[str, Any]:
        """
        将配置更新到数据库（实现与Java项目相同的功能）
        
        Args:
            cluster_id: 集群ID（可选，默认使用配置文件中的集群ID）
            clear_old_data: 是否清空旧数据（可选，默认使用配置文件中的设置）
            
        Returns:
            Dict: 更新结果
        """
        if cluster_id is None:
            cluster_id = self.cluster_id
        if clear_old_data is None:
            clear_old_data = self.config_manager.get_features_config().get('clear_old_data', False)
            
        logger.info("开始更新数据库配置...")
        
        # 连接数据库
        if not self.db_manager.connect():
            logger.error("数据库连接失败，无法更新配置")
            return {"success": False, "error": "数据库连接失败"}
        
        try:
            result = {
                "timestamp": datetime.now().isoformat(),
                "cluster_id": cluster_id,
                "services_updated": 0,
                "configs_updated": 0,
                "success": True
            }
            
            # 可选：清空旧数据
            if clear_old_data:
                self.db_manager.clear_old_data()
            
            # 处理集群服务
            services = self.get_services(cluster_id)
            if services:
                for service in services:
                    if service.get('health') != 'HEALTHY':
                        continue
                    
                    # 保存服务信息
                    service_id = self.db_manager.save_service(
                        service.get('version', ''),
                        service.get('type', '')
                    )
                    
                    if service_id:
                        result["services_updated"] += 1
                        
                        # 获取并保存配置
                        configs = self.get_service_configs(service.get('id'))
                        if configs:
                            for config in configs:
                                if self.db_manager.save_pull_config(service_id, config):
                                    result["configs_updated"] += 1
                        
                        logger.info(f"服务 {service.get('name', 'Unknown')} 配置更新完成")
            
            # 处理全局服务（根据配置决定）
            if self.config_manager.get_features_config().get('get_global_services', True):
                global_services = self.get_global_services()
                if global_services:
                    for service in global_services:
                        if service.get('health') != 'HEALTHY':
                            continue
                        
                        # 保存服务信息
                        service_id = self.db_manager.save_service(
                            service.get('version', ''),
                            service.get('type', '')
                        )
                        
                        if service_id:
                            result["services_updated"] += 1
                            
                            # 获取并保存配置
                            configs = self.get_service_configs(service.get('id'))
                            if configs:
                                for config in configs:
                                    if self.db_manager.save_pull_config(service_id, config):
                                        result["configs_updated"] += 1
                            
                            logger.info(f"全局服务 {service.get('name', 'Unknown')} 配置更新完成")
            
            logger.info(f"数据库更新完成！服务: {result['services_updated']}, 配置: {result['configs_updated']}")
            return result
            
        except Exception as e:
            logger.error(f"数据库更新过程中发生错误: {str(e)}")
            return {"success": False, "error": str(e)}
        
        finally:
            # 断开数据库连接
            self.db_manager.disconnect()
    
    def run_full_process(self, username: str = None, password: str = None, 
                        update_database: bool = None, save_config_file: bool = None) -> None:
        """
        运行完整的处理流程，主要输出为CSV格式，并可选择更新数据库
        
        Args:
            username: 用户名（可选，默认使用配置文件中的用户名）
            password: 密码（可选，默认使用配置文件中的密码）
            update_database: 是否更新数据库（可选，默认使用配置文件中的设置）
            save_config_file: 是否保存配置文件（可选，默认使用配置文件中的设置）
        """
        # 使用配置文件中的默认值
        if update_database is None:
            update_database = self.config_manager.get_features_config().get('update_database', True)
        if save_config_file is None:
            save_config_file = self.config_manager.get_output_config().get('save_config_file', True)
            
        logger.info("开始TDH自动登录和处理流程")
        
        # 1. 登录
        if not self.login(username, password):
            logger.error("登录失败，退出流程")
            return
        
        # 2. 爬取健康状态服务的配置（主要输出为CSV）
        logger.info("开始爬取健康状态服务的配置...")
        crawl_result = self.crawl_healthy_services_configs()
        
        # 3. 更新数据库（可选）
        if update_database:
            logger.info("开始更新数据库配置...")
            db_result = self.update_database_with_configs()
            if db_result.get("success"):
                logger.info(f"数据库更新成功！服务: {db_result.get('services_updated', 0)}, 配置: {db_result.get('configs_updated', 0)}")
            else:
                logger.error(f"数据库更新失败: {db_result.get('error', '未知错误')}")
        
        # 保存爬取结果摘要
        if save_config_file:
            result_file = os.path.join(self.session_output_dir, f"crawl_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(crawl_result, f, indent=2, ensure_ascii=False)
            logger.info(f"爬取结果摘要已保存到: {result_file}")
        
        logger.info("TDH自动登录和处理流程完成")

    def get_session_output_dir(self) -> str:
        """
        获取当前会话的输出目录
        
        Returns:
            str: 当前会话的输出目录路径
        """
        return self.session_output_dir
    
    def run_scheduled_task(self, username: str = None, password: str = None, 
                          update_database: bool = None, save_config_file: bool = None):
        """
        运行定时任务（模拟Java项目的@Scheduled注解）
        
        Args:
            username: 用户名（可选，默认使用配置文件中的用户名）
            password: 密码（可选，默认使用配置文件中的密码）
            update_database: 是否更新数据库（可选，默认使用配置文件中的设置）
            save_config_file: 是否保存配置文件（可选，默认使用配置文件中的设置）
        """
        logger.info("执行定时任务...")
        self.run_full_process(username, password, update_database, save_config_file)


def run_scheduler(config_manager: ConfigManager):
    """
    运行定时调度器
    
    Args:
        config_manager: 配置管理器
    """
    scheduler_config = config_manager.get_scheduler_config()
    interval_minutes = scheduler_config.get('interval_minutes', 1)
    
    tdh = TDHAutoLogin(config_manager)
    
    # 设置定时任务
    schedule.every(interval_minutes).minutes.do(tdh.run_scheduled_task)
    
    logger.info(f"定时调度器已启动，每 {interval_minutes} 分钟执行一次")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次
    except KeyboardInterrupt:
        logger.info("定时调度器已停止")


def main():
    """主函数"""
    try:
        # 加载配置
        config_manager = ConfigManager()
        
        # 创建TDH自动登录实例
        tdh = TDHAutoLogin(config_manager)
        
        # 检查是否启用定时任务
        scheduler_config = config_manager.get_scheduler_config()
        if scheduler_config.get('enabled', False):
            # 运行定时调度器
            run_scheduler(config_manager)
        else:
            # 运行完整流程（包括数据库更新）
            tdh.run_full_process()
            
    except FileNotFoundError as e:
        logger.error(f"配置文件错误: {str(e)}")
        print(f"\n错误: {str(e)}")
        print("请确保 config.yaml 文件存在且格式正确")
    except Exception as e:
        logger.error(f"程序运行错误: {str(e)}")
        print(f"\n程序运行错误: {str(e)}")
        print("请检查配置文件和相关设置")


if __name__ == "__main__":
    main() 