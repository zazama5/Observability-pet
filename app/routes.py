from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from db import SessionLocal
from models import User
from security import hash_password, verify_password, make_access_token, make_refresh_token, decode_token
from logging_setup import app_logger, log_audit
from config import settings

router = APIRouter()


# ─── Dependency ───
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── Models ───
class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


# ─── Helper для получения текущего пользователя ───
def get_current_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header.split(" ")[1]
    try:
        payload = decode_token(token)
        return payload.get("sub")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


# ─── Endpoints ───
@router.post("/register")
def register(creds: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == creds.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    user = User(username=creds.username, password_hash=hash_password(creds.password))
    db.add(user)
    db.commit()

    app_logger.info(
        "user_registered",
        extra={"username": creds.username, "instance": settings.instance_id}
    )

    return {"message": "User registered successfully"}


@router.post("/login")
def login(creds: LoginRequest, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host
    ua = request.headers.get("user-agent", "unknown")

    user = db.query(User).filter(User.username == creds.username).first()

    if not user or not verify_password(creds.password, user.password_hash):
        log_audit("login_failed", creds.username, ip, ua, success=False)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = make_access_token(user.username)
    refresh_token = make_refresh_token(user.username)
    
    log_audit("login_success", user.username, ip, ua, success=True)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.get("/me")
def me(current_user: str = Depends(get_current_user)):
    app_logger.info(
        "token_validated",
        extra={"username": current_user, "instance": settings.instance_id}
    )
    return {"username": current_user}


@router.post("/refresh")
def refresh_token(current_user: str = Depends(get_current_user), request: Request = None):
    new_access_token = make_access_token(current_user)
    new_refresh_token = make_refresh_token(current_user)
    
    ip = request.client.host if request else "unknown"

    app_logger.info(
        "token_refreshed",
        extra={"username": current_user, "ip": ip, "instance": settings.instance_id}
    )

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.get("/healthz")
def healthz():
    app_logger.info(
        "health_check",
        extra={"status": "healthy", "instance": settings.instance_id}
    )
    return {"status": "healthy"}


@router.get("/metrics")
def metrics():
    app_logger.info(
        "metrics_request",
        extra={"instance": settings.instance_id}
    )
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)