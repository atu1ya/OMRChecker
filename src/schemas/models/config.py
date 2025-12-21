"""Typed dataclass models for configuration."""

from dataclasses import dataclass, field
from pathlib import Path


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

    max_parallel_workers: int = 4


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
        return {
            "path": str(self.path),
            "thresholding": {
                "GAMMA_LOW": self.thresholding.GAMMA_LOW,
                "MIN_GAP_TWO_BUBBLES": self.thresholding.MIN_GAP_TWO_BUBBLES,
                "MIN_JUMP": self.thresholding.MIN_JUMP,
                "CONFIDENT_JUMP_SURPLUS_FOR_DISPARITY": self.thresholding.CONFIDENT_JUMP_SURPLUS_FOR_DISPARITY,
                "MIN_JUMP_SURPLUS_FOR_GLOBAL_FALLBACK": self.thresholding.MIN_JUMP_SURPLUS_FOR_GLOBAL_FALLBACK,
                "GLOBAL_THRESHOLD_MARGIN": self.thresholding.GLOBAL_THRESHOLD_MARGIN,
                "JUMP_DELTA": self.thresholding.JUMP_DELTA,
                "GLOBAL_PAGE_THRESHOLD": self.thresholding.GLOBAL_PAGE_THRESHOLD,
                "GLOBAL_PAGE_THRESHOLD_STD": self.thresholding.GLOBAL_PAGE_THRESHOLD_STD,
                "MIN_JUMP_STD": self.thresholding.MIN_JUMP_STD,
                "JUMP_DELTA_STD": self.thresholding.JUMP_DELTA_STD,
            },
            "outputs": {
                "output_mode": self.outputs.output_mode,
                "display_image_dimensions": self.outputs.display_image_dimensions,
                "show_image_level": self.outputs.show_image_level,
                "show_preprocessors_diff": self.outputs.show_preprocessors_diff,
                "save_image_level": self.outputs.save_image_level,
                "show_logs_by_type": self.outputs.show_logs_by_type,
                "save_detections": self.outputs.save_detections,
                "colored_outputs_enabled": self.outputs.colored_outputs_enabled,
                "save_image_metrics": self.outputs.save_image_metrics,
                "show_confidence_metrics": self.outputs.show_confidence_metrics,
                "filter_out_multimarked_files": self.outputs.filter_out_multimarked_files,
            },
            "processing": {
                "max_parallel_workers": self.processing.max_parallel_workers,
            },
        }

    def get(self, key: str, default=None):
        """Get value by key (backwards compatibility).

        Args:
            key: The key to retrieve
            default: Default value if key not found

        Returns:
            The value if found, otherwise default
        """
        return getattr(self, key, default)
