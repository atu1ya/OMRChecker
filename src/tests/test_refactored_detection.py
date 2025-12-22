"""Tests for new detection models and threshold strategies.

Tests the refactored code to ensure it works correctly.
"""

import math

import pytest

from src.algorithm.template.detection.models.detection_results import (
    BubbleFieldDetectionResult,
    BubbleMeanValue,
    FileDetectionResults,
    ScanQuality,
)
from src.algorithm.template.repositories.detection_repository import (
    DetectionRepository,
)
from src.algorithm.template.threshold.strategies import (
    AdaptiveThresholdStrategy,
    GlobalThresholdStrategy,
    LocalThresholdStrategy,
    ThresholdConfig,
)


class TestBubbleMeanValue:
    """Test BubbleMeanValue model."""

    def test_creation(self):
        """Test creating a bubble mean value."""
        bubble = BubbleMeanValue(mean_value=120.5, unit_bubble=None, position=(10, 20))

        assert bubble.mean_value == 120.5
        assert bubble.position == (10, 20)

    def test_sorting(self):
        """Test that bubble means can be sorted."""
        bubbles = [
            BubbleMeanValue(200, None),
            BubbleMeanValue(100, None),
            BubbleMeanValue(150, None),
        ]

        sorted_bubbles = sorted(bubbles)

        assert sorted_bubbles[0].mean_value == 100
        assert sorted_bubbles[1].mean_value == 150
        assert sorted_bubbles[2].mean_value == 200


class TestBubbleFieldDetectionResult:
    """Test BubbleFieldDetectionResult model."""

    def create_sample_result(
        self, bubble_values: list[float]
    ) -> BubbleFieldDetectionResult:
        """Helper to create a sample result."""
        bubbles = [BubbleMeanValue(val, None) for val in bubble_values]
        return BubbleFieldDetectionResult(
            field_id="q1", field_label="Question1", bubble_means=bubbles
        )

    def test_std_deviation_calculation(self):
        """Test that std deviation is auto-calculated."""
        result = self.create_sample_result([100, 100, 200, 200])

        # Should be around 50 for this distribution
        assert 45 < result.std_deviation < 55

    def test_scan_quality_excellent(self):
        """Test scan quality assessment - excellent."""
        result = self.create_sample_result([100, 105, 200, 205])

        # High std deviation = excellent quality
        assert result.scan_quality == ScanQuality.EXCELLENT
        assert result.is_reliable

    def test_scan_quality_poor(self):
        """Test scan quality assessment - poor."""
        result = self.create_sample_result([100, 102, 104, 106])

        # Low std deviation = poor quality
        assert result.scan_quality == ScanQuality.POOR
        assert not result.is_reliable

    def test_sorted_bubble_means(self):
        """Test sorted bubble means property."""
        result = self.create_sample_result([200, 100, 150])

        sorted_means = result.sorted_bubble_means

        assert sorted_means[0].mean_value == 100
        assert sorted_means[1].mean_value == 150
        assert sorted_means[2].mean_value == 200

    def test_mean_values_property(self):
        """Test mean_values property extracts floats."""
        result = self.create_sample_result([120.5, 200.3, 115.8])

        assert result.mean_values == [120.5, 200.3, 115.8]

    def test_jumps_calculation(self):
        """Test jumps property calculates gaps."""
        result = self.create_sample_result([100, 120, 200])

        jumps = result.jumps

        assert len(jumps) == 2
        assert jumps[0][0] == 20.0  # 120 - 100
        assert jumps[1][0] == 80.0  # 200 - 120

    def test_max_jump(self):
        """Test max_jump property."""
        result = self.create_sample_result([100, 105, 200])

        assert result.max_jump == 95.0  # 200 - 105

    def test_min_max_mean(self):
        """Test min and max mean properties."""
        result = self.create_sample_result([100, 150, 200])

        assert result.min_mean == 100
        assert result.max_mean == 200


