from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Dict, List
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

router = APIRouter(prefix="/batch")

templates = Jinja2Templates(directory="web/templates")

ROOT_DIR = Path(__file__).resolve().parents[2]
READING_TEMPLATE = ROOT_DIR / "config" / "aset_reading_template.json"
QRAR_TEMPLATE = ROOT_DIR / "config" / "aset_qrar_template.json"


@router.get("/", response_class=HTMLResponse)
async def batch_page(
    request: Request, session: SessionData = Depends(require_login_page)
) -> HTMLResponse:
    return templates.TemplateResponse(
        "batch.html",
        {"request": request, "has_config": bool(session.config)},
    )


@router.post("/process")
async def process_batch(
    request: Request,
    manifest: UploadFile = File(...),
    archive: UploadFile = File(...),
    session: SessionData = Depends(require_login_page),
) -> StreamingResponse:
    if not session.config:
        raise HTTPException(status_code=400, detail="Session configuration not found.")

    reading_key = session.config.get("reading_key")
    qrar_key = session.config.get("qrar_key")
    concept_mapping = session.config.get("concept_mapping")

    manifest_data = await manifest.read()
    zip_data = await archive.read()

    manifest_json = _parse_manifest(manifest_data)
    zip_file = zipfile.ZipFile(BytesIO(zip_data))

    service = MarkingService(READING_TEMPLATE, QRAR_TEMPLATE)
    summary: List[Dict] = []

    output_buffer = BytesIO()
    with zipfile.ZipFile(output_buffer, "w", zipfile.ZIP_DEFLATED) as output_zip:
        for student in manifest_json["students"]:
            name = student.get("name")
            reading_name = student.get("reading_sheet")
            qrar_name = student.get("qrar_sheet")
            writing_score = int(student.get("writing_score", 0))
            if not name or not reading_name or not qrar_name:
                summary.append({"name": name, "status": "missing_manifest_fields"})
                continue

            try:
                reading_bytes = zip_file.read(reading_name)
                qrar_bytes = zip_file.read(qrar_name)
            except KeyError:
                summary.append({"name": name, "status": "missing_files"})
                continue

            try:
                reading_marked = service.mark_reading(reading_bytes, reading_key)
                qrar_marked_list = service.mark_qrar(qrar_bytes, qrar_key)
            except MarkingError:
                summary.append({"name": name, "status": "marking_error"})
                continue

            subject_results = [reading_marked.result] + [m.result for m in qrar_marked_list]
            analysis = analyze_results(subject_results, concept_mapping)

            report_pdf = generate_student_report(
                student_name=name,
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
                name,
                writing_score,
                reading_marked.result,
                qrar_marked_list,
                analysis,
            )

            folder = _slugify(name)
            output_zip.writestr(f"{folder}/{folder}_reading_marked.pdf", reading_pdf)
            output_zip.writestr(f"{folder}/{folder}_qrar_marked.pdf", qrar_pdf)
            output_zip.writestr(f"{folder}/{folder}_report.pdf", report_pdf)
            output_zip.writestr(
                f"{folder}/{folder}_results.json", json.dumps(results_payload, indent=2)
            )

            summary.append({"name": name, "status": "ok"})

        output_zip.writestr("summary.json", json.dumps(summary, indent=2))

    output_buffer.seek(0)
    headers = {"Content-Disposition": "attachment; filename=batch_results.zip"}
    return StreamingResponse(
        output_buffer, media_type="application/zip", headers=headers
    )


def _parse_manifest(data: bytes) -> Dict:
    try:
        payload = json.loads(data.decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Manifest must be valid JSON.") from exc
    if "students" not in payload or not isinstance(payload["students"], list):
        raise HTTPException(status_code=400, detail="Manifest must include students list.")
    return payload


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
