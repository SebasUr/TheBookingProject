import os
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Header
from models import UserRegister, UserLogin

router = APIRouter()
repo = None

SECRET_KEY = os.getenv("JWT_SECRET", "change-this-in-production")
ALGORITHM = "HS256"
EXPIRE_HOURS = 24 * 7  # 7 days


def _create_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=EXPIRE_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _decode_token(authorization: str | None) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "missing or invalid authorization header")
    token = authorization[7:]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "invalid token")


@router.post("/register", status_code=201)
async def register(data: UserRegister):
    existing = await repo.find_by_email(data.email)
    if existing:
        raise HTTPException(400, "email already registered")
    user = await repo.create(data.model_dump())
    token = _create_token(user["id"], user["email"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user["id"],
        "email": user["email"],
    }


@router.post("/login")
async def login(data: UserLogin):
    user = await repo.find_by_email(data.email)
    if not user or not repo.verify_password(data.password, user["password_hash"]):
        raise HTTPException(401, "invalid credentials")
    token = _create_token(user["id"], user["email"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user["id"],
        "email": user["email"],
    }


@router.post("/validate")
async def validate_token(authorization: str = Header(None)):
    """Internal endpoint used by the gateway to validate a token."""
    payload = _decode_token(authorization)
    return {"user_id": payload["sub"], "email": payload["email"]}


@router.get("/me")
async def me(authorization: str = Header(None)):
    payload = _decode_token(authorization)
    return {"user_id": payload["sub"], "email": payload["email"]}
