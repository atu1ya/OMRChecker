from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple, TYPE_CHECKING
import csv
import json
import tempfile

import cv2
import numpy as np

from src.utils.parsing import get_concatenated_response

if TYPE_CHECKING:
    from src.template import Template


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


@dataclass
class QuestionResult:
    question_id: str
    selected: str
    correct: str
    is_correct: bool


@dataclass
class SubjectResult:
    subject: str
    total: int
    correct: int
    questions: List[QuestionResult]


@dataclass
class MarkedSheet:
    subject: str
    responses: Dict[str, str]
    result: SubjectResult
    marked_image: np.ndarray


class MarkingError(Exception):
    pass


def _validate_png(image_bytes: bytes) -> None:
    if not image_bytes.startswith(PNG_SIGNATURE):
        raise MarkingError("Only PNG files are supported.")


def _decode_image(image_bytes: bytes) -> np.ndarray:
    data = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise MarkingError("Unable to decode PNG image.")
    return image


def parse_answer_key(file_name: str, data: bytes) -> Dict[str, str]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise MarkingError("Answer key must be valid UTF-8 text.") from exc

    if file_name.lower().endswith(".json"):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise MarkingError("Answer key JSON is invalid.") from exc
        if isinstance(parsed, dict):
            return {str(k).strip(): str(v).strip().upper() for k, v in parsed.items()}
        raise MarkingError("Answer key JSON must be an object mapping question IDs to answers.")

    reader = csv.reader(text.splitlines())
    answer_key: Dict[str, str] = {}
    for row in reader:
        if not row or all(not cell.strip() for cell in row):
            continue
        if len(row) < 2:
            raise MarkingError("Answer key rows must include question ID and answer.")
        question_id = row[0].strip()
        answer = row[1].strip().upper()
        if not question_id:
            continue
        answer_key[question_id] = answer
    if not answer_key:
        raise MarkingError("Answer key is empty.")
    return answer_key


def _score_response(
    subject: str,
    response: Dict[str, str],
    answer_key: Dict[str, str],
    question_order: Iterable[str],
) -> SubjectResult:
    questions: List[QuestionResult] = []
    correct_count = 0
    for question_id in question_order:
        if question_id not in answer_key:
            continue
        selected = response.get(question_id, "")
        correct = answer_key.get(question_id, "")
        is_correct = selected == correct and selected != ""
        if is_correct:
            correct_count += 1
        questions.append(
            QuestionResult(
                question_id=question_id,
                selected=selected,
                correct=correct,
                is_correct=is_correct,
            )
        )
    return SubjectResult(
        subject=subject,
        total=len(questions),
        correct=correct_count,
        questions=questions,
    )


def _filter_questions(keys: Iterable[str], prefix: str) -> List[str]:
    return [key for key in keys if key.startswith(prefix)]


class MarkingService:
    def __init__(
        self,
        reading_template_path: Path,
        qrar_template_path: Path,
    ) -> None:
        from src.defaults import CONFIG_DEFAULTS
        from src.template import Template

        self.reading_template = Template(reading_template_path, CONFIG_DEFAULTS)
        self.qrar_template = Template(qrar_template_path, CONFIG_DEFAULTS)

    def _read_response(self, template: "Template", image_bytes: bytes) -> Tuple[Dict[str, str], np.ndarray]:
        _validate_png(image_bytes)
        image = _decode_image(image_bytes)
        template.image_instance_ops.reset_all_save_img()
        template.image_instance_ops.append_save_img(1, image)
        image = template.image_instance_ops.apply_preprocessors(
            Path("uploaded.png"), image, template
        )
        if image is None:
            raise MarkingError("Image alignment failed. Check scan quality and template.")

        with tempfile.TemporaryDirectory() as temp_dir:
            response_dict, marked_image, _, _ = template.image_instance_ops.read_omr_response(
                template=template,
                image=image,
                name="uploaded",
                save_dir=Path(temp_dir),
            )
        response = get_concatenated_response(response_dict, template)
        return response, marked_image

    def mark_reading(self, image_bytes: bytes, answer_key: Dict[str, str]) -> MarkedSheet:
        response, marked_image = self._read_response(self.reading_template, image_bytes)
        question_order = self.reading_template.output_columns
        result = _score_response("Reading", response, answer_key, question_order)
        return MarkedSheet(
            subject="Reading",
            responses=response,
            result=result,
            marked_image=marked_image,
        )

    def mark_qrar(self, image_bytes: bytes, answer_key: Dict[str, str]) -> List[MarkedSheet]:
        response, marked_image = self._read_response(self.qrar_template, image_bytes)
        question_order = self.qrar_template.output_columns
        qr_questions = _filter_questions(question_order, "QR")
        ar_questions = _filter_questions(question_order, "AR")
        qr_result = _score_response("QR", response, answer_key, qr_questions)
        ar_result = _score_response("AR", response, answer_key, ar_questions)
        return [
            MarkedSheet(
                subject="QR",
                responses=response,
                result=qr_result,
                marked_image=marked_image,
            ),
            MarkedSheet(
                subject="AR",
                responses=response,
                result=ar_result,
                marked_image=marked_image,
            ),
        ]
