"""Typed dataclass models for evaluation configuration."""

from dataclasses import dataclass, field

from src.utils.serialization import dataclass_to_dict


@dataclass
class DrawScoreConfig:
    """Configuration for drawing score on output images."""

    enabled: bool = False
    position: list[int] = field(default_factory=lambda: [200, 200])
    score_format_string: str = "Score: {score}"
    size: float = 1.5


@dataclass
class DrawAnswersSummaryConfig:
    """Configuration for drawing answers summary on output images."""

    enabled: bool = False
    position: list[int] = field(default_factory=lambda: [200, 600])
    answers_summary_format_string: str = (
        "Correct: {correct} Incorrect: {incorrect} Unmarked: {unmarked}"
    )
    size: float = 1.0


@dataclass
class DrawAnswerGroupsConfig:
    """Configuration for drawing answer groups."""

    enabled: bool = True
    color_sequence: list[str] = field(
        default_factory=lambda: ["#8DFBC4", "#F7FB8D", "#8D9EFB", "#EA666F"]
    )


@dataclass
class DrawQuestionVerdictsConfig:
    """Configuration for drawing question verdicts on output images."""

    enabled: bool = True
    verdict_colors: dict[str, str | None] = field(
        default_factory=lambda: {
            "correct": "#00FF00",
            "neutral": None,
            "incorrect": "#FF0000",
            "bonus": "#00DDDD",
        }
    )
    verdict_symbol_colors: dict[str, str] = field(
        default_factory=lambda: {
            "positive": "#000000",
            "neutral": "#000000",
            "negative": "#000000",
            "bonus": "#000000",
        }
    )
    draw_answer_groups: DrawAnswerGroupsConfig = field(
        default_factory=DrawAnswerGroupsConfig
    )


@dataclass
class DrawDetectedBubbleTextsConfig:
    """Configuration for drawing detected bubble texts."""

    enabled: bool = True


@dataclass
class OutputsConfiguration:
    """Configuration for evaluation outputs and visualization."""

    should_explain_scoring: bool = False
    should_export_explanation_csv: bool = False
    draw_score: DrawScoreConfig = field(default_factory=DrawScoreConfig)
    draw_answers_summary: DrawAnswersSummaryConfig = field(
        default_factory=DrawAnswersSummaryConfig
    )
    draw_question_verdicts: DrawQuestionVerdictsConfig = field(
        default_factory=DrawQuestionVerdictsConfig
    )
    draw_detected_bubble_texts: DrawDetectedBubbleTextsConfig = field(
        default_factory=DrawDetectedBubbleTextsConfig
    )


@dataclass
class EvaluationConfig:
    """Main evaluation configuration object.

    This represents the structure of evaluation.json files used for answer key
    matching and scoring configuration.
    """

    options: dict = field(default_factory=dict)
    marking_schemes: dict = field(default_factory=dict)
    conditional_sets: list = field(default_factory=list)
    outputs_configuration: OutputsConfiguration = field(
        default_factory=OutputsConfiguration
    )

    @classmethod
    def from_dict(cls, data: dict) -> "EvaluationConfig":
        """Create EvaluationConfig from dictionary (typically from JSON).

        Args:
            data: Dictionary containing evaluation configuration data

        Returns:
            EvaluationConfig instance with nested dataclasses
        """
        # Parse outputs_configuration if present
        outputs_config_data = data.get("outputs_configuration", {})
        outputs_config = OutputsConfiguration(
            should_explain_scoring=outputs_config_data.get(
                "should_explain_scoring", False
            ),
            should_export_explanation_csv=outputs_config_data.get(
                "should_export_explanation_csv", False
            ),
            draw_score=DrawScoreConfig(**outputs_config_data.get("draw_score", {})),
            draw_answers_summary=DrawAnswersSummaryConfig(
                **outputs_config_data.get("draw_answers_summary", {})
            ),
            draw_question_verdicts=DrawQuestionVerdictsConfig(
                enabled=outputs_config_data.get("draw_question_verdicts", {}).get(
                    "enabled", True
                ),
                verdict_colors=outputs_config_data.get(
                    "draw_question_verdicts", {}
                ).get(
                    "verdict_colors",
                    {
                        "correct": "#00FF00",
                        "neutral": None,
                        "incorrect": "#FF0000",
                        "bonus": "#00DDDD",
                    },
                ),
                verdict_symbol_colors=outputs_config_data.get(
                    "draw_question_verdicts", {}
                ).get(
                    "verdict_symbol_colors",
                    {
                        "positive": "#000000",
                        "neutral": "#000000",
                        "negative": "#000000",
                        "bonus": "#000000",
                    },
                ),
                draw_answer_groups=DrawAnswerGroupsConfig(
                    **outputs_config_data.get("draw_question_verdicts", {}).get(
                        "draw_answer_groups", {}
                    )
                ),
            ),
            draw_detected_bubble_texts=DrawDetectedBubbleTextsConfig(
                **outputs_config_data.get("draw_detected_bubble_texts", {})
            ),
        )

        return cls(
            options=data.get("options", {}),
            marking_schemes=data.get("marking_schemes", {}),
            conditional_sets=data.get("conditional_sets", []),
            outputs_configuration=outputs_config,
        )

    def to_dict(self) -> dict:
        """Convert EvaluationConfig to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the evaluation config
        """
        return dataclass_to_dict(self)
