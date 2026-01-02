from src.processors.constants import FieldDetectionType
from src.processors.detection.base.file_runner import FieldTypeFileLevelRunner
from src.processors.detection.bubbles_threshold.detection_pass import (
    BubblesThresholdDetectionPass,
)
from src.processors.detection.bubbles_threshold.interpretation_pass import (
    BubblesThresholdInterpretationPass,
)


class BubblesThresholdFileRunner(FieldTypeFileLevelRunner):
    def __init__(self, tuning_config) -> None:
        field_detection_type = FieldDetectionType.BUBBLES_THRESHOLD
        detection_pass = BubblesThresholdDetectionPass(
            tuning_config, field_detection_type
        )
        interpretation_pass = BubblesThresholdInterpretationPass(
            tuning_config, field_detection_type
        )
        super().__init__(
            tuning_config, field_detection_type, detection_pass, interpretation_pass
        )
