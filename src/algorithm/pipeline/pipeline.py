"""Main processing pipeline for OMR templates."""

from pathlib import Path

from cv2.typing import MatLike

from src.algorithm.pipeline.base import PipelineStage, ProcessingContext
from src.algorithm.pipeline.stages import (
    AlignmentStage,
    DetectionInterpretationStage,
    PreprocessingStage,
)
from src.utils.logger import logger


class TemplateProcessingPipeline:
    """Main pipeline that orchestrates all stages of OMR processing.

    This pipeline provides a clean, testable interface for processing
    OMR images through multiple stages:
    1. Preprocessing (rotation, cropping, filtering)
    2. Alignment (feature-based alignment)
    3. Detection & Interpretation (reading bubbles, OCR, barcodes)

    Benefits:
    - Clear separation of concerns
    - Easy to test each stage independently
    - Simple to extend with new stages
    - Type-safe interfaces
    - Consistent error handling
    """

    def __init__(self, template) -> None:
        """Initialize the pipeline with a template.

        Args:
            template: The template containing all configuration and runners
        """
        self.template = template
        self.tuning_config = template.tuning_config

        # Initialize all stages
        self.stages: list[PipelineStage] = [
            PreprocessingStage(template),
            AlignmentStage(template),
            DetectionInterpretationStage(template),
        ]

    def process_file(
        self,
        file_path: Path | str,
        gray_image: MatLike,
        colored_image: MatLike,
    ) -> ProcessingContext:
        """Process a single OMR file through the entire pipeline.

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

        # Execute each stage in sequence
        for stage in self.stages:
            stage_name = stage.get_stage_name()
            logger.debug(f"Executing stage: {stage_name}")

            try:
                context = stage.execute(context)
            except Exception as e:
                logger.error(f"Error in stage {stage_name}: {e}")
                raise

        logger.info(f"Completed pipeline for file: {file_path}")

        return context

    def add_stage(self, stage: PipelineStage) -> None:
        """Add a custom stage to the pipeline.

        This allows for extensibility - users can add their own stages
        for custom processing requirements.

        Args:
            stage: The stage to add to the pipeline
        """
        self.stages.append(stage)

    def remove_stage(self, stage_name: str) -> None:
        """Remove a stage from the pipeline by name.

        Args:
            stage_name: Name of the stage to remove
        """
        self.stages = [s for s in self.stages if s.get_stage_name() != stage_name]

    def get_stage_names(self) -> list[str]:
        """Get the names of all stages in the pipeline.

        Returns:
            List of stage names
        """
        return [stage.get_stage_name() for stage in self.stages]
