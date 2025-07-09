"""
Claude MCP - 极简版本

专注做一件事：调用Claude API
遵循MCP设计原则：Simple, Single, Solid
"""

import asyncio
import aiohttp
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ClaudeMCP:
    """
    Claude MCP - 极简Claude API调用器
    
    职责：
    - 调用Claude API
    - 基础错误处理
    - 就这么简单！
    """
    
    def __init__(self, api_key: str):
        """
        初始化Claude MCP
        
        Args:
            api_key: Claude API密钥
        """
        if not api_key:
            raise ValueError("Claude API key is required")
            
        self.api_key = api_key
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.default_model = "claude-3-5-sonnet-20241022"
        
    async def call_claude(self, 
                         message: str, 
                         model: Optional[str] = None,
                         max_tokens: int = 4096,
                         temperature: float = 0.7,
                         system: Optional[str] = None) -> str:
        """
        调用Claude API - 核心功能
        
        Args:
            message: 用户消息
            model: 模型名称 (可选)
            max_tokens: 最大token数
            temperature: 温度参数
            system: 系统提示 (可选)
            
        Returns:
            Claude的响应文本
            
        Raises:
            Exception: API调用失败时
        """
        if not message.strip():
            raise ValueError("Message cannot be empty")
            
        # 使用默认模型
        if model is None:
            model = self.default_model
            
        # 构建请求头
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        # 构建请求数据
        data = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": message}]
        }
        
        # 添加系统提示
        if system:
            data["system"] = system
            
        try:
            # 发送请求
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=headers, json=data) as response:
                    response_text = await response.text()
                    
                    if response.status == 200:
                        result = json.loads(response_text)
                        # 提取响应内容
                        if "content" in result and result["content"]:
                            return result["content"][0]["text"]
                        else:
                            return ""
                    else:
                        # 记录错误并抛出异常
                        logger.error(f"Claude API error: {response.status}, {response_text}")
                        raise Exception(f"Claude API error: {response.status}")
                        
        except aiohttp.ClientError as e:
            logger.error(f"Network error calling Claude API: {str(e)}")
            raise Exception(f"Network error: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            raise Exception(f"Invalid response format: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise
            
    async def health_check(self) -> bool:
        """
        健康检查 - 测试API连接
        
        Returns:
            True if API is accessible, False otherwise
        """
        try:
            response = await self.call_claude("Hello", max_tokens=10)
            return len(response) > 0
        except Exception as e:
            logger.warning(f"Health check failed: {str(e)}")
            return False
            
    def get_info(self) -> Dict[str, Any]:
        """
        获取MCP信息
        
        Returns:
            MCP基本信息
        """
        return {
            "name": "claude_mcp",
            "version": "1.0.0",
            "description": "Simple Claude API MCP",
            "default_model": self.default_model,
            "capabilities": ["text_generation", "code_generation", "analysis"]
        }


# 便利函数
async def quick_call(api_key: str, message: str, **kwargs) -> str:
    """
    快速调用Claude API的便利函数
    
    Args:
        api_key: Claude API密钥
        message: 用户消息
        **kwargs: 其他参数
        
    Returns:
        Claude的响应
    """
    claude = ClaudeMCP(api_key)
    return await claude.call_claude(message, **kwargs)

