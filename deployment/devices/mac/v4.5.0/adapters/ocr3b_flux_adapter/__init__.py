"""
OCR3B_Flux Adapter for ClaudeEditor 4.5

This module provides OCR3B_Flux integration for ClaudeEditor,
enabling advanced image text recognition capabilities.
"""

from .ocr_adapter import OCR3BFluxAdapter
from .ocr_model import OCR3BFluxModel
from .cache_manager import OCRCacheManager

__version__ = "4.5.0"
__all__ = ["OCR3BFluxAdapter", "OCR3BFluxModel", "OCRCacheManager"]

