from fastapi import APIRouter, Depends, HTTPException, Request
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from sqlalchemy.orm import Session
from pydantic import BaseModel
from starlette.responses import Response

from db import get_db
from models import User
from security import (
    hash_password, verify_password,
    make_access_token, make_refresh_token, decode_token,
)
from logging_setup import app_logger, log_audit
from metrics import login_attempts_total
from config import settings

router = APIRouter()

class Credentials(BaseModel):
    username: str
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str

def _client_ctx(request: Request):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    return ip, ua

def _record_audit(event_type: str, username, ip, ua, success: bool):
    # Пишем только в файл/stdout, чтобы Vector забрал. В БД не пишем.
    log_audit(event_type, username, ip, ua, success)

@router.get("/healthz")
def healthz():
    return {"status": "ok", "instance": settings.instance_id}

@router.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@router.post("/register")
def register(creds: Credentials, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == creds.username).first():
        raise HTTPException(status_code=409, detail="user exists")
    
    user = User(username=creds.username, password_hash=hash_password(creds.password))
    db.add(user)
    db.commit()
    
    app_logger.info("user_registered", extra={"username": creds.username, "instance": settings.instance_id})
    return {"status": "created", "username": creds.username}

@router.post("/login")
def login(creds: Credentials, request: Request, db: Session = Depends(get_db)):
    ip, ua = _client_ctx(request)
    user = db.query(User).filter(User.username == creds.username).first()
    
    if not user or not verify_password(creds.password, user.password_hash):
        login_attempts_total.labels(result="failed").inc()
        _record_audit("login_failed", creds.username, ip, ua, success=False)
        app_logger.warning("login_failed", extra={"username": creds.username, "ip": ip, "instance": settings.instance_id})
        raise HTTPException(status_code=401, detail="invalid credentials")

    login_attempts_total.labels(result="success").inc()
    _record_audit("login_success", creds.username, ip, ua, success=True)
    app_logger.info("login_success", extra={"username": creds.username, "ip": ip, "instance": settings.instance_id})
    
    return {
        "access_token": make_access_token(user.username),
        "refresh_token": make_refresh_token(user.username),
        "token_type": "bearer",
    }

@router.post("/refresh")
def refresh(req: RefreshRequest):
    try:
        payload = decode_token(req.refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("wrong token type")
    except Exception:
        raise HTTPException(status_code=401, detail="invalid refresh token")
    
    return {
        "access_token": make_access_token(payload["sub"]),
        "token_type": "bearer",
    }

@router.get("/me")
def me(request: Request):
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing token")
    try:
        payload = decode_token(auth.split(" ", 1)[1])
        if payload.get("type") != "access":
            raise ValueError("wrong token type")
    except Exception:
        raise HTTPException(status_code=401, detail="invalid token")
    
    return {"username": payload["sub"]}
