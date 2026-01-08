from __future__ import annotations

from typing import Dict

from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from web.dependencies import require_login_page
from web.services import parse_answer_key
from web.session_store import SessionData

router = APIRouter()

templates = Jinja2Templates(directory="web/templates")


@router.get("/", response_class=HTMLResponse)
async def dashboard_page(
    request: Request, session: SessionData = Depends(require_login_page)
) -> HTMLResponse:
    config = session.config or {}
    status = {
        "reading_key": "reading_key" in config,
        "qrar_key": "qrar_key" in config,
        "concept_mapping": "concept_mapping" in config,
    }
    counts = {
        "reading_questions": len(config.get("reading_key", {})),
        "qrar_questions": len(config.get("qrar_key", {})),
        "mapping_subjects": len(config.get("concept_mapping", {})),
    }
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "status": status,
            "counts": counts,
        },
    )


@router.post("/config")
async def upload_config(
    request: Request,
    reading_key: UploadFile = File(...),
    qrar_key: UploadFile = File(...),
    concept_mapping: UploadFile = File(...),
    session: SessionData = Depends(require_login_page),
) -> HTMLResponse:
    reading_data = await reading_key.read()
    qrar_data = await qrar_key.read()
    concept_data = await concept_mapping.read()

    try:
        reading_parsed = parse_answer_key(reading_key.filename or "reading.csv", reading_data)
        qrar_parsed = parse_answer_key(qrar_key.filename or "qrar.csv", qrar_data)
    except Exception as exc:
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "status": {},
                "counts": {},
                "error": str(exc),
            },
            status_code=400,
        )

    try:
        concept_mapping_json = _parse_json(concept_data)
    except Exception as exc:
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "status": {},
                "counts": {},
                "error": str(exc),
            },
            status_code=400,
        )

    session.config = {
        "reading_key": reading_parsed,
        "qrar_key": qrar_parsed,
        "concept_mapping": concept_mapping_json,
    }

    return RedirectResponse(url="/", status_code=303)


def _parse_json(data: bytes) -> Dict:
    import json

    try:
        return json.loads(data.decode("utf-8"))
    except Exception as exc:
        raise ValueError("Concept mapping must be valid JSON.") from exc
