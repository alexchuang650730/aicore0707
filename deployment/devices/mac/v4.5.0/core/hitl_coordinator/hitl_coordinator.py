"""
HITL (Human-in-the-Loop) Coordinator for ClaudeEditor 4.5
人机协作决策协调器
"""

import asyncio
import logging
import json
import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class DecisionType(Enum):
    """决策类型"""
    CONFIRMATION = "confirmation"  # 确认操作
    SELECTION = "selection"       # 选择选项
    INPUT = "input"              # 输入参数
    APPROVAL = "approval"        # 审批流程

class DecisionStatus(Enum):
    """决策状态"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"

@dataclass
class HITLRequest:
    """HITL请求"""
    id: str
    operation: str
    description: str
    risk_level: RiskLevel
    decision_type: DecisionType
    context: Dict[str, Any]
    options: Optional[List[str]] = None
    timeout: int = 300  # 5分钟默认超时
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class HITLResponse:
    """HITL响应"""
    request_id: str
    status: DecisionStatus
    decision: Any
    reason: Optional[str] = None
    user_id: Optional[str] = None
    responded_at: datetime = None
    
    def __post_init__(self):
        if self.responded_at is None:
            self.responded_at = datetime.now()

class HITLCoordinator:
    """HITL协调器"""
    
    def __init__(self, claudeditor_context=None):
        self.context = claudeditor_context
        self.pending_requests: Dict[str, HITLRequest] = {}
        self.completed_requests: Dict[str, HITLResponse] = {}
        self.decision_handlers: Dict[str, Callable] = {}
        self.ui_callbacks: List[Callable] = []
        
        # 配置
        self.max_pending = 50
        self.max_history = 200
        self.auto_approve_low_risk = False
        
        # 统计
        self.total_requests = 0
        self.approved_count = 0
        self.rejected_count = 0
        self.timeout_count = 0
        
        logger.info("HITL协调器初始化完成")
    
    async def request_decision(
        self,
        operation: str,
        description: str,
        risk_level: RiskLevel,
        decision_type: DecisionType = DecisionType.CONFIRMATION,
        context: Dict[str, Any] = None,
        options: List[str] = None,
        timeout: int = 300
    ) -> HITLResponse:
        """请求人工决策"""
        
        # 创建请求
        request = HITLRequest(
            id=str(uuid.uuid4()),
            operation=operation,
            description=description,
            risk_level=risk_level,
            decision_type=decision_type,
            context=context or {},
            options=options,
            timeout=timeout
        )
        
        logger.info(f"创建HITL请求: {request.operation} (风险等级: {risk_level.value})")
        
        # 检查是否需要自动批准
        if await self._should_auto_approve(request):
            return HITLResponse(
                request_id=request.id,
                status=DecisionStatus.APPROVED,
                decision=True,
                reason="低风险操作自动批准"
            )
        
        # 添加到待处理队列
        self.pending_requests[request.id] = request
        self.total_requests += 1
        
        # 通知UI
        await self._notify_ui(request)
        
        # 等待决策
        try:
            response = await self._wait_for_decision(request)
            return response
        except asyncio.TimeoutError:
            # 超时处理
            response = HITLResponse(
                request_id=request.id,
                status=DecisionStatus.TIMEOUT,
                decision=False,
                reason="决策超时"
            )
            await self._complete_request(request.id, response)
            self.timeout_count += 1
            return response
    
    async def provide_decision(
        self,
        request_id: str,
        decision: Any,
        reason: str = None,
        user_id: str = None
    ) -> bool:
        """提供决策响应"""
        
        if request_id not in self.pending_requests:
            logger.warning(f"未找到待处理请求: {request_id}")
            return False
        
        request = self.pending_requests[request_id]
        
        # 验证决策
        if not await self._validate_decision(request, decision):
            logger.warning(f"无效决策: {decision}")
            return False
        
        # 创建响应
        status = DecisionStatus.APPROVED if decision else DecisionStatus.REJECTED
        if isinstance(decision, bool) and not decision:
            status = DecisionStatus.REJECTED
        elif decision is not None:
            status = DecisionStatus.APPROVED
        
        response = HITLResponse(
            request_id=request_id,
            status=status,
            decision=decision,
            reason=reason,
            user_id=user_id
        )
        
        # 完成请求
        await self._complete_request(request_id, response)
        
        # 更新统计
        if status == DecisionStatus.APPROVED:
            self.approved_count += 1
        elif status == DecisionStatus.REJECTED:
            self.rejected_count += 1
        
        logger.info(f"HITL决策完成: {request.operation} -> {status.value}")
        return True
    
    async def _should_auto_approve(self, request: HITLRequest) -> bool:
        """判断是否应该自动批准"""
        if not self.auto_approve_low_risk:
            return False
        
        # 只有低风险操作才考虑自动批准
        if request.risk_level != RiskLevel.LOW:
            return False
        
        # 检查操作类型
        safe_operations = {
            "read_file", "list_directory", "get_status",
            "view_logs", "check_health", "get_info"
        }
        
        return request.operation in safe_operations
    
    async def _notify_ui(self, request: HITLRequest):
        """通知UI有新的决策请求"""
        for callback in self.ui_callbacks:
            try:
                await callback(request)
            except Exception as e:
                logger.error(f"UI通知失败: {e}")
    
    async def _wait_for_decision(self, request: HITLRequest) -> HITLResponse:
        """等待决策响应"""
        start_time = time.time()
        
        while time.time() - start_time < request.timeout:
            # 检查是否已有响应
            if request.id in self.completed_requests:
                return self.completed_requests[request.id]
            
            # 短暂等待
            await asyncio.sleep(0.5)
        
        # 超时
        raise asyncio.TimeoutError()
    
    async def _validate_decision(self, request: HITLRequest, decision: Any) -> bool:
        """验证决策的有效性"""
        if request.decision_type == DecisionType.CONFIRMATION:
            return isinstance(decision, bool)
        
        elif request.decision_type == DecisionType.SELECTION:
            if request.options and decision not in request.options:
                return False
            return True
        
        elif request.decision_type == DecisionType.INPUT:
            return decision is not None
        
        elif request.decision_type == DecisionType.APPROVAL:
            return isinstance(decision, bool)
        
        return True
    
    async def _complete_request(self, request_id: str, response: HITLResponse):
        """完成请求处理"""
        if request_id in self.pending_requests:
            del self.pending_requests[request_id]
        
        self.completed_requests[request_id] = response
        
        # 限制历史记录大小
        if len(self.completed_requests) > self.max_history:
            oldest_id = min(self.completed_requests.keys(), 
                          key=lambda k: self.completed_requests[k].responded_at)
            del self.completed_requests[oldest_id]
    
    def register_ui_callback(self, callback: Callable):
        """注册UI回调"""
        self.ui_callbacks.append(callback)
    
    def get_pending_requests(self) -> List[HITLRequest]:
        """获取待处理请求"""
        return list(self.pending_requests.values())
    
    def get_request_history(self, limit: int = 50) -> List[HITLResponse]:
        """获取请求历史"""
        responses = list(self.completed_requests.values())
        responses.sort(key=lambda r: r.responded_at, reverse=True)
        return responses[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_requests": self.total_requests,
            "pending_count": len(self.pending_requests),
            "approved_count": self.approved_count,
            "rejected_count": self.rejected_count,
            "timeout_count": self.timeout_count,
            "approval_rate": (
                self.approved_count / max(1, self.total_requests - self.timeout_count)
            ) if self.total_requests > 0 else 0.0
        }
    
    async def cancel_request(self, request_id: str) -> bool:
        """取消请求"""
        if request_id not in self.pending_requests:
            return False
        
        response = HITLResponse(
            request_id=request_id,
            status=DecisionStatus.CANCELLED,
            decision=False,
            reason="用户取消"
        )
        
        await self._complete_request(request_id, response)
        return True
    
    def configure(self, **kwargs):
        """配置协调器"""
        if "auto_approve_low_risk" in kwargs:
            self.auto_approve_low_risk = kwargs["auto_approve_low_risk"]
        
        if "max_pending" in kwargs:
            self.max_pending = kwargs["max_pending"]
        
        if "max_history" in kwargs:
            self.max_history = kwargs["max_history"]
        
        logger.info(f"HITL协调器配置更新: {kwargs}")

# ClaudeEditor集成接口
class ClaudeEditorHITLIntegration:
    """ClaudeEditor HITL集成"""
    
    def __init__(self, claudeditor_context=None):
        self.context = claudeditor_context
        self.coordinator = HITLCoordinator(claudeditor_context)
        
        # 注册UI回调
        self.coordinator.register_ui_callback(self._handle_ui_notification)
    
    async def _handle_ui_notification(self, request: HITLRequest):
        """处理UI通知"""
        if self.context and hasattr(self.context, 'show_hitl_request'):
            await self.context.show_hitl_request(request)
    
    async def request_confirmation(
        self,
        operation: str,
        description: str,
        risk_level: RiskLevel = RiskLevel.MEDIUM
    ) -> bool:
        """请求确认"""
        response = await self.coordinator.request_decision(
            operation=operation,
            description=description,
            risk_level=risk_level,
            decision_type=DecisionType.CONFIRMATION
        )
        
        return response.status == DecisionStatus.APPROVED
    
    async def request_selection(
        self,
        operation: str,
        description: str,
        options: List[str],
        risk_level: RiskLevel = RiskLevel.MEDIUM
    ) -> Optional[str]:
        """请求选择"""
        response = await self.coordinator.request_decision(
            operation=operation,
            description=description,
            risk_level=risk_level,
            decision_type=DecisionType.SELECTION,
            options=options
        )
        
        if response.status == DecisionStatus.APPROVED:
            return response.decision
        return None
    
    def get_coordinator(self) -> HITLCoordinator:
        """获取协调器实例"""
        return self.coordinator

