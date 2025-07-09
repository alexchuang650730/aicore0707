#!/usr/bin/env python3
"""
集成API管理系统
PowerAutomation 4.1 - 企业级API管理和集成平台

功能特性:
- API网关和路由
- 认证和授权管理
- 限流和配额控制
- API监控和分析
- 自动文档生成
- 第三方系统集成
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import uuid
import hashlib
import hmac
import jwt
import time
from collections import defaultdict, deque
import aiohttp
import yaml
from urllib.parse import urlparse, parse_qs
import re

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIMethod(Enum):
    """API方法枚举"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"

class AuthType(Enum):
    """认证类型枚举"""
    NONE = "none"
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    BASIC_AUTH = "basic_auth"
    OAUTH2 = "oauth2"
    JWT = "jwt"
    CUSTOM = "custom"

class RateLimitType(Enum):
    """限流类型枚举"""
    PER_SECOND = "per_second"
    PER_MINUTE = "per_minute"
    PER_HOUR = "per_hour"
    PER_DAY = "per_day"
    CUSTOM = "custom"

class APIStatus(Enum):
    """API状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    MAINTENANCE = "maintenance"

class IntegrationType(Enum):
    """集成类型枚举"""
    REST_API = "rest_api"
    GRAPHQL = "graphql"
    WEBHOOK = "webhook"
    DATABASE = "database"
    MESSAGE_QUEUE = "message_queue"
    FILE_SYSTEM = "file_system"

@dataclass
class APIEndpoint:
    """API端点"""
    endpoint_id: str
    path: str
    method: APIMethod
    name: str
    description: str
    version: str = "v1"
    status: APIStatus = APIStatus.ACTIVE
    auth_type: AuthType = AuthType.API_KEY
    rate_limit: Optional[Dict[str, Any]] = None
    request_schema: Optional[Dict[str, Any]] = None
    response_schema: Optional[Dict[str, Any]] = None
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    handler: Optional[Callable] = None
    middleware: List[str] = field(default_factory=list)
    documentation: Dict[str, Any] = field(default_factory=dict)

@dataclass
class APIKey:
    """API密钥"""
    key_id: str
    api_key: str
    name: str
    description: str
    user_id: str
    permissions: List[str] = field(default_factory=list)
    rate_limits: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    is_active: bool = True
    last_used: Optional[datetime] = None
    usage_count: int = 0

@dataclass
class APIRequest:
    """API请求"""
    request_id: str
    endpoint_id: str
    method: str
    path: str
    headers: Dict[str, str]
    query_params: Dict[str, Any]
    body: Optional[str] = None
    user_id: Optional[str] = None
    api_key_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

@dataclass
class APIResponse:
    """API响应"""
    request_id: str
    status_code: int
    headers: Dict[str, str]
    body: Optional[str] = None
    response_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None

@dataclass
class RateLimit:
    """限流规则"""
    rule_id: str
    name: str
    description: str
    limit_type: RateLimitType
    limit_value: int
    window_size: int  # 时间窗口大小（秒）
    scope: str = "global"  # global, user, api_key, endpoint
    target: Optional[str] = None  # 具体的目标ID
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Integration:
    """第三方集成"""
    integration_id: str
    name: str
    description: str
    integration_type: IntegrationType
    config: Dict[str, Any]
    auth_config: Dict[str, Any] = field(default_factory=dict)
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    health_check_url: Optional[str] = None
    last_health_check: Optional[datetime] = None
    health_status: str = "unknown"

@dataclass
class Webhook:
    """Webhook配置"""
    webhook_id: str
    name: str
    url: str
    events: List[str]
    secret: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    retry_config: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_triggered: Optional[datetime] = None
    success_count: int = 0
    failure_count: int = 0

class APIIntegrationManager:
    """API集成管理器"""
    
    def __init__(self):
        self.endpoints: Dict[str, APIEndpoint] = {}
        self.api_keys: Dict[str, APIKey] = {}
        self.rate_limits: Dict[str, RateLimit] = {}
        self.integrations: Dict[str, Integration] = {}
        self.webhooks: Dict[str, Webhook] = {}
        
        # 请求和响应日志
        self.request_logs: deque = deque(maxlen=100000)
        self.response_logs: deque = deque(maxlen=100000)
        
        # 限流计数器
        self.rate_limit_counters: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.rate_limit_windows: Dict[str, datetime] = {}
        
        # 路由表
        self.route_table: Dict[str, Dict[str, APIEndpoint]] = defaultdict(dict)
        
        # 中间件
        self.middleware_registry: Dict[str, Callable] = {}
        
        # 监控统计
        self.api_stats = {
            "total_requests": 0,
            "total_responses": 0,
            "total_errors": 0,
            "average_response_time": 0.0,
            "active_endpoints": 0,
            "active_integrations": 0
        }
        
        # 初始化默认组件
        self._initialize_default_middleware()
        self._initialize_default_rate_limits()
        
        # 启动后台任务
        asyncio.create_task(self._start_background_tasks())
        
        logger.info("API集成管理器初始化完成")
    
    def _initialize_default_middleware(self):
        """初始化默认中间件"""
        self.middleware_registry.update({
            "cors": self._cors_middleware,
            "logging": self._logging_middleware,
            "auth": self._auth_middleware,
            "rate_limit": self._rate_limit_middleware,
            "validation": self._validation_middleware,
            "error_handler": self._error_handler_middleware
        })
    
    def _initialize_default_rate_limits(self):
        """初始化默认限流规则"""
        default_limits = [
            RateLimit("global_per_second", "全局每秒限制", "全局每秒请求限制", 
                     RateLimitType.PER_SECOND, 1000, 1, "global"),
            RateLimit("global_per_minute", "全局每分钟限制", "全局每分钟请求限制", 
                     RateLimitType.PER_MINUTE, 10000, 60, "global"),
            RateLimit("user_per_minute", "用户每分钟限制", "单用户每分钟请求限制", 
                     RateLimitType.PER_MINUTE, 1000, 60, "user"),
            RateLimit("api_key_per_hour", "API密钥每小时限制", "单API密钥每小时请求限制", 
                     RateLimitType.PER_HOUR, 10000, 3600, "api_key")
        ]
        
        for limit in default_limits:
            self.rate_limits[limit.rule_id] = limit
    
    async def _start_background_tasks(self):
        """启动后台任务"""
        # 统计更新任务
        asyncio.create_task(self._stats_update_task())
        
        # 限流计数器清理任务
        asyncio.create_task(self._rate_limit_cleanup_task())
        
        # 健康检查任务
        asyncio.create_task(self._health_check_task())
        
        # 日志清理任务
        asyncio.create_task(self._log_cleanup_task())
    
    async def _stats_update_task(self):
        """统计更新任务"""
        while True:
            try:
                await self._update_api_statistics()
                await asyncio.sleep(60)  # 每分钟更新一次
                
            except Exception as e:
                logger.error(f"统计更新任务失败: {e}")
                await asyncio.sleep(60)
    
    async def _rate_limit_cleanup_task(self):
        """限流计数器清理任务"""
        while True:
            try:
                current_time = datetime.now()
                
                # 清理过期的限流窗口
                expired_windows = []
                for window_key, window_time in self.rate_limit_windows.items():
                    if (current_time - window_time).total_seconds() > 3600:  # 1小时过期
                        expired_windows.append(window_key)
                
                for key in expired_windows:
                    del self.rate_limit_windows[key]
                    if key in self.rate_limit_counters:
                        del self.rate_limit_counters[key]
                
                await asyncio.sleep(300)  # 每5分钟清理一次
                
            except Exception as e:
                logger.error(f"限流清理任务失败: {e}")
                await asyncio.sleep(300)
    
    async def _health_check_task(self):
        """健康检查任务"""
        while True:
            try:
                for integration in self.integrations.values():
                    if integration.is_active and integration.health_check_url:
                        await self._check_integration_health(integration)
                
                await asyncio.sleep(300)  # 每5分钟检查一次
                
            except Exception as e:
                logger.error(f"健康检查任务失败: {e}")
                await asyncio.sleep(300)
    
    async def _log_cleanup_task(self):
        """日志清理任务"""
        while True:
            try:
                # 保持最近的日志记录
                max_logs = 100000
                
                if len(self.request_logs) > max_logs:
                    # 移除最旧的日志
                    for _ in range(len(self.request_logs) - max_logs):
                        self.request_logs.popleft()
                
                if len(self.response_logs) > max_logs:
                    for _ in range(len(self.response_logs) - max_logs):
                        self.response_logs.popleft()
                
                await asyncio.sleep(3600)  # 每小时清理一次
                
            except Exception as e:
                logger.error(f"日志清理任务失败: {e}")
                await asyncio.sleep(3600)
    
    async def register_endpoint(self, path: str, method: APIMethod, name: str,
                              description: str, handler: Callable,
                              auth_type: AuthType = AuthType.API_KEY,
                              rate_limit: Optional[Dict[str, Any]] = None,
                              middleware: Optional[List[str]] = None,
                              request_schema: Optional[Dict[str, Any]] = None,
                              response_schema: Optional[Dict[str, Any]] = None,
                              tags: Optional[List[str]] = None) -> str:
        """注册API端点"""
        try:
            endpoint_id = str(uuid.uuid4())
            
            endpoint = APIEndpoint(
                endpoint_id=endpoint_id,
                path=path,
                method=method,
                name=name,
                description=description,
                auth_type=auth_type,
                rate_limit=rate_limit,
                request_schema=request_schema,
                response_schema=response_schema,
                tags=tags or [],
                handler=handler,
                middleware=middleware or ["logging", "auth", "rate_limit", "validation"]
            )
            
            self.endpoints[endpoint_id] = endpoint
            self.route_table[path][method.value] = endpoint
            
            logger.info(f"API端点已注册: {method.value} {path} ({endpoint_id})")
            return endpoint_id
            
        except Exception as e:
            logger.error(f"注册API端点失败: {e}")
            raise
    
    async def create_api_key(self, name: str, description: str, user_id: str,
                           permissions: Optional[List[str]] = None,
                           rate_limits: Optional[Dict[str, Any]] = None,
                           expires_at: Optional[datetime] = None) -> str:
        """创建API密钥"""
        try:
            key_id = str(uuid.uuid4())
            api_key = self._generate_api_key()
            
            api_key_obj = APIKey(
                key_id=key_id,
                api_key=api_key,
                name=name,
                description=description,
                user_id=user_id,
                permissions=permissions or [],
                rate_limits=rate_limits or {},
                expires_at=expires_at
            )
            
            self.api_keys[key_id] = api_key_obj
            
            logger.info(f"API密钥已创建: {name} ({key_id})")
            return api_key
            
        except Exception as e:
            logger.error(f"创建API密钥失败: {e}")
            raise
    
    def _generate_api_key(self) -> str:
        """生成API密钥"""
        import secrets
        return f"pa_{secrets.token_urlsafe(32)}"
    
    async def process_request(self, method: str, path: str, headers: Dict[str, str],
                            query_params: Dict[str, Any], body: Optional[str] = None,
                            ip_address: Optional[str] = None) -> Dict[str, Any]:
        """处理API请求"""
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        try:
            # 查找匹配的端点
            endpoint = await self._find_endpoint(method, path)
            if not endpoint:
                return await self._create_error_response(
                    request_id, 404, "API端点不存在", start_time
                )
            
            # 创建请求对象
            api_request = APIRequest(
                request_id=request_id,
                endpoint_id=endpoint.endpoint_id,
                method=method,
                path=path,
                headers=headers,
                query_params=query_params,
                body=body,
                ip_address=ip_address,
                user_agent=headers.get("User-Agent")
            )
            
            # 记录请求
            self.request_logs.append(api_request)
            self.api_stats["total_requests"] += 1
            
            # 执行中间件链
            context = {
                "request": api_request,
                "endpoint": endpoint,
                "user_id": None,
                "api_key_id": None
            }
            
            for middleware_name in endpoint.middleware:
                if middleware_name in self.middleware_registry:
                    middleware_result = await self.middleware_registry[middleware_name](context)
                    if middleware_result.get("error"):
                        return await self._create_error_response(
                            request_id, 
                            middleware_result.get("status_code", 400),
                            middleware_result.get("message", "中间件错误"),
                            start_time
                        )
            
            # 执行端点处理器
            if endpoint.handler:
                try:
                    result = await endpoint.handler(api_request, context)
                    
                    response = await self._create_success_response(
                        request_id, result, start_time
                    )
                    
                    # 记录响应
                    api_response = APIResponse(
                        request_id=request_id,
                        status_code=response["status_code"],
                        headers=response["headers"],
                        body=json.dumps(response["data"]) if response.get("data") else None,
                        response_time=response["response_time"]
                    )
                    
                    self.response_logs.append(api_response)
                    self.api_stats["total_responses"] += 1
                    
                    return response
                    
                except Exception as handler_error:
                    logger.error(f"端点处理器错误: {handler_error}")
                    return await self._create_error_response(
                        request_id, 500, f"处理器错误: {str(handler_error)}", start_time
                    )
            else:
                return await self._create_error_response(
                    request_id, 501, "端点处理器未实现", start_time
                )
            
        except Exception as e:
            logger.error(f"处理API请求失败: {e}")
            self.api_stats["total_errors"] += 1
            return await self._create_error_response(
                request_id, 500, f"内部服务器错误: {str(e)}", start_time
            )
    
    async def _find_endpoint(self, method: str, path: str) -> Optional[APIEndpoint]:
        """查找匹配的端点"""
        try:
            # 精确匹配
            if path in self.route_table and method in self.route_table[path]:
                endpoint = self.route_table[path][method]
                if endpoint.status == APIStatus.ACTIVE:
                    return endpoint
            
            # 路径参数匹配
            for route_path, methods in self.route_table.items():
                if method in methods:
                    endpoint = methods[method]
                    if endpoint.status == APIStatus.ACTIVE and self._match_path_pattern(route_path, path):
                        return endpoint
            
            return None
            
        except Exception as e:
            logger.error(f"查找端点失败: {e}")
            return None
    
    def _match_path_pattern(self, pattern: str, path: str) -> bool:
        """匹配路径模式"""
        try:
            # 简化的路径匹配逻辑
            # 支持 {param} 格式的路径参数
            pattern_parts = pattern.split('/')
            path_parts = path.split('/')
            
            if len(pattern_parts) != len(path_parts):
                return False
            
            for pattern_part, path_part in zip(pattern_parts, path_parts):
                if pattern_part.startswith('{') and pattern_part.endswith('}'):
                    # 路径参数，跳过
                    continue
                elif pattern_part != path_part:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"路径匹配失败: {e}")
            return False
    
    async def _cors_middleware(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """CORS中间件"""
        try:
            # 简化的CORS处理
            return {"success": True}
            
        except Exception as e:
            logger.error(f"CORS中间件失败: {e}")
            return {"error": True, "message": "CORS处理失败"}
    
    async def _logging_middleware(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """日志中间件"""
        try:
            request = context["request"]
            endpoint = context["endpoint"]
            
            logger.info(f"API请求: {request.method} {request.path} - 端点: {endpoint.name}")
            return {"success": True}
            
        except Exception as e:
            logger.error(f"日志中间件失败: {e}")
            return {"error": True, "message": "日志记录失败"}
    
    async def _auth_middleware(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """认证中间件"""
        try:
            request = context["request"]
            endpoint = context["endpoint"]
            
            if endpoint.auth_type == AuthType.NONE:
                return {"success": True}
            
            elif endpoint.auth_type == AuthType.API_KEY:
                api_key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
                if not api_key:
                    return {"error": True, "status_code": 401, "message": "缺少API密钥"}
                
                # 验证API密钥
                api_key_obj = await self._validate_api_key(api_key)
                if not api_key_obj:
                    return {"error": True, "status_code": 401, "message": "无效的API密钥"}
                
                context["api_key_id"] = api_key_obj.key_id
                context["user_id"] = api_key_obj.user_id
                
                # 更新使用统计
                api_key_obj.last_used = datetime.now()
                api_key_obj.usage_count += 1
                
            elif endpoint.auth_type == AuthType.BEARER_TOKEN:
                auth_header = request.headers.get("Authorization", "")
                if not auth_header.startswith("Bearer "):
                    return {"error": True, "status_code": 401, "message": "缺少Bearer令牌"}
                
                token = auth_header[7:]  # 移除 "Bearer " 前缀
                
                # 验证令牌
                user_id = await self._validate_bearer_token(token)
                if not user_id:
                    return {"error": True, "status_code": 401, "message": "无效的Bearer令牌"}
                
                context["user_id"] = user_id
            
            elif endpoint.auth_type == AuthType.JWT:
                auth_header = request.headers.get("Authorization", "")
                if not auth_header.startswith("Bearer "):
                    return {"error": True, "status_code": 401, "message": "缺少JWT令牌"}
                
                token = auth_header[7:]
                
                # 验证JWT
                payload = await self._validate_jwt_token(token)
                if not payload:
                    return {"error": True, "status_code": 401, "message": "无效的JWT令牌"}
                
                context["user_id"] = payload.get("user_id")
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"认证中间件失败: {e}")
            return {"error": True, "status_code": 500, "message": "认证处理失败"}
    
    async def _rate_limit_middleware(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """限流中间件"""
        try:
            request = context["request"]
            endpoint = context["endpoint"]
            
            # 检查端点特定的限流
            if endpoint.rate_limit:
                if not await self._check_rate_limit(
                    f"endpoint_{endpoint.endpoint_id}",
                    endpoint.rate_limit
                ):
                    return {"error": True, "status_code": 429, "message": "请求频率超限"}
            
            # 检查全局限流
            for limit in self.rate_limits.values():
                if not limit.is_active:
                    continue
                
                limit_key = self._get_rate_limit_key(limit, context)
                if limit_key and not await self._check_rate_limit(limit_key, {
                    "type": limit.limit_type.value,
                    "limit": limit.limit_value,
                    "window": limit.window_size
                }):
                    return {"error": True, "status_code": 429, "message": f"超过{limit.name}限制"}
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"限流中间件失败: {e}")
            return {"error": True, "status_code": 500, "message": "限流检查失败"}
    
    async def _validation_middleware(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """验证中间件"""
        try:
            request = context["request"]
            endpoint = context["endpoint"]
            
            # 验证请求schema
            if endpoint.request_schema and request.body:
                try:
                    request_data = json.loads(request.body)
                    # 这里可以添加JSON Schema验证
                    # jsonschema.validate(request_data, endpoint.request_schema)
                except json.JSONDecodeError:
                    return {"error": True, "status_code": 400, "message": "无效的JSON格式"}
                except Exception as validation_error:
                    return {"error": True, "status_code": 400, "message": f"请求验证失败: {validation_error}"}
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"验证中间件失败: {e}")
            return {"error": True, "status_code": 500, "message": "请求验证失败"}
    
    async def _error_handler_middleware(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """错误处理中间件"""
        try:
            # 错误处理逻辑
            return {"success": True}
            
        except Exception as e:
            logger.error(f"错误处理中间件失败: {e}")
            return {"error": True, "status_code": 500, "message": "错误处理失败"}
    
    async def _validate_api_key(self, api_key: str) -> Optional[APIKey]:
        """验证API密钥"""
        try:
            for key_obj in self.api_keys.values():
                if key_obj.api_key == api_key and key_obj.is_active:
                    # 检查过期时间
                    if key_obj.expires_at and datetime.now() > key_obj.expires_at:
                        return None
                    return key_obj
            return None
            
        except Exception as e:
            logger.error(f"验证API密钥失败: {e}")
            return None
    
    async def _validate_bearer_token(self, token: str) -> Optional[str]:
        """验证Bearer令牌"""
        try:
            # 简化的令牌验证逻辑
            # 实际实现中应该验证令牌的有效性和获取用户ID
            if token.startswith("valid_"):
                return token.replace("valid_", "user_")
            return None
            
        except Exception as e:
            logger.error(f"验证Bearer令牌失败: {e}")
            return None
    
    async def _validate_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证JWT令牌"""
        try:
            # 简化的JWT验证逻辑
            # 实际实现中应该使用正确的密钥验证JWT
            try:
                payload = jwt.decode(token, "secret_key", algorithms=["HS256"])
                return payload
            except jwt.InvalidTokenError:
                return None
            
        except Exception as e:
            logger.error(f"验证JWT令牌失败: {e}")
            return None
    
    def _get_rate_limit_key(self, limit: RateLimit, context: Dict[str, Any]) -> Optional[str]:
        """获取限流键"""
        try:
            if limit.scope == "global":
                return f"global_{limit.rule_id}"
            elif limit.scope == "user" and context.get("user_id"):
                return f"user_{context['user_id']}_{limit.rule_id}"
            elif limit.scope == "api_key" and context.get("api_key_id"):
                return f"api_key_{context['api_key_id']}_{limit.rule_id}"
            elif limit.scope == "endpoint":
                endpoint = context.get("endpoint")
                if endpoint:
                    return f"endpoint_{endpoint.endpoint_id}_{limit.rule_id}"
            
            return None
            
        except Exception as e:
            logger.error(f"获取限流键失败: {e}")
            return None
    
    async def _check_rate_limit(self, limit_key: str, limit_config: Dict[str, Any]) -> bool:
        """检查限流"""
        try:
            current_time = datetime.now()
            window_size = limit_config.get("window", 60)
            limit_value = limit_config.get("limit", 100)
            
            # 获取或创建时间窗口
            if limit_key not in self.rate_limit_windows:
                self.rate_limit_windows[limit_key] = current_time
                self.rate_limit_counters[limit_key] = defaultdict(int)
            
            window_start = self.rate_limit_windows[limit_key]
            
            # 检查是否需要重置窗口
            if (current_time - window_start).total_seconds() >= window_size:
                self.rate_limit_windows[limit_key] = current_time
                self.rate_limit_counters[limit_key] = defaultdict(int)
                window_start = current_time
            
            # 检查当前计数
            current_count = self.rate_limit_counters[limit_key]["count"]
            
            if current_count >= limit_value:
                return False
            
            # 增加计数
            self.rate_limit_counters[limit_key]["count"] += 1
            return True
            
        except Exception as e:
            logger.error(f"检查限流失败: {e}")
            return True  # 出错时允许请求
    
    async def _create_success_response(self, request_id: str, data: Any, start_time: float) -> Dict[str, Any]:
        """创建成功响应"""
        response_time = (time.time() - start_time) * 1000  # 转换为毫秒
        
        return {
            "request_id": request_id,
            "status_code": 200,
            "headers": {
                "Content-Type": "application/json",
                "X-Request-ID": request_id,
                "X-Response-Time": f"{response_time:.2f}ms"
            },
            "data": data,
            "response_time": response_time,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _create_error_response(self, request_id: str, status_code: int, 
                                   message: str, start_time: float) -> Dict[str, Any]:
        """创建错误响应"""
        response_time = (time.time() - start_time) * 1000
        
        return {
            "request_id": request_id,
            "status_code": status_code,
            "headers": {
                "Content-Type": "application/json",
                "X-Request-ID": request_id,
                "X-Response-Time": f"{response_time:.2f}ms"
            },
            "error": {
                "code": status_code,
                "message": message
            },
            "response_time": response_time,
            "timestamp": datetime.now().isoformat()
        }
    
    async def create_integration(self, name: str, description: str, 
                               integration_type: IntegrationType,
                               config: Dict[str, Any], created_by: str,
                               auth_config: Optional[Dict[str, Any]] = None) -> str:
        """创建第三方集成"""
        try:
            integration_id = str(uuid.uuid4())
            
            integration = Integration(
                integration_id=integration_id,
                name=name,
                description=description,
                integration_type=integration_type,
                config=config,
                auth_config=auth_config or {},
                created_by=created_by
            )
            
            self.integrations[integration_id] = integration
            
            # 测试集成连接
            await self._test_integration(integration)
            
            logger.info(f"集成已创建: {name} ({integration_id})")
            return integration_id
            
        except Exception as e:
            logger.error(f"创建集成失败: {e}")
            raise
    
    async def _test_integration(self, integration: Integration):
        """测试集成连接"""
        try:
            if integration.integration_type == IntegrationType.REST_API:
                base_url = integration.config.get("base_url")
                if base_url:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f"{base_url}/health") as response:
                            if response.status == 200:
                                integration.health_status = "healthy"
                            else:
                                integration.health_status = "unhealthy"
                        
            elif integration.integration_type == IntegrationType.DATABASE:
                # 数据库连接测试
                integration.health_status = "healthy"  # 简化实现
                
            integration.last_health_check = datetime.now()
            
        except Exception as e:
            logger.error(f"测试集成连接失败: {e}")
            integration.health_status = "error"
    
    async def _check_integration_health(self, integration: Integration):
        """检查集成健康状态"""
        try:
            await self._test_integration(integration)
            
        except Exception as e:
            logger.error(f"检查集成健康状态失败: {e}")
            integration.health_status = "error"
    
    async def create_webhook(self, name: str, url: str, events: List[str],
                           secret: Optional[str] = None,
                           headers: Optional[Dict[str, str]] = None,
                           retry_config: Optional[Dict[str, Any]] = None) -> str:
        """创建Webhook"""
        try:
            webhook_id = str(uuid.uuid4())
            
            webhook = Webhook(
                webhook_id=webhook_id,
                name=name,
                url=url,
                events=events,
                secret=secret,
                headers=headers or {},
                retry_config=retry_config or {"max_retries": 3, "retry_delay": 5}
            )
            
            self.webhooks[webhook_id] = webhook
            
            logger.info(f"Webhook已创建: {name} ({webhook_id})")
            return webhook_id
            
        except Exception as e:
            logger.error(f"创建Webhook失败: {e}")
            raise
    
    async def trigger_webhook(self, event_type: str, data: Dict[str, Any]):
        """触发Webhook"""
        try:
            for webhook in self.webhooks.values():
                if webhook.is_active and event_type in webhook.events:
                    await self._send_webhook(webhook, event_type, data)
            
        except Exception as e:
            logger.error(f"触发Webhook失败: {e}")
    
    async def _send_webhook(self, webhook: Webhook, event_type: str, data: Dict[str, Any]):
        """发送Webhook"""
        try:
            payload = {
                "event": event_type,
                "data": data,
                "timestamp": datetime.now().isoformat(),
                "webhook_id": webhook.webhook_id
            }
            
            headers = webhook.headers.copy()
            headers["Content-Type"] = "application/json"
            
            # 添加签名
            if webhook.secret:
                signature = self._generate_webhook_signature(
                    json.dumps(payload), webhook.secret
                )
                headers["X-Webhook-Signature"] = signature
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook.url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        webhook.success_count += 1
                        webhook.last_triggered = datetime.now()
                    else:
                        webhook.failure_count += 1
                        logger.warning(f"Webhook发送失败: {webhook.name} - 状态码: {response.status}")
            
        except Exception as e:
            logger.error(f"发送Webhook失败: {e}")
            webhook.failure_count += 1
    
    def _generate_webhook_signature(self, payload: str, secret: str) -> str:
        """生成Webhook签名"""
        signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"
    
    async def generate_api_documentation(self) -> Dict[str, Any]:
        """生成API文档"""
        try:
            doc = {
                "openapi": "3.0.0",
                "info": {
                    "title": "PowerAutomation API",
                    "version": "4.1.0",
                    "description": "PowerAutomation 4.1 API文档"
                },
                "servers": [
                    {"url": "https://api.powerautomation.com/v1", "description": "生产环境"},
                    {"url": "https://api-staging.powerautomation.com/v1", "description": "测试环境"}
                ],
                "paths": {},
                "components": {
                    "securitySchemes": {
                        "ApiKeyAuth": {
                            "type": "apiKey",
                            "in": "header",
                            "name": "X-API-Key"
                        },
                        "BearerAuth": {
                            "type": "http",
                            "scheme": "bearer"
                        }
                    }
                }
            }
            
            # 生成路径文档
            for endpoint in self.endpoints.values():
                if endpoint.status == APIStatus.ACTIVE:
                    path_doc = {
                        "summary": endpoint.name,
                        "description": endpoint.description,
                        "tags": endpoint.tags,
                        "security": self._get_security_requirements(endpoint.auth_type),
                        "responses": {
                            "200": {
                                "description": "成功响应",
                                "content": {
                                    "application/json": {
                                        "schema": endpoint.response_schema or {"type": "object"}
                                    }
                                }
                            },
                            "400": {"description": "请求错误"},
                            "401": {"description": "认证失败"},
                            "429": {"description": "请求频率超限"},
                            "500": {"description": "服务器错误"}
                        }
                    }
                    
                    if endpoint.request_schema:
                        path_doc["requestBody"] = {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": endpoint.request_schema
                                }
                            }
                        }
                    
                    if endpoint.path not in doc["paths"]:
                        doc["paths"][endpoint.path] = {}
                    
                    doc["paths"][endpoint.path][endpoint.method.value.lower()] = path_doc
            
            return doc
            
        except Exception as e:
            logger.error(f"生成API文档失败: {e}")
            return {}
    
    def _get_security_requirements(self, auth_type: AuthType) -> List[Dict[str, List]]:
        """获取安全要求"""
        if auth_type == AuthType.API_KEY:
            return [{"ApiKeyAuth": []}]
        elif auth_type in [AuthType.BEARER_TOKEN, AuthType.JWT]:
            return [{"BearerAuth": []}]
        else:
            return []
    
    async def get_api_analytics(self, time_range: Optional[str] = "24h") -> Dict[str, Any]:
        """获取API分析数据"""
        try:
            current_time = datetime.now()
            
            # 确定时间范围
            if time_range == "1h":
                start_time = current_time - timedelta(hours=1)
            elif time_range == "24h":
                start_time = current_time - timedelta(hours=24)
            elif time_range == "7d":
                start_time = current_time - timedelta(days=7)
            elif time_range == "30d":
                start_time = current_time - timedelta(days=30)
            else:
                start_time = current_time - timedelta(hours=24)
            
            # 过滤日志
            filtered_requests = [
                req for req in self.request_logs
                if req.timestamp >= start_time
            ]
            
            filtered_responses = [
                resp for resp in self.response_logs
                if resp.timestamp >= start_time
            ]
            
            # 计算统计数据
            total_requests = len(filtered_requests)
            total_responses = len(filtered_responses)
            
            # 响应时间统计
            response_times = [resp.response_time for resp in filtered_responses if resp.response_time > 0]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # 状态码统计
            status_codes = defaultdict(int)
            for resp in filtered_responses:
                status_codes[resp.status_code] += 1
            
            # 端点使用统计
            endpoint_usage = defaultdict(int)
            for req in filtered_requests:
                endpoint_usage[req.endpoint_id] += 1
            
            # 错误率计算
            error_responses = len([resp for resp in filtered_responses if resp.status_code >= 400])
            error_rate = (error_responses / total_responses * 100) if total_responses > 0 else 0
            
            return {
                "time_range": time_range,
                "period": {
                    "start": start_time.isoformat(),
                    "end": current_time.isoformat()
                },
                "summary": {
                    "total_requests": total_requests,
                    "total_responses": total_responses,
                    "average_response_time": avg_response_time,
                    "error_rate": error_rate,
                    "success_rate": 100 - error_rate
                },
                "status_codes": dict(status_codes),
                "endpoint_usage": {
                    endpoint_id: {
                        "count": count,
                        "name": self.endpoints.get(endpoint_id, {}).name if endpoint_id in self.endpoints else "Unknown"
                    }
                    for endpoint_id, count in endpoint_usage.items()
                },
                "performance_metrics": {
                    "avg_response_time": avg_response_time,
                    "min_response_time": min(response_times) if response_times else 0,
                    "max_response_time": max(response_times) if response_times else 0,
                    "p95_response_time": np.percentile(response_times, 95) if response_times else 0,
                    "p99_response_time": np.percentile(response_times, 99) if response_times else 0
                }
            }
            
        except Exception as e:
            logger.error(f"获取API分析数据失败: {e}")
            return {}
    
    async def _update_api_statistics(self):
        """更新API统计"""
        try:
            self.api_stats["active_endpoints"] = len([
                ep for ep in self.endpoints.values() 
                if ep.status == APIStatus.ACTIVE
            ])
            
            self.api_stats["active_integrations"] = len([
                integration for integration in self.integrations.values()
                if integration.is_active
            ])
            
            # 计算平均响应时间
            recent_responses = list(self.response_logs)[-1000:]  # 最近1000个响应
            if recent_responses:
                response_times = [resp.response_time for resp in recent_responses if resp.response_time > 0]
                if response_times:
                    self.api_stats["average_response_time"] = sum(response_times) / len(response_times)
            
        except Exception as e:
            logger.error(f"更新API统计失败: {e}")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        try:
            return {
                "system_info": {
                    "version": "4.1.0",
                    "status": "healthy",
                    "uptime": "运行中",
                    "timestamp": datetime.now().isoformat()
                },
                "api_statistics": self.api_stats,
                "endpoints": {
                    "total": len(self.endpoints),
                    "active": len([ep for ep in self.endpoints.values() if ep.status == APIStatus.ACTIVE]),
                    "inactive": len([ep for ep in self.endpoints.values() if ep.status == APIStatus.INACTIVE]),
                    "deprecated": len([ep for ep in self.endpoints.values() if ep.status == APIStatus.DEPRECATED])
                },
                "api_keys": {
                    "total": len(self.api_keys),
                    "active": len([key for key in self.api_keys.values() if key.is_active])
                },
                "integrations": {
                    "total": len(self.integrations),
                    "active": len([integration for integration in self.integrations.values() if integration.is_active]),
                    "healthy": len([integration for integration in self.integrations.values() 
                                  if integration.health_status == "healthy"])
                },
                "webhooks": {
                    "total": len(self.webhooks),
                    "active": len([webhook for webhook in self.webhooks.values() if webhook.is_active])
                },
                "rate_limits": {
                    "total_rules": len(self.rate_limits),
                    "active_rules": len([limit for limit in self.rate_limits.values() if limit.is_active]),
                    "active_counters": len(self.rate_limit_counters)
                }
            }
            
        except Exception as e:
            logger.error(f"获取系统状态失败: {e}")
            return {}