class TestFileDetectionResults:
    """Test FileDetectionResults model."""

    def test_creation(self):
        """Test creating file detection results."""
        results = FileDetectionResults(file_path="/path/to/file.jpg")

        assert results.file_path == "/path/to/file.jpg"
        assert results.num_fields == 0

    def test_adding_bubble_fields(self):
        """Test adding bubble field results."""
        results = FileDetectionResults(file_path="/path/to/file.jpg")

        bubble_result = BubbleFieldDetectionResult(
            field_id="q1",
            field_label="Question1",
            bubble_means=[BubbleMeanValue(120, None)],
        )

        results.bubble_fields["q1"] = bubble_result

        assert results.num_fields == 1
        assert results.get_field_result("q1") == bubble_result

    def test_all_bubble_means(self):
        """Test all_bubble_means property aggregates across fields."""
        results = FileDetectionResults(file_path="/path/to/file.jpg")

        results.bubble_fields["q1"] = BubbleFieldDetectionResult(
            field_id="q1",
            field_label="Q1",
            bubble_means=[BubbleMeanValue(100, None), BubbleMeanValue(200, None)],
        )

        results.bubble_fields["q2"] = BubbleFieldDetectionResult(
            field_id="q2",
            field_label="Q2",
            bubble_means=[BubbleMeanValue(150, None)],
        )

        all_means = results.all_bubble_means
        assert len(all_means) == 3

        all_values = results.all_bubble_mean_values
        assert all_values == [100, 200, 150]


class TestGlobalThresholdStrategy:
    """Test GlobalThresholdStrategy."""

    def test_basic_threshold_calculation(self):
        """Test basic threshold with clear gap."""
        strategy = GlobalThresholdStrategy()
        bubble_values = [100, 105, 110, 200, 205, 210]  # Clear gap around 155

        result = strategy.calculate_threshold(bubble_values, ThresholdConfig())

        # Threshold should be around the gap
        assert 140 < result.threshold_value < 170
        assert result.confidence > 0.5
        assert not result.fallback_used

    def test_no_clear_gap(self):
        """Test with gradual increase (no clear gap)."""
        strategy = GlobalThresholdStrategy()
        bubble_values = [100, 110, 120, 130, 140, 150]

        result = strategy.calculate_threshold(bubble_values, ThresholdConfig())

        # Should have lower confidence
        assert result.confidence < 0.7

    def test_empty_input(self):
        """Test with empty bubble values."""
        strategy = GlobalThresholdStrategy()

        result = strategy.calculate_threshold([], ThresholdConfig())

        assert result.threshold_value == 127.5  # Default
        assert result.confidence == 0.0
        assert result.fallback_used

    def test_single_bubble(self):
        """Test with single bubble."""
        strategy = GlobalThresholdStrategy()

        result = strategy.calculate_threshold([100], ThresholdConfig())

        assert result.threshold_value == 127.5  # Default
        assert result.fallback_used


class TestLocalThresholdStrategy:
    """Test LocalThresholdStrategy."""

    def test_two_bubbles_large_gap(self):
        """Test with two bubbles with significant gap."""
        strategy = LocalThresholdStrategy()
        bubble_values = [100, 200]  # Large gap

        result = strategy.calculate_threshold(bubble_values, ThresholdConfig())

        # Should use mean
        assert 140 < result.threshold_value < 160
        assert result.confidence > 0.5
        assert not result.fallback_used

    def test_two_bubbles_small_gap_with_fallback(self):
        """Test with two bubbles with small gap uses fallback."""
        strategy = LocalThresholdStrategy(global_fallback=150.0)
        bubble_values = [100, 110]  # Small gap

        result = strategy.calculate_threshold(bubble_values, ThresholdConfig())

        assert result.fallback_used
        # Should use global fallback
        assert result.threshold_value == 150.0

    def test_multiple_bubbles_confident(self):
        """Test with multiple bubbles and clear jump."""
        strategy = LocalThresholdStrategy()
        bubble_values = [100, 102, 104, 200, 202, 204]

        result = strategy.calculate_threshold(bubble_values, ThresholdConfig())

        # Should find gap around 150
        assert 140 < result.threshold_value < 160
        assert result.confidence > 0.5

    def test_low_confidence_uses_global_fallback(self):
        """Test that low confidence uses global fallback."""
        strategy = LocalThresholdStrategy(global_fallback=180.0)
        bubble_values = [100, 110, 120, 130]  # No clear jump

        result = strategy.calculate_threshold(bubble_values, ThresholdConfig())

        assert result.fallback_used
        assert result.threshold_value == 180.0


class TestAdaptiveThresholdStrategy:
    """Test AdaptiveThresholdStrategy."""

    def test_combines_strategies(self):
        """Test that adaptive strategy combines multiple strategies."""
        adaptive = AdaptiveThresholdStrategy(
            strategies=[GlobalThresholdStrategy(), LocalThresholdStrategy()],
            weights=[0.5, 0.5],
        )

        bubble_values = [100, 105, 200, 205]

        result = adaptive.calculate_threshold(bubble_values, ThresholdConfig())

        assert result.method_used == "adaptive_weighted"
        assert "strategy_results" in result.metadata
        assert len(result.metadata["strategy_results"]) == 2

    def test_zero_confidence_fallback(self):
        """Test behavior when all strategies have zero confidence."""
        adaptive = AdaptiveThresholdStrategy(
            strategies=[GlobalThresholdStrategy()], weights=[1.0]
        )

        # Empty values = zero confidence
        result = adaptive.calculate_threshold([], ThresholdConfig())

        assert result.threshold_value == 127.5  # Default
        assert result.confidence == 0.0
        assert result.fallback_used


