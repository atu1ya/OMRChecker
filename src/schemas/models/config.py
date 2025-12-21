"""Typed dataclass models for configuration."""

from dataclasses import dataclass, field
from pathlib import Path

from src.utils.serialization import dataclass_to_dict


@dataclass
class ThresholdingConfig:
    """Configuration for bubble thresholding algorithm."""

    GAMMA_LOW: float = 0.7
    MIN_GAP_TWO_BUBBLES: int = 30
    MIN_JUMP: int = 25
    CONFIDENT_JUMP_SURPLUS_FOR_DISPARITY: int = 25
    MIN_JUMP_SURPLUS_FOR_GLOBAL_FALLBACK: int = 5
    GLOBAL_THRESHOLD_MARGIN: int = 10
    JUMP_DELTA: int = 30
    GLOBAL_PAGE_THRESHOLD: int = 200
    GLOBAL_PAGE_THRESHOLD_STD: int = 10
    MIN_JUMP_STD: int = 15
    JUMP_DELTA_STD: int = 5


@dataclass
class OutputsConfig:
    """Configuration for output behavior and visualization."""

    output_mode: str = "default"
    display_image_dimensions: list[int] = field(default_factory=lambda: [720, 1080])
    show_image_level: int = 0
    show_preprocessors_diff: dict[str, bool] = field(default_factory=dict)
    save_image_level: int = 1
    show_logs_by_type: dict[str, bool] = field(
        default_factory=lambda: {
            "critical": True,
            "error": True,
            "warning": True,
            "info": True,
            "debug": False,
        }
    )
    save_detections: bool = True
    colored_outputs_enabled: bool = False
    save_image_metrics: bool = False
    show_confidence_metrics: bool = False
    filter_out_multimarked_files: bool = False


@dataclass
class ProcessingConfig:
    """Configuration for parallel processing."""

    max_parallel_workers: int = 1


@dataclass
class Config:
    """Main configuration object for OMRChecker.

    This replaces the DotMap-based tuning_config throughout the codebase.
    """

    path: Path
    thresholding: ThresholdingConfig = field(default_factory=ThresholdingConfig)
    outputs: OutputsConfig = field(default_factory=OutputsConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)

    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        """Create Config from dictionary (typically from JSON).

        Args:
            data: Dictionary containing configuration data

        Returns:
            Config instance with nested dataclasses
        """
        return cls(
            path=Path(data.get("path", "config.json")),
            thresholding=ThresholdingConfig(**data.get("thresholding", {})),
            outputs=OutputsConfig(**data.get("outputs", {})),
            processing=ProcessingConfig(**data.get("processing", {})),
        )

    def to_dict(self) -> dict:
        """Convert Config to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the config
        """
        return dataclass_to_dict(self)

    def get(self, key: str, default=None):
        """Get value by key (backwards compatibility).

        Args:
            key: The key to retrieve
            default: Default value if key not found

        Returns:
            The value if found, otherwise default
        """
        return getattr(self, key, default)
