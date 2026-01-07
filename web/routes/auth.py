from __future__ import annotations

from fastapi import APIRouter, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from web.auth import AuthError, login, sign_session_id, SESSION_COOKIE

router = APIRouter()

templates = Jinja2Templates(directory="web/templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login_action(request: Request, password: str = Form(...)) -> Response:
    try:
        session = login(password)
    except AuthError as exc:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": str(exc)},
            status_code=401,
        )
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        SESSION_COOKIE,
        sign_session_id(session.session_id),
        httponly=True,
        samesite="lax",
    )
    return response


@router.post("/logout")
async def logout_action() -> Response:
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE)
    return response
