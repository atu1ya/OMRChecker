"""Geometry utility functions for ML detection and alignment.

Provides common geometric calculations used across ML processors
to maintain consistency and reduce code duplication.
"""

from collections.abc import Sequence


def euclidean_distance(point1: Sequence[float], point2: Sequence[float]) -> float:
    """Calculate Euclidean distance between two points.

    Args:
        point1: First point coordinates [x, y]
        point2: Second point coordinates [x, y]

    Returns:
        Euclidean distance between the points
    """
    return sum((a - b) ** 2 for a, b in zip(point1, point2, strict=True)) ** 0.5


def vector_magnitude(vector: Sequence[float]) -> float:
    """Calculate magnitude (length) of a vector.

    Args:
        vector: Vector coordinates (e.g., [dx, dy] for 2D)

    Returns:
        Vector magnitude
    """
    return sum(x**2 for x in vector) ** 0.5


def bbox_center(origin: Sequence[float], dimensions: Sequence[float]) -> list[float]:
    """Calculate center point of a bounding box.

    Args:
        origin: Bounding box origin [x, y]
        dimensions: Bounding box dimensions [width, height]

    Returns:
        Center point [x, y]
    """
    return [
        origin[0] + dimensions[0] / 2,
        origin[1] + dimensions[1] / 2,
    ]
