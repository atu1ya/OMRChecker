"""Simplified processing pipeline using unified Processor interface."""

from pathlib import Path

from cv2.typing import MatLike

from src.algorithm.processor.alignment import AlignmentProcessor
from src.algorithm.processor.base import ProcessingContext, Processor
from src.algorithm.processor.image import PreprocessingProcessor
from src.algorithm.processor.read_omr import ReadOMRProcessor
from src.utils.logger import logger


class ProcessingPipeline:
    """Simplified pipeline that orchestrates processors.

    This pipeline provides a clean, testable interface for processing
    OMR images through multiple processors with a unified interface:
    1. Preprocessing (rotation, cropping, filtering)
    2. Alignment (feature-based alignment)
    3. ReadOMR (detection & interpretation)

    Benefits:
    - All processors use the same interface
    - Easy to test each processor independently
    - Simple to extend with new processors
    - Type-safe ProcessingContext
    - Consistent error handling
    """

    def __init__(self, template) -> None:
        """Initialize the pipeline with a template.

        Args:
            template: The template containing all configuration and runners
        """
        self.template = template
        self.tuning_config = template.tuning_config

        # Initialize all processors with unified interface
        self.processors: list[Processor] = [
            PreprocessingProcessor(template),
            AlignmentProcessor(template),
            ReadOMRProcessor(template),
        ]

    def process_file(
        self,
        file_path: Path | str,
        gray_image: MatLike,
        colored_image: MatLike,
    ) -> ProcessingContext:
        """Process a single OMR file through all processors.

        Args:
            file_path: Path to the file being processed
            gray_image: Grayscale input image
            colored_image: Colored input image

        Returns:
            ProcessingContext containing all results (omr_response, metrics, etc.)
        """
        logger.info(f"Starting pipeline for file: {file_path}")

        # Create initial context
        context = ProcessingContext(
            file_path=file_path,
            gray_image=gray_image,
            colored_image=colored_image,
            template=self.template,
        )

        # Execute each processor in sequence
        for processor in self.processors:
            processor_name = processor.get_name()
            logger.debug(f"Executing processor: {processor_name}")

            try:
                context = processor.process(context)
            except Exception as e:
                logger.error(f"Error in processor {processor_name}: {e}")
                raise

        logger.info(f"Completed pipeline for file: {file_path}")

        return context

    def add_processor(self, processor: Processor) -> None:
        """Add a custom processor to the pipeline.

        This allows for extensibility - users can add their own processors
        for custom processing requirements.

        Args:
            processor: The processor to add to the pipeline
        """
        self.processors.append(processor)

    def remove_processor(self, processor_name: str) -> None:
        """Remove a processor from the pipeline by name.

        Args:
            processor_name: Name of the processor to remove
        """
        self.processors = [p for p in self.processors if p.get_name() != processor_name]

    def get_processor_names(self) -> list[str]:
        """Get the names of all processors in the pipeline.

        Returns:
            List of processor names
        """
        return [processor.get_name() for processor in self.processors]
