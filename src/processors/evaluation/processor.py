"""Evaluation Processor for scoring OMR responses."""

from src.processors.base import ProcessingContext, Processor
from src.processors.evaluation.evaluation_meta import evaluate_concatenated_response
from src.schemas.constants import DEFAULT_ANSWERS_SUMMARY_FORMAT_STRING
from src.utils.logger import logger


class EvaluationProcessor(Processor):
    """Processor that evaluates OMR responses against an answer key.

    This processor:
    1. Takes the concatenated OMR response
    2. Evaluates it against the answer key from evaluation config
    3. Computes score and evaluation metadata
    4. Stores results in context
    """

    def __init__(self, evaluation_config) -> None:
        """Initialize the Evaluation processor.

        Args:
            evaluation_config: The evaluation configuration containing answer keys
        """
        self.evaluation_config = evaluation_config

    def get_name(self) -> str:
        """Get the name of this processor."""
        return "Evaluation"

    def process(self, context: ProcessingContext) -> ProcessingContext:
        """Execute evaluation and scoring.

        Args:
            context: Processing context with OMR response

        Returns:
            Updated context with score and evaluation metadata
        """
        logger.debug(f"Starting {self.get_name()} processor")

        if not self.evaluation_config:
            logger.debug("No evaluation config provided, skipping evaluation")
            context.score = 0
            context.evaluation_meta = None
            return context

        concatenated_omr_response = context.omr_response
        file_path = context.file_path

        # Get the evaluation config for this specific response
        evaluation_config_for_response = (
            self.evaluation_config.get_evaluation_config_for_response(
                concatenated_omr_response, file_path
            )
        )

        if evaluation_config_for_response is None:
            logger.debug("No matching evaluation config for this response")
            context.score = 0
            context.evaluation_meta = None
            return context

        # Log the read response if not explaining scoring
        if not evaluation_config_for_response.get_should_explain_scoring():
            logger.info(f"Read Response: \n{concatenated_omr_response}")

        # Evaluate the response
        score, evaluation_meta = evaluate_concatenated_response(
            concatenated_omr_response, evaluation_config_for_response
        )

        # Get formatted answers summary
        (
            default_answers_summary,
            *_,
        ) = evaluation_config_for_response.get_formatted_answers_summary(
            DEFAULT_ANSWERS_SUMMARY_FORMAT_STRING
        )

        # Store results in context
        context.score = score
        context.evaluation_meta = evaluation_meta
        context.evaluation_config_for_response = evaluation_config_for_response
        context.default_answers_summary = default_answers_summary

        logger.debug(f"Completed {self.get_name()} processor with score: {score}")

        return context
