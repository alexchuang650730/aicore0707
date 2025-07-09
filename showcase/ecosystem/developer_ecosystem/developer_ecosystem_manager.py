"""
开发者生态系统管理器

统一管理开发者生态系统的各个组件，提供完整的开发者服务。
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import hashlib
from collections import defaultdict

logger = logging.getLogger(__name__)

class DeveloperTier(Enum):
    """开发者等级枚举"""
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    PARTNER = "partner"

class SDKLanguage(Enum):
    """SDK语言枚举"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CSHARP = "csharp"
    GO = "go"
    RUST = "rust"
    PHP = "php"
    RUBY = "ruby"
    SWIFT = "swift"

class PluginStatus(Enum):
    """插件状态枚举"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    PUBLISHED = "published"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"

class MarketplaceCategory(Enum):
    """市场分类枚举"""
    PRODUCTIVITY = "productivity"
    DEVELOPMENT = "development"
    AUTOMATION = "automation"
    INTEGRATION = "integration"
    ANALYTICS = "analytics"
    SECURITY = "security"
    COLLABORATION = "collaboration"
    UTILITIES = "utilities"

@dataclass
class Developer:
    """开发者数据结构"""
    id: str
    username: str
    email: str
    full_name: str
    tier: DeveloperTier
    api_key: str
    created_at: datetime
    last_active: datetime
    total_downloads: int
    total_revenue: float
    reputation_score: float
    verified: bool
    profile: Dict[str, Any]
    preferences: Dict[str, Any]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class SDK:
    """SDK数据结构"""
    id: str
    name: str
    language: SDKLanguage
    version: str
    description: str
    download_url: str
    documentation_url: str
    examples_url: str
    created_at: datetime
    updated_at: datetime
    download_count: int
    rating: float
    features: List[str]
    dependencies: List[str]
    changelog: List[Dict[str, Any]]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class Plugin:
    """插件数据结构"""
    id: str
    name: str
    developer_id: str
    category: MarketplaceCategory
    status: PluginStatus
    version: str
    description: str
    price: float
    download_count: int
    rating: float
    reviews_count: int
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]
    features: List[str]
    screenshots: List[str]
    documentation: str
    support_url: str
    license: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class MarketplaceTransaction:
    """市场交易数据结构"""
    id: str
    plugin_id: str
    buyer_id: str
    seller_id: str
    amount: float
    commission: float
    transaction_type: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class CommunityPost:
    """社区帖子数据结构"""
    id: str
    author_id: str
    title: str
    content: str
    category: str
    tags: List[str]
    upvotes: int
    downvotes: int
    replies_count: int
    views_count: int
    created_at: datetime
    updated_at: datetime
    is_pinned: bool
    is_locked: bool
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class DeveloperEcosystemManager:
    """开发者生态系统管理器核心类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化开发者生态系统管理器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.developers: Dict[str, Developer] = {}
        self.sdks: Dict[str, SDK] = {}
        self.plugins: Dict[str, Plugin] = {}
        self.transactions: Dict[str, MarketplaceTransaction] = {}
        self.community_posts: Dict[str, CommunityPost] = {}
        self.api_usage: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.revenue_sharing: Dict[str, float] = {}
        
        # 配置参数
        self.commission_rate = self.config.get('commission_rate', 0.3)  # 30%平台分成
        self.max_developers = self.config.get('max_developers', 100000)
        self.max_plugins_per_developer = self.config.get('max_plugins_per_developer', 50)
        self.api_rate_limits = self.config.get('api_rate_limits', {
            'starter': 1000,
            'professional': 10000,
            'enterprise': 100000,
            'partner': 1000000
        })
        
        # 收入分成配置
        self.revenue_sharing_tiers = {
            DeveloperTier.STARTER: 0.7,      # 开发者获得70%
            DeveloperTier.PROFESSIONAL: 0.75, # 开发者获得75%
            DeveloperTier.ENTERPRISE: 0.8,   # 开发者获得80%
            DeveloperTier.PARTNER: 0.85      # 开发者获得85%
        }
        
        # 事件回调
        self.event_callbacks: Dict[str, List[Callable]] = {
            'developer_registered': [],
            'plugin_published': [],
            'transaction_completed': [],
            'sdk_downloaded': [],
            'community_post_created': []
        }
        
        # 初始化SDK
        self._initialize_sdks()
        
        logger.info("开发者生态系统管理器初始化完成")
    
    async def register_developer(self,
                                username: str,
                                email: str,
                                full_name: str,
                                tier: DeveloperTier = DeveloperTier.STARTER,
                                profile: Dict[str, Any] = None) -> str:
        """
        注册开发者
        
        Args:
            username: 用户名
            email: 邮箱
            full_name: 全名
            tier: 开发者等级
            profile: 个人资料
            
        Returns:
            开发者ID
        """
        try:
            if len(self.developers) >= self.max_developers:
                raise ValueError(f"开发者数量已达上限: {self.max_developers}")
            
            # 检查用户名和邮箱唯一性
            for dev in self.developers.values():
                if dev.username == username:
                    raise ValueError(f"用户名已存在: {username}")
                if dev.email == email:
                    raise ValueError(f"邮箱已存在: {email}")
            
            developer_id = str(uuid.uuid4())
            api_key = self._generate_api_key(developer_id)
            
            developer = Developer(
                id=developer_id,
                username=username,
                email=email,
                full_name=full_name,
                tier=tier,
                api_key=api_key,
                created_at=datetime.now(),
                last_active=datetime.now(),
                total_downloads=0,
                total_revenue=0.0,
                reputation_score=50.0,  # 初始声誉分数
                verified=False,
                profile=profile or {},
                preferences={}
            )
            
            self.developers[developer_id] = developer
            
            # 触发事件回调
            await self._trigger_event('developer_registered', developer)
            
            logger.info(f"开发者注册成功: {developer_id} ({username})")
            return developer_id
            
        except Exception as e:
            logger.error(f"注册开发者失败: {e}")
            raise
    
    async def submit_plugin(self,
                           developer_id: str,
                           name: str,
                           category: MarketplaceCategory,
                           description: str,
                           price: float,
                           features: List[str],
                           documentation: str,
                           license: str = "MIT") -> str:
        """
        提交插件
        
        Args:
            developer_id: 开发者ID
            name: 插件名称
            category: 分类
            description: 描述
            price: 价格
            features: 功能列表
            documentation: 文档
            license: 许可证
            
        Returns:
            插件ID
        """
        try:
            if developer_id not in self.developers:
                raise ValueError(f"开发者不存在: {developer_id}")
            
            developer = self.developers[developer_id]
            
            # 检查插件数量限制
            developer_plugins = [p for p in self.plugins.values() if p.developer_id == developer_id]
            if len(developer_plugins) >= self.max_plugins_per_developer:
                raise ValueError(f"插件数量已达上限: {self.max_plugins_per_developer}")
            
            plugin_id = str(uuid.uuid4())
            
            plugin = Plugin(
                id=plugin_id,
                name=name,
                developer_id=developer_id,
                category=category,
                status=PluginStatus.SUBMITTED,
                version="1.0.0",
                description=description,
                price=price,
                download_count=0,
                rating=0.0,
                reviews_count=0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                published_at=None,
                features=features,
                screenshots=[],
                documentation=documentation,
                support_url="",
                license=license
            )
            
            self.plugins[plugin_id] = plugin
            
            # 自动审核（简化实现）
            await self._auto_review_plugin(plugin_id)
            
            logger.info(f"插件提交成功: {plugin_id} ({name})")
            return plugin_id
            
        except Exception as e:
            logger.error(f"提交插件失败: {e}")
            raise
    
    async def purchase_plugin(self,
                             buyer_id: str,
                             plugin_id: str) -> str:
        """
        购买插件
        
        Args:
            buyer_id: 购买者ID
            plugin_id: 插件ID
            
        Returns:
            交易ID
        """
        try:
            if buyer_id not in self.developers:
                raise ValueError(f"购买者不存在: {buyer_id}")
            
            if plugin_id not in self.plugins:
                raise ValueError(f"插件不存在: {plugin_id}")
            
            plugin = self.plugins[plugin_id]
            
            if plugin.status != PluginStatus.PUBLISHED:
                raise ValueError(f"插件未发布: {plugin.status.value}")
            
            if plugin.developer_id == buyer_id:
                raise ValueError("不能购买自己的插件")
            
            transaction_id = str(uuid.uuid4())
            
            # 计算分成
            seller = self.developers[plugin.developer_id]
            revenue_share = self.revenue_sharing_tiers[seller.tier]
            seller_amount = plugin.price * revenue_share
            commission = plugin.price - seller_amount
            
            transaction = MarketplaceTransaction(
                id=transaction_id,
                plugin_id=plugin_id,
                buyer_id=buyer_id,
                seller_id=plugin.developer_id,
                amount=plugin.price,
                commission=commission,
                transaction_type="purchase",
                status="completed",
                created_at=datetime.now(),
                completed_at=datetime.now()
            )
            
            self.transactions[transaction_id] = transaction
            
            # 更新统计数据
            plugin.download_count += 1
            seller.total_revenue += seller_amount
            seller.reputation_score += 0.1  # 增加声誉分数
            
            # 触发事件回调
            await self._trigger_event('transaction_completed', transaction)
            
            logger.info(f"插件购买成功: {transaction_id}")
            return transaction_id
            
        except Exception as e:
            logger.error(f"购买插件失败: {e}")
            raise
    
    async def download_sdk(self,
                          developer_id: str,
                          sdk_id: str) -> Dict[str, Any]:
        """
        下载SDK
        
        Args:
            developer_id: 开发者ID
            sdk_id: SDK ID
            
        Returns:
            下载信息
        """
        try:
            if developer_id not in self.developers:
                raise ValueError(f"开发者不存在: {developer_id}")
            
            if sdk_id not in self.sdks:
                raise ValueError(f"SDK不存在: {sdk_id}")
            
            developer = self.developers[developer_id]
            sdk = self.sdks[sdk_id]
            
            # 检查API使用限制
            if not await self._check_api_rate_limit(developer_id):
                raise ValueError("API使用频率超限")
            
            # 记录下载
            download_info = {
                'sdk_id': sdk_id,
                'developer_id': developer_id,
                'download_url': sdk.download_url,
                'documentation_url': sdk.documentation_url,
                'examples_url': sdk.examples_url,
                'version': sdk.version,
                'timestamp': datetime.now().isoformat()
            }
            
            # 更新统计
            sdk.download_count += 1
            developer.total_downloads += 1
            developer.last_active = datetime.now()
            
            # 记录API使用
            self.api_usage[developer_id].append({
                'action': 'sdk_download',
                'resource': sdk_id,
                'timestamp': datetime.now()
            })
            
            # 触发事件回调
            await self._trigger_event('sdk_downloaded', {
                'developer_id': developer_id,
                'sdk_id': sdk_id,
                'download_info': download_info
            })
            
            logger.info(f"SDK下载成功: {sdk_id} by {developer_id}")
            return download_info
            
        except Exception as e:
            logger.error(f"下载SDK失败: {e}")
            raise
    
    async def create_community_post(self,
                                   author_id: str,
                                   title: str,
                                   content: str,
                                   category: str,
                                   tags: List[str] = None) -> str:
        """
        创建社区帖子
        
        Args:
            author_id: 作者ID
            title: 标题
            content: 内容
            category: 分类
            tags: 标签
            
        Returns:
            帖子ID
        """
        try:
            if author_id not in self.developers:
                raise ValueError(f"作者不存在: {author_id}")
            
            post_id = str(uuid.uuid4())
            
            post = CommunityPost(
                id=post_id,
                author_id=author_id,
                title=title,
                content=content,
                category=category,
                tags=tags or [],
                upvotes=0,
                downvotes=0,
                replies_count=0,
                views_count=0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                is_pinned=False,
                is_locked=False
            )
            
            self.community_posts[post_id] = post
            
            # 增加作者声誉分数
            author = self.developers[author_id]
            author.reputation_score += 0.5
            
            # 触发事件回调
            await self._trigger_event('community_post_created', post)
            
            logger.info(f"社区帖子创建成功: {post_id}")
            return post_id
            
        except Exception as e:
            logger.error(f"创建社区帖子失败: {e}")
            raise
    
    async def get_marketplace_analytics(self) -> Dict[str, Any]:
        """
        获取市场分析数据
        
        Returns:
            分析数据
        """
        try:
            total_developers = len(self.developers)
            total_plugins = len(self.plugins)
            total_transactions = len(self.transactions)
            total_revenue = sum(t.amount for t in self.transactions.values())
            
            # 开发者等级分布
            tier_distribution = {}
            for developer in self.developers.values():
                tier = developer.tier.value
                tier_distribution[tier] = tier_distribution.get(tier, 0) + 1
            
            # 插件分类分布
            category_distribution = {}
            for plugin in self.plugins.values():
                category = plugin.category.value
                category_distribution[category] = category_distribution.get(category, 0) + 1
            
            # 收入分析
            monthly_revenue = await self._calculate_monthly_revenue()
            top_earning_plugins = await self._get_top_earning_plugins(10)
            top_developers = await self._get_top_developers(10)
            
            # SDK使用统计
            sdk_stats = {}
            for sdk in self.sdks.values():
                sdk_stats[sdk.language.value] = {
                    'download_count': sdk.download_count,
                    'rating': sdk.rating
                }
            
            # 社区活跃度
            community_stats = {
                'total_posts': len(self.community_posts),
                'active_users': len(set(post.author_id for post in self.community_posts.values())),
                'total_views': sum(post.views_count for post in self.community_posts.values())
            }
            
            analytics = {
                'overview': {
                    'total_developers': total_developers,
                    'total_plugins': total_plugins,
                    'total_transactions': total_transactions,
                    'total_revenue': round(total_revenue, 2),
                    'average_plugin_price': round(total_revenue / max(total_transactions, 1), 2)
                },
                'developer_analytics': {
                    'tier_distribution': tier_distribution,
                    'top_developers': top_developers,
                    'average_revenue_per_developer': round(total_revenue / max(total_developers, 1), 2)
                },
                'plugin_analytics': {
                    'category_distribution': category_distribution,
                    'top_earning_plugins': top_earning_plugins,
                    'average_downloads_per_plugin': sum(p.download_count for p in self.plugins.values()) / max(total_plugins, 1)
                },
                'revenue_analytics': {
                    'monthly_revenue': monthly_revenue,
                    'commission_earned': sum(t.commission for t in self.transactions.values()),
                    'developer_earnings': total_revenue - sum(t.commission for t in self.transactions.values())
                },
                'sdk_analytics': sdk_stats,
                'community_analytics': community_stats
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"获取市场分析数据失败: {e}")
            return {}
    
    async def get_developer_dashboard(self, developer_id: str) -> Dict[str, Any]:
        """
        获取开发者仪表板数据
        
        Args:
            developer_id: 开发者ID
            
        Returns:
            仪表板数据
        """
        try:
            if developer_id not in self.developers:
                raise ValueError(f"开发者不存在: {developer_id}")
            
            developer = self.developers[developer_id]
            
            # 开发者插件
            developer_plugins = [p for p in self.plugins.values() if p.developer_id == developer_id]
            
            # 收入统计
            developer_transactions = [t for t in self.transactions.values() if t.seller_id == developer_id]
            monthly_earnings = await self._calculate_developer_monthly_earnings(developer_id)
            
            # API使用统计
            api_usage_stats = await self._get_api_usage_stats(developer_id)
            
            # 社区活动
            developer_posts = [p for p in self.community_posts.values() if p.author_id == developer_id]
            
            dashboard = {
                'developer_info': {
                    'id': developer.id,
                    'username': developer.username,
                    'tier': developer.tier.value,
                    'reputation_score': developer.reputation_score,
                    'verified': developer.verified,
                    'member_since': developer.created_at.isoformat()
                },
                'plugin_statistics': {
                    'total_plugins': len(developer_plugins),
                    'published_plugins': len([p for p in developer_plugins if p.status == PluginStatus.PUBLISHED]),
                    'total_downloads': sum(p.download_count for p in developer_plugins),
                    'average_rating': sum(p.rating for p in developer_plugins) / max(len(developer_plugins), 1)
                },
                'revenue_statistics': {
                    'total_revenue': developer.total_revenue,
                    'monthly_earnings': monthly_earnings,
                    'total_transactions': len(developer_transactions),
                    'revenue_share_rate': self.revenue_sharing_tiers[developer.tier]
                },
                'api_usage': api_usage_stats,
                'community_activity': {
                    'total_posts': len(developer_posts),
                    'total_upvotes': sum(p.upvotes for p in developer_posts),
                    'reputation_score': developer.reputation_score
                },
                'recent_plugins': [
                    {
                        'id': p.id,
                        'name': p.name,
                        'status': p.status.value,
                        'downloads': p.download_count,
                        'rating': p.rating
                    }
                    for p in sorted(developer_plugins, key=lambda x: x.created_at, reverse=True)[:5]
                ]
            }
            
            return dashboard
            
        except Exception as e:
            logger.error(f"获取开发者仪表板数据失败: {e}")
            return {}
    
    async def upgrade_developer_tier(self, developer_id: str, new_tier: DeveloperTier) -> bool:
        """
        升级开发者等级
        
        Args:
            developer_id: 开发者ID
            new_tier: 新等级
            
        Returns:
            升级是否成功
        """
        try:
            if developer_id not in self.developers:
                raise ValueError(f"开发者不存在: {developer_id}")
            
            developer = self.developers[developer_id]
            old_tier = developer.tier
            
            # 检查升级条件
            if not await self._check_tier_upgrade_eligibility(developer, new_tier):
                raise ValueError(f"不满足升级条件: {new_tier.value}")
            
            developer.tier = new_tier
            
            # 更新API限制
            new_api_limit = self.api_rate_limits[new_tier.value]
            
            logger.info(f"开发者等级升级成功: {developer_id} ({old_tier.value} -> {new_tier.value})")
            return True
            
        except Exception as e:
            logger.error(f"升级开发者等级失败: {e}")
            return False
    
    async def _auto_review_plugin(self, plugin_id: str):
        """自动审核插件"""
        try:
            plugin = self.plugins[plugin_id]
            
            # 简化的自动审核逻辑
            review_score = 0
            
            # 检查描述长度
            if len(plugin.description) >= 100:
                review_score += 20
            
            # 检查功能列表
            if len(plugin.features) >= 3:
                review_score += 20
            
            # 检查文档
            if len(plugin.documentation) >= 500:
                review_score += 20
            
            # 检查价格合理性
            if 0 <= plugin.price <= 1000:
                review_score += 20
            
            # 检查许可证
            if plugin.license in ['MIT', 'Apache-2.0', 'GPL-3.0']:
                review_score += 20
            
            # 根据评分决定审核结果
            if review_score >= 80:
                plugin.status = PluginStatus.APPROVED
                plugin.published_at = datetime.now()
                
                # 触发发布事件
                await self._trigger_event('plugin_published', plugin)
                
                logger.info(f"插件自动审核通过: {plugin_id}")
            else:
                plugin.status = PluginStatus.REVIEWING
                logger.info(f"插件需要人工审核: {plugin_id} (评分: {review_score})")
            
        except Exception as e:
            logger.error(f"自动审核插件失败: {e}")
    
    async def _check_api_rate_limit(self, developer_id: str) -> bool:
        """检查API使用频率限制"""
        try:
            developer = self.developers[developer_id]
            limit = self.api_rate_limits[developer.tier.value]
            
            # 检查过去1小时的API使用次数
            one_hour_ago = datetime.now() - timedelta(hours=1)
            recent_usage = [
                usage for usage in self.api_usage[developer_id]
                if usage['timestamp'] > one_hour_ago
            ]
            
            return len(recent_usage) < limit
            
        except Exception:
            return False
    
    def _generate_api_key(self, developer_id: str) -> str:
        """生成API密钥"""
        try:
            data = f"{developer_id}_{datetime.now().isoformat()}_{uuid.uuid4()}"
            return hashlib.sha256(data.encode()).hexdigest()[:32]
        except Exception:
            return str(uuid.uuid4()).replace('-', '')
    
    def _initialize_sdks(self):
        """初始化SDK"""
        try:
            sdk_configs = [
                {
                    'name': 'PowerAutomation Python SDK',
                    'language': SDKLanguage.PYTHON,
                    'description': 'Official Python SDK for PowerAutomation platform'
                },
                {
                    'name': 'PowerAutomation JavaScript SDK',
                    'language': SDKLanguage.JAVASCRIPT,
                    'description': 'Official JavaScript SDK for PowerAutomation platform'
                },
                {
                    'name': 'PowerAutomation TypeScript SDK',
                    'language': SDKLanguage.TYPESCRIPT,
                    'description': 'Official TypeScript SDK for PowerAutomation platform'
                },
                {
                    'name': 'PowerAutomation Java SDK',
                    'language': SDKLanguage.JAVA,
                    'description': 'Official Java SDK for PowerAutomation platform'
                },
                {
                    'name': 'PowerAutomation Go SDK',
                    'language': SDKLanguage.GO,
                    'description': 'Official Go SDK for PowerAutomation platform'
                }
            ]
            
            for config in sdk_configs:
                sdk_id = str(uuid.uuid4())
                sdk = SDK(
                    id=sdk_id,
                    name=config['name'],
                    language=config['language'],
                    version="1.0.0",
                    description=config['description'],
                    download_url=f"https://sdk.powerautomation.com/{config['language'].value}/v1.0.0",
                    documentation_url=f"https://docs.powerautomation.com/sdk/{config['language'].value}",
                    examples_url=f"https://examples.powerautomation.com/sdk/{config['language'].value}",
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    download_count=0,
                    rating=4.5,
                    features=['Authentication', 'API Client', 'Error Handling', 'Async Support'],
                    dependencies=[],
                    changelog=[]
                )
                
                self.sdks[sdk_id] = sdk
            
            logger.info(f"初始化 {len(sdk_configs)} 个SDK")
            
        except Exception as e:
            logger.error(f"初始化SDK失败: {e}")
    
    async def _calculate_monthly_revenue(self) -> Dict[str, float]:
        """计算月度收入"""
        try:
            monthly_revenue = {}
            
            for transaction in self.transactions.values():
                if transaction.completed_at:
                    month_key = transaction.completed_at.strftime('%Y-%m')
                    monthly_revenue[month_key] = monthly_revenue.get(month_key, 0) + transaction.amount
            
            return monthly_revenue
            
        except Exception:
            return {}
    
    async def _get_top_earning_plugins(self, limit: int) -> List[Dict[str, Any]]:
        """获取收入最高的插件"""
        try:
            plugin_earnings = {}
            
            for transaction in self.transactions.values():
                plugin_id = transaction.plugin_id
                plugin_earnings[plugin_id] = plugin_earnings.get(plugin_id, 0) + transaction.amount
            
            sorted_plugins = sorted(plugin_earnings.items(), key=lambda x: x[1], reverse=True)
            
            result = []
            for plugin_id, earnings in sorted_plugins[:limit]:
                if plugin_id in self.plugins:
                    plugin = self.plugins[plugin_id]
                    result.append({
                        'id': plugin.id,
                        'name': plugin.name,
                        'earnings': earnings,
                        'downloads': plugin.download_count,
                        'rating': plugin.rating
                    })
            
            return result
            
        except Exception:
            return []
    
    async def _get_top_developers(self, limit: int) -> List[Dict[str, Any]]:
        """获取收入最高的开发者"""
        try:
            sorted_developers = sorted(
                self.developers.values(),
                key=lambda x: x.total_revenue,
                reverse=True
            )
            
            result = []
            for developer in sorted_developers[:limit]:
                result.append({
                    'id': developer.id,
                    'username': developer.username,
                    'tier': developer.tier.value,
                    'total_revenue': developer.total_revenue,
                    'reputation_score': developer.reputation_score,
                    'plugin_count': len([p for p in self.plugins.values() if p.developer_id == developer.id])
                })
            
            return result
            
        except Exception:
            return []
    
    async def _calculate_developer_monthly_earnings(self, developer_id: str) -> Dict[str, float]:
        """计算开发者月度收入"""
        try:
            monthly_earnings = {}
            
            for transaction in self.transactions.values():
                if transaction.seller_id == developer_id and transaction.completed_at:
                    month_key = transaction.completed_at.strftime('%Y-%m')
                    seller_amount = transaction.amount - transaction.commission
                    monthly_earnings[month_key] = monthly_earnings.get(month_key, 0) + seller_amount
            
            return monthly_earnings
            
        except Exception:
            return {}
    
    async def _get_api_usage_stats(self, developer_id: str) -> Dict[str, Any]:
        """获取API使用统计"""
        try:
            usage_data = self.api_usage[developer_id]
            
            # 按天统计
            daily_usage = {}
            for usage in usage_data:
                day_key = usage['timestamp'].strftime('%Y-%m-%d')
                daily_usage[day_key] = daily_usage.get(day_key, 0) + 1
            
            # 按操作类型统计
            action_usage = {}
            for usage in usage_data:
                action = usage['action']
                action_usage[action] = action_usage.get(action, 0) + 1
            
            developer = self.developers[developer_id]
            current_limit = self.api_rate_limits[developer.tier.value]
            
            return {
                'total_requests': len(usage_data),
                'daily_usage': daily_usage,
                'action_usage': action_usage,
                'current_limit': current_limit,
                'usage_rate': len(usage_data) / max(current_limit, 1)
            }
            
        except Exception:
            return {}
    
    async def _check_tier_upgrade_eligibility(self, developer: Developer, new_tier: DeveloperTier) -> bool:
        """检查等级升级资格"""
        try:
            # 简化的升级条件检查
            if new_tier == DeveloperTier.PROFESSIONAL:
                return (developer.total_revenue >= 100 and 
                       developer.reputation_score >= 70)
            elif new_tier == DeveloperTier.ENTERPRISE:
                return (developer.total_revenue >= 1000 and 
                       developer.reputation_score >= 80 and
                       len([p for p in self.plugins.values() if p.developer_id == developer.id]) >= 5)
            elif new_tier == DeveloperTier.PARTNER:
                return (developer.total_revenue >= 10000 and 
                       developer.reputation_score >= 90)
            
            return True
            
        except Exception:
            return False
    
    async def _trigger_event(self, event_type: str, data: Any):
        """触发事件回调"""
        try:
            if event_type in self.event_callbacks:
                for callback in self.event_callbacks[event_type]:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
        except Exception as e:
            logger.error(f"触发事件回调失败: {e}")
    
    def register_event_callback(self, event_type: str, callback: Callable):
        """注册事件回调"""
        if event_type in self.event_callbacks:
            self.event_callbacks[event_type].append(callback)
        else:
            logger.warning(f"未知事件类型: {event_type}")
    
    async def shutdown(self):
        """关闭开发者生态系统"""
        try:
            # 保存所有数据
            await self._save_ecosystem_data()
            
            # 清理资源
            self.developers.clear()
            self.sdks.clear()
            self.plugins.clear()
            self.transactions.clear()
            self.community_posts.clear()
            self.api_usage.clear()
            
            logger.info("开发者生态系统已关闭")
            
        except Exception as e:
            logger.error(f"关闭开发者生态系统失败: {e}")
    
    async def _save_ecosystem_data(self):
        """保存生态系统数据"""
        try:
            # 这里可以实现将数据保存到持久化存储
            logger.debug("保存生态系统数据")
            
        except Exception as e:
            logger.error(f"保存生态系统数据失败: {e}")

