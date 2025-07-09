"""
商业化平台模块

提供完整的商业化功能，包括：
- 收入模式管理
- 订阅服务
- 企业销售
- 合作伙伴管理
- 市场运营
"""

from .revenue_model_manager import RevenueModelManager
from .subscription_service import SubscriptionService
from .enterprise_sales import EnterpriseSales
from .partner_management import PartnerManagement
from .market_operations import MarketOperations
from .commercialization_platform import CommercializationPlatform

__all__ = [
    'RevenueModelManager',
    'SubscriptionService',
    'EnterpriseSales',
    'PartnerManagement',
    'MarketOperations',
    'CommercializationPlatform'
]

__version__ = "1.0.0"

