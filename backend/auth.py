import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request, Response, status

from app.config import load_settings

SESSION_COOKIE = "session_token"
SESSION_TTL_HOURS = 24


def _sign(payload: str, secret: str) -> str:
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


def _encode_token(login: str, secret: str, now: datetime) -> str:
    exp = int((now + timedelta(hours=SESSION_TTL_HOURS)).timestamp())
    nonce = secrets.token_hex(8)
    payload = f"{login}:{exp}:{nonce}"
    signature = _sign(payload, secret)
    return f"{payload}:{signature}"


def _decode_token(token: str, secret: str) -> Optional[str]:
    try:
        login, exp_str, nonce, signature = token.split(":")
        payload = f"{login}:{exp_str}:{nonce}"
        if not hmac.compare_digest(signature, _sign(payload, secret)):
            return None
        if int(exp_str) < int(datetime.now(tz=timezone.utc).timestamp()):
            return None
        return login
    except Exception:
        return None


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=SESSION_TTL_HOURS * 3600,
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE)


def get_settings():
    return load_settings()


def require_auth(request: Request, settings=Depends(get_settings)) -> str:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized")
    login = _decode_token(token, settings.auth_secret)
    if login != settings.admin_login:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized")
    return login

