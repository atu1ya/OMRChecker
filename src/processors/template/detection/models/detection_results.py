"""Typed models for detection results.

This module provides strongly-typed, validated models for detection results
to replace dictionary-based aggregates.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np


class ScanQuality(str, Enum):
    """Quality assessment of scanned field."""

    EXCELLENT = "excellent"  # Clear contrast, high confidence
    GOOD = "good"  # Acceptable quality
    ACCEPTABLE = "acceptable"  # Marginal, may need review
    POOR = "poor"  # Likely to have errors


@dataclass
class BubbleMeanValue:
    """Single bubble mean intensity value with metadata."""

    mean_value: float
    unit_bubble: Any  # BubblesScanBox - avoiding circular import
    position: tuple[int, int] = (0, 0)

    def __lt__(self, other: "BubbleMeanValue") -> bool:
        """Enable sorting by mean value."""
        return self.mean_value < other.mean_value

    def __str__(self) -> str:
        """String representation for debugging."""
        return f"BubbleMean({self.mean_value:.1f})"


@dataclass
class BubbleFieldDetectionResult:
    """Typed result for bubble field detection.

    Replaces nested dictionary structure with strongly-typed model.
    Includes auto-calculated properties to eliminate utility functions.
    """

    field_id: str
    field_label: str
    bubble_means: list[BubbleMeanValue]
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def std_deviation(self) -> float:
        """Calculate standard deviation from bubble means."""
        if not self.bubble_means:
            return 0.0
        values = [bm.mean_value for bm in self.bubble_means]
        return float(np.std(values))

    @property
    def scan_quality(self) -> ScanQuality:
        """Automatically assess scan quality based on std deviation."""
        std = self.std_deviation
        if std > 50:
            return ScanQuality.EXCELLENT
        if std > 30:
            return ScanQuality.GOOD
        if std > 15:
            return ScanQuality.ACCEPTABLE
        return ScanQuality.POOR

    @property
    def is_reliable(self) -> bool:
        """Check if detection is reliable enough for interpretation."""
        return self.scan_quality in [ScanQuality.EXCELLENT, ScanQuality.GOOD]

    @property
    def sorted_bubble_means(self) -> list[BubbleMeanValue]:
        """Get bubble means sorted by value."""
        return sorted(self.bubble_means)

    @property
    def mean_values(self) -> list[float]:
        """Get just the mean values as floats."""
        return [bm.mean_value for bm in self.bubble_means]

    @property
    def sorted_mean_values(self) -> list[float]:
        """Get sorted mean values as floats."""
        return [bm.mean_value for bm in self.sorted_bubble_means]

    @property
    def jumps(self) -> list[tuple[float, BubbleMeanValue]]:
        """Calculate jumps between consecutive sorted bubble means.

        Returns list of (jump_size, bubble_after_jump) tuples.
        Replaces get_jumps_in_bubble_means utility function.
        """
        sorted_means = self.sorted_bubble_means
        if len(sorted_means) < 2:
            return []

        jumps_list = []
        for i in range(1, len(sorted_means)):
            jump = sorted_means[i].mean_value - sorted_means[i - 1].mean_value
            jumps_list.append((round(jump, 2), sorted_means[i - 1]))

        return jumps_list

    @property
    def max_jump(self) -> float:
        """Get maximum jump between consecutive sorted means."""
        if len(self.bubble_means) < 2:
            return 0.0
        jumps = self.jumps
        return max(jump for jump, _ in jumps) if jumps else 0.0

    @property
    def min_mean(self) -> float:
        """Get minimum bubble mean value."""
        return min(self.mean_values) if self.bubble_means else 0.0

    @property
    def max_mean(self) -> float:
        """Get maximum bubble mean value."""
        return max(self.mean_values) if self.bubble_means else 255.0

    def __len__(self) -> int:
        """Return number of bubbles."""
        return len(self.bubble_means)

    def __repr__(self) -> str:
        """Readable representation."""
        return (
            f"BubbleFieldDetectionResult(field={self.field_label}, "
            f"bubbles={len(self)}, std={self.std_deviation:.1f}, "
            f"quality={self.scan_quality.value})"
        )


@dataclass
class OCRFieldDetectionResult:
    """Typed result for OCR field detection."""

    field_id: str
    field_label: str
    detections: list[Any]  # List of OCRDetection
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def __repr__(self) -> str:
        """Readable representation."""
        return (
            f"OCRFieldDetectionResult(field={self.field_label}, "
            f"detections={len(self.detections)}, confidence={self.confidence:.2f})"
        )


@dataclass
class BarcodeFieldDetectionResult:
    """Typed result for barcode field detection."""

    field_id: str
    field_label: str
    detections: list[Any]  # List of BarcodeDetection
    timestamp: datetime = field(default_factory=datetime.now)

    def __repr__(self) -> str:
        """Readable representation."""
        return (
            f"BarcodeFieldDetectionResult(field={self.field_label}, "
            f"detections={len(self.detections)})"
        )


@dataclass
class FileDetectionResults:
    """All detection results for a single file.

    Replaces nested file_level_aggregates dictionary structure.
    """

    file_path: str
    bubble_fields: dict[str, BubbleFieldDetectionResult] = field(default_factory=dict)
    ocr_fields: dict[str, OCRFieldDetectionResult] = field(default_factory=dict)
    barcode_fields: dict[str, BarcodeFieldDetectionResult] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def get_field_result(
        self, field_id: str
    ) -> (
        BubbleFieldDetectionResult
        | OCRFieldDetectionResult
        | BarcodeFieldDetectionResult
    ):
        """Get result for any field type."""
        if field_id in self.bubble_fields:
            return self.bubble_fields[field_id]
        if field_id in self.ocr_fields:
            return self.ocr_fields[field_id]
        if field_id in self.barcode_fields:
            return self.barcode_fields[field_id]
        msg = f"Field {field_id} not found in detection results"
        raise KeyError(msg)

    @property
    def all_bubble_means(self) -> list[BubbleMeanValue]:
        """Get all bubble means across all bubble fields."""
        return [
            mean
            for field_result in self.bubble_fields.values()
            for mean in field_result.bubble_means
        ]

    @property
    def all_bubble_mean_values(self) -> list[float]:
        """Get all bubble mean values as floats."""
        return [bm.mean_value for bm in self.all_bubble_means]

    @property
    def num_fields(self) -> int:
        """Total number of fields detected."""
        return len(self.bubble_fields) + len(self.ocr_fields) + len(self.barcode_fields)

    def __repr__(self) -> str:
        """Readable representation."""
        return f"FileDetectionResults(file={self.file_path}, fields={self.num_fields})"
