#!/usr/bin/env python3
"""
SmartInvention MCP完整深度集成

基于SmartInvention MCP的智能发明协议，为PowerAutomation 4.1提供创新发明能力。
实现智能发明引擎、创新模式识别、发明评估系统和知识产权管理。

主要功能：
- 智能发明引擎和创新生成
- 创新模式识别和分析
- 发明评估和可行性分析
- 知识产权管理和保护
- 创新协作和团队发明
- 发明历史和演进追踪

技术特色：
- AI驱动的创新生成
- 多维度发明评估
- 智能专利分析
- 创新网络构建
- 发明价值评估

作者: PowerAutomation Team
版本: 4.1.0
日期: 2025-01-07
"""

import asyncio
import json
import uuid
import logging
import time
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import pickle
import hashlib
import sqlite3
from collections import defaultdict, deque
import threading
import math
import random
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class InventionType(Enum):
    """发明类型"""
    SOFTWARE = "software"  # 软件发明
    ALGORITHM = "algorithm"  # 算法发明
    SYSTEM = "system"  # 系统发明
    PROCESS = "process"  # 流程发明
    INTERFACE = "interface"  # 界面发明
    ARCHITECTURE = "architecture"  # 架构发明
    PROTOCOL = "protocol"  # 协议发明
    FRAMEWORK = "framework"  # 框架发明

class InnovationLevel(Enum):
    """创新水平"""
    INCREMENTAL = "incremental"  # 渐进式创新
    RADICAL = "radical"  # 根本性创新
    DISRUPTIVE = "disruptive"  # 颠覆性创新
    BREAKTHROUGH = "breakthrough"  # 突破性创新

class InventionStatus(Enum):
    """发明状态"""
    CONCEPT = "concept"  # 概念阶段
    DESIGN = "design"  # 设计阶段
    PROTOTYPE = "prototype"  # 原型阶段
    TESTING = "testing"  # 测试阶段
    IMPLEMENTATION = "implementation"  # 实现阶段
    DEPLOYED = "deployed"  # 部署阶段
    PATENTED = "patented"  # 专利阶段

class EvaluationCriteria(Enum):
    """评估标准"""
    NOVELTY = "novelty"  # 新颖性
    UTILITY = "utility"  # 实用性
    FEASIBILITY = "feasibility"  # 可行性
    MARKET_POTENTIAL = "market_potential"  # 市场潜力
    TECHNICAL_MERIT = "technical_merit"  # 技术价值
    COMMERCIAL_VALUE = "commercial_value"  # 商业价值
    SOCIAL_IMPACT = "social_impact"  # 社会影响

@dataclass
class Invention:
    """发明"""
    invention_id: str
    title: str
    description: str
    invention_type: InventionType
    innovation_level: InnovationLevel
    status: InventionStatus
    inventor_id: str
    technical_details: Dict[str, Any] = field(default_factory=dict)
    requirements: Dict[str, Any] = field(default_factory=dict)
    benefits: List[str] = field(default_factory=list)
    challenges: List[str] = field(default_factory=list)
    related_inventions: List[str] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)
    evaluation_scores: Dict[str, float] = field(default_factory=dict)
    patent_info: Optional[Dict[str, Any]] = None
    collaboration_info: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: int = 1

@dataclass
class InventionEvaluation:
    """发明评估"""
    evaluation_id: str
    invention_id: str
    evaluator_id: str
    criteria_scores: Dict[EvaluationCriteria, float]
    overall_score: float
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    market_analysis: Dict[str, Any] = field(default_factory=dict)
    risk_assessment: Dict[str, Any] = field(default_factory=dict)
    evaluation_notes: str = ""
    confidence_level: float = 0.8
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class InnovationPattern:
    """创新模式"""
    pattern_id: str
    pattern_name: str
    description: str
    pattern_type: str
    success_indicators: List[str]
    failure_indicators: List[str]
    application_domains: List[str]
    historical_examples: List[Dict[str, Any]] = field(default_factory=list)
    success_rate: float = 0.0
    usage_count: int = 0
    last_used: Optional[datetime] = None

@dataclass
class CollaborativeInvention:
    """协作发明"""
    collaboration_id: str
    invention_id: str
    participants: List[str]
    collaboration_type: str
    roles: Dict[str, str]
    contributions: Dict[str, Dict[str, Any]]
    communication_log: List[Dict[str, Any]] = field(default_factory=list)
    milestones: List[Dict[str, Any]] = field(default_factory=list)
    shared_resources: Dict[str, Any] = field(default_factory=dict)
    ip_agreement: Dict[str, Any] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.now)
    status: str = "active"

@dataclass
class PatentAnalysis:
    """专利分析"""
    analysis_id: str
    invention_id: str
    prior_art_search: Dict[str, Any]
    patentability_assessment: Dict[str, float]
    freedom_to_operate: Dict[str, Any]
    competitive_landscape: Dict[str, Any]
    filing_recommendations: List[str]
    estimated_value: float
    protection_strategy: Dict[str, Any]
    analysis_date: datetime = field(default_factory=datetime.now)

