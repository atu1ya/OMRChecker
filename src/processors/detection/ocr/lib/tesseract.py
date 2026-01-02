# TODO: support pytesseract methods as well.
from typing import Never

from src.processors.detection.ocr.lib.text_ocr import TextOCR


class TesseractOCR(TextOCR):
    @staticmethod
    def get_all_text_detections(_image, _confidence_threshold=0.8) -> Never:
        # TODO: pytesseract.image_to_string
        # To be implemented
        raise NotImplementedError

    @staticmethod
    def get_single_text_detection(
        _image, _confidence_threshold=0.8, _clear_whitespace=True
    ) -> Never:
        # To be implemented
        raise NotImplementedError

    @staticmethod
    def read_texts_with_boxes(
        _image, _confidence_threshold=0.8, _sort_by_score=True
    ) -> Never:
        # To be implemented
        raise NotImplementedError
