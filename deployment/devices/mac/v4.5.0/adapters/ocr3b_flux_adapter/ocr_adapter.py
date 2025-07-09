"""
OCR3B_Flux Adapter for ClaudeEditor 4.5
集成现有的OCRFlux组件到ClaudeEditor中
"""

import asyncio
import logging
import hashlib
from typing import Dict, Any, Optional, List
from pathlib import Path
import time

from .ocrflux_integration import LocalAIModelIntegration, OCRConfig, OCRResult

logger = logging.getLogger(__name__)

class OCR3BFluxAdapter:
    """OCR3B_Flux适配器 - 集成现有OCRFlux到ClaudeEditor"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # 初始化OCRFlux集成
        ocr_config = OCRConfig(
            model_path=self.config.get("model_path", "OCRFlux-3B"),
            device=self.config.get("device", "cuda"),
            batch_size=self.config.get("batch_size", 1),
            language=self.config.get("language", "auto"),
            enable_cross_page_merge=self.config.get("enable_cross_page_merge", True),
            enable_table_parsing=self.config.get("enable_table_parsing", True)
        )
        
        self.ocr_integration = LocalAIModelIntegration(ocr_config)
        self.is_initialized = False
        
        # 缓存设置
        self.cache_dir = Path(self.config.get("cache_dir", "./cache/ocr"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache = {}
        self.max_cache_size = self.config.get("max_cache_size", 100)
        
        # 支持的文件格式
        self.supported_formats = {".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"}
        
        logger.info("OCR3B_Flux适配器初始化完成")
    
    async def initialize(self) -> bool:
        """初始化适配器"""
        try:
            logger.info("初始化OCR3B_Flux适配器...")
            
            # 初始化OCRFlux模型
            success = await self.ocr_integration.initialize_model()
            
            if success:
                self.is_initialized = True
                logger.info("OCR3B_Flux适配器初始化成功")
                return True
            else:
                logger.error("OCRFlux模型初始化失败")
                return False
                
        except Exception as e:
            logger.error(f"OCR3B_Flux适配器初始化失败: {e}")
            return False
    
    async def process_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """处理文件并进行OCR识别"""
        if not self.is_initialized:
            logger.warning("适配器未初始化，尝试初始化...")
            if not await self.initialize():
                return None
        
        try:
            file_path = Path(file_path)
            
            # 检查文件格式
            if file_path.suffix.lower() not in self.supported_formats:
                logger.warning(f"不支持的文件格式: {file_path.suffix}")
                return None
            
            # 检查缓存
            file_hash = await self._generate_file_hash(str(file_path))
            if file_hash in self.cache:
                logger.info(f"使用缓存结果: {file_path.name}")
                return self.cache[file_hash]
            
            # 处理文件
            start_time = time.time()
            
            if file_path.suffix.lower() == ".pdf":
                # PDF文件处理
                ocr_result = await self.ocr_integration.process_pdf_to_markdown(str(file_path))
            else:
                # 图像文件处理
                ocr_result = await self.ocr_integration.process_image_to_text(str(file_path))
            
            processing_time = time.time() - start_time
            
            # 转换为ClaudeEditor格式
            result = await self._convert_to_claudeditor_format(ocr_result, str(file_path), processing_time)
            
            # 缓存结果
            await self._cache_result(file_hash, result)
            
            return result
            
        except Exception as e:
            logger.error(f"文件处理失败 {file_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_path": str(file_path)
            }
    
    async def process_image_data(self, image_data: bytes) -> Dict[str, Any]:
        """处理图像数据"""
        if not self.is_initialized:
            if not await self.initialize():
                return {"success": False, "error": "适配器初始化失败"}
        
        try:
            # 创建临时文件
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                temp_file.write(image_data)
                temp_path = temp_file.name
            
            try:
                # 处理临时文件
                result = await self.process_file(temp_path)
                return result or {"success": False, "error": "处理失败"}
            finally:
                # 清理临时文件
                Path(temp_path).unlink(missing_ok=True)
                
        except Exception as e:
            logger.error(f"图像数据处理失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def _convert_to_claudeditor_format(self, ocr_result: OCRResult, file_path: str, processing_time: float) -> Dict[str, Any]:
        """转换OCR结果为ClaudeEditor格式"""
        return {
            "success": ocr_result.success,
            "file_path": file_path,
            "extracted_text": ocr_result.markdown_content if ocr_result.success else "",
            "confidence": 0.95 if ocr_result.success else 0.0,  # OCRFlux没有置信度，使用默认值
            "language": "auto",
            "page_count": ocr_result.page_count,
            "processing_time": processing_time,
            "metadata": {
                "model": "OCRFlux-3B",
                "timestamp": ocr_result.timestamp.isoformat() if ocr_result.timestamp else None,
                "original_metadata": ocr_result.metadata,
                "error_message": ocr_result.error_message
            },
            "format": "markdown" if ocr_result.success else "error"
        }
    
    async def _generate_file_hash(self, file_path: str) -> str:
        """生成文件哈希用于缓存"""
        hasher = hashlib.md5()
        
        # 包含文件路径和修改时间
        file_stat = Path(file_path).stat()
        hash_input = f"{file_path}_{file_stat.st_mtime}_{file_stat.st_size}"
        hasher.update(hash_input.encode())
        
        return hasher.hexdigest()
    
    async def _cache_result(self, file_hash: str, result: Dict[str, Any]):
        """缓存处理结果"""
        if len(self.cache) >= self.max_cache_size:
            # 移除最旧的缓存项
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        self.cache[file_hash] = result
        logger.debug(f"缓存结果: {file_hash}")
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的文件格式"""
        return list(self.supported_formats)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        if hasattr(self.ocr_integration, 'total_processed'):
            return {
                "total_processed": self.ocr_integration.total_processed,
                "total_pages": self.ocr_integration.total_pages,
                "success_count": self.ocr_integration.success_count,
                "error_count": self.ocr_integration.error_count,
                "average_processing_time": (
                    self.ocr_integration.total_processing_time / max(1, self.ocr_integration.total_processed)
                ),
                "cache_size": len(self.cache),
                "model_loaded": self.is_initialized
            }
        else:
            return {
                "cache_size": len(self.cache),
                "model_loaded": self.is_initialized
            }
    
    async def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        logger.info("OCR缓存已清空")
    
    async def shutdown(self):
        """关闭适配器"""
        await self.clear_cache()
        self.is_initialized = False
        logger.info("OCR3B_Flux适配器已关闭")