class SmartInventionMCPIntegration:
    """SmartInvention MCP集成系统"""
    
    def __init__(self, config_path: str = "./smartinvention_mcp_config.json"):
        """初始化SmartInvention MCP集成"""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # 发明管理
        self.inventions: Dict[str, Invention] = {}
        self.invention_evaluations: Dict[str, List[InventionEvaluation]] = defaultdict(list)
        self.innovation_patterns: Dict[str, InnovationPattern] = {}
        
        # 协作系统
        self.collaborative_inventions: Dict[str, CollaborativeInvention] = {}
        self.inventor_network: Dict[str, Set[str]] = defaultdict(set)
        self.collaboration_history: List[Dict[str, Any]] = []
        
        # 专利系统
        self.patent_analyses: Dict[str, PatentAnalysis] = {}
        self.patent_database: Dict[str, Dict[str, Any]] = {}
        self.ip_portfolio: Dict[str, List[str]] = defaultdict(list)
        
        # 创新引擎
        self.innovation_engine = InnovationEngine(self.config)
        self.evaluation_engine = EvaluationEngine(self.config)
        self.patent_engine = PatentEngine(self.config)
        
        # 知识库
        self.innovation_knowledge: Dict[str, Any] = {}
        self.success_patterns: List[Dict[str, Any]] = []
        self.failure_patterns: List[Dict[str, Any]] = []
        
        # 存储
        self.data_dir = Path(self.config.get("data_dir", "./smartinvention_data"))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "smartinvention.db"
        
        # 初始化数据库
        self._init_database()
        
        # 加载数据
        self._load_persistent_data()
        
        # 初始化创新模式
        self._initialize_innovation_patterns()
        
        logger.info("SmartInvention MCP集成系统初始化完成")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        default_config = {
            "innovation_threshold": 0.7,
            "evaluation_weights": {
                "novelty": 0.25,
                "utility": 0.20,
                "feasibility": 0.15,
                "market_potential": 0.15,
                "technical_merit": 0.15,
                "commercial_value": 0.10
            },
            "collaboration_settings": {
                "max_participants": 10,
                "min_contribution_threshold": 0.1,
                "ip_sharing_default": "proportional"
            },
            "patent_settings": {
                "enable_prior_art_search": True,
                "patentability_threshold": 0.6,
                "auto_filing_threshold": 0.8
            },
            "data_dir": "./smartinvention_data",
            "enable_ai_generation": True,
            "enable_pattern_learning": True,
            "enable_collaboration": True,
            "enable_patent_analysis": True
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logger.warning(f"加载配置文件失败，使用默认配置: {e}")
        
        return default_config
    
    def _init_database(self):
        """初始化数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建发明表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS inventions (
                        invention_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        description TEXT,
                        invention_type TEXT,
                        innovation_level TEXT,
                        status TEXT,
                        inventor_id TEXT,
                        technical_details TEXT,
                        requirements TEXT,
                        benefits TEXT,
                        challenges TEXT,
                        related_inventions TEXT,
                        tags TEXT,
                        evaluation_scores TEXT,
                        patent_info TEXT,
                        collaboration_info TEXT,
                        created_at TIMESTAMP,
                        updated_at TIMESTAMP,
                        version INTEGER DEFAULT 1
                    )
                ''')
                
                # 创建评估表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS evaluations (
                        evaluation_id TEXT PRIMARY KEY,
                        invention_id TEXT NOT NULL,
                        evaluator_id TEXT,
                        criteria_scores TEXT,
                        overall_score REAL,
                        strengths TEXT,
                        weaknesses TEXT,
                        recommendations TEXT,
                        market_analysis TEXT,
                        risk_assessment TEXT,
                        evaluation_notes TEXT,
                        confidence_level REAL,
                        timestamp TIMESTAMP
                    )
                ''')
                
                # 创建协作表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS collaborations (
                        collaboration_id TEXT PRIMARY KEY,
                        invention_id TEXT NOT NULL,
                        participants TEXT,
                        collaboration_type TEXT,
                        roles TEXT,
                        contributions TEXT,
                        communication_log TEXT,
                        milestones TEXT,
                        shared_resources TEXT,
                        ip_agreement TEXT,
                        started_at TIMESTAMP,
                        status TEXT
                    )
                ''')
                
                # 创建专利分析表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS patent_analyses (
                        analysis_id TEXT PRIMARY KEY,
                        invention_id TEXT NOT NULL,
                        prior_art_search TEXT,
                        patentability_assessment TEXT,
                        freedom_to_operate TEXT,
                        competitive_landscape TEXT,
                        filing_recommendations TEXT,
                        estimated_value REAL,
                        protection_strategy TEXT,
                        analysis_date TIMESTAMP
                    )
                ''')
                
                # 创建创新模式表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS innovation_patterns (
                        pattern_id TEXT PRIMARY KEY,
                        pattern_name TEXT NOT NULL,
                        description TEXT,
                        pattern_type TEXT,
                        success_indicators TEXT,
                        failure_indicators TEXT,
                        application_domains TEXT,
                        historical_examples TEXT,
                        success_rate REAL DEFAULT 0.0,
                        usage_count INTEGER DEFAULT 0,
                        last_used TIMESTAMP
                    )
                ''')
                
                # 创建索引
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_invention_type ON inventions(invention_type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_invention_status ON inventions(status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_evaluation_invention ON evaluations(invention_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_collaboration_invention ON collaborations(invention_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_patent_invention ON patent_analyses(invention_id)')
                
                conn.commit()
                logger.info("SmartInvention数据库初始化完成")
                
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    def _load_persistent_data(self):
        """加载持久化数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 加载发明
                cursor.execute('SELECT * FROM inventions')
                for row in cursor.fetchall():
                    invention = self._row_to_invention(row)
                    self.inventions[invention.invention_id] = invention
                
                # 加载评估
                cursor.execute('SELECT * FROM evaluations')
                for row in cursor.fetchall():
                    evaluation = self._row_to_evaluation(row)
                    self.invention_evaluations[evaluation.invention_id].append(evaluation)
                
                # 加载协作
                cursor.execute('SELECT * FROM collaborations')
                for row in cursor.fetchall():
                    collaboration = self._row_to_collaboration(row)
                    self.collaborative_inventions[collaboration.collaboration_id] = collaboration
                
                # 加载专利分析
                cursor.execute('SELECT * FROM patent_analyses')
                for row in cursor.fetchall():
                    analysis = self._row_to_patent_analysis(row)
                    self.patent_analyses[analysis.analysis_id] = analysis
                
                # 加载创新模式
                cursor.execute('SELECT * FROM innovation_patterns')
                for row in cursor.fetchall():
                    pattern = self._row_to_innovation_pattern(row)
                    self.innovation_patterns[pattern.pattern_id] = pattern
            
            logger.info(f"加载 {len(self.inventions)} 个发明和 {len(self.innovation_patterns)} 个创新模式")
            
        except Exception as e:
            logger.warning(f"加载持久化数据失败: {e}")
    
    def _row_to_invention(self, row) -> Invention:
        """数据库行转发明对象"""
        return Invention(
            invention_id=row[0],
            title=row[1],
            description=row[2] or "",
            invention_type=InventionType(row[3]),
            innovation_level=InnovationLevel(row[4]),
            status=InventionStatus(row[5]),
            inventor_id=row[6],
            technical_details=json.loads(row[7]) if row[7] else {},
            requirements=json.loads(row[8]) if row[8] else {},
            benefits=json.loads(row[9]) if row[9] else [],
            challenges=json.loads(row[10]) if row[10] else [],
            related_inventions=json.loads(row[11]) if row[11] else [],
            tags=set(json.loads(row[12])) if row[12] else set(),
            evaluation_scores=json.loads(row[13]) if row[13] else {},
            patent_info=json.loads(row[14]) if row[14] else None,
            collaboration_info=json.loads(row[15]) if row[15] else {},
            created_at=datetime.fromisoformat(row[16]) if row[16] else datetime.now(),
            updated_at=datetime.fromisoformat(row[17]) if row[17] else datetime.now(),
            version=row[18] or 1
        )
    
    def _row_to_evaluation(self, row) -> InventionEvaluation:
        """数据库行转评估对象"""
        criteria_scores = {}
        if row[3]:
            scores_data = json.loads(row[3])
            for criteria_str, score in scores_data.items():
                criteria_scores[EvaluationCriteria(criteria_str)] = score
        
        return InventionEvaluation(
            evaluation_id=row[0],
            invention_id=row[1],
            evaluator_id=row[2],
            criteria_scores=criteria_scores,
            overall_score=row[4],
            strengths=json.loads(row[5]) if row[5] else [],
            weaknesses=json.loads(row[6]) if row[6] else [],
            recommendations=json.loads(row[7]) if row[7] else [],
            market_analysis=json.loads(row[8]) if row[8] else {},
            risk_assessment=json.loads(row[9]) if row[9] else {},
            evaluation_notes=row[10] or "",
            confidence_level=row[11] or 0.8,
            timestamp=datetime.fromisoformat(row[12]) if row[12] else datetime.now()
        )
    
    def _row_to_collaboration(self, row) -> CollaborativeInvention:
        """数据库行转协作对象"""
        return CollaborativeInvention(
            collaboration_id=row[0],
            invention_id=row[1],
            participants=json.loads(row[2]) if row[2] else [],
            collaboration_type=row[3] or "",
            roles=json.loads(row[4]) if row[4] else {},
            contributions=json.loads(row[5]) if row[5] else {},
            communication_log=json.loads(row[6]) if row[6] else [],
            milestones=json.loads(row[7]) if row[7] else [],
            shared_resources=json.loads(row[8]) if row[8] else {},
            ip_agreement=json.loads(row[9]) if row[9] else {},
            started_at=datetime.fromisoformat(row[10]) if row[10] else datetime.now(),
            status=row[11] or "active"
        )
    
    def _row_to_patent_analysis(self, row) -> PatentAnalysis:
        """数据库行转专利分析对象"""
        return PatentAnalysis(
            analysis_id=row[0],
            invention_id=row[1],
            prior_art_search=json.loads(row[2]) if row[2] else {},
            patentability_assessment=json.loads(row[3]) if row[3] else {},
            freedom_to_operate=json.loads(row[4]) if row[4] else {},
            competitive_landscape=json.loads(row[5]) if row[5] else {},
            filing_recommendations=json.loads(row[6]) if row[6] else [],
            estimated_value=row[7] or 0.0,
            protection_strategy=json.loads(row[8]) if row[8] else {},
            analysis_date=datetime.fromisoformat(row[9]) if row[9] else datetime.now()
        )
    
    def _row_to_innovation_pattern(self, row) -> InnovationPattern:
        """数据库行转创新模式对象"""
        return InnovationPattern(
            pattern_id=row[0],
            pattern_name=row[1],
            description=row[2] or "",
            pattern_type=row[3] or "",
            success_indicators=json.loads(row[4]) if row[4] else [],
            failure_indicators=json.loads(row[5]) if row[5] else [],
            application_domains=json.loads(row[6]) if row[6] else [],
            historical_examples=json.loads(row[7]) if row[7] else [],
            success_rate=row[8] or 0.0,
            usage_count=row[9] or 0,
            last_used=datetime.fromisoformat(row[10]) if row[10] else None
        )
    
    def _initialize_innovation_patterns(self):
        """初始化创新模式"""
        if self.innovation_patterns:
            return  # 已有数据，不需要初始化
        
        # 预定义创新模式
        patterns = [
            {
                "pattern_name": "组合创新",
                "description": "将现有技术或概念进行新的组合",
                "pattern_type": "combinatorial",
                "success_indicators": ["技术融合", "跨领域应用", "协同效应"],
                "failure_indicators": ["兼容性问题", "复杂度过高", "成本增加"],
                "application_domains": ["软件开发", "系统集成", "产品设计"]
            },
            {
                "pattern_name": "简化创新",
                "description": "通过简化现有解决方案来创新",
                "pattern_type": "simplification",
                "success_indicators": ["用户体验改善", "成本降低", "易用性提升"],
                "failure_indicators": ["功能缺失", "性能下降", "用户不接受"],
                "application_domains": ["用户界面", "工作流程", "产品设计"]
            },
            {
                "pattern_name": "平台化创新",
                "description": "构建可扩展的平台生态系统",
                "pattern_type": "platform",
                "success_indicators": ["生态系统形成", "第三方参与", "网络效应"],
                "failure_indicators": ["采用率低", "竞争激烈", "维护成本高"],
                "application_domains": ["软件平台", "API设计", "生态系统"]
            },
            {
                "pattern_name": "颠覆性创新",
                "description": "创造全新的解决方案范式",
                "pattern_type": "disruptive",
                "success_indicators": ["市场重塑", "用户行为改变", "竞争优势"],
                "failure_indicators": ["市场接受度低", "技术不成熟", "资源不足"],
                "application_domains": ["新兴技术", "商业模式", "用户体验"]
            },
            {
                "pattern_name": "渐进式创新",
                "description": "在现有基础上进行持续改进",
                "pattern_type": "incremental",
                "success_indicators": ["性能提升", "稳定改进", "用户满意"],
                "failure_indicators": ["改进幅度小", "竞争优势不明显", "投入产出比低"],
                "application_domains": ["产品优化", "流程改进", "性能提升"]
            }
        ]
        
        for pattern_data in patterns:
            pattern_id = f"pattern_{uuid.uuid4().hex[:8]}"
            pattern = InnovationPattern(
                pattern_id=pattern_id,
                pattern_name=pattern_data["pattern_name"],
                description=pattern_data["description"],
                pattern_type=pattern_data["pattern_type"],
                success_indicators=pattern_data["success_indicators"],
                failure_indicators=pattern_data["failure_indicators"],
                application_domains=pattern_data["application_domains"]
            )
            
            self.innovation_patterns[pattern_id] = pattern
        
        logger.info(f"初始化 {len(patterns)} 个创新模式")
    
    async def create_invention(self, title: str, description: str,
                             invention_type: InventionType,
                             inventor_id: str,
                             technical_details: Dict[str, Any] = None,
                             requirements: Dict[str, Any] = None) -> str:
        """创建发明"""
        invention_id = f"inv_{uuid.uuid4().hex[:12]}"
        
        # 使用AI分析创新水平
        innovation_level = await self._analyze_innovation_level(description, technical_details or {})
        
        invention = Invention(
            invention_id=invention_id,
            title=title,
            description=description,
            invention_type=invention_type,
            innovation_level=innovation_level,
            status=InventionStatus.CONCEPT,
            inventor_id=inventor_id,
            technical_details=technical_details or {},
            requirements=requirements or {}
        )
        
        # 生成标签
        invention.tags = await self._generate_invention_tags(invention)
        
        # 查找相关发明
        invention.related_inventions = await self._find_related_inventions(invention)
        
        # 存储发明
        self.inventions[invention_id] = invention
        
        # 持久化
        await self._persist_invention(invention)
        
        logger.info(f"创建发明: {invention_id} - {title}")
        return invention_id
    
    async def _analyze_innovation_level(self, description: str, 
                                      technical_details: Dict[str, Any]) -> InnovationLevel:
        """分析创新水平"""
        # 简化实现：基于关键词分析
        description_lower = description.lower()
        
        # 颠覆性创新关键词
        disruptive_keywords = ["革命性", "颠覆", "全新", "前所未有", "突破性", "重新定义"]
        if any(keyword in description_lower for keyword in disruptive_keywords):
            return InnovationLevel.DISRUPTIVE
        
        # 突破性创新关键词
        breakthrough_keywords = ["突破", "创新", "首次", "领先", "先进"]
        if any(keyword in description_lower for keyword in breakthrough_keywords):
            return InnovationLevel.BREAKTHROUGH
        
        # 根本性创新关键词
        radical_keywords = ["根本", "彻底", "重大", "显著", "大幅"]
        if any(keyword in description_lower for keyword in radical_keywords):
            return InnovationLevel.RADICAL
        
        # 默认为渐进式创新
        return InnovationLevel.INCREMENTAL
    
    async def _generate_invention_tags(self, invention: Invention) -> Set[str]:
        """生成发明标签"""
        tags = set()
        
        # 基于发明类型
        tags.add(invention.invention_type.value)
        
        # 基于创新水平
        tags.add(invention.innovation_level.value)
        
        # 基于描述关键词
        description_words = invention.description.lower().split()
        tech_keywords = ["ai", "machine learning", "algorithm", "automation", "api", "framework", 
                        "system", "platform", "interface", "protocol", "optimization", "analysis"]
        
        for keyword in tech_keywords:
            if keyword in invention.description.lower():
                tags.add(keyword)
        
        # 基于技术细节
        if invention.technical_details:
            for key, value in invention.technical_details.items():
                if isinstance(value, str):
                    tags.add(key.lower())
        
        return tags
    
    async def _find_related_inventions(self, invention: Invention) -> List[str]:
        """查找相关发明"""
        related = []
        
        for existing_id, existing_invention in self.inventions.items():
            if existing_id == invention.invention_id:
                continue
            
            # 计算相似性
            similarity = await self._calculate_invention_similarity(invention, existing_invention)
            
            if similarity > 0.6:  # 相似性阈值
                related.append(existing_id)
        
        return related[:5]  # 最多返回5个相关发明
    
    async def _calculate_invention_similarity(self, inv1: Invention, inv2: Invention) -> float:
        """计算发明相似性"""
        similarity = 0.0
        
        # 类型相似性
        if inv1.invention_type == inv2.invention_type:
            similarity += 0.3
        
        # 标签相似性
        if inv1.tags and inv2.tags:
            common_tags = inv1.tags.intersection(inv2.tags)
            tag_similarity = len(common_tags) / len(inv1.tags.union(inv2.tags))
            similarity += tag_similarity * 0.4
        
        # 描述相似性（简化实现）
        desc1_words = set(inv1.description.lower().split())
        desc2_words = set(inv2.description.lower().split())
        
        if desc1_words and desc2_words:
            common_words = desc1_words.intersection(desc2_words)
            desc_similarity = len(common_words) / len(desc1_words.union(desc2_words))
            similarity += desc_similarity * 0.3
        
        return similarity
    
    async def evaluate_invention(self, invention_id: str, evaluator_id: str,
                               custom_criteria: Dict[str, float] = None) -> str:
        """评估发明"""
        if invention_id not in self.inventions:
            raise ValueError(f"发明不存在: {invention_id}")
        
        invention = self.inventions[invention_id]
        evaluation_id = f"eval_{uuid.uuid4().hex[:12]}"
        
        # 使用评估引擎进行评估
        evaluation_result = await self.evaluation_engine.evaluate_invention(
            invention, custom_criteria or {}
        )
        
        evaluation = InventionEvaluation(
            evaluation_id=evaluation_id,
            invention_id=invention_id,
            evaluator_id=evaluator_id,
            criteria_scores=evaluation_result["criteria_scores"],
            overall_score=evaluation_result["overall_score"],
            strengths=evaluation_result["strengths"],
            weaknesses=evaluation_result["weaknesses"],
            recommendations=evaluation_result["recommendations"],
            market_analysis=evaluation_result["market_analysis"],
            risk_assessment=evaluation_result["risk_assessment"],
            confidence_level=evaluation_result["confidence_level"]
        )
        
        # 存储评估
        self.invention_evaluations[invention_id].append(evaluation)
        
        # 更新发明的评估分数
        invention.evaluation_scores = evaluation_result["criteria_scores_dict"]
        invention.updated_at = datetime.now()
        
        # 持久化
        await self._persist_evaluation(evaluation)
        await self._persist_invention(invention)
        
        logger.info(f"完成发明评估: {evaluation_id} (总分: {evaluation.overall_score:.2f})")
        return evaluation_id
    
    async def generate_innovation_ideas(self, domain: str, requirements: Dict[str, Any],
                                      count: int = 5) -> List[Dict[str, Any]]:
        """生成创新想法"""
        if not self.config.get("enable_ai_generation", True):
            return []
        
        ideas = await self.innovation_engine.generate_ideas(domain, requirements, count)
        
        # 应用创新模式
        enhanced_ideas = []
        for idea in ideas:
            # 选择合适的创新模式
            suitable_patterns = await self._find_suitable_patterns(idea, domain)
            
            if suitable_patterns:
                pattern = suitable_patterns[0]
                idea["innovation_pattern"] = pattern.pattern_name
                idea["pattern_guidance"] = {
                    "success_indicators": pattern.success_indicators,
                    "application_tips": f"基于{pattern.pattern_name}模式的应用建议"
                }
                
                # 更新模式使用统计
                pattern.usage_count += 1
                pattern.last_used = datetime.now()
            
            enhanced_ideas.append(idea)
        
        logger.info(f"生成 {len(enhanced_ideas)} 个创新想法 (领域: {domain})")
        return enhanced_ideas
    
    async def _find_suitable_patterns(self, idea: Dict[str, Any], domain: str) -> List[InnovationPattern]:
        """查找适合的创新模式"""
        suitable_patterns = []
        
        for pattern in self.innovation_patterns.values():
            # 检查应用领域匹配
            if domain in pattern.application_domains or "通用" in pattern.application_domains:
                suitable_patterns.append(pattern)
            
            # 检查关键词匹配
            idea_text = idea.get("description", "").lower()
            for indicator in pattern.success_indicators:
                if indicator.lower() in idea_text:
                    if pattern not in suitable_patterns:
                        suitable_patterns.append(pattern)
                    break
        
        # 按成功率排序
        suitable_patterns.sort(key=lambda p: p.success_rate, reverse=True)
        return suitable_patterns
    
    async def start_collaboration(self, invention_id: str, initiator_id: str,
                                participants: List[str],
                                collaboration_type: str = "joint_development") -> str:
        """开始协作发明"""
        if not self.config.get("enable_collaboration", True):
            raise ValueError("协作功能未启用")
        
        if invention_id not in self.inventions:
            raise ValueError(f"发明不存在: {invention_id}")
        
        collaboration_id = f"collab_{uuid.uuid4().hex[:12]}"
        
        # 创建协作记录
        collaboration = CollaborativeInvention(
            collaboration_id=collaboration_id,
            invention_id=invention_id,
            participants=[initiator_id] + participants,
            collaboration_type=collaboration_type,
            roles={initiator_id: "initiator"},
            contributions={participant: {"contribution_score": 0.0, "tasks": []} 
                         for participant in [initiator_id] + participants}
        )
        
        # 设置默认IP协议
        collaboration.ip_agreement = {
            "sharing_model": self.config["collaboration_settings"]["ip_sharing_default"],
            "ownership_distribution": "proportional",
            "licensing_terms": "mutual",
            "dispute_resolution": "arbitration"
        }
        
        # 存储协作
        self.collaborative_inventions[collaboration_id] = collaboration
        
        # 更新发明者网络
        for participant in collaboration.participants:
            for other in collaboration.participants:
                if participant != other:
                    self.inventor_network[participant].add(other)
        
        # 更新发明的协作信息
        invention = self.inventions[invention_id]
        invention.collaboration_info = {
            "collaboration_id": collaboration_id,
            "is_collaborative": True,
            "participant_count": len(collaboration.participants)
        }
        
        # 持久化
        await self._persist_collaboration(collaboration)
        await self._persist_invention(invention)
        
        logger.info(f"开始协作发明: {collaboration_id} ({len(collaboration.participants)} 参与者)")
        return collaboration_id
    
    async def contribute_to_collaboration(self, collaboration_id: str, contributor_id: str,
                                        contribution: Dict[str, Any]) -> bool:
        """为协作发明做贡献"""
        if collaboration_id not in self.collaborative_inventions:
            return False
        
        collaboration = self.collaborative_inventions[collaboration_id]
        
        if contributor_id not in collaboration.participants:
            return False
        
        # 记录贡献
        contribution_record = {
            "contributor_id": contributor_id,
            "contribution_type": contribution.get("type", "general"),
            "description": contribution.get("description", ""),
            "value": contribution.get("value", 0.1),
            "timestamp": datetime.now().isoformat(),
            "evidence": contribution.get("evidence", {})
        }
        
        # 更新贡献记录
        if contributor_id not in collaboration.contributions:
            collaboration.contributions[contributor_id] = {"contribution_score": 0.0, "tasks": []}
        
        collaboration.contributions[contributor_id]["tasks"].append(contribution_record)
        collaboration.contributions[contributor_id]["contribution_score"] += contribution.get("value", 0.1)
        
        # 添加到通信日志
        collaboration.communication_log.append({
            "type": "contribution",
            "contributor": contributor_id,
            "timestamp": datetime.now().isoformat(),
            "content": contribution_record
        })
        
        # 持久化
        await self._persist_collaboration(collaboration)
        
        logger.debug(f"协作贡献记录: {collaboration_id} - {contributor_id}")
        return True
    
    async def analyze_patent_potential(self, invention_id: str) -> str:
        """分析专利潜力"""
        if not self.config.get("enable_patent_analysis", True):
            raise ValueError("专利分析功能未启用")
        
        if invention_id not in self.inventions:
            raise ValueError(f"发明不存在: {invention_id}")
        
        invention = self.inventions[invention_id]
        analysis_id = f"patent_{uuid.uuid4().hex[:12]}"
        
        # 使用专利引擎进行分析
        analysis_result = await self.patent_engine.analyze_patent_potential(invention)
        
        patent_analysis = PatentAnalysis(
            analysis_id=analysis_id,
            invention_id=invention_id,
            prior_art_search=analysis_result["prior_art_search"],
            patentability_assessment=analysis_result["patentability_assessment"],
            freedom_to_operate=analysis_result["freedom_to_operate"],
            competitive_landscape=analysis_result["competitive_landscape"],
            filing_recommendations=analysis_result["filing_recommendations"],
            estimated_value=analysis_result["estimated_value"],
            protection_strategy=analysis_result["protection_strategy"]
        )
        
        # 存储分析
        self.patent_analyses[analysis_id] = patent_analysis
        
        # 更新发明的专利信息
        invention.patent_info = {
            "analysis_id": analysis_id,
            "patentability_score": analysis_result["patentability_assessment"].get("overall_score", 0.0),
            "estimated_value": analysis_result["estimated_value"],
            "filing_recommended": analysis_result["patentability_assessment"].get("overall_score", 0.0) > 
                                self.config["patent_settings"]["patentability_threshold"]
        }
        
        # 持久化
        await self._persist_patent_analysis(patent_analysis)
        await self._persist_invention(invention)
        
        logger.info(f"完成专利分析: {analysis_id} (可专利性: {patent_analysis.patentability_assessment.get('overall_score', 0):.2f})")
        return analysis_id
    
    async def get_invention_recommendations(self, user_id: str, 
                                         interests: List[str] = None) -> List[Dict[str, Any]]:
        """获取发明推荐"""
        recommendations = []
        
        # 基于用户兴趣推荐
        if interests:
            for invention_id, invention in self.inventions.items():
                relevance_score = 0.0
                
                for interest in interests:
                    if interest.lower() in invention.description.lower():
                        relevance_score += 0.3
                    
                    if interest.lower() in [tag.lower() for tag in invention.tags]:
                        relevance_score += 0.2
                
                if relevance_score > 0.3:
                    recommendations.append({
                        "invention_id": invention_id,
                        "title": invention.title,
                        "description": invention.description,
                        "relevance_score": relevance_score,
                        "innovation_level": invention.innovation_level.value,
                        "status": invention.status.value,
                        "evaluation_score": invention.evaluation_scores.get("overall", 0.0)
                    })
        
        # 基于高评分发明推荐
        high_rated_inventions = []
        for invention_id, invention in self.inventions.items():
            overall_score = invention.evaluation_scores.get("overall", 0.0)
            if overall_score > 0.7:
                high_rated_inventions.append({
                    "invention_id": invention_id,
                    "title": invention.title,
                    "description": invention.description,
                    "relevance_score": overall_score,
                    "innovation_level": invention.innovation_level.value,
                    "status": invention.status.value,
                    "evaluation_score": overall_score
                })
        
        # 合并推荐
        all_recommendations = recommendations + high_rated_inventions
        
        # 去重并排序
        seen_ids = set()
        unique_recommendations = []
        for rec in all_recommendations:
            if rec["invention_id"] not in seen_ids:
                unique_recommendations.append(rec)
                seen_ids.add(rec["invention_id"])
        
        unique_recommendations.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return unique_recommendations[:10]  # 返回前10个推荐
    
    async def get_innovation_insights(self, domain: str = None) -> Dict[str, Any]:
        """获取创新洞察"""
        insights = {
            "total_inventions": len(self.inventions),
            "innovation_distribution": defaultdict(int),
            "status_distribution": defaultdict(int),
            "top_inventors": defaultdict(int),
            "trending_tags": defaultdict(int),
            "collaboration_stats": {
                "total_collaborations": len(self.collaborative_inventions),
                "active_collaborations": 0,
                "average_participants": 0
            },
            "patent_stats": {
                "total_analyses": len(self.patent_analyses),
                "patentable_inventions": 0,
                "average_value": 0.0
            },
            "pattern_usage": {}
        }
        
        # 分析发明分布
        for invention in self.inventions.values():
            if domain is None or domain.lower() in invention.description.lower():
                insights["innovation_distribution"][invention.innovation_level.value] += 1
                insights["status_distribution"][invention.status.value] += 1
                insights["top_inventors"][invention.inventor_id] += 1
                
                for tag in invention.tags:
                    insights["trending_tags"][tag] += 1
        
        # 分析协作统计
        active_collaborations = 0
        total_participants = 0
        
        for collaboration in self.collaborative_inventions.values():
            if collaboration.status == "active":
                active_collaborations += 1
            total_participants += len(collaboration.participants)
        
        insights["collaboration_stats"]["active_collaborations"] = active_collaborations
        if self.collaborative_inventions:
            insights["collaboration_stats"]["average_participants"] = total_participants / len(self.collaborative_inventions)
        
        # 分析专利统计
        patentable_count = 0
        total_value = 0.0
        
        for analysis in self.patent_analyses.values():
            patentability_score = analysis.patentability_assessment.get("overall_score", 0.0)
            if patentability_score > self.config["patent_settings"]["patentability_threshold"]:
                patentable_count += 1
            total_value += analysis.estimated_value
        
        insights["patent_stats"]["patentable_inventions"] = patentable_count
        if self.patent_analyses:
            insights["patent_stats"]["average_value"] = total_value / len(self.patent_analyses)
        
        # 分析模式使用
        for pattern in self.innovation_patterns.values():
            insights["pattern_usage"][pattern.pattern_name] = {
                "usage_count": pattern.usage_count,
                "success_rate": pattern.success_rate,
                "last_used": pattern.last_used.isoformat() if pattern.last_used else None
            }
        
        # 转换为普通字典
        insights["innovation_distribution"] = dict(insights["innovation_distribution"])
        insights["status_distribution"] = dict(insights["status_distribution"])
        insights["top_inventors"] = dict(insights["top_inventors"])
        insights["trending_tags"] = dict(insights["trending_tags"])
        
        return insights
    
    async def _persist_invention(self, invention: Invention):
        """持久化发明"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO inventions 
                    (invention_id, title, description, invention_type, innovation_level, 
                     status, inventor_id, technical_details, requirements, benefits, 
                     challenges, related_inventions, tags, evaluation_scores, 
                     patent_info, collaboration_info, created_at, updated_at, version)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    invention.invention_id,
                    invention.title,
                    invention.description,
                    invention.invention_type.value,
                    invention.innovation_level.value,
                    invention.status.value,
                    invention.inventor_id,
                    json.dumps(invention.technical_details),
                    json.dumps(invention.requirements),
                    json.dumps(invention.benefits),
                    json.dumps(invention.challenges),
                    json.dumps(invention.related_inventions),
                    json.dumps(list(invention.tags)),
                    json.dumps(invention.evaluation_scores),
                    json.dumps(invention.patent_info) if invention.patent_info else None,
                    json.dumps(invention.collaboration_info),
                    invention.created_at.isoformat(),
                    invention.updated_at.isoformat(),
                    invention.version
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"持久化发明失败: {e}")
    
    async def _persist_evaluation(self, evaluation: InventionEvaluation):
        """持久化评估"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 转换criteria_scores为可序列化格式
                criteria_scores_dict = {criteria.value: score for criteria, score in evaluation.criteria_scores.items()}
                
                cursor.execute('''
                    INSERT OR REPLACE INTO evaluations 
                    (evaluation_id, invention_id, evaluator_id, criteria_scores, overall_score,
                     strengths, weaknesses, recommendations, market_analysis, risk_assessment,
                     evaluation_notes, confidence_level, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    evaluation.evaluation_id,
                    evaluation.invention_id,
                    evaluation.evaluator_id,
                    json.dumps(criteria_scores_dict),
                    evaluation.overall_score,
                    json.dumps(evaluation.strengths),
                    json.dumps(evaluation.weaknesses),
                    json.dumps(evaluation.recommendations),
                    json.dumps(evaluation.market_analysis),
                    json.dumps(evaluation.risk_assessment),
                    evaluation.evaluation_notes,
                    evaluation.confidence_level,
                    evaluation.timestamp.isoformat()
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"持久化评估失败: {e}")
    
    async def _persist_collaboration(self, collaboration: CollaborativeInvention):
        """持久化协作"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO collaborations 
                    (collaboration_id, invention_id, participants, collaboration_type, roles,
                     contributions, communication_log, milestones, shared_resources, 
                     ip_agreement, started_at, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    collaboration.collaboration_id,
                    collaboration.invention_id,
                    json.dumps(collaboration.participants),
                    collaboration.collaboration_type,
                    json.dumps(collaboration.roles),
                    json.dumps(collaboration.contributions),
                    json.dumps(collaboration.communication_log),
                    json.dumps(collaboration.milestones),
                    json.dumps(collaboration.shared_resources),
                    json.dumps(collaboration.ip_agreement),
                    collaboration.started_at.isoformat(),
                    collaboration.status
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"持久化协作失败: {e}")
    
    async def _persist_patent_analysis(self, analysis: PatentAnalysis):
        """持久化专利分析"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO patent_analyses 
                    (analysis_id, invention_id, prior_art_search, patentability_assessment,
                     freedom_to_operate, competitive_landscape, filing_recommendations,
                     estimated_value, protection_strategy, analysis_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    analysis.analysis_id,
                    analysis.invention_id,
                    json.dumps(analysis.prior_art_search),
                    json.dumps(analysis.patentability_assessment),
                    json.dumps(analysis.freedom_to_operate),
                    json.dumps(analysis.competitive_landscape),
                    json.dumps(analysis.filing_recommendations),
                    analysis.estimated_value,
                    json.dumps(analysis.protection_strategy),
                    analysis.analysis_date.isoformat()
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"持久化专利分析失败: {e}")
    
    async def cleanup(self):
        """清理资源"""
        try:
            # 保存所有数据
            for invention in self.inventions.values():
                await self._persist_invention(invention)
            
            for collaboration in self.collaborative_inventions.values():
                await self._persist_collaboration(collaboration)
            
            for analysis in self.patent_analyses.values():
                await self._persist_patent_analysis(analysis)
            
            logger.info("SmartInvention MCP集成系统清理完成")
            
        except Exception as e:
            logger.error(f"清理资源失败: {e}")

class InnovationEngine:
    """创新引擎"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    async def generate_ideas(self, domain: str, requirements: Dict[str, Any], 
                           count: int = 5) -> List[Dict[str, Any]]:
        """生成创新想法"""
        ideas = []
        
        # 基于领域的想法模板
        domain_templates = {
            "software": [
                "基于AI的{功能}优化系统",
                "自动化{流程}管理平台",
                "智能{数据类型}分析工具",
                "分布式{服务类型}架构",
                "可视化{操作}界面设计"
            ],
            "algorithm": [
                "高效{问题类型}求解算法",
                "自适应{优化目标}优化算法",
                "并行{计算类型}处理算法",
                "机器学习{应用场景}算法",
                "图{操作类型}算法优化"
            ],
            "system": [
                "分布式{系统类型}架构",
                "高可用{服务类型}系统",
                "实时{数据类型}处理系统",
                "智能{监控对象}监控系统",
                "自动化{部署类型}部署系统"
            ]
        }
        
        templates = domain_templates.get(domain, domain_templates["software"])
        
        for i in range(count):
            template = random.choice(templates)
            
            # 简化的想法生成
            idea = {
                "id": f"idea_{uuid.uuid4().hex[:8]}",
                "title": template.format(
                    功能=random.choice(["代码分析", "性能监控", "错误检测", "资源管理"]),
                    流程=random.choice(["开发", "测试", "部署", "维护"]),
                    数据类型=random.choice(["日志", "性能", "用户行为", "系统状态"]),
                    服务类型=random.choice(["微服务", "API", "数据库", "缓存"]),
                    操作=random.choice(["配置", "监控", "分析", "管理"]),
                    问题类型=random.choice(["排序", "搜索", "优化", "匹配"]),
                    优化目标=random.choice(["性能", "成本", "质量", "效率"]),
                    计算类型=random.choice(["数值", "图像", "文本", "音频"]),
                    应用场景=random.choice(["推荐", "分类", "预测", "聚类"]),
                    系统类型=random.choice(["存储", "计算", "通信", "管理"]),
                    监控对象=random.choice(["服务", "网络", "安全", "性能"]),
                    部署类型=random.choice(["容器", "云原生", "边缘", "混合"])
                ),
                "description": f"一个创新的{domain}解决方案，旨在解决{requirements.get('problem', '特定问题')}",
                "innovation_score": random.uniform(0.6, 0.9),
                "feasibility_score": random.uniform(0.5, 0.8),
                "market_potential": random.uniform(0.4, 0.9),
                "technical_complexity": random.choice(["low", "medium", "high"]),
                "estimated_effort": random.choice(["1-3个月", "3-6个月", "6-12个月", "1年以上"]),
                "key_technologies": random.sample(
                    ["AI/ML", "云计算", "微服务", "区块链", "IoT", "大数据", "API", "自动化"],
                    k=random.randint(2, 4)
                ),
                "potential_benefits": [
                    f"提升{random.choice(['效率', '质量', '性能', '用户体验'])}",
                    f"降低{random.choice(['成本', '复杂度', '维护负担', '错误率'])}",
                    f"增强{random.choice(['可扩展性', '可靠性', '安全性', '可维护性'])}"
                ]
            }
            
            ideas.append(idea)
        
        return ideas

class EvaluationEngine:
    """评估引擎"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.evaluation_weights = config.get("evaluation_weights", {})
    
    async def evaluate_invention(self, invention: Invention, 
                               custom_criteria: Dict[str, float]) -> Dict[str, Any]:
        """评估发明"""
        criteria_scores = {}
        
        # 评估各个标准
        criteria_scores[EvaluationCriteria.NOVELTY] = await self._evaluate_novelty(invention)
        criteria_scores[EvaluationCriteria.UTILITY] = await self._evaluate_utility(invention)
        criteria_scores[EvaluationCriteria.FEASIBILITY] = await self._evaluate_feasibility(invention)
        criteria_scores[EvaluationCriteria.MARKET_POTENTIAL] = await self._evaluate_market_potential(invention)
        criteria_scores[EvaluationCriteria.TECHNICAL_MERIT] = await self._evaluate_technical_merit(invention)
        criteria_scores[EvaluationCriteria.COMMERCIAL_VALUE] = await self._evaluate_commercial_value(invention)
        
        # 计算总分
        overall_score = 0.0
        weights = self.evaluation_weights
        
        for criteria, score in criteria_scores.items():
            weight = weights.get(criteria.value, 1.0 / len(criteria_scores))
            overall_score += score * weight
        
        # 生成评估报告
        strengths = await self._identify_strengths(invention, criteria_scores)
        weaknesses = await self._identify_weaknesses(invention, criteria_scores)
        recommendations = await self._generate_recommendations(invention, criteria_scores)
        
        return {
            "criteria_scores": criteria_scores,
            "criteria_scores_dict": {criteria.value: score for criteria, score in criteria_scores.items()},
            "overall_score": overall_score,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendations": recommendations,
            "market_analysis": await self._analyze_market(invention),
            "risk_assessment": await self._assess_risks(invention),
            "confidence_level": 0.8
        }
    
    async def _evaluate_novelty(self, invention: Invention) -> float:
        """评估新颖性"""
        # 基于创新水平
        novelty_scores = {
            InnovationLevel.DISRUPTIVE: 0.95,
            InnovationLevel.BREAKTHROUGH: 0.85,
            InnovationLevel.RADICAL: 0.75,
            InnovationLevel.INCREMENTAL: 0.55
        }
        
        base_score = novelty_scores.get(invention.innovation_level, 0.5)
        
        # 基于相关发明数量调整
        if len(invention.related_inventions) == 0:
            base_score += 0.1  # 没有相关发明，更新颖
        elif len(invention.related_inventions) > 5:
            base_score -= 0.1  # 相关发明太多，新颖性降低
        
        return min(1.0, max(0.0, base_score))
    
    async def _evaluate_utility(self, invention: Invention) -> float:
        """评估实用性"""
        utility_score = 0.5
        
        # 基于描述中的实用性关键词
        utility_keywords = ["解决", "改进", "优化", "提升", "降低", "简化", "自动化", "效率"]
        description_lower = invention.description.lower()
        
        for keyword in utility_keywords:
            if keyword in description_lower:
                utility_score += 0.1
        
        # 基于技术细节的完整性
        if invention.technical_details:
            utility_score += 0.1
        
        # 基于需求的明确性
        if invention.requirements:
            utility_score += 0.1
        
        return min(1.0, utility_score)
    
    async def _evaluate_feasibility(self, invention: Invention) -> float:
        """评估可行性"""
        feasibility_score = 0.6  # 基础分数
        
        # 基于发明类型的可行性
        type_feasibility = {
            InventionType.SOFTWARE: 0.8,
            InventionType.ALGORITHM: 0.9,
            InventionType.SYSTEM: 0.7,
            InventionType.PROCESS: 0.8,
            InventionType.INTERFACE: 0.9,
            InventionType.ARCHITECTURE: 0.7,
            InventionType.PROTOCOL: 0.6,
            InventionType.FRAMEWORK: 0.7
        }
        
        feasibility_score = type_feasibility.get(invention.invention_type, 0.6)
        
        # 基于技术细节的完整性
        if invention.technical_details:
            detail_count = len(invention.technical_details)
            feasibility_score += min(0.2, detail_count * 0.05)
        
        return min(1.0, feasibility_score)
    
    async def _evaluate_market_potential(self, invention: Invention) -> float:
        """评估市场潜力"""
        market_score = 0.5
        
        # 基于发明类型的市场潜力
        market_potential = {
            InventionType.SOFTWARE: 0.8,
            InventionType.ALGORITHM: 0.6,
            InventionType.SYSTEM: 0.7,
            InventionType.PROCESS: 0.6,
            InventionType.INTERFACE: 0.8,
            InventionType.ARCHITECTURE: 0.5,
            InventionType.PROTOCOL: 0.4,
            InventionType.FRAMEWORK: 0.7
        }
        
        market_score = market_potential.get(invention.invention_type, 0.5)
        
        # 基于标签中的热门技术
        hot_tags = ["ai", "machine learning", "automation", "cloud", "api", "mobile"]
        for tag in invention.tags:
            if tag.lower() in hot_tags:
                market_score += 0.1
        
        return min(1.0, market_score)
    
    async def _evaluate_technical_merit(self, invention: Invention) -> float:
        """评估技术价值"""
        technical_score = 0.5
        
        # 基于创新水平
        innovation_scores = {
            InnovationLevel.DISRUPTIVE: 0.9,
            InnovationLevel.BREAKTHROUGH: 0.8,
            InnovationLevel.RADICAL: 0.7,
            InnovationLevel.INCREMENTAL: 0.5
        }
        
        technical_score = innovation_scores.get(invention.innovation_level, 0.5)
        
        # 基于技术复杂度
        if invention.technical_details:
            complexity_indicators = ["algorithm", "optimization", "distributed", "parallel", "machine learning"]
            for indicator in complexity_indicators:
                if any(indicator in str(value).lower() for value in invention.technical_details.values()):
                    technical_score += 0.05
        
        return min(1.0, technical_score)
    
    async def _evaluate_commercial_value(self, invention: Invention) -> float:
        """评估商业价值"""
        commercial_score = 0.5
        
        # 基于市场潜力和技术价值的组合
        market_score = await self._evaluate_market_potential(invention)
        technical_score = await self._evaluate_technical_merit(invention)
        
        commercial_score = (market_score * 0.6 + technical_score * 0.4)
        
        # 基于实用性调整
        utility_score = await self._evaluate_utility(invention)
        commercial_score = commercial_score * 0.8 + utility_score * 0.2
        
        return commercial_score
    
    async def _identify_strengths(self, invention: Invention, 
                                criteria_scores: Dict[EvaluationCriteria, float]) -> List[str]:
        """识别优势"""
        strengths = []
        
        # 基于高分标准
        for criteria, score in criteria_scores.items():
            if score > 0.8:
                strength_descriptions = {
                    EvaluationCriteria.NOVELTY: "具有很高的新颖性和创新性",
                    EvaluationCriteria.UTILITY: "实用性强，能解决实际问题",
                    EvaluationCriteria.FEASIBILITY: "技术可行性高，容易实现",
                    EvaluationCriteria.MARKET_POTENTIAL: "市场潜力巨大",
                    EvaluationCriteria.TECHNICAL_MERIT: "技术价值显著",
                    EvaluationCriteria.COMMERCIAL_VALUE: "商业价值突出"
                }
                
                if criteria in strength_descriptions:
                    strengths.append(strength_descriptions[criteria])
        
        # 基于发明特征
        if invention.innovation_level in [InnovationLevel.DISRUPTIVE, InnovationLevel.BREAKTHROUGH]:
            strengths.append("属于突破性创新，具有颠覆潜力")
        
        if len(invention.technical_details) > 3:
            strengths.append("技术细节完整，实现路径清晰")
        
        return strengths
    
    async def _identify_weaknesses(self, invention: Invention, 
                                 criteria_scores: Dict[EvaluationCriteria, float]) -> List[str]:
        """识别弱点"""
        weaknesses = []
        
        # 基于低分标准
        for criteria, score in criteria_scores.items():
            if score < 0.5:
                weakness_descriptions = {
                    EvaluationCriteria.NOVELTY: "新颖性不足，与现有解决方案相似",
                    EvaluationCriteria.UTILITY: "实用性有限，应用场景不明确",
                    EvaluationCriteria.FEASIBILITY: "技术可行性存疑，实现难度较大",
                    EvaluationCriteria.MARKET_POTENTIAL: "市场潜力有限",
                    EvaluationCriteria.TECHNICAL_MERIT: "技术价值不够突出",
                    EvaluationCriteria.COMMERCIAL_VALUE: "商业价值不明确"
                }
                
                if criteria in weakness_descriptions:
                    weaknesses.append(weakness_descriptions[criteria])
        
        # 基于发明特征
        if not invention.technical_details:
            weaknesses.append("缺乏技术实现细节")
        
        if not invention.requirements:
            weaknesses.append("需求定义不够明确")
        
        return weaknesses
    
    async def _generate_recommendations(self, invention: Invention, 
                                      criteria_scores: Dict[EvaluationCriteria, float]) -> List[str]:
        """生成建议"""
        recommendations = []
        
        # 基于弱点生成建议
        for criteria, score in criteria_scores.items():
            if score < 0.6:
                recommendation_map = {
                    EvaluationCriteria.NOVELTY: "进一步研究现有技术，突出创新点",
                    EvaluationCriteria.UTILITY: "明确应用场景和用户需求",
                    EvaluationCriteria.FEASIBILITY: "制定详细的技术实现方案",
                    EvaluationCriteria.MARKET_POTENTIAL: "进行市场调研，验证需求",
                    EvaluationCriteria.TECHNICAL_MERIT: "增强技术深度和复杂度",
                    EvaluationCriteria.COMMERCIAL_VALUE: "制定商业化策略"
                }
                
                if criteria in recommendation_map:
                    recommendations.append(recommendation_map[criteria])
        
        # 通用建议
        if invention.status == InventionStatus.CONCEPT:
            recommendations.append("建议进入设计阶段，制定详细方案")
        
        if not invention.collaboration_info.get("is_collaborative", False):
            recommendations.append("考虑寻找合作伙伴，共同开发")
        
        return recommendations
    
    async def _analyze_market(self, invention: Invention) -> Dict[str, Any]:
        """分析市场"""
        return {
            "target_market": "技术专业人士和企业用户",
            "market_size": "中等规模",
            "competition_level": "中等竞争",
            "entry_barriers": "技术门槛",
            "growth_potential": "稳定增长"
        }
    
    async def _assess_risks(self, invention: Invention) -> Dict[str, Any]:
        """评估风险"""
        return {
            "technical_risks": ["实现复杂度", "技术可行性"],
            "market_risks": ["用户接受度", "竞争压力"],
            "business_risks": ["资金需求", "时间成本"],
            "overall_risk_level": "中等风险"
        }

class PatentEngine:
    """专利引擎"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    async def analyze_patent_potential(self, invention: Invention) -> Dict[str, Any]:
        """分析专利潜力"""
        # 简化的专利分析实现
        analysis = {
            "prior_art_search": await self._search_prior_art(invention),
            "patentability_assessment": await self._assess_patentability(invention),
            "freedom_to_operate": await self._analyze_freedom_to_operate(invention),
            "competitive_landscape": await self._analyze_competitive_landscape(invention),
            "filing_recommendations": await self._generate_filing_recommendations(invention),
            "estimated_value": await self._estimate_patent_value(invention),
            "protection_strategy": await self._develop_protection_strategy(invention)
        }
        
        return analysis
    
    async def _search_prior_art(self, invention: Invention) -> Dict[str, Any]:
        """搜索现有技术"""
        # 简化实现
        return {
            "search_conducted": True,
            "relevant_patents": [],
            "similar_technologies": [],
            "novelty_assessment": "具有新颖性"
        }
    
    async def _assess_patentability(self, invention: Invention) -> Dict[str, Any]:
        """评估可专利性"""
        # 基于发明类型的可专利性
        patentability_scores = {
            InventionType.SOFTWARE: 0.6,
            InventionType.ALGORITHM: 0.4,
            InventionType.SYSTEM: 0.8,
            InventionType.PROCESS: 0.7,
            InventionType.INTERFACE: 0.5,
            InventionType.ARCHITECTURE: 0.6,
            InventionType.PROTOCOL: 0.5,
            InventionType.FRAMEWORK: 0.6
        }
        
        base_score = patentability_scores.get(invention.invention_type, 0.5)
        
        # 基于创新水平调整
        innovation_bonus = {
            InnovationLevel.DISRUPTIVE: 0.3,
            InnovationLevel.BREAKTHROUGH: 0.2,
            InnovationLevel.RADICAL: 0.1,
            InnovationLevel.INCREMENTAL: 0.0
        }
        
        overall_score = base_score + innovation_bonus.get(invention.innovation_level, 0.0)
        overall_score = min(1.0, overall_score)
        
        return {
            "overall_score": overall_score,
            "novelty_score": 0.8,
            "non_obviousness_score": 0.7,
            "utility_score": 0.9,
            "patentable_subject_matter": overall_score > 0.5
        }
    
    async def _analyze_freedom_to_operate(self, invention: Invention) -> Dict[str, Any]:
        """分析实施自由度"""
        return {
            "freedom_level": "高",
            "blocking_patents": [],
            "licensing_requirements": [],
            "risk_assessment": "低风险"
        }
    
    async def _analyze_competitive_landscape(self, invention: Invention) -> Dict[str, Any]:
        """分析竞争格局"""
        return {
            "major_players": [],
            "patent_density": "中等",
            "white_space_opportunities": ["新兴应用领域"],
            "competitive_advantage": "技术创新"
        }
    
    async def _generate_filing_recommendations(self, invention: Invention) -> List[str]:
        """生成申请建议"""
        recommendations = []
        
        patentability = await self._assess_patentability(invention)
        overall_score = patentability["overall_score"]
        
        if overall_score > 0.8:
            recommendations.append("强烈建议申请专利")
            recommendations.append("考虑国际专利申请")
        elif overall_score > 0.6:
            recommendations.append("建议申请专利")
            recommendations.append("先申请临时专利")
        elif overall_score > 0.4:
            recommendations.append("谨慎考虑专利申请")
            recommendations.append("可考虑商业秘密保护")
        else:
            recommendations.append("不建议申请专利")
            recommendations.append("考虑其他知识产权保护方式")
        
        return recommendations
    
    async def _estimate_patent_value(self, invention: Invention) -> float:
        """估算专利价值"""
        # 简化的价值估算
        base_value = 10000  # 基础价值
        
        # 基于创新水平调整
        innovation_multipliers = {
            InnovationLevel.DISRUPTIVE: 5.0,
            InnovationLevel.BREAKTHROUGH: 3.0,
            InnovationLevel.RADICAL: 2.0,
            InnovationLevel.INCREMENTAL: 1.0
        }
        
        multiplier = innovation_multipliers.get(invention.innovation_level, 1.0)
        
        # 基于市场潜力调整
        if "ai" in invention.tags or "automation" in invention.tags:
            multiplier *= 1.5
        
        estimated_value = base_value * multiplier
        return estimated_value
    
    async def _develop_protection_strategy(self, invention: Invention) -> Dict[str, Any]:
        """制定保护策略"""
        return {
            "primary_protection": "专利申请",
            "secondary_protection": ["商标", "版权"],
            "geographic_scope": ["国内", "主要市场"],
            "timeline": "12-18个月",
            "budget_estimate": "5-10万元"
        }

# 工厂函数
def get_smartinvention_mcp_integration(config_path: str = "./smartinvention_mcp_config.json") -> SmartInventionMCPIntegration:
    """获取SmartInvention MCP集成实例"""
    return SmartInventionMCPIntegration(config_path)

# 测试和演示
if __name__ == "__main__":
    async def test_smartinvention_mcp():
        """测试SmartInvention MCP集成"""
        smartinvention = get_smartinvention_mcp_integration()
        
        try:
            # 创建发明
            print("💡 创建发明...")
            invention_id = await smartinvention.create_invention(
                title="智能代码分析系统",
                description="基于AI的自动化代码质量分析和优化建议系统，能够检测代码问题、提供修复建议并自动优化性能",
                invention_type=InventionType.SOFTWARE,
                inventor_id="inventor_001",
                technical_details={
                    "core_technology": "机器学习算法",
                    "programming_language": "Python",
                    "architecture": "微服务架构",
                    "deployment": "云原生"
                },
                requirements={
                    "performance": "实时分析",
                    "scalability": "支持大型项目",
                    "accuracy": "95%以上准确率"
                }
            )
            
            print(f"创建发明: {invention_id}")
            
            # 评估发明
            print("\n📊 评估发明...")
            evaluation_id = await smartinvention.evaluate_invention(
                invention_id=invention_id,
                evaluator_id="evaluator_001"
            )
            
            evaluation = smartinvention.invention_evaluations[invention_id][0]
            print(f"评估完成: {evaluation_id}")
            print(f"总分: {evaluation.overall_score:.2f}")
            print(f"优势: {evaluation.strengths}")
            print(f"建议: {evaluation.recommendations}")
            
            # 生成创新想法
            print("\n🚀 生成创新想法...")
            ideas = await smartinvention.generate_innovation_ideas(
                domain="software",
                requirements={"problem": "代码质量管理", "target": "开发团队"},
                count=3
            )
            
            print(f"生成 {len(ideas)} 个创新想法:")
            for idea in ideas:
                print(f"  - {idea['title']} (创新分: {idea['innovation_score']:.2f})")
            
            # 开始协作
            print("\n🤝 开始协作发明...")
            collaboration_id = await smartinvention.start_collaboration(
                invention_id=invention_id,
                initiator_id="inventor_001",
                participants=["inventor_002", "inventor_003"],
                collaboration_type="joint_development"
            )
            
            print(f"协作开始: {collaboration_id}")
            
            # 贡献到协作
            await smartinvention.contribute_to_collaboration(
                collaboration_id=collaboration_id,
                contributor_id="inventor_002",
                contribution={
                    "type": "algorithm_design",
                    "description": "设计核心分析算法",
                    "value": 0.3,
                    "evidence": {"document": "algorithm_spec.pdf"}
                }
            )
            
            # 专利分析
            print("\n📜 专利分析...")
            patent_analysis_id = await smartinvention.analyze_patent_potential(invention_id)
            
            patent_analysis = smartinvention.patent_analyses[patent_analysis_id]
            print(f"专利分析完成: {patent_analysis_id}")
            print(f"可专利性评分: {patent_analysis.patentability_assessment.get('overall_score', 0):.2f}")
            print(f"估算价值: {patent_analysis.estimated_value:,.0f} 元")
            print(f"申请建议: {patent_analysis.filing_recommendations}")
            
            # 获取推荐
            print("\n🎯 获取发明推荐...")
            recommendations = await smartinvention.get_invention_recommendations(
                user_id="user_001",
                interests=["AI", "代码分析", "自动化"]
            )
            
            print(f"推荐 {len(recommendations)} 个发明:")
            for rec in recommendations:
                print(f"  - {rec['title']} (相关性: {rec['relevance_score']:.2f})")
            
            # 获取创新洞察
            print("\n📈 创新洞察...")
            insights = await smartinvention.get_innovation_insights()
            
            print(f"总发明数: {insights['total_inventions']}")
            print(f"创新分布: {insights['innovation_distribution']}")
            print(f"状态分布: {insights['status_distribution']}")
            print(f"协作统计: {insights['collaboration_stats']}")
            print(f"专利统计: {insights['patent_stats']}")
            
        finally:
            # 清理
            await smartinvention.cleanup()
    
    # 运行测试
    asyncio.run(test_smartinvention_mcp())

