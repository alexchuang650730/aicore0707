#!/usr/bin/env python3
"""
录制即测试核心服务

提供录制即测试的核心功能，包括录制管理、测试生成、
AI优化和与其他系统的集成。
"""

import asyncio
import uuid
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

from .browser_recorder import BrowserRecorder
from .test_generator import TestGenerator
from .playback_engine import PlaybackEngine
from .ai_optimizer import AIOptimizer
from ..stagewise_mcp.stagewise_service import StagewiseService
from ..memoryos_mcp.memory_engine import MemoryEngine

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RecordingSession:
    """录制会话数据结构"""
    id: str
    name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "recording"  # recording, completed, failed
    actions: List[Dict] = None
    screenshots: List[str] = None
    video_path: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.actions is None:
            self.actions = []
        if self.screenshots is None:
            self.screenshots = []
        if self.metadata is None:
            self.metadata = {}

@dataclass
class TestCase:
    """测试用例数据结构"""
    id: str
    name: str
    description: str
    steps: List[Dict]
    assertions: List[Dict]
    created_time: datetime
    source_session_id: str
    file_path: Optional[str] = None
    optimized: bool = False
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class RecordAsTestService:
    """录制即测试核心服务"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化服务"""
        self.config = self._load_config(config_path)
        self.sessions: Dict[str, RecordingSession] = {}
        self.test_cases: Dict[str, TestCase] = {}
        
        # 初始化组件
        self.browser_recorder = BrowserRecorder(self.config.get('browser', {}))
        self.test_generator = TestGenerator(self.config.get('test_generation', {}))
        self.playback_engine = PlaybackEngine(self.config.get('playback', {}))
        self.ai_optimizer = AIOptimizer(self.config.get('ai', {}))
        
        # 集成其他服务
        self.stagewise_service = StagewiseService()
        self.memory_engine = MemoryEngine()
        
        # 创建存储目录
        self._setup_storage_directories()
        
        logger.info("录制即测试服务初始化完成")
    
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """加载配置文件"""
        if config_path is None:
            config_path = Path(__file__).parent / "config" / "record_as_test_config.yaml"
        
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config.get('record_as_test', {})
        except Exception as e:
            logger.warning(f"无法加载配置文件 {config_path}: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            'recording': {
                'auto_start': False,
                'video_quality': 'high',
                'screenshot_interval': 1000,
                'max_session_duration': 3600
            },
            'test_generation': {
                'auto_generate': True,
                'include_screenshots': True,
                'include_video': True,
                'ai_optimization': True
            },
            'browser': {
                'headless': False,
                'window_size': [1920, 1080],
                'user_agent': 'ClaudEditor-RecordAsTest/4.1'
            },
            'ai': {
                'claude_model': 'claude-3-sonnet-20240229',
                'optimization_enabled': True,
                'smart_assertions': True
            },
            'storage': {
                'recordings_path': './recordings',
                'tests_path': './generated_tests',
                'videos_path': './videos',
                'max_storage_size': '10GB'
            }
        }
    
    def _setup_storage_directories(self):
        """设置存储目录"""
        storage_config = self.config.get('storage', {})
        
        self.recordings_path = Path(storage_config.get('recordings_path', './recordings'))
        self.tests_path = Path(storage_config.get('tests_path', './generated_tests'))
        self.videos_path = Path(storage_config.get('videos_path', './videos'))
        
        # 创建目录
        for path in [self.recordings_path, self.tests_path, self.videos_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    async def start_recording_session(self, session_name: str, metadata: Optional[Dict] = None) -> RecordingSession:
        """开始录制会话"""
        session_id = str(uuid.uuid4())
        
        session = RecordingSession(
            id=session_id,
            name=session_name,
            start_time=datetime.now(),
            metadata=metadata or {}
        )
        
        self.sessions[session_id] = session
        
        # 启动浏览器录制
        await self.browser_recorder.start_recording(session_id)
        
        # 保存会话到MemoryOS
        await self._save_session_to_memory(session)
        
        logger.info(f"录制会话已开始: {session_name} (ID: {session_id})")
        return session
    
    async def stop_recording_session(self, session_id: str) -> RecordingSession:
        """停止录制会话"""
        if session_id not in self.sessions:
            raise ValueError(f"录制会话不存在: {session_id}")
        
        session = self.sessions[session_id]
        
        # 停止浏览器录制
        recording_data = await self.browser_recorder.stop_recording(session_id)
        
        # 更新会话数据
        session.end_time = datetime.now()
        session.status = "completed"
        session.actions = recording_data.get('actions', [])
        session.screenshots = recording_data.get('screenshots', [])
        session.video_path = recording_data.get('video_path')
        
        # 保存录制数据
        await self._save_recording_data(session)
        
        # 自动生成测试用例（如果启用）
        if self.config.get('test_generation', {}).get('auto_generate', True):
            await self.generate_test_from_recording(session_id)
        
        logger.info(f"录制会话已完成: {session.name} (ID: {session_id})")
        return session
    
    async def generate_test_from_recording(self, session_id: str) -> TestCase:
        """从录制生成测试用例"""
        if session_id not in self.sessions:
            raise ValueError(f"录制会话不存在: {session_id}")
        
        session = self.sessions[session_id]
        
        # 生成测试用例
        test_case_data = await self.test_generator.generate_from_recording(session)
        
        test_case = TestCase(
            id=str(uuid.uuid4()),
            name=f"Test_{session.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            description=f"从录制会话 '{session.name}' 生成的测试用例",
            steps=test_case_data['steps'],
            assertions=test_case_data['assertions'],
            created_time=datetime.now(),
            source_session_id=session_id
        )
        
        self.test_cases[test_case.id] = test_case
        
        # 保存测试用例文件
        await self._save_test_case_file(test_case)
        
        # AI优化（如果启用）
        if self.config.get('ai', {}).get('optimization_enabled', True):
            await self.optimize_test_with_ai(test_case.id)
        
        logger.info(f"测试用例已生成: {test_case.name} (ID: {test_case.id})")
        return test_case
    
    async def optimize_test_with_ai(self, test_case_id: str) -> TestCase:
        """使用AI优化测试用例"""
        if test_case_id not in self.test_cases:
            raise ValueError(f"测试用例不存在: {test_case_id}")
        
        test_case = self.test_cases[test_case_id]
        
        # AI优化
        optimized_data = await self.ai_optimizer.optimize_test_case(test_case)
        
        # 更新测试用例
        test_case.steps = optimized_data['steps']
        test_case.assertions = optimized_data['assertions']
        test_case.optimized = True
        test_case.metadata['optimization_suggestions'] = optimized_data.get('suggestions', [])
        
        # 重新保存文件
        await self._save_test_case_file(test_case)
        
        logger.info(f"测试用例已优化: {test_case.name}")
        return test_case
    
    async def playback_test_case(self, test_case_id: str) -> Dict:
        """回放测试用例"""
        if test_case_id not in self.test_cases:
            raise ValueError(f"测试用例不存在: {test_case_id}")
        
        test_case = self.test_cases[test_case_id]
        
        # 执行回放
        result = await self.playback_engine.execute_test_case(test_case)
        
        logger.info(f"测试用例回放完成: {test_case.name}, 结果: {result['status']}")
        return result
    
    async def convert_to_stagewise_test(self, test_case_id: str) -> str:
        """转换为Stagewise测试"""
        if test_case_id not in self.test_cases:
            raise ValueError(f"测试用例不存在: {test_case_id}")
        
        test_case = self.test_cases[test_case_id]
        
        # 转换为Stagewise格式
        stagewise_test_id = await self.stagewise_service.create_test_from_record_as_test(test_case)
        
        logger.info(f"已转换为Stagewise测试: {stagewise_test_id}")
        return stagewise_test_id
    
    async def get_session_list(self) -> List[Dict]:
        """获取会话列表"""
        return [
            {
                'id': session.id,
                'name': session.name,
                'start_time': session.start_time.isoformat(),
                'end_time': session.end_time.isoformat() if session.end_time else None,
                'status': session.status,
                'actions_count': len(session.actions),
                'duration': self._calculate_session_duration(session)
            }
            for session in self.sessions.values()
        ]
    
    async def get_test_case_list(self) -> List[Dict]:
        """获取测试用例列表"""
        return [
            {
                'id': test_case.id,
                'name': test_case.name,
                'description': test_case.description,
                'created_time': test_case.created_time.isoformat(),
                'source_session_id': test_case.source_session_id,
                'optimized': test_case.optimized,
                'steps_count': len(test_case.steps),
                'file_path': test_case.file_path
            }
            for test_case in self.test_cases.values()
        ]
    
    async def _save_session_to_memory(self, session: RecordingSession):
        """保存会话到MemoryOS"""
        try:
            context_data = {
                'type': 'recording_session',
                'session_id': session.id,
                'session_name': session.name,
                'start_time': session.start_time.isoformat(),
                'metadata': session.metadata
            }
            
            await self.memory_engine.save_context(
                f"recording_session_{session.id}",
                context_data
            )
        except Exception as e:
            logger.warning(f"保存会话到MemoryOS失败: {e}")
    
    async def _save_recording_data(self, session: RecordingSession):
        """保存录制数据"""
        recording_file = self.recordings_path / f"{session.id}.json"
        
        recording_data = {
            'session': asdict(session),
            'timestamp': datetime.now().isoformat()
        }
        
        with open(recording_file, 'w', encoding='utf-8') as f:
            json.dump(recording_data, f, ensure_ascii=False, indent=2)
    
    async def _save_test_case_file(self, test_case: TestCase):
        """保存测试用例文件"""
        test_file = self.tests_path / f"{test_case.id}.py"
        
        # 生成Python测试文件
        test_code = await self.test_generator.generate_python_test_file(test_case)
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_code)
        
        test_case.file_path = str(test_file)
    
    def _calculate_session_duration(self, session: RecordingSession) -> Optional[float]:
        """计算会话持续时间"""
        if session.end_time:
            return (session.end_time - session.start_time).total_seconds()
        return None
    
    async def cleanup_old_recordings(self, days: int = 30):
        """清理旧的录制数据"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        cleaned_count = 0
        for session_id, session in list(self.sessions.items()):
            if session.start_time < cutoff_date:
                # 删除文件
                recording_file = self.recordings_path / f"{session_id}.json"
                if recording_file.exists():
                    recording_file.unlink()
                
                # 删除视频文件
                if session.video_path and Path(session.video_path).exists():
                    Path(session.video_path).unlink()
                
                # 从内存中删除
                del self.sessions[session_id]
                cleaned_count += 1
        
        logger.info(f"清理了 {cleaned_count} 个旧录制会话")
        return cleaned_count

# 全局服务实例
_service_instance = None

def get_record_as_test_service() -> RecordAsTestService:
    """获取录制即测试服务实例（单例模式）"""
    global _service_instance
    if _service_instance is None:
        _service_instance = RecordAsTestService()
    return _service_instance

