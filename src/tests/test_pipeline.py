"""Tests for the processing pipeline infrastructure."""

from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pytest

from src.algorithm.pipeline.base import PipelineStage, ProcessingContext
from src.algorithm.pipeline.pipeline import TemplateProcessingPipeline
from src.algorithm.pipeline.stages import (
    AlignmentStage,
    DetectionInterpretationStage,
    PreprocessingStage,
)


@pytest.fixture
def mock_template():
    """Create a mock template for testing."""
    template = Mock()
    template.tuning_config = Mock()
    template.tuning_config.outputs = Mock()
    template.tuning_config.outputs.colored_outputs_enabled = True
    template.tuning_config.outputs.show_preprocessors_diff = {}
    template.tuning_config.outputs.show_image_level = 1

    template.template_layout = Mock()
    template.template_layout.processing_image_shape = [800, 600]
    template.template_layout.output_image_shape = None
    template.template_layout.pre_processors = []
    template.template_layout.get_copy_for_shifting = Mock(
        return_value=template.template_layout
    )
    template.template_layout.reset_all_shifts = Mock()

    template.alignment = {}
    template.template_dimensions = [1000, 800]
    template.save_image_ops = Mock()
    template.save_image_ops.append_save_image = Mock()

    template.template_file_runner = Mock()
    template.template_file_runner.read_omr_and_update_metrics = Mock(
        return_value={"Q1": "A", "Q2": "B"}
    )
    template.template_file_runner.get_directory_level_interpretation_aggregates = Mock(
        return_value={
            "file_wise_aggregates": {
                "test.jpg": {
                    "read_response_flags": {"is_multi_marked": False},
                    "field_id_to_interpretation": {},
                }
            }
        }
    )

    template.get_concatenated_omr_response = Mock(return_value={"Q1": "A", "Q2": "B"})

    return template


@pytest.fixture
def mock_images():
    """Create mock images for testing."""
    gray_image = np.zeros((1000, 800), dtype=np.uint8)
    colored_image = np.zeros((1000, 800, 3), dtype=np.uint8)
    return gray_image, colored_image


class TestProcessingContext:
    """Tests for ProcessingContext."""

    def test_context_initialization(self, mock_template, mock_images):
        """Test that context initializes correctly."""
        gray_image, colored_image = mock_images
        context = ProcessingContext(
            file_path="test.jpg",
            gray_image=gray_image,
            colored_image=colored_image,
            template=mock_template,
        )

        assert context.file_path == "test.jpg"
        assert context.gray_image is gray_image
        assert context.colored_image is colored_image
        assert context.template is mock_template
        assert context.omr_response == {}
        assert context.is_multi_marked is False
        assert context.field_id_to_interpretation == {}
        assert context.metadata == {}

    def test_context_path_conversion(self, mock_template, mock_images):
        """Test that Path objects are converted to strings."""
        gray_image, colored_image = mock_images
        context = ProcessingContext(
            file_path=Path("test.jpg"),
            gray_image=gray_image,
            colored_image=colored_image,
            template=mock_template,
        )

        assert isinstance(context.file_path, str)
        assert context.file_path == "test.jpg"