# ClaudeEditor集成接口
class ClaudeEditorOCRProcessor:
    """ClaudeEditor OCR处理器"""
    
    def __init__(self, claudeditor_context=None):
        self.context = claudeditor_context
        self.adapter = OCR3BFluxAdapter()
        
    async def initialize(self) -> bool:
        """初始化处理器"""
        return await self.adapter.initialize()
    
    async def process_uploaded_file(self, file_path: str) -> Dict[str, Any]:
        """处理用户上传的文件"""
        result = await self.adapter.process_file(file_path)
        
        if result and result.get("success"):
            # 集成到ClaudeEditor上下文
            if self.context:
                await self._integrate_to_context(result)
            
            return {
                "type": "ocr_result",
                "success": True,
                "content": result["extracted_text"],
                "metadata": result["metadata"],
                "display_info": {
                    "title": f"OCR提取: {Path(file_path).name}",
                    "description": f"处理时间: {result['processing_time']:.2f}秒",
                    "format": result.get("format", "text"),
                    "page_count": result.get("page_count", 1)
                }
            }
        else:
            return {
                "type": "ocr_error",
                "success": False,
                "error": result.get("error", "OCR处理失败") if result else "处理失败"
            }
    
    async def _integrate_to_context(self, ocr_result: Dict[str, Any]):
        """将OCR结果集成到ClaudeEditor上下文"""
        if self.context and hasattr(self.context, 'add_content'):
            await self.context.add_content(
                type="ocr_result",
                content=ocr_result["extracted_text"],
                metadata=ocr_result["metadata"]
            )

