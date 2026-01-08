from __future__ import annotations

import os
from typing import Optional

from itsdangerous import BadSignature, URLSafeSerializer

from web.session_store import SESSION_STORE, SessionData

SESSION_COOKIE = "aset_session"


class AuthError(Exception):
    pass


def _serializer() -> URLSafeSerializer:
    secret_key = os.getenv("SECRET_KEY", "change-me")
    return URLSafeSerializer(secret_key, salt="aset-session")


def sign_session_id(session_id: str) -> str:
    return _serializer().dumps(session_id)


def unsign_session_id(cookie_value: str) -> Optional[str]:
    try:
        return _serializer().loads(cookie_value)
    except BadSignature:
        return None


def login(password: str) -> SessionData:
    staff_password = os.getenv("STAFF_PASSWORD", "password")
    if password != staff_password:
        raise AuthError("Invalid password")
    session = SESSION_STORE.create_session()
    session.is_authenticated = True
    return session


def authenticate_session(session_id: Optional[str]) -> SessionData:
    if not session_id:
        raise AuthError("Missing session")
    session = SESSION_STORE.require_session(session_id)
    if not session.is_authenticated:
        raise AuthError("Not authenticated")
    return session