class TestPreprocessingStage:
    """Tests for PreprocessingStage."""

    @patch("src.algorithm.pipeline.stages.preprocessing_stage.ImageUtils")
    def test_preprocessing_basic_flow(
        self, mock_image_utils, mock_template, mock_images
    ):
        """Test basic preprocessing flow."""
        gray_image, colored_image = mock_images

        # Mock ImageUtils methods
        mock_image_utils.resize_to_shape.side_effect = lambda _shape, img: img

        stage = PreprocessingStage(mock_template)

        context = ProcessingContext(
            file_path="test.jpg",
            gray_image=gray_image,
            colored_image=colored_image,
            template=mock_template,
        )

        result = stage.execute(context)

        assert result is context
        assert stage.get_stage_name() == "Preprocessing"
        # Verify that get_copy_for_shifting was called
        mock_template.template_layout.get_copy_for_shifting.assert_called_once()

    @patch("src.algorithm.pipeline.stages.preprocessing_stage.ImageUtils")
    def test_preprocessing_with_preprocessors(
        self, mock_image_utils, mock_template, mock_images
    ):
        """Test preprocessing with actual preprocessors."""
        gray_image, colored_image = mock_images

        # Mock ImageUtils methods
        mock_image_utils.resize_to_shape.side_effect = lambda _shape, img: img

        # Add mock preprocessor
        mock_preprocessor = Mock()
        mock_preprocessor.get_class_name.return_value = "TestPreprocessor"
        mock_preprocessor.resize_and_apply_filter.return_value = (
            gray_image,
            colored_image,
            mock_template.template_layout,
        )

        mock_template.template_layout.pre_processors = [mock_preprocessor]
        mock_template.tuning_config.outputs.show_preprocessors_diff = {
            "TestPreprocessor": False
        }

        stage = PreprocessingStage(mock_template)

        context = ProcessingContext(
            file_path="test.jpg",
            gray_image=gray_image,
            colored_image=colored_image,
            template=mock_template,
        )

        result = stage.execute(context)

        assert result is context
        # Verify preprocessor was called
        mock_preprocessor.resize_and_apply_filter.assert_called_once()


class TestAlignmentStage:
    """Tests for AlignmentStage."""

    @patch("src.algorithm.pipeline.stages.alignment_stage.apply_template_alignment")
    def test_alignment_with_reference_image(
        self, mock_apply_alignment, mock_template, mock_images
    ):
        """Test alignment when reference image is configured."""
        gray_image, colored_image = mock_images

        # Configure alignment
        mock_template.alignment = {"gray_alignment_image": np.zeros((100, 100))}

        # Mock the alignment function
        mock_apply_alignment.return_value = (gray_image, colored_image, mock_template)

        stage = AlignmentStage(mock_template)

        context = ProcessingContext(
            file_path="test.jpg",
            gray_image=gray_image,
            colored_image=colored_image,
            template=mock_template,
        )

        result = stage.execute(context)

        assert result is context
        assert stage.get_stage_name() == "Alignment"
        # Verify alignment was called
        mock_apply_alignment.assert_called_once_with(
            gray_image, colored_image, mock_template, mock_template.tuning_config
        )

    def test_alignment_without_reference_image(self, mock_template, mock_images):
        """Test alignment when no reference image is configured."""
        gray_image, colored_image = mock_images

        # No alignment configured
        mock_template.alignment = {}

        stage = AlignmentStage(mock_template)

        context = ProcessingContext(
            file_path="test.jpg",
            gray_image=gray_image,
            colored_image=colored_image,
            template=mock_template,
        )

        result = stage.execute(context)

        assert result is context
        # Images should be unchanged
        assert result.gray_image is gray_image
        assert result.colored_image is colored_image


class TestDetectionInterpretationStage:
    """Tests for DetectionInterpretationStage."""

    @patch("src.algorithm.pipeline.stages.detection_interpretation_stage.ImageUtils")
    def test_detection_interpretation_flow(
        self, mock_image_utils, mock_template, mock_images
    ):
        """Test detection and interpretation flow."""
        gray_image, colored_image = mock_images

        # Mock ImageUtils methods
        mock_image_utils.resize_to_dimensions.return_value = (gray_image, colored_image)
        mock_image_utils.normalize.return_value = (gray_image, colored_image)

        stage = DetectionInterpretationStage(mock_template)

        context = ProcessingContext(
            file_path="test.jpg",
            gray_image=gray_image,
            colored_image=colored_image,
            template=mock_template,
        )

        result = stage.execute(context)

        assert result is context
        assert stage.get_stage_name() == "Detection & Interpretation"
        assert result.omr_response == {"Q1": "A", "Q2": "B"}
        assert result.is_multi_marked is False
        assert "raw_omr_response" in result.metadata

        # Verify template_file_runner methods were called
        mock_template.template_file_runner.read_omr_and_update_metrics.assert_called_once()
        mock_template.get_concatenated_omr_response.assert_called_once()


