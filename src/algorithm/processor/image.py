"""Image processing adapters for the unified processor architecture."""

from src.algorithm.processor.base import ProcessingContext, Processor
from src.utils.image import ImageUtils
from src.utils.interaction import InteractionUtils
from src.utils.logger import logger


class ImageProcessorAdapter(Processor):
    """Adapter that wraps existing ImageTemplatePreprocessor to work with new Processor interface.

    This allows existing image preprocessors (AutoRotate, CropOnMarkers, etc.)
    to work with the new unified processor architecture without modification.
    """

    def __init__(self, image_preprocessor) -> None:
        """Initialize the adapter with an existing preprocessor.

        Args:
            image_preprocessor: An instance of ImageTemplatePreprocessor to wrap
        """
        self.image_preprocessor = image_preprocessor
        self.tuning_config = image_preprocessor.tuning_config

    def get_name(self) -> str:
        """Get the name of the wrapped preprocessor."""
        return self.image_preprocessor.get_class_name()

    def process(self, context: ProcessingContext) -> ProcessingContext:
        """Process images using the wrapped preprocessor.

        Args:
            context: Processing context with images

        Returns:
            Updated context with processed images
        """
        logger.debug(f"Starting {self.get_name()} processor")

        gray_image = context.gray_image
        colored_image = context.colored_image
        template = context.template
        file_path = context.file_path

        # Call the original preprocessor's method
        gray_image, colored_image, template = (
            self.image_preprocessor.resize_and_apply_filter(
                gray_image, colored_image, template, file_path
            )
        )

        # Update context
        context.gray_image = gray_image
        context.colored_image = colored_image
        context.template = template

        logger.debug(f"Completed {self.get_name()} processor")

        return context


class PreprocessingProcessor(Processor):
    """Processor that runs all image preprocessing steps.

    This processor:
    1. Creates a copy of the template layout
    2. Resizes images to processing dimensions
    3. Runs all preprocessors in sequence
    4. Optionally resizes to output dimensions
    """

    def __init__(self, template) -> None:
        """Initialize the preprocessing processor.

        Args:
            template: The template containing preprocessors and configuration
        """
        self.template = template
        self.tuning_config = template.tuning_config

    def get_name(self) -> str:
        """Get the name of this processor."""
        return "Preprocessing"

    def process(self, context: ProcessingContext) -> ProcessingContext:
        """Execute all preprocessing steps.

        Args:
            context: Processing context with input images

        Returns:
            Updated context with preprocessed images and updated template
        """
        logger.debug(f"Starting {self.get_name()} processor")

        # Get a copy of the template layout for mutation
        next_template_layout = context.template.template_layout.get_copy_for_shifting()

        # Reset the shifts in the copied template layout
        next_template_layout.reset_all_shifts()

        gray_image = context.gray_image
        colored_image = context.colored_image

        # Resize to conform to common preprocessor input requirements
        gray_image = ImageUtils.resize_to_shape(
            next_template_layout.processing_image_shape, gray_image
        )
        if self.tuning_config.outputs.colored_outputs_enabled:
            colored_image = ImageUtils.resize_to_shape(
                next_template_layout.processing_image_shape, colored_image
            )

        show_preprocessors_diff = self.tuning_config.outputs.show_preprocessors_diff

        # Run preprocessors in sequence
        for pre_processor in next_template_layout.pre_processors:
            pre_processor_name = pre_processor.get_class_name()

            # Show Before Preview
            if show_preprocessors_diff[pre_processor_name]:
                InteractionUtils.show(
                    f"Before {pre_processor_name}: {context.file_path}",
                    (
                        colored_image
                        if self.tuning_config.outputs.colored_outputs_enabled
                        else gray_image
                    ),
                )

            # Apply filter
            (
                gray_image,
                colored_image,
                next_template_layout,
            ) = pre_processor.resize_and_apply_filter(
                gray_image, colored_image, next_template_layout, context.file_path
            )

            # Show After Preview
            if show_preprocessors_diff[pre_processor_name]:
                InteractionUtils.show(
                    f"After {pre_processor_name}: {context.file_path}",
                    (
                        colored_image
                        if self.tuning_config.outputs.colored_outputs_enabled
                        else gray_image
                    ),
                )

        template_layout = next_template_layout

        # Resize to output requirements if specified
        if template_layout.output_image_shape:
            gray_image = ImageUtils.resize_to_shape(
                template_layout.output_image_shape, gray_image
            )
            if self.tuning_config.outputs.colored_outputs_enabled:
                colored_image = ImageUtils.resize_to_shape(
                    template_layout.output_image_shape, colored_image
                )

        # Update the context with processed images and template
        context.gray_image = gray_image
        context.colored_image = colored_image
        context.template.template_layout = template_layout

        logger.debug(f"Completed {self.get_name()} processor")

        return context
