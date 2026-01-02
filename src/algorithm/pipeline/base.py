"""Base classes for the processing pipeline."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from cv2.typing import MatLike


@dataclass
class ProcessingContext:
    """Context object that flows through the pipeline stages.

    This encapsulates all the data that gets passed between stages,
    making it easy to add new data without changing method signatures.
    """

    # Input data
    file_path: Path | str
    gray_image: MatLike
    colored_image: MatLike
    template: Any  # Template type (avoiding circular import)

    # Processing results (populated by stages)
    omr_response: dict[str, str] = field(default_factory=dict)
    is_multi_marked: bool = False
    field_id_to_interpretation: dict[str, Any] = field(default_factory=dict)

    # Additional metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Convert file_path to string if it's a Path."""
        if isinstance(self.file_path, Path):
            self.file_path = str(self.file_path)


class PipelineStage(ABC):
    """Abstract base class for a pipeline stage.

    Each stage represents a distinct phase of processing (preprocessing,
    alignment, detection, etc.) and has a clear input/output contract.
    """

    @abstractmethod
    def execute(self, context: ProcessingContext) -> ProcessingContext:
        """Execute this stage of the pipeline.

        Args:
            context: The processing context containing all current state

        Returns:
            Updated processing context with results from this stage
        """

    @abstractmethod
    def get_stage_name(self) -> str:
        """Get a human-readable name for this stage.

        Returns:
            String name of the stage (e.g., "Preprocessing", "Detection")
        """
