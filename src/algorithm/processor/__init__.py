"""Unified processor infrastructure for OMR processing."""

from src.algorithm.processor.alignment import AlignmentProcessor
from src.algorithm.processor.base import ProcessingContext, Processor
from src.algorithm.processor.image import ImageProcessorAdapter, PreprocessingProcessor
from src.algorithm.processor.pipeline import ProcessingPipeline
from src.algorithm.processor.read_omr import ReadOMRProcessor

__all__ = [
    "AlignmentProcessor",
    "ImageProcessorAdapter",
    "PreprocessingProcessor",
    "ProcessingContext",
    "ProcessingPipeline",
    "Processor",
    "ReadOMRProcessor",
]