class TestDetectionRepository:
    """Test DetectionRepository."""

    def test_initialization(self):
        """Test repository initialization."""
        repo = DetectionRepository()

        assert repo.get_total_files_processed() == 0

    def test_file_operations(self):
        """Test file-level operations."""
        repo = DetectionRepository()

        repo.initialize_file("/path/to/file.jpg")

        current = repo.get_current_file_results()
        assert current.file_path == "/path/to/file.jpg"

        repo.finalize_file()

        # Can retrieve finalized file
        retrieved = repo.get_file_results("/path/to/file.jpg")
        assert retrieved.file_path == "/path/to/file.jpg"

    def test_save_and_get_bubble_field(self):
        """Test saving and retrieving bubble field."""
        repo = DetectionRepository()
        repo.initialize_file("/path/to/file.jpg")

        bubble_result = BubbleFieldDetectionResult(
            field_id="q1",
            field_label="Question1",
            bubble_means=[BubbleMeanValue(120, None)],
        )

        repo.save_bubble_field("q1", bubble_result)

        retrieved = repo.get_bubble_field("q1")
        assert retrieved.field_id == "q1"
        assert retrieved.field_label == "Question1"

    def test_get_all_bubble_means(self):
        """Test querying all bubble means across fields."""
        repo = DetectionRepository()
        repo.initialize_file("/path/to/file.jpg")

        # Add two fields
        repo.save_bubble_field(
            "q1",
            BubbleFieldDetectionResult(
                field_id="q1",
                field_label="Q1",
                bubble_means=[BubbleMeanValue(100, None), BubbleMeanValue(200, None)],
            ),
        )

        repo.save_bubble_field(
            "q2",
            BubbleFieldDetectionResult(
                field_id="q2",
                field_label="Q2",
                bubble_means=[BubbleMeanValue(150, None)],
            ),
        )

        all_means = repo.get_all_bubble_means_for_current_file()
        assert len(all_means) == 3

        all_values = repo.get_all_bubble_mean_values_for_current_file()
        assert all_values == [100, 200, 150]

    def test_directory_operations(self):
        """Test directory-level operations."""
        repo = DetectionRepository()

        repo.initialize_directory("/path/to/dir")

        # Process multiple files
        for i in range(3):
            repo.initialize_file(f"/path/to/dir/file{i}.jpg")
            repo.finalize_file()

        assert repo.get_total_files_processed() == 3

        all_results = repo.get_all_file_results()
        assert len(all_results) == 3

    def test_error_when_no_current_file(self):
        """Test that error is raised when accessing current file without initialization."""
        repo = DetectionRepository()

        with pytest.raises(RuntimeError):
            repo.get_current_file_results()

    def test_error_when_field_not_found(self):
        """Test that error is raised when field not found."""
        repo = DetectionRepository()
        repo.initialize_file("/path/to/file.jpg")

        with pytest.raises(KeyError):
            repo.get_bubble_field("nonexistent")


# Property-based tests using hypothesis (optional but powerful)
try:
    from hypothesis import given
    from hypothesis import strategies as st

    class TestThresholdProperties:
        """Property-based tests for threshold strategies."""

        @given(
            bubble_values=st.lists(
                st.floats(min_value=0, max_value=255), min_size=2, max_size=20
            )
        )
        def test_threshold_in_range(self, bubble_values):
            """Threshold should always be between min and max values."""
            if not bubble_values or any(
                math.isnan(v) for v in bubble_values
            ):  # Skip NaN
                return

            strategy = GlobalThresholdStrategy()
            result = strategy.calculate_threshold(bubble_values, ThresholdConfig())

            assert min(bubble_values) <= result.threshold_value <= max(bubble_values)

        @given(
            bubble_values=st.lists(
                st.floats(min_value=0, max_value=255), min_size=1, max_size=20
            )
        )
        def test_confidence_in_range(self, bubble_values):
            """Confidence should always be between 0 and 1."""
            if not bubble_values or any(
                math.isnan(v) for v in bubble_values
            ):  # Skip NaN
                return

            strategy = GlobalThresholdStrategy()
            result = strategy.calculate_threshold(bubble_values, ThresholdConfig())

            assert 0.0 <= result.confidence <= 1.0

except ImportError:
    # hypothesis not installed
    pass
