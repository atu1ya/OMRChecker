"""Typed dataclass models for configuration objects."""

from src.schemas.models.config import (
    Config,
    OutputsConfig,
    ProcessingConfig,
    ThresholdingConfig,
)
from src.schemas.models.evaluation import (
    DrawAnswerGroupsConfig,
    DrawAnswersSummaryConfig,
    DrawDetectedBubbleTextsConfig,
    DrawQuestionVerdictsConfig,
    DrawScoreConfig,
    EvaluationConfig,
    OutputsConfiguration,
)
from src.schemas.models.template import (
    AlignmentConfig,
    AlignmentMarginsConfig,
    OutputColumnsConfig,
    SortFilesConfig,
    TemplateConfig,
)

__all__ = [
    "AlignmentConfig",
    "AlignmentMarginsConfig",
    # Config models
    "Config",
    "DrawAnswerGroupsConfig",
    "DrawAnswersSummaryConfig",
    "DrawDetectedBubbleTextsConfig",
    "DrawQuestionVerdictsConfig",
    "DrawScoreConfig",
    # Evaluation models
    "EvaluationConfig",
    "OutputColumnsConfig",
    "OutputsConfig",
    "OutputsConfiguration",
    "ProcessingConfig",
    "SortFilesConfig",
    # Template models
    "TemplateConfig",
    "ThresholdingConfig",
]
