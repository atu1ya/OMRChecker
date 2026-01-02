"""ReadOMR Processor for OMR detection and interpretation."""

from src.processors.base import ProcessingContext, Processor
from src.utils.image import ImageUtils
from src.utils.logger import logger


class ReadOMRProcessor(Processor):
    """Processor that performs OMR detection and interpretation.

    This processor:
    1. Resizes images to template dimensions
    2. Normalizes the images
    3. Runs field detection (bubbles, OCR, barcodes)
    4. Interprets the detected data
    5. Stores results in context
    """

    def __init__(self, template) -> None:
        """Initialize the ReadOMR processor.

        Args:
            template: The template containing field definitions and runners
        """
        self.template = template
        self.tuning_config = template.tuning_config

    def get_name(self) -> str:
        """Get the name of this processor."""
        return "ReadOMR"

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
        raw_omr_response = template.template_file_runner.read_omr_and_update_metrics(
            file_path, gray_image, colored_image
        )

        # Get concatenated response (handles custom labels)
        concatenated_omr_response = template.get_concatenated_omr_response(
            raw_omr_response
        )

        # Extract interpretation metrics
        directory_level_interpretation_aggregates = template.template_file_runner.get_directory_level_interpretation_aggregates()

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

        # Store raw response in metadata
        context.metadata["raw_omr_response"] = raw_omr_response

        logger.debug(f"Completed {self.get_name()} processor")

        return context
