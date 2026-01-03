"""Detection fusion module for merging ML and traditional bubble detection results.

Combines outputs from ML-based and traditional detection methods using
confidence-weighted voting and discrepancy flagging.
"""

from typing import ClassVar

from src.utils.logger import logger


class DetectionFusion:
    """Fuses ML-based and traditional bubble detection results.

    Strategy:
    1. Use ML field blocks to refine alignment shifts
    2. Compare traditional vs ML bubble detections per field
    3. Use confidence-weighted voting for final bubble states
    4. Flag discrepancies for manual review
    """

    # Mapping of fusion strategy names to method names
    FUSION_STRATEGIES: ClassVar[dict[str, str]] = {
        "confidence_weighted": "_confidence_weighted_fusion",
        "ml_fallback": "_ml_fallback_fusion",
        "traditional_primary": "_traditional_primary_fusion",
    }

    def __init__(
        self,
        fusion_strategy: str = "confidence_weighted",
        discrepancy_threshold: float = 0.3,
    ) -> None:
        """Initialize detection fusion.

        Args:
            fusion_strategy: Strategy for fusion - "confidence_weighted", "ml_fallback", "traditional_primary"
            discrepancy_threshold: Threshold for flagging discrepancies
        """
        self.fusion_strategy = fusion_strategy
        self.discrepancy_threshold = discrepancy_threshold

    def fuse_detections(
        self,
        _traditional_response: dict,
        ml_blocks_response: list[dict],
        field_id_to_interpretation: dict,
        confidence_threshold: float = 0.85,
    ) -> tuple[dict, list[dict]]:
        """Fuse traditional and ML detection results.

        Args:
            _traditional_response: Traditional OMR response dictionary (unused, for future use)
            ml_blocks_response: ML-detected blocks with bubble detections
            field_id_to_interpretation: Field interpretations from traditional detection
            confidence_threshold: Minimum confidence for high-confidence classification

        Returns:
            Tuple of (fused_response, discrepancies)
        """
        fused_response = {}
        discrepancies = []

        for field_id, trad_interp in field_id_to_interpretation.items():
            # Get ML interpretation for same field
            ml_interp = self._find_ml_interpretation(field_id, ml_blocks_response)

            if ml_interp is None:
                # No ML detection, use traditional
                fused_response[field_id] = trad_interp
                continue

            # Both available - apply fusion strategy using strategy pattern
            strategy_method_name = self.FUSION_STRATEGIES.get(self.fusion_strategy)
            if strategy_method_name:
                strategy_method = getattr(self, strategy_method_name)
                fused, discrepancy = strategy_method(
                    field_id,
                    trad_interp,
                    ml_interp,
                    confidence_threshold,
                )
            else:
                # Unknown strategy - default to traditional
                fused = trad_interp
                discrepancy = None
                logger.warning(
                    f"Unknown fusion strategy '{self.fusion_strategy}', using traditional detection"
                )

            fused_response[field_id] = fused
            if discrepancy:
                discrepancies.append(discrepancy)

        logger.info(
            f"Detection fusion complete: {len(fused_response)} fields, {len(discrepancies)} discrepancies"
        )

        return fused_response, discrepancies

    def _confidence_weighted_fusion(
        self,
        field_id: str,
        trad_interp,
        ml_interp: dict,
        confidence_threshold: float,
    ) -> tuple[any, dict | None]:
        """Confidence-weighted fusion strategy.

        Args:
            field_id: Field identifier
            trad_interp: Traditional interpretation
            ml_interp: ML interpretation
            confidence_threshold: High confidence threshold

        Returns:
            Tuple of (fused_interpretation, discrepancy_info)
        """
        # Get confidence scores
        trad_confidence = getattr(trad_interp, "overall_confidence_score", 0.0)
        ml_confidence = ml_interp.get("confidence", 0.0)

        # Check agreement
        trad_response = getattr(trad_interp, "matched_bubbles", [])
        ml_response = ml_interp.get("detected_bubbles", [])

        responses_agree = self._responses_agree(trad_response, ml_response)

        if (
            trad_confidence > confidence_threshold
            and ml_confidence > confidence_threshold
        ):
            # Both high confidence
            if responses_agree:
                # Agreement - use traditional (more tested)
                return trad_interp, None
            # Disagreement - flag for review, use higher confidence
            discrepancy = {
                "field_id": field_id,
                "traditional": {
                    "response": trad_response,
                    "confidence": trad_confidence,
                },
                "ml": {"response": ml_response, "confidence": ml_confidence},
                "reason": "high_confidence_disagreement",
            }

            # Use higher confidence
            if trad_confidence > ml_confidence:
                return trad_interp, discrepancy
            # Create ML-based interpretation (simplified)
            return self._create_ml_interpretation(ml_interp), discrepancy

        if trad_confidence < 0.6 and ml_confidence > confidence_threshold:
            # Low traditional confidence, high ML confidence - use ML
            logger.debug(
                f"Using ML for {field_id}: trad_conf={trad_confidence:.2f}, ml_conf={ml_confidence:.2f}"
            )
            return self._create_ml_interpretation(ml_interp), None
        # Default to traditional
        return trad_interp, None

    def _ml_fallback_fusion(
        self,
        _field_id: str,
        trad_interp,
        ml_interp: dict,
        _confidence_threshold: float,
    ) -> tuple[any, dict | None]:
        """ML fallback fusion strategy - use ML only when traditional is low confidence.

        Args:
            _field_id: Field identifier (unused, for future use)
            trad_interp: Traditional interpretation
            ml_interp: ML interpretation
            _confidence_threshold: High confidence threshold (unused, for future use)

        Returns:
            Tuple of (fused_interpretation, discrepancy_info)
        """
        trad_confidence = getattr(trad_interp, "overall_confidence_score", 0.0)

        if trad_confidence < 0.6:
            # Use ML as fallback
            return self._create_ml_interpretation(ml_interp), None
        # Use traditional
        return trad_interp, None

    def _traditional_primary_fusion(
        self,
        field_id: str,
        trad_interp,
        ml_interp: dict,
    ) -> tuple[any, dict | None]:
        """Traditional primary fusion strategy - always use traditional, log ML for comparison.

        Args:
            field_id: Field identifier
            trad_interp: Traditional interpretation
            ml_interp: ML interpretation

        Returns:
            Tuple of (fused_interpretation, discrepancy_info)
        """
        # Always use traditional, but log if ML differs significantly
        trad_response = getattr(trad_interp, "matched_bubbles", [])
        ml_response = ml_interp.get("detected_bubbles", [])

        if not self._responses_agree(trad_response, ml_response):
            discrepancy = {
                "field_id": field_id,
                "traditional": trad_response,
                "ml": ml_response,
                "reason": "informational_difference",
            }
            return trad_interp, discrepancy

        return trad_interp, None

    def _find_ml_interpretation(
        self,
        _field_id: str,
        _ml_blocks_response: list[dict],
    ) -> dict | None:
        """Find ML interpretation for a specific field.

        Args:
            _field_id: Field identifier to find (unused, placeholder for future implementation)
            _ml_blocks_response: ML-detected blocks with bubbles (unused, placeholder)

        Returns:
            ML interpretation dictionary or None if not found
        """
        # This is a simplified implementation
        # In reality, you'd need to map field_id to specific bubbles in ML blocks
        # For now, return None to use traditional detection
        # TODO: Implement proper field-to-bubble mapping

        return None

    def _responses_agree(self, _trad_response: list, _ml_response: list) -> bool:
        """Check if traditional and ML responses agree.

        Args:
            _trad_response: Traditional response (unused, placeholder for future implementation)
            _ml_response: ML response (unused, placeholder for future implementation)

        Returns:
            True if responses substantially agree
        """
        # Simplified agreement check
        # TODO: Implement proper comparison based on bubble positions and states

        return True

    def _create_ml_interpretation(self, ml_interp: dict) -> dict:
        """Create an interpretation object from ML detection results.

        Args:
            ml_interp: ML interpretation dictionary

        Returns:
            Interpretation-like object (simplified placeholder for future implementation)
        """
        # Simplified placeholder
        # TODO: Create proper interpretation object matching FieldInterpretation structure

        return ml_interp
