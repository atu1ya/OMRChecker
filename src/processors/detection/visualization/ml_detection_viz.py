"""Visualization tools for debugging ML detections and comparisons.

Provides utilities to visualize ML-detected field blocks, bubbles,
and compare traditional vs ML detection results.
"""

from pathlib import Path

import cv2
import numpy as np

from src.utils.logger import logger


class MLDetectionVisualizer:
    """Visualize ML detection results for debugging.

    Draws detected field blocks, bubbles, and comparison overlays.
    """

    # Colors (BGR format for OpenCV)
    COLOR_FIELD_BLOCK = (0, 255, 0)  # Green
    COLOR_BUBBLE_EMPTY = (255, 0, 0)  # Blue
    COLOR_BUBBLE_FILLED = (0, 0, 255)  # Red
    COLOR_TRADITIONAL = (255, 255, 0)  # Cyan
    COLOR_ML = (255, 0, 255)  # Magenta
    COLOR_DISCREPANCY = (0, 165, 255)  # Orange

    def __init__(self, output_dir: Path | None = None) -> None:
        """Initialize visualizer.

        Args:
            output_dir: Directory to save visualization images
        """
        self.output_dir = Path(output_dir) if output_dir else Path("outputs/ml_viz")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def visualize_field_blocks(
        self,
        image: np.ndarray,
        ml_blocks: list[dict],
        output_name: str = "field_blocks.jpg",
    ) -> np.ndarray:
        """Visualize detected field blocks.

        Args:
            image: Input image
            ml_blocks: ML-detected field blocks
            output_name: Output filename

        Returns:
            Annotated image
        """
        viz_image = image.copy()
        if len(viz_image.shape) == 2:
            viz_image = cv2.cvtColor(viz_image, cv2.COLOR_GRAY2BGR)

        for block in ml_blocks:
            x1, y1, x2, y2 = block["bbox_xyxy"]
            confidence = block["confidence"]
            class_name = block["class_name"]

            # Draw bounding box
            cv2.rectangle(viz_image, (x1, y1), (x2, y2), self.COLOR_FIELD_BLOCK, 2)

            # Draw label
            label = f"{class_name}: {confidence:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
            cv2.rectangle(
                viz_image,
                (x1, y1 - label_size[1] - 5),
                (x1 + label_size[0], y1),
                self.COLOR_FIELD_BLOCK,
                -1,
            )
            cv2.putText(
                viz_image,
                label,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 0),
                1,
            )

        # Save
        output_path = self.output_dir / output_name
        cv2.imwrite(str(output_path), viz_image)
        logger.debug(f"Saved field block visualization to {output_path}")

        return viz_image

    def visualize_bubbles(
        self,
        image: np.ndarray,
        ml_blocks: list[dict],
        output_name: str = "bubbles.jpg",
    ) -> np.ndarray:
        """Visualize detected bubbles within field blocks.

        Args:
            image: Input image
            ml_blocks: ML-detected blocks with bubble detections
            output_name: Output filename

        Returns:
            Annotated image
        """
        viz_image = image.copy()
        if len(viz_image.shape) == 2:
            viz_image = cv2.cvtColor(viz_image, cv2.COLOR_GRAY2BGR)

        for block in ml_blocks:
            # Draw block outline
            x1, y1, x2, y2 = block["bbox_xyxy"]
            cv2.rectangle(viz_image, (x1, y1), (x2, y2), self.COLOR_FIELD_BLOCK, 1)

            # Draw bubbles
            for bubble in block.get("ml_bubbles", []):
                bx1, by1, bx2, by2 = bubble["bbox_xyxy"]
                state = bubble["state"]
                confidence = bubble["confidence"]

                color = (
                    self.COLOR_BUBBLE_FILLED
                    if state == "filled"
                    else self.COLOR_BUBBLE_EMPTY
                )

                # Draw bubble
                cv2.rectangle(viz_image, (bx1, by1), (bx2, by2), color, 1)

                # Draw confidence
                label = f"{confidence:.2f}"
                cv2.putText(
                    viz_image,
                    label,
                    (bx1, by1 - 2),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.3,
                    color,
                    1,
                )

        # Save
        output_path = self.output_dir / output_name
        cv2.imwrite(str(output_path), viz_image)
        logger.debug(f"Saved bubble visualization to {output_path}")

        return viz_image

    def visualize_comparison(
        self,
        image: np.ndarray,
        _traditional_response: dict,
        ml_blocks: list[dict],
        discrepancies: list[dict],
        output_name: str = "comparison.jpg",
    ) -> np.ndarray:
        """Visualize side-by-side comparison of traditional vs ML detection.

        Args:
            image: Input image
            _traditional_response: Traditional detection results (unused, placeholder)
            ml_blocks: ML detection results
            discrepancies: List of discrepancies
            output_name: Output filename

        Returns:
            Annotated comparison image
        """
        # Create side-by-side comparison
        if len(image.shape) == 2:
            image_bgr = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        else:
            image_bgr = image.copy()

        traditional_viz = image_bgr.copy()
        ml_viz = image_bgr.copy()

        # Draw traditional results (simplified - would need actual implementation)
        cv2.putText(
            traditional_viz,
            "Traditional Detection",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            self.COLOR_TRADITIONAL,
            2,
        )

        # Draw ML results
        ml_viz = self.visualize_bubbles(ml_viz, ml_blocks, "temp.jpg")
        cv2.putText(
            ml_viz,
            "ML Detection",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            self.COLOR_ML,
            2,
        )

        # Concatenate horizontally
        comparison = np.concatenate([traditional_viz, ml_viz], axis=1)

        # Draw discrepancies count
        if discrepancies:
            cv2.putText(
                comparison,
                f"Discrepancies: {len(discrepancies)}",
                (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                self.COLOR_DISCREPANCY,
                2,
            )

        # Save
        output_path = self.output_dir / output_name
        cv2.imwrite(str(output_path), comparison)
        logger.info(f"Saved comparison visualization to {output_path}")

        return comparison

    def create_detection_dashboard(
        self,
        image: np.ndarray,
        ml_blocks: list[dict],
        _traditional_response: dict | None = None,
        discrepancies: list[dict] | None = None,
        file_name: str = "dashboard.jpg",
    ) -> None:
        """Create a comprehensive detection dashboard.

        Args:
            image: Input image
            ml_blocks: ML-detected blocks
            _traditional_response: Traditional detection results (unused, placeholder)
            discrepancies: List of discrepancies (optional)
            file_name: Output filename
        """
        # Create subplots
        field_blocks_viz = self.visualize_field_blocks(
            image, ml_blocks, "temp_blocks.jpg"
        )
        bubbles_viz = self.visualize_bubbles(image, ml_blocks, "temp_bubbles.jpg")

        # Stack vertically
        dashboard = np.concatenate([field_blocks_viz, bubbles_viz], axis=0)

        # Add statistics overlay
        stats_text = [
            f"Field Blocks Detected: {len(ml_blocks)}",
            f"Total Bubbles: {sum(len(b.get('ml_bubbles', [])) for b in ml_blocks)}",
        ]

        if discrepancies:
            stats_text.append(f"Discrepancies: {len(discrepancies)}")

        y_offset = 30
        for text in stats_text:
            cv2.putText(
                dashboard,
                text,
                (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )
            y_offset += 30

        # Save dashboard
        output_path = self.output_dir / file_name
        cv2.imwrite(str(output_path), dashboard)
        logger.info(f"Created detection dashboard at {output_path}")
