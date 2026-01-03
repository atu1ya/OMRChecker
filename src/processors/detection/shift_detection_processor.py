"""ML-based field block shift detection and validation processor.

This processor applies ML-detected field block position shifts to the template,
runs traditional detection with adjusted positions, and validates results by
comparing shifted vs non-shifted outputs.
"""

from typing import TYPE_CHECKING

from src.processors.base import ProcessingContext, Processor
from src.processors.detection.template_file_runner import TemplateFileRunner
from src.schemas.models.config import ShiftDetectionConfig
from src.utils.geometry import vector_magnitude
from src.utils.logger import logger

if TYPE_CHECKING:
    from src.processors.layout.field_block.base import FieldBlock


class ShiftDetectionProcessor(Processor):
    """Applies ML-detected field block shifts and validates results.

    This processor:
    1. Reads ML-detected block alignments from context (populated by MLFieldBlockDetector)
    2. Validates shifts against configured max margins (global + per-block)
    3. Creates shifted copies of field blocks
    4. Runs traditional detection twice (with and without shifts)
    5. Compares results at bubble and field level
    6. Adjusts confidence based on mismatch severity
    7. Stores final results (shifted version) in context
    """

    def __init__(self, template, shift_config: ShiftDetectionConfig) -> None:
        """Initialize the shift detection processor.

        Args:
            template: The template containing field blocks and configuration.
            shift_config: Configuration for shift detection and validation.
        """
        self.template = template
        self.shift_config = shift_config
        self.template_file_runner = TemplateFileRunner(template)
        self.stats = {
            "shifts_applied": 0,
            "shifts_rejected": 0,
            "mismatches_detected": 0,
            "confidence_reductions": [],
        }

    def get_name(self) -> str:
        """Get the name of this processor."""
        return "ShiftDetection"

    def process(self, context: ProcessingContext) -> ProcessingContext:
        """Apply shifts and validate detection results.

        Args:
            context: Processing context with aligned image and ML shift data.

        Returns:
            Updated context with shifted detection results and metadata.
        """
        # Extract ML shifts from context (set by MLFieldBlockDetector)
        ml_alignments = context.metadata.get("ml_block_alignments", {})

        if not ml_alignments or not self.shift_config.enabled:
            logger.debug("Shift detection skipped (no shifts or disabled)")
            return context  # No shifts or disabled

        logger.info(
            f"Shift detection enabled with {len(ml_alignments)} potential shifts"
        )

        # Validate and apply shifts
        validated_shifts = self._validate_shifts(ml_alignments)

        if not validated_shifts:
            logger.info("No valid shifts to apply")
            return context

        logger.info(f"Applying {len(validated_shifts)} validated shifts")

        # Run detection with shifts
        shifted_results = self._run_detection_with_shifts(context, validated_shifts)

        # Run detection without shifts (baseline)
        baseline_results = self._run_detection_without_shifts(context)

        # Compare and compute confidence
        final_results, comparison_meta = self._compare_and_adjust_confidence(
            shifted_results, baseline_results, validated_shifts
        )

        # Store final results and metadata
        context.field_id_to_interpretation = final_results["interpretations"]
        context.omr_response = final_results["omr_response"]
        context.is_multi_marked = final_results["is_multi_marked"]
        context.metadata["shift_detection"] = {
            "applied_shifts": validated_shifts,
            "comparison": comparison_meta,
            "confidence_adjustments": comparison_meta["confidence_reductions"],
        }

        logger.info(
            f"Shift detection complete: {self.stats['mismatches_detected']} mismatches detected"
        )

        return context

    def _validate_shifts(self, ml_alignments: dict) -> dict:
        """Validate shifts against configured margins.

        Args:
            ml_alignments: ML-detected block alignments with shift data.

        Returns:
            Dictionary of validated shifts (block_name -> {dx, dy}).
        """
        validated = {}

        for block_name, shift_data in ml_alignments.items():
            dx, dy = shift_data["shift"]

            # Get max allowed shift (per-block override or global)
            max_shift = self.shift_config.per_block_max_shift_pixels.get(
                block_name, self.shift_config.global_max_shift_pixels
            )

            # Check magnitude using geometry utility
            shift_magnitude = vector_magnitude([dx, dy])

            if shift_magnitude <= max_shift:
                validated[block_name] = {"dx": dx, "dy": dy}
                self.stats["shifts_applied"] += 1
                logger.debug(
                    f"Shift for {block_name} validated: ({dx:.1f}, {dy:.1f})px"
                )
            else:
                logger.warning(
                    f"Shift for {block_name} rejected: {shift_magnitude:.1f}px > {max_shift}px"
                )
                self.stats["shifts_rejected"] += 1

        return validated

    def _run_detection_with_shifts(
        self, context: ProcessingContext, shifts: dict
    ) -> dict:
        """Run traditional detection with shifted field blocks.

        Args:
            context: Processing context with image data.
            shifts: Validated shifts to apply.

        Returns:
            Detection results dictionary.
        """
        # Apply shifts to template blocks
        for block_name, shift in shifts.items():
            block = self._find_block_by_name(block_name)
            if block:
                block.shifts = [shift["dx"], shift["dy"]]
                logger.debug(
                    f"Applied shift to {block_name}: ({shift['dx']}, {shift['dy']})"
                )

        # Run traditional detection
        results = self._run_traditional_detection(context)

        # Reset shifts
        for block in self.template.field_blocks:
            block.reset_all_shifts()

        return results

    def _run_detection_without_shifts(self, context: ProcessingContext) -> dict:
        """Run traditional detection without any shifts (baseline).

        Args:
            context: Processing context with image data.

        Returns:
            Detection results dictionary.
        """
        return self._run_traditional_detection(context)

    def _run_traditional_detection(self, context: ProcessingContext) -> dict:
        """Helper to run traditional OMR detection.

        Args:
            context: Processing context with image data.

        Returns:
            Dictionary with interpretations, omr_response, and is_multi_marked.
        """
        # Run detection and interpretation using TemplateFileRunner
        omr_response, is_multi_marked, interpretations = (
            self.template_file_runner.read_omr_and_update_metrics(
                context.file_path, context.gray_image, context.colored_image
            )
        )

        return {
            "interpretations": interpretations,
            "omr_response": omr_response,
            "is_multi_marked": is_multi_marked,
        }

    def _compare_and_adjust_confidence(
        self, shifted_results: dict, baseline_results: dict, _shifts: dict
    ) -> tuple[dict, dict]:
        """Compare shifted vs baseline results and adjust confidence.

        Args:
            shifted_results: Detection results with shifts applied.
            baseline_results: Detection results without shifts.
            _shifts: Applied shifts for logging (unused, kept for interface consistency).

        Returns:
            Tuple of (final_results, comparison_metadata).
        """
        comparison = {
            "bubble_mismatches": [],
            "field_mismatches": [],
            "confidence_reductions": {},
        }

        shifted_interpretations = shifted_results["interpretations"]
        baseline_interpretations = baseline_results["interpretations"]

        for field_id in shifted_interpretations:
            shifted_interp = shifted_interpretations[field_id]
            baseline_interp = baseline_interpretations.get(field_id)

            if not baseline_interp:
                continue

            # Bubble-level comparison
            bubble_diffs = self._compare_bubbles(shifted_interp, baseline_interp)

            # Field-level comparison
            field_diff = self._compare_field_responses(shifted_interp, baseline_interp)

            # Calculate mismatch severity (0.0 = identical, 1.0 = completely different)
            total_bubbles = len(shifted_interp.get("bubble_values", []))
            severity = (
                len(bubble_diffs) / max(total_bubbles, 1) if total_bubbles > 0 else 0.0
            )

            if bubble_diffs:
                comparison["bubble_mismatches"].append(
                    {
                        "field_id": field_id,
                        "count": len(bubble_diffs),
                        "bubbles": bubble_diffs,
                    }
                )

            if field_diff:
                comparison["field_mismatches"].append(
                    {
                        "field_id": field_id,
                        "shifted_response": shifted_interp.get("response"),
                        "baseline_response": baseline_interp.get("response"),
                    }
                )

            # Adjust confidence proportionally if there are differences
            if bubble_diffs or field_diff:
                reduction = self._calculate_confidence_reduction(severity)
                original_conf = shifted_interp.get("confidence", 1.0)
                adjusted_conf = max(0.0, original_conf - reduction)

                shifted_interp["confidence"] = adjusted_conf
                comparison["confidence_reductions"][field_id] = {
                    "original": original_conf,
                    "reduction": reduction,
                    "final": adjusted_conf,
                    "reason": "shift_mismatch",
                }

                self.stats["mismatches_detected"] += 1
                self.stats["confidence_reductions"].append(reduction)

                logger.debug(
                    f"Mismatch in {field_id}: {len(bubble_diffs)} bubbles, "
                    f"confidence {original_conf:.2f} -> {adjusted_conf:.2f}"
                )

        return shifted_results, comparison

    def _calculate_confidence_reduction(self, severity: float) -> float:
        """Calculate proportional confidence reduction based on mismatch severity.

        Args:
            severity: Mismatch severity (0.0 = identical, 1.0 = completely different).

        Returns:
            Confidence reduction value.
        """
        min_reduction = self.shift_config.confidence_reduction_min
        max_reduction = self.shift_config.confidence_reduction_max

        # Linear interpolation between min and max
        return min_reduction + (severity * (max_reduction - min_reduction))

    def _compare_bubbles(self, shifted: dict, baseline: dict) -> list:
        """Compare individual bubble states.

        Args:
            shifted: Shifted interpretation data.
            baseline: Baseline interpretation data.

        Returns:
            List of bubble differences.
        """
        diffs = []
        shifted_bubbles = shifted.get("bubble_values", [])
        baseline_bubbles = baseline.get("bubble_values", [])

        for i, (s_val, b_val) in enumerate(
            zip(shifted_bubbles, baseline_bubbles, strict=True)
        ):
            if s_val != b_val:
                diffs.append({"index": i, "shifted": s_val, "baseline": b_val})

        return diffs

    def _compare_field_responses(self, shifted: dict, baseline: dict) -> dict | None:
        """Compare field-level responses.

        Args:
            shifted: Shifted interpretation data.
            baseline: Baseline interpretation data.

        Returns:
            Difference dictionary if responses differ, None otherwise.
        """
        shifted_resp = shifted.get("response")
        baseline_resp = baseline.get("response")

        if shifted_resp != baseline_resp:
            return {"shifted": shifted_resp, "baseline": baseline_resp}
        return None

    def _find_block_by_name(self, block_name: str) -> "FieldBlock | None":
        """Find a field block by name.

        Args:
            block_name: Name of the field block to find.

        Returns:
            FieldBlock instance or None if not found.
        """
        for block in self.template.field_blocks:
            if block.name == block_name:
                return block
        return None
