"""Base classes for the unified processor architecture."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from cv2.typing import MatLike


@dataclass
class ProcessingContext:
    """Context object that flows through all processors.

    This encapsulates all the data that gets passed between processors,
    making it easy to add new data without changing method signatures.
    """

    # Input data
    file_path: Path | str
    gray_image: MatLike
    colored_image: MatLike
    template: Any  # Template type (avoiding circular import)

    # Processing results (populated by processors)
    omr_response: dict[str, str] = field(default_factory=dict)
    is_multi_marked: bool = False
    field_id_to_interpretation: dict[str, Any] = field(default_factory=dict)

    # Evaluation results (populated by EvaluationProcessor)
    score: float = 0.0
    evaluation_meta: dict[str, Any] | None = None
    evaluation_config_for_response: Any = None
    default_answers_summary: str = ""

    # Additional metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Convert file_path to string if it's a Path."""
        if isinstance(self.file_path, Path):
            self.file_path = str(self.file_path)


class Processor(ABC):
    """Abstract base class for all processors.

    All processing steps (image preprocessing, alignment, detection, etc.)
    inherit from this class and implement the same interface for consistency.
    """

    @abstractmethod
    def process(self, context: ProcessingContext) -> ProcessingContext:
        """Process the context and return updated context.

        Args:
            context: The processing context containing all current state

        Returns:
            Updated processing context with results from this processor
        """

    @abstractmethod
    def get_name(self) -> str:
        """Get a human-readable name for this processor.

        Returns:
            String name of the processor (e.g., "AutoRotate", "ReadOMR")
        """
