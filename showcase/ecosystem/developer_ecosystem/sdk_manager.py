"""
SDK管理器模块

提供SDK的管理、分发和版本控制功能
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class SDKLanguage(Enum):
    """SDK语言枚举"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    CSHARP = "csharp"

@dataclass
class SDK:
    """SDK数据结构"""
    id: str
    name: str
    language: SDKLanguage
    version: str
    download_url: str
    documentation_url: str

class SDKManager:
    """SDK管理器"""
    
    def __init__(self):
        """初始化SDK管理器"""
        self.sdks: Dict[str, SDK] = {}
        self._initialize_default_sdks()
        logger.info("SDK管理器初始化完成")
    
    def _initialize_default_sdks(self):
        """初始化默认SDK"""
        default_sdks = [
            SDK(
                id="python_sdk",
                name="PowerAutomation Python SDK",
                language=SDKLanguage.PYTHON,
                version="1.0.0",
                download_url="https://pypi.org/project/powerautomation/",
                documentation_url="https://docs.powerautomation.com/python"
            ),
            SDK(
                id="js_sdk",
                name="PowerAutomation JavaScript SDK",
                language=SDKLanguage.JAVASCRIPT,
                version="1.0.0",
                download_url="https://npmjs.com/package/powerautomation",
                documentation_url="https://docs.powerautomation.com/javascript"
            )
        ]
        
        for sdk in default_sdks:
            self.sdks[sdk.id] = sdk
    
    async def get_sdk(self, sdk_id: str) -> Optional[SDK]:
        """
        获取SDK
        
        Args:
            sdk_id: SDK ID
            
        Returns:
            SDK对象
        """
        return self.sdks.get(sdk_id)
    
    async def list_sdks(self) -> List[SDK]:
        """
        列出所有SDK
        
        Returns:
            SDK列表
        """
        return list(self.sdks.values())
    
    async def download_sdk(self, sdk_id: str) -> Dict[str, Any]:
        """
        下载SDK
        
        Args:
            sdk_id: SDK ID
            
        Returns:
            下载信息
        """
        sdk = await self.get_sdk(sdk_id)
        if not sdk:
            return {"success": False, "error": "SDK不存在"}
        
        return {
            "success": True,
            "download_url": sdk.download_url,
            "documentation_url": sdk.documentation_url,
            "version": sdk.version
        }

