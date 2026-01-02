"""ReadOMR Processor for OMR detection and interpretation."""

from src.processors.base import ProcessingContext, Processor
from src.processors.template.detection.template_file_runner import TemplateFileRunner
from src.utils.image import ImageUtils
from src.utils.logger import logger


class ReadOMRProcessor(Processor):
    """Processor that performs OMR detection and interpretation.

    This processor:
    1. Creates a TemplateFileRunner for the template
    2. Resizes images to template dimensions
    3. Normalizes the images
    4. Runs field detection (bubbles, OCR, barcodes)
    5. Interprets the detected data
    6. Stores results in context
    """

    def __init__(self, template) -> None:
        """Initialize the ReadOMR processor.

        Args:
            template: The template containing field definitions and layout
        """
        self.template = template
        self.tuning_config = template.tuning_config

        # Instantiate the TemplateFileRunner here instead of in Template
        # This decouples Template from processing logic
        self.template_file_runner = TemplateFileRunner(template)

    def get_name(self) -> str:
        """Get the name of this processor."""
        return "ReadOMR"

    def finish_processing_directory(self):
        """Finish processing directory and get aggregated results."""
        return self.template_file_runner.finish_processing_directory()

    def process(self, context: ProcessingContext) -> ProcessingContext:
        """Execute OMR detection and interpretation.

        Args:
            context: Processing context with preprocessed and aligned images

        Returns:
            Updated context with OMR response and interpretation metrics
        """
        logger.debug(f"Starting {self.get_name()} processor")

        template = context.template
        file_path = context.file_path
        input_gray_image = context.gray_image
        colored_image = context.colored_image

        # Resize to template dimensions for saved outputs
        gray_image, colored_image = ImageUtils.resize_to_dimensions(
            template.template_dimensions, input_gray_image, colored_image
        )

        # Save resized image
        template.save_image_ops.append_save_image(
            "Resized Image", range(3, 7), gray_image, colored_image
        )

        # Normalize images
        gray_image, colored_image = ImageUtils.normalize(gray_image, colored_image)

        # Run detection and interpretation via TemplateFileRunner
        raw_omr_response = self.template_file_runner.read_omr_and_update_metrics(
            file_path, gray_image, colored_image
        )

        # Get concatenated response (handles custom labels)
        concatenated_omr_response = template.get_concatenated_omr_response(
            raw_omr_response
        )

        # Extract interpretation metrics
        directory_level_interpretation_aggregates = (
            self.template_file_runner.get_directory_level_interpretation_aggregates()
        )

        template_file_level_interpretation_aggregates = (
            directory_level_interpretation_aggregates["file_wise_aggregates"][file_path]
        )

        is_multi_marked = template_file_level_interpretation_aggregates[
            "read_response_flags"
        ]["is_multi_marked"]

        field_id_to_interpretation = template_file_level_interpretation_aggregates[
            "field_id_to_interpretation"
        ]

        # Update context with results
        context.omr_response = concatenated_omr_response
        context.is_multi_marked = is_multi_marked
        context.field_id_to_interpretation = field_id_to_interpretation
        context.gray_image = gray_image
        context.colored_image = colored_image

        # Store raw response and aggregates in metadata
        context.metadata["raw_omr_response"] = raw_omr_response
        context.metadata["directory_level_interpretation_aggregates"] = (
            directory_level_interpretation_aggregates
        )

        logger.debug(f"Completed {self.get_name()} processor")

        return context
