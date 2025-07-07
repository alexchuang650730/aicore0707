"""
PowerAutomation 4.0 Claude Client
Claude API客户端，支持异步通信和并行处理
"""

import asyncio
import logging
import aiohttp
import json
from typing import Dict, List, Any, Optional, AsyncGenerator
from dataclasses import dataclass
import time

from core.config import get_config


@dataclass
class Message:
    """消息数据类"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


@dataclass
class ConversationContext:
    """对话上下文数据类"""
    conversation_id: str
    messages: List[Message]
    system_prompt: Optional[str] = None
    model: str = "claude-3-sonnet-20240229"
    max_tokens: int = 4000
    temperature: float = 0.7


class ClaudeClient:
    """Claude API客户端类"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = logging.getLogger(__name__)
        self.api_key = self.config.claude_api_key
        self.base_url = "https://api.anthropic.com/v1"
        self.session: Optional[aiohttp.ClientSession] = None
        
        # 请求限制和重试
        self.max_retries = 3
        self.retry_delay = 1.0
        self.request_timeout = 30.0
        
        # 统计信息
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens": 0
        }
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
    
    async def initialize(self):
        """初始化客户端"""
        if not self.api_key:
            raise ValueError("Claude API密钥未配置")
        
        # 创建HTTP会话
        timeout = aiohttp.ClientTimeout(total=self.request_timeout)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01"
            }
        )
        
        self.logger.info("Claude客户端已初始化")
    
    async def close(self):
        """关闭客户端"""
        if self.session:
            await self.session.close()
            self.session = None
        
        self.logger.info("Claude客户端已关闭")
    
    async def send_message(
        self,
        message: str,
        context: ConversationContext,
        stream: bool = False
    ) -> Dict[str, Any]:
        """发送消息到Claude"""
        if not self.session:
            await self.initialize()
        
        # 添加用户消息到上下文
        user_message = Message(role="user", content=message)
        context.messages.append(user_message)
        
        # 构建请求数据
        request_data = {
            "model": context.model,
            "max_tokens": context.max_tokens,
            "temperature": context.temperature,
            "messages": [
                {"role": msg.role, "content": msg.content}
                for msg in context.messages
            ]
        }
        
        if context.system_prompt:
            request_data["system"] = context.system_prompt
        
        if stream:
            request_data["stream"] = True
        
        # 发送请求
        try:
            self.stats["total_requests"] += 1
            
            if stream:
                return await self._send_streaming_request(request_data, context)
            else:
                return await self._send_regular_request(request_data, context)
                
        except Exception as e:
            self.stats["failed_requests"] += 1
            self.logger.error(f"发送消息失败: {e}")
            raise
    
    async def _send_regular_request(
        self,
        request_data: Dict[str, Any],
        context: ConversationContext
    ) -> Dict[str, Any]:
        """发送常规请求"""
        for attempt in range(self.max_retries):
            try:
                async with self.session.post(
                    f"{self.base_url}/messages",
                    json=request_data
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        # 提取助手回复
                        assistant_content = result["content"][0]["text"]
                        assistant_message = Message(role="assistant", content=assistant_content)
                        context.messages.append(assistant_message)
                        
                        # 更新统计信息
                        self.stats["successful_requests"] += 1
                        if "usage" in result:
                            self.stats["total_tokens"] += result["usage"].get("total_tokens", 0)
                        
                        return {
                            "success": True,
                            "content": assistant_content,
                            "usage": result.get("usage", {}),
                            "conversation_id": context.conversation_id
                        }
                    
                    elif response.status == 429:  # Rate limit
                        if attempt < self.max_retries - 1:
                            wait_time = self.retry_delay * (2 ** attempt)
                            self.logger.warning(f"请求限制，等待 {wait_time} 秒后重试")
                            await asyncio.sleep(wait_time)
                            continue
                    
                    # 其他错误
                    error_text = await response.text()
                    raise Exception(f"API请求失败: {response.status} - {error_text}")
                    
            except asyncio.TimeoutError:
                if attempt < self.max_retries - 1:
                    self.logger.warning(f"请求超时，重试第 {attempt + 1} 次")
                    await asyncio.sleep(self.retry_delay)
                    continue
                raise Exception("请求超时")
            
            except Exception as e:
                if attempt < self.max_retries - 1:
                    self.logger.warning(f"请求失败，重试第 {attempt + 1} 次: {e}")
                    await asyncio.sleep(self.retry_delay)
                    continue
                raise
        
        raise Exception("达到最大重试次数")
    
    async def _send_streaming_request(
        self,
        request_data: Dict[str, Any],
        context: ConversationContext
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """发送流式请求"""
        try:
            async with self.session.post(
                f"{self.base_url}/messages",
                json=request_data
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"流式请求失败: {response.status} - {error_text}")
                
                assistant_content = ""
                
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    
                    if line.startswith('data: '):
                        data_str = line[6:]  # 移除 'data: ' 前缀
                        
                        if data_str == '[DONE]':
                            break
                        
                        try:
                            data = json.loads(data_str)
                            
                            if data.get("type") == "content_block_delta":
                                delta = data.get("delta", {})
                                if "text" in delta:
                                    text_chunk = delta["text"]
                                    assistant_content += text_chunk
                                    
                                    yield {
                                        "type": "chunk",
                                        "content": text_chunk,
                                        "conversation_id": context.conversation_id
                                    }
                            
                        except json.JSONDecodeError:
                            continue
                
                # 添加完整的助手回复到上下文
                if assistant_content:
                    assistant_message = Message(role="assistant", content=assistant_content)
                    context.messages.append(assistant_message)
                
                self.stats["successful_requests"] += 1
                
                yield {
                    "type": "complete",
                    "content": assistant_content,
                    "conversation_id": context.conversation_id
                }
                
        except Exception as e:
            self.stats["failed_requests"] += 1
            self.logger.error(f"流式请求失败: {e}")
            raise
    
    async def create_conversation_context(
        self,
        conversation_id: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> ConversationContext:
        """创建对话上下文"""
        return ConversationContext(
            conversation_id=conversation_id,
            messages=[],
            system_prompt=system_prompt,
            model=model or self.config.claude_model,
            max_tokens=max_tokens or self.config.claude_max_tokens
        )
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()


# 全局Claude客户端实例
_client: Optional[ClaudeClient] = None


async def get_claude_client() -> ClaudeClient:
    """获取全局Claude客户端实例"""
    global _client
    if _client is None:
        _client = ClaudeClient()
        await _client.initialize()
    return _client


async def close_claude_client():
    """关闭全局Claude客户端"""
    global _client
    if _client:
        await _client.close()
        _client = None

