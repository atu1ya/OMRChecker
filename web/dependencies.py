from __future__ import annotations

from typing import Optional

from fastapi import Cookie, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

from web.auth import AuthError, authenticate_session, unsign_session_id
from web.session_store import SessionData


def get_session_id(aset_session: Optional[str] = Cookie(default=None)) -> Optional[str]:
    if not aset_session:
        return None
    return unsign_session_id(aset_session)


def require_login(session_id: Optional[str] = Depends(get_session_id)) -> SessionData:
    try:
        return authenticate_session(session_id)
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def require_login_page(session_id: Optional[str] = Depends(get_session_id)) -> SessionData:
    try:
        return authenticate_session(session_id)
    except AuthError:
        raise HTTPException(status_code=307, headers={"Location": "/login"})


def redirect_to_login(request: Request) -> RedirectResponse:
    return RedirectResponse(url="/login", status_code=303)
