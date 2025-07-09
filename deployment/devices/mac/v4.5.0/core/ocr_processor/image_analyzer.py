"""
Image Analyzer for ClaudeEditor 4.5
Demonstrates OCR3B_Flux integration with uploaded images
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from ..adapters.ocr3b_flux_adapter import OCR3BFluxAdapter

logger = logging.getLogger(__name__)

class ImageAnalyzer:
    """图像分析器 - 演示OCR3B_Flux集成"""
    
    def __init__(self):
        self.ocr_adapter = OCR3BFluxAdapter()
        self.is_initialized = False
    
    async def initialize(self) -> bool:
        """初始化图像分析器"""
        try:
            success = await self.ocr_adapter.initialize()
            self.is_initialized = success
            return success
        except Exception as e:
            logger.error(f"Failed to initialize ImageAnalyzer: {e}")
            return False
    
    async def analyze_uploaded_image(self, image_path: str) -> Dict[str, Any]:
        """分析用户上传的图像"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # 读取图像文件
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # 使用OCR3B_Flux进行分析
            ocr_result = await self.ocr_adapter.process_image_data(image_data)
            
            # 分析VS Code界面内容
            analysis = await self._analyze_vscode_interface(ocr_result)
            
            return {
                "file_path": image_path,
                "ocr_result": ocr_result,
                "interface_analysis": analysis,
                "claudeditor_integration_status": await self._check_integration_status(analysis)
            }
            
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            return {
                "error": str(e),
                "file_path": image_path
            }
    
    async def _analyze_vscode_interface(self, ocr_result: Dict[str, Any]) -> Dict[str, Any]:
        """分析VS Code界面内容"""
        extracted_text = ocr_result.get("text", "")
        
        # 识别项目列表
        projects = []
        lines = extracted_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('~'):
                # 过滤掉路径行，只保留项目名
                if not any(char in line for char in ['/', '~', '.']):
                    projects.append(line)
        
        # 分析界面元素
        interface_elements = {
            "has_file_explorer": "打开文件夹" in extracted_text or "文件" in extracted_text,
            "has_git_integration": "Git" in extracted_text or "仓库" in extracted_text,
            "has_remote_connection": "远程" in extracted_text or "remote" in extracted_text.lower(),
            "recent_projects": projects
        }
        
        return interface_elements
    
    async def _check_integration_status(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """检查ClaudeEditor集成状态"""
        recent_projects = analysis.get("recent_projects", [])
        
        # 检查是否有ClaudeEditor相关项目
        claudeditor_projects = [
            proj for proj in recent_projects 
            if "claude" in proj.lower() or "editor" in proj.lower()
        ]
        
        # 检查PowerAutomation相关项目
        powerautomation_projects = [
            proj for proj in recent_projects 
            if "power" in proj.lower() or "automation" in proj.lower() or "auto" in proj.lower()
        ]
        
        # 检查AI Core相关项目
        aicore_projects = [
            proj for proj in recent_projects 
            if "aicore" in proj.lower() or "ai" in proj.lower()
        ]
        
        return {
            "claudeditor_projects_found": claudeditor_projects,
            "powerautomation_projects_found": powerautomation_projects,
            "aicore_projects_found": aicore_projects,
            "total_projects": len(recent_projects),
            "integration_indicators": {
                "has_claudeditor": len(claudeditor_projects) > 0,
                "has_powerautomation": len(powerautomation_projects) > 0,
                "has_aicore": len(aicore_projects) > 0
            }
        }

# 演示OCR3B_Flux功能
async def demo_ocr_analysis():
    """演示OCR分析功能"""
    analyzer = ImageAnalyzer()
    
    # 分析用户上传的图片
    image_path = "/home/ubuntu/upload/image.png"
    
    if Path(image_path).exists():
        result = await analyzer.analyze_uploaded_image(image_path)
        return result
    else:
        return {"error": "Image file not found"}

if __name__ == "__main__":
    # 运行演示
    result = asyncio.run(demo_ocr_analysis())
    print("OCR Analysis Result:", result)

