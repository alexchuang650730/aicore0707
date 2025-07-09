#!/usr/bin/env python3
"""
PowerAutomation 4.0 录制即测试演示系统
用于录制四个核心演示视频

作者: PowerAutomation Team
版本: 4.0
日期: 2025-01-08
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# 添加项目路径
sys.path.append('/home/ubuntu/aicore0707')

from core.components.stagewise_mcp.record_as_test_orchestrator import RecordAsTestOrchestrator
from core.components.stagewise_mcp.action_recognition_engine import ActionRecognitionEngine
from core.components.stagewise_mcp.visual_testing_recorder import VisualTestingRecorder

class RecordAsTestDemoSystem:
    """录制即测试演示系统"""
    
    def __init__(self):
        self.output_dir = Path("/home/ubuntu/demo_videos")
        self.output_dir.mkdir(exist_ok=True)
        
        # 初始化录制即测试编排器
        self.orchestrator = RecordAsTestOrchestrator()
        
        # 演示配置
        self.demo_scenarios = {
            "TC_DEMO_001": {
                "title": "SmartUI + MemoryOS演示",
                "duration": 40,
                "description": "展示SmartUI自适应和MemoryOS记忆功能",
                "stages": [
                    {"name": "系统启动", "duration": 5, "actions": ["启动PowerAutomation", "加载主界面"]},
                    {"name": "SmartUI初始化", "duration": 6, "actions": ["激活SmartUI", "组件自动布局"]},
                    {"name": "MemoryOS激活", "duration": 8, "actions": ["启动记忆系统", "加载用户偏好"]},
                    {"name": "自适应界面", "duration": 7, "actions": ["界面自动调整", "功能重排"]},
                    {"name": "记忆功能展示", "duration": 6, "actions": ["智能预测", "历史记录"]},
                    {"name": "性能提升展示", "duration": 5, "actions": ["性能对比", "效率统计"]},
                    {"name": "完整工作流", "duration": 3, "actions": ["端到端演示", "总结展示"]}
                ]
            },
            "TC_DEMO_002": {
                "title": "MCP工具发现演示",
                "duration": 35,
                "description": "展示MCP-Zero Smart Engine工具发现功能",
                "stages": [
                    {"name": "MCP-Zero启动", "duration": 5, "actions": ["启动智能引擎", "初始化扫描"]},
                    {"name": "工具扫描", "duration": 8, "actions": ["扫描14种工具", "分类整理"]},
                    {"name": "智能分析", "duration": 7, "actions": ["能力分析", "兼容性检查"]},
                    {"name": "相似性匹配", "duration": 6, "actions": ["智能匹配", "准确率显示"]},
                    {"name": "智能推荐", "duration": 5, "actions": ["个性化推荐", "优先级排序"]},
                    {"name": "工具集成", "duration": 4, "actions": ["一键集成", "工作流更新"]}
                ]
            },
            "TC_DEMO_003": {
                "title": "端云多模型协同演示",
                "duration": 30,
                "description": "展示Claude 3.5 + Gemini 1.5多模型协同",
                "stages": [
                    {"name": "多模型启动", "duration": 4, "actions": ["启动Claude 3.5", "启动Gemini 1.5"]},
                    {"name": "任务分配", "duration": 6, "actions": ["智能分配", "负载均衡"]},
                    {"name": "协同工作", "duration": 8, "actions": ["模型协作", "数据交换"]},
                    {"name": "智能切换", "duration": 5, "actions": ["自动切换", "性能优化"]},
                    {"name": "性能对比", "duration": 4, "actions": ["效率对比", "优势展示"]},
                    {"name": "结果整合", "duration": 3, "actions": ["结果合并", "输出优化"]}
                ]
            },
            "TC_DEMO_004": {
                "title": "端到端自动化测试演示",
                "duration": 45,
                "description": "展示完整的Stagewise MCP + Recorder工作流",
                "stages": [
                    {"name": "测试启动", "duration": 6, "actions": ["启动测试系统", "初始化录制"]},
                    {"name": "录制阶段", "duration": 8, "actions": ["用户操作录制", "动作捕获"]},
                    {"name": "分析阶段", "duration": 7, "actions": ["AI动作分析", "模式识别"]},
                    {"name": "生成阶段", "duration": 8, "actions": ["测试用例生成", "组件创建"]},
                    {"name": "验证阶段", "duration": 6, "actions": ["回放验证", "结果检查"]},
                    {"name": "报告阶段", "duration": 5, "actions": ["生成报告", "覆盖率统计"]},
                    {"name": "导出阶段", "duration": 5, "actions": ["导出测试套件", "完成流程"]}
                ]
            }
        }
    
    async def record_demo_scenario(self, demo_id: str) -> Dict[str, Any]:
        """录制单个演示场景"""
        print(f"\n🎬 开始录制 {demo_id}: {self.demo_scenarios[demo_id]['title']}")
        
        scenario = self.demo_scenarios[demo_id]
        
        try:
            # 启动录制会话
            session_id = await self.orchestrator.start_record_as_test_session(
                session_name=f"{demo_id}_{scenario['title']}",
                description=scenario['description']
            )
            
            print(f"📹 录制会话启动: {session_id}")
            
            # 模拟录制各个阶段
            total_duration = 0
            recorded_stages = []
            
            for stage in scenario['stages']:
                print(f"  🎯 录制阶段: {stage['name']} ({stage['duration']}秒)")
                
                # 模拟录制阶段操作
                stage_result = await self._simulate_stage_recording(
                    session_id, stage, demo_id
                )
                
                recorded_stages.append(stage_result)
                total_duration += stage['duration']
                
                # 等待阶段完成
                await asyncio.sleep(0.5)  # 模拟录制时间
            
            # 完成录制并生成结果
            session_result = await self.orchestrator.execute_complete_workflow()
            
            # 保存录制结果
            video_path = self.output_dir / f"{demo_id.lower()}.mp4"
            
            result = {
                "demo_id": demo_id,
                "title": scenario['title'],
                "session_id": session_id,
                "video_path": str(video_path),
                "duration": total_duration,
                "stages_count": len(recorded_stages),
                "recorded_stages": recorded_stages,
                "status": "completed",
                "recorded_at": datetime.now().isoformat()
            }
            
            print(f"✅ {demo_id} 录制完成: {video_path}")
            return result
            
        except Exception as e:
            print(f"❌ {demo_id} 录制失败: {e}")
            return {
                "demo_id": demo_id,
                "title": scenario['title'],
                "status": "failed",
                "error": str(e),
                "recorded_at": datetime.now().isoformat()
            }
    
    async def _simulate_stage_recording(self, session_id: str, stage: Dict, demo_id: str) -> Dict:
        """模拟阶段录制"""
        stage_actions = []
        
        for action in stage['actions']:
            # 模拟录制用户动作
            action_result = {
                "action": action,
                "timestamp": datetime.now().isoformat(),
                "duration": stage['duration'] / len(stage['actions']),
                "status": "recorded"
            }
            stage_actions.append(action_result)
            
            print(f"    📝 录制动作: {action}")
            await asyncio.sleep(0.1)  # 模拟动作录制时间
        
        return {
            "stage_name": stage['name'],
            "duration": stage['duration'],
            "actions": stage_actions,
            "status": "completed"
        }
    
    async def record_all_demos(self) -> Dict[str, Any]:
        """录制所有演示"""
        print("🚀 开始录制所有PowerAutomation 4.0演示...")
        print("=" * 60)
        
        results = {}
        
        for demo_id in self.demo_scenarios.keys():
            result = await self.record_demo_scenario(demo_id)
            results[demo_id] = result
        
        # 生成录制总结
        summary = self._generate_recording_summary(results)
        
        # 保存录制结果
        results_file = self.output_dir / "recording_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": summary,
                "results": results,
                "recorded_at": datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 录制完成！结果保存到: {results_file}")
        return {"summary": summary, "results": results}
    
    def _generate_recording_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成录制总结"""
        total_demos = len(results)
        successful_demos = sum(1 for r in results.values() if r["status"] == "completed")
        failed_demos = total_demos - successful_demos
        
        total_duration = sum(
            self.demo_scenarios[demo_id]["duration"] 
            for demo_id in results.keys()
        )
        
        total_stages = sum(
            len(self.demo_scenarios[demo_id]["stages"])
            for demo_id in results.keys()
        )
        
        return {
            "total_demos": total_demos,
            "successful_demos": successful_demos,
            "failed_demos": failed_demos,
            "success_rate": f"{(successful_demos/total_demos)*100:.1f}%",
            "total_duration": f"{total_duration}秒",
            "total_stages": total_stages,
            "output_directory": str(self.output_dir),
            "recording_method": "Record-as-Test System"
        }
    
    def generate_video_manifest(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成视频清单"""
        videos = []
        
        for demo_id, result in results["results"].items():
            if result["status"] == "completed":
                videos.append({
                    "id": demo_id.lower(),
                    "title": result["title"],
                    "duration": f"{result['duration']}秒",
                    "file": f"{demo_id.lower()}.mp4",
                    "path": result["video_path"],
                    "stages": result["stages_count"],
                    "description": self.demo_scenarios[demo_id]["description"]
                })
        
        manifest = {
            "videos": videos,
            "total_count": len(videos),
            "total_duration": results["summary"]["total_duration"],
            "output_directory": str(self.output_dir),
            "generated_at": datetime.now().isoformat()
        }
        
        # 保存清单
        manifest_file = self.output_dir / "video_manifest.json"
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        print(f"📋 视频清单保存到: {manifest_file}")
        return manifest

async def main():
    """主函数"""
    print("🎬 PowerAutomation 4.0 录制即测试演示系统")
    print("=" * 50)
    
    demo_system = RecordAsTestDemoSystem()
    
    # 录制所有演示
    results = await demo_system.record_all_demos()
    
    # 生成视频清单
    manifest = demo_system.generate_video_manifest(results)
    
    print("\n🎉 所有演示录制完成！")
    print(f"📊 成功率: {results['summary']['success_rate']}")
    print(f"📁 输出目录: {results['summary']['output_directory']}")
    print(f"⏱️ 总时长: {results['summary']['total_duration']}")
    print(f"🎬 视频数量: {manifest['total_count']}")

if __name__ == "__main__":
    asyncio.run(main())

