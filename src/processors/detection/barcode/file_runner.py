from src.processors.constants import FieldDetectionType
from src.processors.detection.barcode.detection_pass import (
    BarcodeDetectionPass,
)
from src.processors.detection.barcode.interpretation_pass import (
    BarcodeInterpretationPass,
)
from src.processors.detection.base.file_runner import FieldTypeFileLevelRunner


class BarcodeFileRunner(FieldTypeFileLevelRunner):
    def __init__(self, tuning_config) -> None:
        field_detection_type = FieldDetectionType.BARCODE_QR
        detection_pass = BarcodeDetectionPass(tuning_config, field_detection_type)
        interpretation_pass = BarcodeInterpretationPass(
            tuning_config, field_detection_type
        )
        super().__init__(
            tuning_config, field_detection_type, detection_pass, interpretation_pass
        )
