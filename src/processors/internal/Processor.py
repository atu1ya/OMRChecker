from pathlib import Path

from src.algorithm.processor.base import Processor as BaseProcessor


class Processor(BaseProcessor):
    """Base class that each processor must inherit from.

    This now extends the unified Processor base class from the processor pipeline.
    Legacy preprocessors that inherit from this will work with both old and new interfaces.
    """

    def __init__(
        self,
        options,
        relative_dir,
    ) -> None:
        self.options = options
        self.tuning_options = options.get("tuningOptions", {})
        self.relative_dir = Path(relative_dir)
        self.description = "UNKNOWN"

    def __str__(self) -> str:
        return self.__module__

    def get_name(self) -> str:
        """Get the name of this processor (required by unified Processor interface)."""
        return (
            self.get_class_name()
            if hasattr(self, "get_class_name")
            else self.__class__.__name__
        )
