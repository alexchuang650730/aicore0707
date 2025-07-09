"""
PowerAutomation 智能任务分析器

基于NLP和机器学习技术，智能分析用户任务：
- 任务特征提取和分类
- 软件工程任务识别
- 复杂度评估和优先级排序
- 与现有AI增强组件集成

支持多种任务类型的智能分析和路由决策支持。
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

# NLP相关导入
try:
    import nltk
    from nltk.tokenize import word_tokenize, sent_tokenize
    from nltk.corpus import stopwords
    from nltk.stem import PorterStemmer
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

# 导入已完成的AI增强组件
from ..components.local_adapter_mcp.ai_enhanced.intelligent_task_optimizer import IntelligentTaskOptimizer


class TaskType(Enum):
    """任务类型枚举"""
    DEVELOPMENT = "development"
    DEPLOYMENT = "deployment"
    TESTING = "testing"
    MONITORING = "monitoring"
    SECURITY = "security"
    ARCHITECTURE = "architecture"
    DOCUMENTATION = "documentation"
    ANALYSIS = "analysis"
    AUTOMATION = "automation"
    GENERAL = "general"


class TaskComplexity(Enum):
    """任务复杂度枚举"""
    SIMPLE = 1      # 简单任务 (< 1小时)
    MODERATE = 2    # 中等任务 (1-4小时)
    COMPLEX = 3     # 复杂任务 (4-24小时)
    ADVANCED = 4    # 高级任务 (1-7天)
    EXPERT = 5      # 专家级任务 (> 1周)


class TaskDomain(Enum):
    """任务领域枚举"""
    FRONTEND = "frontend"
    BACKEND = "backend"
    FULLSTACK = "fullstack"
    DEVOPS = "devops"
    DATA_SCIENCE = "data_science"
    MACHINE_LEARNING = "machine_learning"
    MOBILE = "mobile"
    DESKTOP = "desktop"
    WEB = "web"
    API = "api"
    DATABASE = "database"
    CLOUD = "cloud"
    SECURITY = "security"
    GENERAL = "general"


@dataclass
class TaskAnalysisResult:
    """任务分析结果"""
    task_type: TaskType
    complexity: TaskComplexity
    domain: TaskDomain
    estimated_time: float  # 预估时间（小时）
    required_skills: List[str]
    suggested_agents: List[str]
    suggested_mcps: List[str]
    confidence_score: float  # 分析置信度 (0-1)
    keywords: List[str]
    entities: List[str]
    sentiment: str  # positive, neutral, negative
    metadata: Dict[str, Any]


class TaskAnalyzer:
    """
    智能任务分析器
    
    使用NLP和机器学习技术分析用户任务，
    提供智能的任务分类、复杂度评估和路由建议。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化任务分析器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 初始化NLP组件
        self._init_nlp()
        
        # 初始化AI增强组件
        self.task_optimizer = IntelligentTaskOptimizer()
        
        # 加载任务模式和规则
        self._load_task_patterns()
        
        # 统计信息
        self.stats = {
            "total_analyzed": 0,
            "by_type": {},
            "by_complexity": {},
            "average_confidence": 0.0
        }
        
        self.logger.info("智能任务分析器初始化完成")
    
    def _init_nlp(self):
        """初始化NLP组件"""
        if NLTK_AVAILABLE:
            try:
                # 下载必要的NLTK数据
                nltk.download('punkt', quiet=True)
                nltk.download('stopwords', quiet=True)
                nltk.download('averaged_perceptron_tagger', quiet=True)
                
                self.stemmer = PorterStemmer()
                self.stop_words = set(stopwords.words('english'))
                
                self.logger.info("NLTK组件初始化成功")
            except Exception as e:
                self.logger.warning(f"NLTK初始化失败: {e}")
                NLTK_AVAILABLE = False
        
        if not NLTK_AVAILABLE:
            self.logger.warning("NLTK不可用，使用基础文本处理")
    
    def _load_task_patterns(self):
        """加载任务模式和规则"""
        # 任务类型关键词映射
        self.type_keywords = {
            TaskType.DEVELOPMENT: [
                "develop", "code", "program", "implement", "create", "build", 
                "write", "script", "function", "class", "module", "api",
                "frontend", "backend", "web", "app", "application"
            ],
            TaskType.DEPLOYMENT: [
                "deploy", "deployment", "release", "publish", "launch",
                "docker", "kubernetes", "aws", "azure", "gcp", "cloud",
                "server", "production", "staging"
            ],
            TaskType.TESTING: [
                "test", "testing", "unit test", "integration test", "e2e",
                "qa", "quality", "bug", "debug", "verify", "validate"
            ],
            TaskType.MONITORING: [
                "monitor", "monitoring", "metrics", "logs", "alert",
                "dashboard", "performance", "health", "status"
            ],
            TaskType.SECURITY: [
                "security", "secure", "authentication", "authorization",
                "encryption", "vulnerability", "audit", "compliance"
            ],
            TaskType.ARCHITECTURE: [
                "architecture", "design", "structure", "pattern",
                "microservice", "system", "component", "framework"
            ],
            TaskType.DOCUMENTATION: [
                "document", "documentation", "readme", "guide", "manual",
                "wiki", "comment", "explain", "describe"
            ],
            TaskType.ANALYSIS: [
                "analyze", "analysis", "research", "investigate", "study",
                "report", "data", "statistics", "metrics"
            ],
            TaskType.AUTOMATION: [
                "automate", "automation", "script", "workflow", "pipeline",
                "ci/cd", "jenkins", "github actions", "cron"
            ]
        }
        
        # 复杂度指标
        self.complexity_indicators = {
            TaskComplexity.SIMPLE: [
                "simple", "basic", "quick", "small", "minor", "fix",
                "update", "change", "modify", "add"
            ],
            TaskComplexity.MODERATE: [
                "moderate", "medium", "standard", "normal", "feature",
                "component", "module", "integration"
            ],
            TaskComplexity.COMPLEX: [
                "complex", "advanced", "large", "system", "architecture",
                "framework", "platform", "enterprise"
            ],
            TaskComplexity.ADVANCED: [
                "advanced", "sophisticated", "comprehensive", "full",
                "complete", "end-to-end", "enterprise", "scalable"
            ],
            TaskComplexity.EXPERT: [
                "expert", "research", "innovative", "cutting-edge",
                "revolutionary", "breakthrough", "ai", "ml", "deep learning"
            ]
        }
        
        # 技术领域关键词
        self.domain_keywords = {
            TaskDomain.FRONTEND: [
                "frontend", "ui", "ux", "react", "vue", "angular",
                "html", "css", "javascript", "typescript", "web"
            ],
            TaskDomain.BACKEND: [
                "backend", "server", "api", "database", "python",
                "java", "node", "go", "rust", "c++", "service"
            ],
            TaskDomain.DEVOPS: [
                "devops", "docker", "kubernetes", "ci/cd", "jenkins",
                "terraform", "ansible", "aws", "azure", "gcp"
            ],
            TaskDomain.DATA_SCIENCE: [
                "data", "analytics", "pandas", "numpy", "jupyter",
                "visualization", "statistics", "analysis"
            ],
            TaskDomain.MACHINE_LEARNING: [
                "ml", "ai", "machine learning", "deep learning",
                "tensorflow", "pytorch", "model", "training"
            ],
            TaskDomain.MOBILE: [
                "mobile", "ios", "android", "react native", "flutter",
                "swift", "kotlin", "app"
            ],
            TaskDomain.CLOUD: [
                "cloud", "aws", "azure", "gcp", "serverless",
                "lambda", "s3", "ec2", "kubernetes"
            ]
        }
        
        # 智能体映射
        self.agent_mapping = {
            TaskType.DEVELOPMENT: ["developer_agent"],
            TaskType.DEPLOYMENT: ["deploy_agent"],
            TaskType.TESTING: ["test_agent"],
            TaskType.MONITORING: ["monitor_agent"],
            TaskType.SECURITY: ["security_agent"],
            TaskType.ARCHITECTURE: ["architect_agent"],
            TaskType.DOCUMENTATION: ["developer_agent"],
            TaskType.ANALYSIS: ["architect_agent", "monitor_agent"],
            TaskType.AUTOMATION: ["developer_agent", "deploy_agent"]
        }
        
        # MCP映射
        self.mcp_mapping = {
            TaskType.DEVELOPMENT: ["stagewise_mcp", "trae_agent_mcp"],
            TaskType.DEPLOYMENT: ["local_adapter_mcp"],
            TaskType.TESTING: ["stagewise_mcp"],
            TaskType.MONITORING: ["local_adapter_mcp"],
            TaskType.SECURITY: ["local_adapter_mcp"],
            TaskType.ARCHITECTURE: ["trae_agent_mcp"],
            TaskType.DOCUMENTATION: ["stagewise_mcp"],
            TaskType.ANALYSIS: ["local_adapter_mcp"],
            TaskType.AUTOMATION: ["local_adapter_mcp", "stagewise_mcp"]
        }
    
    async def analyze_task(self, 
                          description: str, 
                          task_type: Optional[str] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> TaskAnalysisResult:
        """
        分析任务
        
        Args:
            description: 任务描述
            task_type: 任务类型提示
            metadata: 任务元数据
            
        Returns:
            任务分析结果
        """
        try:
            self.logger.info(f"开始分析任务: {description[:100]}...")
            
            # 预处理文本
            processed_text = self._preprocess_text(description)
            
            # 提取关键词和实体
            keywords = self._extract_keywords(processed_text)
            entities = self._extract_entities(processed_text)
            
            # 分析任务类型
            analyzed_type = self._analyze_task_type(processed_text, keywords, task_type)
            
            # 分析复杂度
            complexity = self._analyze_complexity(processed_text, keywords)
            
            # 分析技术领域
            domain = self._analyze_domain(processed_text, keywords)
            
            # 预估时间
            estimated_time = self._estimate_time(complexity, analyzed_type, len(processed_text))
            
            # 提取所需技能
            required_skills = self._extract_required_skills(processed_text, keywords, domain)
            
            # 建议智能体和MCP
            suggested_agents = self._suggest_agents(analyzed_type, domain, complexity)
            suggested_mcps = self._suggest_mcps(analyzed_type, domain, complexity)
            
            # 情感分析
            sentiment = self._analyze_sentiment(description)
            
            # 计算置信度
            confidence_score = self._calculate_confidence(
                analyzed_type, complexity, domain, keywords
            )
            
            # 创建分析结果
            result = TaskAnalysisResult(
                task_type=analyzed_type,
                complexity=complexity,
                domain=domain,
                estimated_time=estimated_time,
                required_skills=required_skills,
                suggested_agents=suggested_agents,
                suggested_mcps=suggested_mcps,
                confidence_score=confidence_score,
                keywords=keywords,
                entities=entities,
                sentiment=sentiment,
                metadata=metadata or {}
            )
            
            # 更新统计信息
            self._update_stats(result)
            
            # 使用AI增强优化
            optimized_result = await self._optimize_with_ai(result, description)
            
            self.logger.info(f"任务分析完成，类型: {analyzed_type.value}, 复杂度: {complexity.value}")
            
            return optimized_result
            
        except Exception as e:
            self.logger.error(f"任务分析失败: {e}")
            # 返回默认结果
            return self._create_default_result(description, metadata)
    
    def _preprocess_text(self, text: str) -> str:
        """预处理文本"""
        # 转换为小写
        text = text.lower()
        
        # 移除特殊字符，保留字母、数字和空格
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        
        # 移除多余空格
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        if NLTK_AVAILABLE:
            try:
                # 分词
                tokens = word_tokenize(text)
                
                # 移除停用词
                keywords = [word for word in tokens if word not in self.stop_words]
                
                # 词干提取
                keywords = [self.stemmer.stem(word) for word in keywords]
                
                # 去重并过滤短词
                keywords = list(set([word for word in keywords if len(word) > 2]))
                
                return keywords[:20]  # 返回前20个关键词
                
            except Exception as e:
                self.logger.warning(f"NLTK关键词提取失败: {e}")
        
        # 基础关键词提取
        words = text.split()
        keywords = [word for word in words if len(word) > 3]
        return list(set(keywords))[:20]
    
    def _extract_entities(self, text: str) -> List[str]:
        """提取实体"""
        entities = []
        
        # 技术栈实体
        tech_patterns = [
            r'\b(python|java|javascript|typescript|react|vue|angular|node|docker|kubernetes)\b',
            r'\b(aws|azure|gcp|github|gitlab|jenkins|terraform|ansible)\b',
            r'\b(mysql|postgresql|mongodb|redis|elasticsearch)\b',
            r'\b(tensorflow|pytorch|pandas|numpy|scikit-learn)\b'
        ]
        
        for pattern in tech_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities.extend(matches)
        
        # 文件类型实体
        file_patterns = r'\b\w+\.(py|js|ts|html|css|json|yaml|yml|md|txt|sql)\b'
        file_matches = re.findall(file_patterns, text, re.IGNORECASE)
        entities.extend([f".{ext}" for ext in file_matches])
        
        return list(set(entities))
    
    def _analyze_task_type(self, text: str, keywords: List[str], hint: Optional[str] = None) -> TaskType:
        """分析任务类型"""
        if hint:
            try:
                return TaskType(hint.lower())
            except ValueError:
                pass
        
        # 计算每种类型的匹配分数
        type_scores = {}
        
        for task_type, type_keywords in self.type_keywords.items():
            score = 0
            for keyword in type_keywords:
                if keyword in text:
                    score += 2  # 完整匹配得分更高
                for kw in keywords:
                    if keyword in kw or kw in keyword:
                        score += 1
            
            type_scores[task_type] = score
        
        # 返回得分最高的类型
        if type_scores:
            best_type = max(type_scores, key=type_scores.get)
            if type_scores[best_type] > 0:
                return best_type
        
        return TaskType.GENERAL
    
    def _analyze_complexity(self, text: str, keywords: List[str]) -> TaskComplexity:
        """分析任务复杂度"""
        complexity_scores = {}
        
        for complexity, indicators in self.complexity_indicators.items():
            score = 0
            for indicator in indicators:
                if indicator in text:
                    score += 2
                for kw in keywords:
                    if indicator in kw or kw in indicator:
                        score += 1
            
            complexity_scores[complexity] = score
        
        # 基于文本长度调整复杂度
        text_length_factor = len(text) / 100  # 每100字符增加复杂度
        
        # 基于关键词数量调整复杂度
        keyword_factor = len(keywords) / 10  # 每10个关键词增加复杂度
        
        # 计算最终复杂度
        if complexity_scores:
            best_complexity = max(complexity_scores, key=complexity_scores.get)
            base_score = complexity_scores[best_complexity]
        else:
            best_complexity = TaskComplexity.MODERATE
            base_score = 0
        
        # 根据额外因素调整
        total_factor = text_length_factor + keyword_factor
        
        if total_factor > 5:
            # 非常复杂
            return TaskComplexity.EXPERT
        elif total_factor > 3:
            # 高复杂度
            return max(best_complexity, TaskComplexity.ADVANCED)
        elif total_factor > 1.5:
            # 中等复杂度
            return max(best_complexity, TaskComplexity.COMPLEX)
        elif base_score > 0:
            return best_complexity
        else:
            return TaskComplexity.MODERATE
    
    def _analyze_domain(self, text: str, keywords: List[str]) -> TaskDomain:
        """分析技术领域"""
        domain_scores = {}
        
        for domain, domain_keywords in self.domain_keywords.items():
            score = 0
            for keyword in domain_keywords:
                if keyword in text:
                    score += 2
                for kw in keywords:
                    if keyword in kw or kw in keyword:
                        score += 1
            
            domain_scores[domain] = score
        
        # 返回得分最高的领域
        if domain_scores:
            best_domain = max(domain_scores, key=domain_scores.get)
            if domain_scores[best_domain] > 0:
                return best_domain
        
        return TaskDomain.GENERAL
    
    def _estimate_time(self, complexity: TaskComplexity, task_type: TaskType, text_length: int) -> float:
        """预估任务时间（小时）"""
        # 基础时间映射
        base_times = {
            TaskComplexity.SIMPLE: 0.5,
            TaskComplexity.MODERATE: 2.0,
            TaskComplexity.COMPLEX: 8.0,
            TaskComplexity.ADVANCED: 24.0,
            TaskComplexity.EXPERT: 80.0
        }
        
        # 任务类型调整因子
        type_factors = {
            TaskType.DEVELOPMENT: 1.2,
            TaskType.DEPLOYMENT: 0.8,
            TaskType.TESTING: 1.0,
            TaskType.MONITORING: 0.6,
            TaskType.SECURITY: 1.5,
            TaskType.ARCHITECTURE: 2.0,
            TaskType.DOCUMENTATION: 0.4,
            TaskType.ANALYSIS: 1.0,
            TaskType.AUTOMATION: 1.3,
            TaskType.GENERAL: 1.0
        }
        
        base_time = base_times.get(complexity, 2.0)
        type_factor = type_factors.get(task_type, 1.0)
        
        # 文本长度调整（更详细的描述通常意味着更复杂的任务）
        length_factor = 1 + (text_length / 1000) * 0.5
        
        estimated_time = base_time * type_factor * length_factor
        
        # 确保在合理范围内
        return max(0.1, min(estimated_time, 200.0))
    
    def _extract_required_skills(self, text: str, keywords: List[str], domain: TaskDomain) -> List[str]:
        """提取所需技能"""
        skills = set()
        
        # 基于领域的基础技能
        domain_skills = {
            TaskDomain.FRONTEND: ["HTML", "CSS", "JavaScript", "React", "UI/UX"],
            TaskDomain.BACKEND: ["Python", "API Design", "Database", "Server Management"],
            TaskDomain.FULLSTACK: ["Frontend", "Backend", "Database", "API Integration"],
            TaskDomain.DEVOPS: ["Docker", "Kubernetes", "CI/CD", "Cloud Platforms"],
            TaskDomain.DATA_SCIENCE: ["Python", "Data Analysis", "Statistics", "Visualization"],
            TaskDomain.MACHINE_LEARNING: ["Python", "ML Algorithms", "Data Processing", "Model Training"],
            TaskDomain.MOBILE: ["Mobile Development", "UI/UX", "App Store"],
            TaskDomain.CLOUD: ["Cloud Architecture", "AWS/Azure/GCP", "Serverless"],
            TaskDomain.SECURITY: ["Security Protocols", "Encryption", "Vulnerability Assessment"]
        }
        
        skills.update(domain_skills.get(domain, ["General Programming"]))
        
        # 从文本中提取技能关键词
        skill_keywords = [
            "python", "javascript", "java", "react", "vue", "angular",
            "docker", "kubernetes", "aws", "azure", "gcp", "terraform",
            "mysql", "postgresql", "mongodb", "redis", "api", "rest",
            "graphql", "microservices", "ci/cd", "jenkins", "git"
        ]
        
        for skill in skill_keywords:
            if skill in text or any(skill in kw for kw in keywords):
                skills.add(skill.title())
        
        return list(skills)[:10]  # 返回前10个技能
    
    def _suggest_agents(self, task_type: TaskType, domain: TaskDomain, complexity: TaskComplexity) -> List[str]:
        """建议智能体"""
        agents = set()
        
        # 基于任务类型的基础智能体
        agents.update(self.agent_mapping.get(task_type, ["developer_agent"]))
        
        # 基于复杂度添加额外智能体
        if complexity in [TaskComplexity.COMPLEX, TaskComplexity.ADVANCED, TaskComplexity.EXPERT]:
            agents.add("architect_agent")
        
        if complexity in [TaskComplexity.ADVANCED, TaskComplexity.EXPERT]:
            agents.add("security_agent")
            agents.add("test_agent")
        
        # 基于领域添加专门智能体
        if domain in [TaskDomain.DEVOPS, TaskDomain.CLOUD]:
            agents.add("deploy_agent")
        
        return list(agents)
    
    def _suggest_mcps(self, task_type: TaskType, domain: TaskDomain, complexity: TaskComplexity) -> List[str]:
        """建议MCP"""
        mcps = set()
        
        # 基于任务类型的基础MCP
        mcps.update(self.mcp_mapping.get(task_type, ["local_adapter_mcp"]))
        
        # 基于复杂度和领域添加额外MCP
        if complexity in [TaskComplexity.COMPLEX, TaskComplexity.ADVANCED, TaskComplexity.EXPERT]:
            mcps.add("trae_agent_mcp")
        
        if domain in [TaskDomain.FRONTEND, TaskDomain.WEB]:
            mcps.add()
        
        if domain == TaskDomain.DATA_SCIENCE:
            mcps.add("memoryos_mcp")
        
        return list(mcps)
    
    def _analyze_sentiment(self, text: str) -> str:
        """分析情感倾向"""
        # 简单的情感分析
        positive_words = ["good", "great", "excellent", "amazing", "perfect", "love", "like"]
        negative_words = ["bad", "terrible", "awful", "hate", "dislike", "problem", "issue", "bug"]
        
        text_lower = text.lower()
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def _calculate_confidence(self, task_type: TaskType, complexity: TaskComplexity, 
                            domain: TaskDomain, keywords: List[str]) -> float:
        """计算分析置信度"""
        confidence = 0.5  # 基础置信度
        
        # 基于关键词匹配度
        if len(keywords) > 5:
            confidence += 0.2
        elif len(keywords) > 2:
            confidence += 0.1
        
        # 基于类型匹配度
        if task_type != TaskType.GENERAL:
            confidence += 0.2
        
        # 基于领域匹配度
        if domain != TaskDomain.GENERAL:
            confidence += 0.1
        
        # 确保在0-1范围内
        return max(0.0, min(confidence, 1.0))
    
    def _update_stats(self, result: TaskAnalysisResult):
        """更新统计信息"""
        self.stats["total_analyzed"] += 1
        
        # 按类型统计
        type_key = result.task_type.value
        self.stats["by_type"][type_key] = self.stats["by_type"].get(type_key, 0) + 1
        
        # 按复杂度统计
        complexity_key = result.complexity.value
        self.stats["by_complexity"][complexity_key] = self.stats["by_complexity"].get(complexity_key, 0) + 1
        
        # 更新平均置信度
        total = self.stats["total_analyzed"]
        current_avg = self.stats["average_confidence"]
        self.stats["average_confidence"] = (current_avg * (total - 1) + result.confidence_score) / total
    
    async def _optimize_with_ai(self, result: TaskAnalysisResult, description: str) -> TaskAnalysisResult:
        """使用AI增强组件优化分析结果"""
        try:
            # 使用智能任务优化器进一步优化
            optimization_result = await self.task_optimizer.optimize_task_analysis(
                description, result.__dict__
            )
            
            # 更新结果
            if optimization_result:
                # 更新建议的智能体和MCP
                if "suggested_agents" in optimization_result:
                    result.suggested_agents = optimization_result["suggested_agents"]
                
                if "suggested_mcps" in optimization_result:
                    result.suggested_mcps = optimization_result["suggested_mcps"]
                
                # 更新预估时间
                if "estimated_time" in optimization_result:
                    result.estimated_time = optimization_result["estimated_time"]
                
                # 更新置信度
                if "confidence_score" in optimization_result:
                    result.confidence_score = min(result.confidence_score + 0.1, 1.0)
            
        except Exception as e:
            self.logger.warning(f"AI优化失败: {e}")
        
        return result
    
    def _create_default_result(self, description: str, metadata: Optional[Dict[str, Any]]) -> TaskAnalysisResult:
        """创建默认分析结果"""
        return TaskAnalysisResult(
            task_type=TaskType.GENERAL,
            complexity=TaskComplexity.MODERATE,
            domain=TaskDomain.GENERAL,
            estimated_time=2.0,
            required_skills=["General Programming"],
            suggested_agents=["developer_agent"],
            suggested_mcps=["local_adapter_mcp"],
            confidence_score=0.3,
            keywords=[],
            entities=[],
            sentiment="neutral",
            metadata=metadata or {}
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()
    
    async def batch_analyze(self, tasks: List[Dict[str, Any]]) -> List[TaskAnalysisResult]:
        """批量分析任务"""
        results = []
        
        for task in tasks:
            result = await self.analyze_task(
                task.get("description", ""),
                task.get("task_type"),
                task.get("metadata")
            )
            results.append(result)
        
        return results


if __name__ == "__main__":
    # 测试任务分析器
    import asyncio
    
    async def test_task_analyzer():
        analyzer = TaskAnalyzer()
        
        # 测试任务
        test_tasks = [
            "Create a React frontend application with user authentication",
            "Deploy a Python Flask API to AWS using Docker",
            "Write unit tests for the user management module",
            "Set up monitoring dashboard for microservices",
            "Implement OAuth2 security for the API endpoints",
            "Design the system architecture for a scalable e-commerce platform"
        ]
        
        for task_desc in test_tasks:
            print(f"\n分析任务: {task_desc}")
            result = await analyzer.analyze_task(task_desc)
            
            print(f"类型: {result.task_type.value}")
            print(f"复杂度: {result.complexity.value}")
            print(f"领域: {result.domain.value}")
            print(f"预估时间: {result.estimated_time:.1f}小时")
            print(f"建议智能体: {result.suggested_agents}")
            print(f"建议MCP: {result.suggested_mcps}")
            print(f"置信度: {result.confidence_score:.2f}")
            print(f"关键词: {result.keywords[:5]}")
        
        # 显示统计信息
        print(f"\n统计信息: {analyzer.get_stats()}")
    
    # 运行测试
    asyncio.run(test_task_analyzer())

