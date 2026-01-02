from src.processors.constants import FieldDetectionType
from src.processors.template.detection.base.file_runner import FieldTypeFileLevelRunner
from src.processors.template.detection.ocr.detection_pass import OCRDetectionPass
from src.processors.template.detection.ocr.interpretation_pass import (
    OCRInterpretationPass,
)


class OCRFileRunner(FieldTypeFileLevelRunner):
    def __init__(self, tuning_config) -> None:
        field_detection_type = FieldDetectionType.OCR
        detection_pass = OCRDetectionPass(tuning_config, field_detection_type)
        interpretation_pass = OCRInterpretationPass(tuning_config, field_detection_type)
        super().__init__(
            tuning_config, field_detection_type, detection_pass, interpretation_pass
        )
