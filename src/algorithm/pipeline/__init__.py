"""Pipeline infrastructure for processing OMR images."""

from src.algorithm.pipeline.base import PipelineStage, ProcessingContext
from src.algorithm.pipeline.pipeline import TemplateProcessingPipeline
from src.algorithm.pipeline.stages import (
    AlignmentStage,
    DetectionInterpretationStage,
    PreprocessingStage,
)

__all__ = [
    "AlignmentStage",
    "DetectionInterpretationStage",
    "PipelineStage",
    "PreprocessingStage",
    "ProcessingContext",
    "TemplateProcessingPipeline",
]