# 示例使用
async def main():
    """示例主函数"""
    api_manager = APIIntegrationManager()
    
    # 示例端点处理器
    async def get_users_handler(request: APIRequest, context: Dict[str, Any]):
        return {
            "users": [
                {"id": 1, "name": "Alice", "email": "alice@example.com"},
                {"id": 2, "name": "Bob", "email": "bob@example.com"}
            ],
            "total": 2
        }
    
    async def create_user_handler(request: APIRequest, context: Dict[str, Any]):
        if request.body:
            user_data = json.loads(request.body)
            return {
                "id": 3,
                "name": user_data.get("name"),
                "email": user_data.get("email"),
                "created_at": datetime.now().isoformat()
            }
        return {"error": "Missing user data"}
    
    # 注册API端点
    await api_manager.register_endpoint(
        path="/users",
        method=APIMethod.GET,
        name="获取用户列表",
        description="获取所有用户的列表",
        handler=get_users_handler,
        tags=["users"]
    )
    
    await api_manager.register_endpoint(
        path="/users",
        method=APIMethod.POST,
        name="创建用户",
        description="创建新用户",
        handler=create_user_handler,
        tags=["users"],
        request_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string", "format": "email"}
            },
            "required": ["name", "email"]
        }
    )
    
    # 创建API密钥
    api_key = await api_manager.create_api_key(
        name="测试密钥",
        description="用于测试的API密钥",
        user_id="user123",
        permissions=["read_users", "create_users"]
    )
    
    print(f"API密钥: {api_key}")
    
    # 模拟API请求
    response = await api_manager.process_request(
        method="GET",
        path="/users",
        headers={"X-API-Key": api_key},
        query_params={}
    )
    
    print(f"API响应: {json.dumps(response, indent=2, ensure_ascii=False)}")
    
    # 生成API文档
    documentation = await api_manager.generate_api_documentation()
    print(f"API文档: {json.dumps(documentation, indent=2, ensure_ascii=False)}")
    
    # 获取API分析
    analytics = await api_manager.get_api_analytics()
    print(f"API分析: {json.dumps(analytics, indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    asyncio.run(main())

