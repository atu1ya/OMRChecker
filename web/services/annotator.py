from __future__ import annotations

from io import BytesIO
from typing import Optional

import cv2
import numpy as np
from PIL import Image

from web.services.marker import SubjectResult


class AnnotationError(Exception):
    pass


def annotate_sheet(image: np.ndarray, result: SubjectResult, title: Optional[str] = None) -> np.ndarray:
    if image is None:
        raise AnnotationError("Missing image for annotation.")
    if len(image.shape) == 2:
        annotated = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    else:
        annotated = image.copy()

    header = title or result.subject
    summary = f"{header} Score: {result.correct}/{result.total}"
    cv2.rectangle(annotated, (20, 20), (620, 80), (255, 255, 255), thickness=-1)
    cv2.putText(
        annotated,
        summary,
        (30, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (52, 152, 219),
        2,
        cv2.LINE_AA,
    )
    return annotated


def image_to_pdf_bytes(image: np.ndarray) -> bytes:
    if image is None:
        raise AnnotationError("Cannot convert empty image to PDF.")
    if len(image.shape) == 2:
        rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    else:
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(rgb)
    buffer = BytesIO()
    pil_image.save(buffer, format="PDF")
    buffer.seek(0)
    return buffer.getvalue()
