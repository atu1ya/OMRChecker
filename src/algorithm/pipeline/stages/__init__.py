"""Pipeline stages initialization."""

from src.algorithm.pipeline.stages.alignment_stage import AlignmentStage
from src.algorithm.pipeline.stages.detection_interpretation_stage import (
    DetectionInterpretationStage,
)
from src.algorithm.pipeline.stages.preprocessing_stage import PreprocessingStage

__all__ = ["AlignmentStage", "DetectionInterpretationStage", "PreprocessingStage"]
