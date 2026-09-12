from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr, Field, TypeAdapter, ValidationError, model_validator

from app.config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()
_pending_otps: dict[str, tuple[str, datetime]] = {}


class AuthRequest(BaseModel):
    method: Literal["email", "mobile"]
    destination: str = Field(min_length=5, max_length=320)
    name: str | None = Field(default=None, max_length=120)
    consent: bool = False

    @model_validator(mode="after")
    def validate_destination(self) -> "AuthRequest":
        if self.method == "email":
            try:
                TypeAdapter(EmailStr).validate_python(self.destination)
            except ValidationError as error:
                raise ValueError("Enter a valid email address.") from error
        elif not self.destination.startswith("+"):
            raise ValueError("Mobile numbers must use international format.")
        return self


class VerifyRequest(BaseModel):
    destination: str = Field(min_length=5, max_length=320)
    code: str = Field(pattern=r"^\d{6}$")
    method: Literal["email", "mobile"]
    name: str | None = Field(default=None, max_length=120)


class AuthSession(BaseModel):
    user_id: str
    name: str | None
    email: str | None
    phone: str | None


_sessions: dict[str, AuthSession] = {}


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _cookie_options() -> dict[str, object]:
    return {
        "httponly": True,
        "secure": settings.environment == "production",
        "samesite": "lax",
        "max_age": settings.session_days * 86400,
        "path": "/",
    }


@router.post("/request-code")
async def request_code(payload: AuthRequest) -> dict[str, str]:
    if not payload.consent:
        raise HTTPException(status_code=422, detail="Consent is required to create an account.")
    code = settings.development_otp if settings.environment != "production" else f"{secrets.randbelow(1_000_000):06d}"
    _pending_otps[payload.destination] = (_hash(code), datetime.now(timezone.utc) + timedelta(minutes=10))
    # Delivery adapters can be attached here without exposing OTPs to clients.
    return {
        "status": "sent",
        "destination": payload.destination,
        "expires_in": "600",
    }


@router.get("/google")
async def google_login() -> RedirectResponse:
    if not settings.google_oauth_url:
        raise HTTPException(status_code=503, detail="Google sign-in is not configured.")
    return RedirectResponse(settings.google_oauth_url)


@router.post("/verify", response_model=AuthSession)
async def verify(payload: VerifyRequest, response: Response) -> AuthSession:
    pending = _pending_otps.get(payload.destination)
    if not pending or pending[1] < datetime.now(timezone.utc) or not secrets.compare_digest(pending[0], _hash(payload.code)):
        raise HTTPException(status_code=400, detail="That code is not valid.")
    session_token = secrets.token_urlsafe(32)
    session = AuthSession(
        user_id=_hash(payload.destination)[:24],
        name=payload.name or payload.destination.split("@")[0],
        email=payload.destination if payload.method == "email" else None,
        phone=payload.destination if payload.method == "mobile" else None,
    )
    _sessions[_hash(session_token)] = session
    _pending_otps.pop(payload.destination, None)
    response.set_cookie("urbanquest_session", session_token, **_cookie_options())
    return session


@router.get("/me", response_model=AuthSession)
async def me(request: Request) -> AuthSession:
    token = request.cookies.get("urbanquest_session")
    session = _sessions.get(_hash(token)) if token else None
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not signed in.")
    return session


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response) -> None:
    token = request.cookies.get("urbanquest_session")
    if token:
        _sessions.pop(_hash(token), None)
    response.delete_cookie("urbanquest_session", path="/")
