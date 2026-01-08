from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Dict
import json
import zipfile

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from web.dependencies import require_login_page
from web.services import (
    MarkingError,
    MarkingService,
    SubjectResult,
    annotate_sheet,
    analyze_results,
    generate_student_report,
    image_to_pdf_bytes,
)
from web.session_store import SessionData

router = APIRouter(prefix="/mark")

templates = Jinja2Templates(directory="web/templates")

ROOT_DIR = Path(__file__).resolve().parents[2]
READING_TEMPLATE = ROOT_DIR / "config" / "aset_reading_template.json"
QRAR_TEMPLATE = ROOT_DIR / "config" / "aset_qrar_template.json"


@router.get("/single", response_class=HTMLResponse)
async def single_page(
    request: Request, session: SessionData = Depends(require_login_page)
) -> HTMLResponse:
    return templates.TemplateResponse(
        "single.html",
        {
            "request": request,
            "has_config": bool(session.config),
        },
    )


@router.post("/single/process")
async def process_single(
    request: Request,
    student_name: str = Form(...),
    writing_score: int = Form(...),
    reading_sheet: UploadFile = File(...),
    qrar_sheet: UploadFile = File(...),
    session: SessionData = Depends(require_login_page),
) -> StreamingResponse:
    if not session.config:
        raise HTTPException(status_code=400, detail="Session configuration not found.")

    reading_key = session.config.get("reading_key")
    qrar_key = session.config.get("qrar_key")
    concept_mapping = session.config.get("concept_mapping")

    service = MarkingService(READING_TEMPLATE, QRAR_TEMPLATE)

    try:
        reading_bytes = await reading_sheet.read()
        qrar_bytes = await qrar_sheet.read()
        reading_marked = service.mark_reading(reading_bytes, reading_key)
        qrar_marked_list = service.mark_qrar(qrar_bytes, qrar_key)
    except MarkingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    subject_results = [reading_marked.result] + [m.result for m in qrar_marked_list]
    analysis = analyze_results(subject_results, concept_mapping)

    report_pdf = generate_student_report(
        student_name=student_name,
        writing_score=writing_score,
        reading_result=reading_marked.result,
        qrar_results=[m.result for m in qrar_marked_list],
        analysis=analysis,
    )

    reading_pdf = image_to_pdf_bytes(
        annotate_sheet(reading_marked.marked_image, reading_marked.result, "Reading")
    )

    combined_qrar_result = _combine_results(qrar_marked_list)
    qrar_pdf = image_to_pdf_bytes(
        annotate_sheet(qrar_marked_list[0].marked_image, combined_qrar_result, "QR/AR")
    )

    results_payload = _build_results_json(
        student_name,
        writing_score,
        reading_marked.result,
        qrar_marked_list,
        analysis,
    )

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        prefix = _slugify(student_name)
        zip_file.writestr(f"{prefix}_reading_marked.pdf", reading_pdf)
        zip_file.writestr(f"{prefix}_qrar_marked.pdf", qrar_pdf)
        zip_file.writestr(f"{prefix}_report.pdf", report_pdf)
        zip_file.writestr(
            f"{prefix}_results.json", json.dumps(results_payload, indent=2)
        )

    zip_buffer.seek(0)
    headers = {
        "Content-Disposition": f"attachment; filename={_slugify(student_name)}_results.zip"
    }
    return StreamingResponse(zip_buffer, media_type="application/zip", headers=headers)


def _slugify(name: str) -> str:
    return "_".join(part for part in name.strip().split() if part)


def _combine_results(marked_list) -> object:
    total = sum(marked.result.total for marked in marked_list)
    correct = sum(marked.result.correct for marked in marked_list)
    return SubjectResult(
        subject="QR/AR",
        total=total,
        correct=correct,
        questions=[q for marked in marked_list for q in marked.result.questions],
    )


def _build_results_json(
    student_name: str,
    writing_score: int,
    reading_result,
    qrar_results,
    analysis,
) -> Dict:
    return {
        "student": student_name,
        "writing_score": writing_score,
        "reading": _subject_to_dict(reading_result),
        "qrar": {result.subject: _subject_to_dict(result) for result in qrar_results},
        "analysis": {
            subject.subject: [
                {
                    "area": area.name,
                    "correct": area.correct,
                    "total": area.total,
                    "percentage": round(area.percentage * 100, 2),
                    "status": area.status,
                }
                for area in subject.areas
            ]
            for subject in analysis.subjects
        },
    }


def _subject_to_dict(subject) -> Dict:
    return {
        "correct": subject.correct,
        "total": subject.total,
        "questions": [
            {
                "id": q.question_id,
                "selected": q.selected,
                "correct": q.correct,
                "is_correct": q.is_correct,
            }
            for q in subject.questions
        ],
    }
