"""Threshold calculation strategies for bubble field interpretation.

This module extracts the threshold calculation logic from the monolithic
BubblesFieldInterpretation class into focused, reusable strategies.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np


@dataclass
class ThresholdResult:
    """Result from threshold calculation."""

    threshold_value: float
    confidence: float  # 0.0 to 1.0
    max_jump: float
    method_used: str
    fallback_used: bool = False
    metadata: dict = None

    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ThresholdConfig:
    """Configuration for threshold calculation."""

    min_jump: float = 30.0
    """Minimum jump to consider significant."""

    jump_delta: float = 20.0
    """Delta between jumps for two-jump detection."""

    min_gap_two_bubbles: float = 20.0
    """Minimum gap required when only two bubbles present."""

    min_jump_surplus_for_global_fallback: float = 10.0
    """Extra jump required to avoid global fallback."""

    confident_jump_surplus_for_disparity: float = 15.0
    """Extra jump for high confidence despite disparity."""

    global_threshold_margin: float = 10.0
    """Safety margin for global threshold."""

    outlier_deviation_threshold: float = 5.0
    """Std deviation threshold for outlier detection."""

    default_threshold: float = 127.5
    """Default fallback threshold."""


class ThresholdStrategy(ABC):
    """Abstract base class for threshold calculation strategies."""

    @abstractmethod
    def calculate_threshold(
        self, bubble_mean_values: list[float], config: ThresholdConfig
    ) -> ThresholdResult:
        """Calculate threshold from bubble mean values.

        Args:
            bubble_mean_values: List of bubble mean intensity values
            config: Threshold configuration

        Returns:
            ThresholdResult with threshold and confidence information
        """


class GlobalThresholdStrategy(ThresholdStrategy):
    """Strategy using global file-level statistics.

    Based on the existing get_global_threshold logic.
    Finds the largest gap in sorted bubble means across all fields.
    """

    def calculate_threshold(
        self, bubble_mean_values: list[float], config: ThresholdConfig
    ) -> ThresholdResult:
        """Calculate global threshold by finding largest gap."""
        if len(bubble_mean_values) < 2:
            return ThresholdResult(
                threshold_value=config.default_threshold,
                confidence=0.0,
                max_jump=0.0,
                method_used="global_default",
                fallback_used=True,
            )

        sorted_values = sorted(bubble_mean_values)

        # Find the FIRST LARGE GAP using looseness
        looseness = 1
        ls = (looseness + 1) // 2
        total_bubbles_loose = len(sorted_values) - ls

        max_jump = config.min_jump
        threshold = config.default_threshold

        for i in range(ls, total_bubbles_loose):
            jump = sorted_values[i + ls] - sorted_values[i - ls]
            if jump > max_jump:
                max_jump = jump
                threshold = sorted_values[i - ls] + jump / 2

        # Calculate confidence based on jump size
        # Higher jump = higher confidence
        confidence = min(1.0, max_jump / (config.min_jump * 3))

        return ThresholdResult(
            threshold_value=threshold,
            confidence=confidence,
            max_jump=max_jump,
            method_used="global_max_jump",
            fallback_used=max_jump < config.min_jump,
            metadata={
                "num_bubbles": len(bubble_mean_values),
                "min_value": min(bubble_mean_values),
                "max_value": max(bubble_mean_values),
            },
        )


class LocalThresholdStrategy(ThresholdStrategy):
    """Strategy using field-level statistics.

    Based on the existing get_local_threshold logic.
    Calculates threshold for individual field, with fallback to global.
    """

    def __init__(self, global_fallback: float | None = None) -> None:
        """Initialize with optional global fallback threshold.

        Args:
            global_fallback: Global threshold to use when local confidence is low
        """
        self.global_fallback = global_fallback

    def calculate_threshold(
        self, bubble_mean_values: list[float], config: ThresholdConfig
    ) -> ThresholdResult:
        """Calculate local threshold with global fallback."""
        fallback_threshold = self.global_fallback or config.default_threshold

        # Base case: empty or single bubble
        if len(bubble_mean_values) < 2:
            return ThresholdResult(
                threshold_value=fallback_threshold,
                confidence=0.0,
                max_jump=0.0,
                method_used="local_single_bubble_fallback",
                fallback_used=True,
            )

        sorted_values = sorted(bubble_mean_values)

        # Special case: exactly 2 bubbles
        if len(sorted_values) == 2:
            gap = sorted_values[1] - sorted_values[0]
            if gap < config.min_gap_two_bubbles:
                return ThresholdResult(
                    threshold_value=fallback_threshold,
                    confidence=0.3,
                    max_jump=gap,
                    method_used="local_two_bubbles_small_gap_fallback",
                    fallback_used=True,
                )
            return ThresholdResult(
                threshold_value=float(np.mean(sorted_values)),
                confidence=0.7,
                max_jump=gap,
                method_used="local_two_bubbles_mean",
                fallback_used=False,
            )

        # 3+ bubbles: find largest jump
        max_jump = 0.0
        threshold = fallback_threshold

        for i in range(1, len(sorted_values) - 1):
            jump = sorted_values[i + 1] - sorted_values[i - 1]
            if jump > max_jump:
                max_jump = jump
                threshold = sorted_values[i - 1] + jump / 2

        # Check if jump is confident
        confident_jump = config.min_jump + config.min_jump_surplus_for_global_fallback

        if max_jump < confident_jump:
            # Low confidence - use global fallback
            return ThresholdResult(
                threshold_value=fallback_threshold,
                confidence=0.4,
                max_jump=max_jump,
                method_used="local_low_confidence_global_fallback",
                fallback_used=True,
                metadata={"local_threshold": threshold},
            )

        # High confidence
        confidence = min(1.0, max_jump / (confident_jump * 2))

        return ThresholdResult(
            threshold_value=threshold,
            confidence=confidence,
            max_jump=max_jump,
            method_used="local_max_jump",
            fallback_used=False,
            metadata={"num_bubbles": len(bubble_mean_values)},
        )


class AdaptiveThresholdStrategy(ThresholdStrategy):
    """Adaptive strategy that combines multiple strategies.

    Uses weighted average based on confidence scores.
    """

    def __init__(
        self, strategies: list[ThresholdStrategy], weights: list[float] | None = None
    ) -> None:
        """Initialize with strategies and optional weights.

        Args:
            strategies: List of threshold strategies to combine
            weights: Optional weights for each strategy (default: equal weights)
        """
        self.strategies = strategies
        self.weights = weights or [1.0] * len(strategies)

        if len(self.strategies) != len(self.weights):
            msg = "Number of strategies must match number of weights"
            raise ValueError(msg)

    def calculate_threshold(
        self, bubble_mean_values: list[float], config: ThresholdConfig
    ) -> ThresholdResult:
        """Calculate threshold using weighted average of strategies."""
        # Get results from all strategies
        results = [
            strategy.calculate_threshold(bubble_mean_values, config)
            for strategy in self.strategies
        ]

        # Calculate weighted average based on confidence
        total_weight = sum(
            result.confidence * weight
            for result, weight in zip(results, self.weights, strict=False)
        )

        if total_weight == 0:
            # All strategies have zero confidence
            return ThresholdResult(
                threshold_value=config.default_threshold,
                confidence=0.0,
                max_jump=0.0,
                method_used="adaptive_all_zero_confidence",
                fallback_used=True,
            )

        weighted_threshold = (
            sum(
                result.threshold_value * result.confidence * weight
                for result, weight in zip(results, self.weights, strict=False)
            )
            / total_weight
        )

        # Use max confidence and max jump from all strategies
        max_confidence = max(result.confidence for result in results)
        max_jump_value = max(result.max_jump for result in results)

        return ThresholdResult(
            threshold_value=weighted_threshold,
            confidence=max_confidence,
            max_jump=max_jump_value,
            method_used="adaptive_weighted",
            fallback_used=any(result.fallback_used for result in results),
            metadata={
                "strategy_results": [
                    {
                        "method": result.method_used,
                        "threshold": result.threshold_value,
                        "confidence": result.confidence,
                        "weight": weight,
                    }
                    for result, weight in zip(results, self.weights, strict=False)
                ]
            },
        )


def create_default_threshold_calculator(
    global_threshold: float | None = None,
) -> ThresholdStrategy:
    """Factory function to create default threshold calculator.

    Args:
        global_threshold: Optional global threshold for local strategy fallback

    Returns:
        AdaptiveThresholdStrategy combining global and local strategies
    """
    return AdaptiveThresholdStrategy(
        strategies=[
            GlobalThresholdStrategy(),
            LocalThresholdStrategy(global_fallback=global_threshold),
        ],
        weights=[0.4, 0.6],  # Prefer local threshold
    )
