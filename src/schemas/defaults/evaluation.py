from src.schemas.constants import (
    DEFAULT_ANSWERS_SUMMARY_FORMAT_STRING,
    DEFAULT_SCORE_FORMAT_STRING,
)
from src.schemas.models.evaluation import (
    DrawAnswerGroupsConfig,
    DrawAnswersSummaryConfig,
    DrawDetectedBubbleTextsConfig,
    DrawQuestionVerdictsConfig,
    DrawScoreConfig,
    EvaluationConfig,
    OutputsConfiguration,
)

# Create default evaluation config instance
EVALUATION_CONFIG_DEFAULTS = EvaluationConfig(
    options={},
    marking_schemes={},
    conditional_sets=[],
    outputs_configuration=OutputsConfiguration(
        should_explain_scoring=False,
        should_export_explanation_csv=False,
        draw_score=DrawScoreConfig(
            enabled=False,
            position=[200, 200],
            score_format_string=DEFAULT_SCORE_FORMAT_STRING,
            size=1.5,
        ),
        draw_answers_summary=DrawAnswersSummaryConfig(
            enabled=False,
            position=[200, 600],
            answers_summary_format_string=DEFAULT_ANSWERS_SUMMARY_FORMAT_STRING,
            size=1.0,
        ),
        draw_question_verdicts=DrawQuestionVerdictsConfig(
            enabled=True,
            verdict_colors={
                "correct": "#00FF00",
                "neutral": None,
                "incorrect": "#FF0000",
                "bonus": "#00DDDD",
            },
            verdict_symbol_colors={
                "positive": "#000000",
                "neutral": "#000000",
                "negative": "#000000",
                "bonus": "#000000",
            },
            draw_answer_groups=DrawAnswerGroupsConfig(
                enabled=True,
                color_sequence=["#8DFBC4", "#F7FB8D", "#8D9EFB", "#EA666F"],
            ),
        ),
        draw_detected_bubble_texts=DrawDetectedBubbleTextsConfig(enabled=True),
    ),
)