class TestTemplateProcessingPipeline:
    """Tests for TemplateProcessingPipeline."""

    @patch("src.algorithm.pipeline.stages.detection_interpretation_stage.ImageUtils")
    @patch("src.algorithm.pipeline.stages.preprocessing_stage.ImageUtils")
    def test_full_pipeline_execution(
        self, mock_preproc_utils, mock_detect_utils, mock_template, mock_images
    ):
        """Test complete pipeline execution."""
        gray_image, colored_image = mock_images

        # Mock all ImageUtils methods
        mock_preproc_utils.resize_to_shape.side_effect = lambda _shape, img: img
        mock_detect_utils.resize_to_dimensions.return_value = (
            gray_image,
            colored_image,
        )
        mock_detect_utils.normalize.return_value = (gray_image, colored_image)

        pipeline = TemplateProcessingPipeline(mock_template)

        result = pipeline.process_file("test.jpg", gray_image, colored_image)

        assert isinstance(result, ProcessingContext)
        assert result.file_path == "test.jpg"
        assert result.omr_response == {"Q1": "A", "Q2": "B"}
        assert result.is_multi_marked is False

    def test_pipeline_stage_management(self, mock_template):
        """Test adding and removing pipeline stages."""
        pipeline = TemplateProcessingPipeline(mock_template)

        # Check initial stages
        stage_names = pipeline.get_stage_names()
        assert "Preprocessing" in stage_names
        assert "Alignment" in stage_names
        assert "Detection & Interpretation" in stage_names

        # Add a custom stage
        custom_stage = Mock(spec=PipelineStage)
        custom_stage.get_stage_name.return_value = "Custom Stage"
        pipeline.add_stage(custom_stage)

        stage_names = pipeline.get_stage_names()
        assert "Custom Stage" in stage_names

        # Remove a stage
        pipeline.remove_stage("Custom Stage")
        stage_names = pipeline.get_stage_names()
        assert "Custom Stage" not in stage_names

    @patch("src.algorithm.pipeline.stages.preprocessing_stage.ImageUtils")
    def test_pipeline_error_handling(
        self, mock_image_utils, mock_template, mock_images
    ):
        """Test that pipeline properly propagates errors."""
        gray_image, colored_image = mock_images

        # Make preprocessing fail
        mock_image_utils.resize_to_shape.side_effect = Exception("Resize failed")

        pipeline = TemplateProcessingPipeline(mock_template)

        with pytest.raises(Exception, match="Resize failed"):
            pipeline.process_file("test.jpg", gray_image, colored_image)


class TestPipelineIntegration:
    """Integration tests for the pipeline."""

    @patch("src.algorithm.pipeline.stages.detection_interpretation_stage.ImageUtils")
    @patch("src.algorithm.pipeline.stages.preprocessing_stage.ImageUtils")
    @patch("src.algorithm.pipeline.stages.alignment_stage.apply_template_alignment")
    def test_end_to_end_processing(
        self,
        mock_apply_alignment,
        mock_preproc_utils,
        mock_detect_utils,
        mock_template,
        mock_images,
    ):
        """Test end-to-end processing through all stages."""
        gray_image, colored_image = mock_images

        # Mock all dependencies
        mock_preproc_utils.resize_to_shape.side_effect = lambda _shape, img: img
        mock_apply_alignment.return_value = (gray_image, colored_image, mock_template)
        mock_detect_utils.resize_to_dimensions.return_value = (
            gray_image,
            colored_image,
        )
        mock_detect_utils.normalize.return_value = (gray_image, colored_image)

        # Configure template with alignment
        mock_template.alignment = {"gray_alignment_image": np.zeros((100, 100))}

        # Create pipeline and process
        pipeline = TemplateProcessingPipeline(mock_template)
        result = pipeline.process_file("test.jpg", gray_image, colored_image)

        # Verify all stages executed
        assert result.omr_response == {"Q1": "A", "Q2": "B"}
        assert result.is_multi_marked is False

        # Verify alignment was called
        mock_apply_alignment.assert_called_once()

        # Verify detection was called
        mock_template.template_file_runner.read_omr_and_update_metrics.assert_called_once()
