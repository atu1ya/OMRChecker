from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from web.routes import auth, batch, dashboard, marking

ROOT_DIR = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = ROOT_DIR / "web" / "templates"
STATIC_DIR = ROOT_DIR / "web" / "static"

app = FastAPI(title="Everest Tutoring ASET Marking")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.get("/health", response_class=JSONResponse)
async def health() -> dict:
    return {"status": "healthy"}


@app.exception_handler(404)
async def not_found(request: Request, exc: Exception) -> HTMLResponse:
    return templates.TemplateResponse(
        "not_found.html", {"request": request}, status_code=404
    )


app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(marking.router)
app.include_router(batch.router)
