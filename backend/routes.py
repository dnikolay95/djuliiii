from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, WebSocket, WebSocketDisconnect, status

from app.db import Database

from .auth import _encode_token, clear_session_cookie, require_auth, set_session_cookie
from app.config import load_settings
from .events import broker

router = APIRouter()


def get_db(request: Request) -> Database:
    db: Database | None = getattr(request.app.state, "db", None)
    if not db:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="db_not_ready")
    return db


@router.post("/api/auth/login")
async def login(payload: dict, response: Response, settings=Depends(load_settings)):
    login = (payload.get("login") or "").strip()
    password = (payload.get("password") or "").strip()
    if login != settings.admin_login or password != settings.admin_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")
    token = _encode_token(login, settings.auth_secret, datetime.now(tz=timezone.utc))
    set_session_cookie(response, token)
    return {"ok": True, "login": login}


@router.post("/api/auth/logout")
async def logout(response: Response):
    clear_session_cookie(response)
    return {"ok": True}


@router.get("/api/auth/me")
async def me(login: str = Depends(require_auth)):
    return {"login": login}


@router.get("/api/users")
async def list_users(
    db: Database = Depends(get_db),
    _: str = Depends(require_auth),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    users = await db.list_users(limit=limit, offset=offset)
    return {"items": users, "limit": limit, "offset": offset}


@router.get("/api/users/{tg_user_id}")
async def user_details(
    tg_user_id: int,
    db: Database = Depends(get_db),
    _: str = Depends(require_auth),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    user = await db.get_user(tg_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    greetings = await db.list_greetings(limit=limit, offset=offset, tg_user_id=tg_user_id)
    messages = await db.list_messages(limit=limit, offset=offset, tg_user_id=tg_user_id)
    return {"user": user, "greetings": greetings, "messages": messages}


@router.get("/api/greetings")
async def greetings(
    db: Database = Depends(get_db),
    _: str = Depends(require_auth),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    tg_user_id: Optional[int] = Query(None),
):
    items = await db.list_greetings(limit=limit, offset=offset, tg_user_id=tg_user_id)
    return {"items": items, "limit": limit, "offset": offset}


@router.get("/api/messages")
async def messages(
    db: Database = Depends(get_db),
    _: str = Depends(require_auth),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    tg_user_id: Optional[int] = Query(None),
    message_type: Optional[str] = Query(None),
):
    items = await db.list_messages(
        limit=limit, offset=offset, tg_user_id=tg_user_id, message_type=message_type
    )
    return {"items": items, "limit": limit, "offset": offset}


@router.get("/api/stats")
async def stats(db: Database = Depends(get_db), _: str = Depends(require_auth)):
    data = await db.get_stats()
    return data


@router.post("/api/internal/events")
async def publish_event(
    payload: dict, request: Request, settings=Depends(load_settings)
):  
    secret = request.headers.get("X-Auth-Secret", "")
    if secret != settings.auth_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized")
    await broker.publish(payload)
    return {"ok": True}


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.cookies.get("session_token")
    settings = load_settings()
    login = None
    if token:
        from .auth import _decode_token  # local import to avoid cycle

        login = _decode_token(token, settings.auth_secret)
    if login != settings.admin_login:
        await websocket.close(code=4401)
        return
    await websocket.accept()
    queue = broker.subscribe()
    try:
        while True:
            try:
                event = await queue.get()
                await websocket.send_json(event)
            except WebSocketDisconnect:
                break
    finally:
        broker.unsubscribe(queue)

