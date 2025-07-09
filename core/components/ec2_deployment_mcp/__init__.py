"""
EC2 Deployment MCP - 简化的AWS EC2集成方案

基于SSH连接的EC2实例管理和部署系统
支持通过SSH密钥连接EC2实例并执行Linux命令
"""

__version__ = "1.0.0"
__author__ = "PowerAutomation Team"

from .ec2_ssh_connector import EC2SSHConnector
from .ec2_deployment_engine import EC2DeploymentEngine
from .ec2_monitor import EC2Monitor

__all__ = [
    "EC2SSHConnector",
    "EC2DeploymentEngine", 
    "EC2Monitor"
]

