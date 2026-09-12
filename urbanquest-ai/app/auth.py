from __future__ import annotations

import hashlib
import asyncio
import json
import secrets
from urllib.parse import urlencode
from urllib.request import Request as UrlRequest, urlopen
from datetime import datetime, timedelta, timezone
from typing import Literal
from urllib.error import HTTPError, URLError

from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr, Field, TypeAdapter, ValidationError, model_validator

from app.config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()
_pending_otps: dict[str, tuple[str, datetime]] = {}
_oauth_states: set[str] = set()


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
    if payload.method == "email" and settings.environment == "production":
        if not settings.resend_api_key:
            raise HTTPException(status_code=503, detail="Email delivery is not configured.")
        await _send_email_otp(payload.destination, code)
    _pending_otps[payload.destination] = (_hash(code), datetime.now(timezone.utc) + timedelta(minutes=10))
    return {
        "status": "sent",
        "destination": payload.destination,
        "expires_in": "600",
    }


async def _send_email_otp(destination: str, code: str) -> None:
    body = json.dumps({
        "from": settings.auth_from_email,
        "to": [destination],
        "subject": "Your UrbanQuest verification code",
        "html": f"<p>Your UrbanQuest verification code is <strong>{code}</strong>.</p><p>It expires in 10 minutes.</p>",
    }).encode("utf-8")

    def send() -> None:
        request = UrlRequest(
            "https://api.resend.com/emails",
            data=body,
            headers={
                "Authorization": f"Bearer {settings.resend_api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urlopen(request, timeout=10) as response:
            if response.status >= 300:
                raise RuntimeError(f"Resend returned HTTP {response.status}.")

    try:
        await asyncio.to_thread(send)
    except (HTTPError, URLError, TimeoutError, OSError) as error:
        raise HTTPException(status_code=502, detail="Email delivery failed. Please try again.") from error


@router.get("/google")
async def google_login() -> RedirectResponse:
    if not settings.google_client_id or not settings.google_client_secret or not settings.google_redirect_uri:
        raise HTTPException(status_code=503, detail="Google sign-in is not configured.")
    state = secrets.token_urlsafe(32)
    _oauth_states.add(state)
    query = urlencode({
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    })
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{query}")


@router.get("/google/callback")
async def google_callback(code: str, state: str, response: Response) -> RedirectResponse:
    if state not in _oauth_states:
        raise HTTPException(status_code=400, detail="Invalid Google sign-in state.")
    _oauth_states.remove(state)
    profile = await _exchange_google_code(code)
    session_token = secrets.token_urlsafe(32)
    session = AuthSession(
        user_id=_hash(profile["sub"])[:24],
        name=profile.get("name") or profile.get("email", "").split("@")[0],
        email=profile.get("email"),
        phone=None,
    )
    _sessions[_hash(session_token)] = session
    response = RedirectResponse(f"{settings.frontend_url.rstrip('/')}/")
    response.set_cookie("urbanquest_session", session_token, **_cookie_options())
    return response


async def _exchange_google_code(code: str) -> dict[str, str]:
    body = urlencode({
        "code": code,
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "redirect_uri": settings.google_redirect_uri,
        "grant_type": "authorization_code",
    }).encode("utf-8")

    def request_json(url: str, data: bytes | None = None, headers: dict[str, str] | None = None) -> dict[str, str]:
        request = UrlRequest(url, data=data, headers=headers or {}, method="POST" if data else "GET")
        with urlopen(request, timeout=10) as result:
            return json.loads(result.read().decode("utf-8"))

    try:
        token = await asyncio.to_thread(request_json, "https://oauth2.googleapis.com/token", body, {"Content-Type": "application/x-www-form-urlencoded"})
        return await asyncio.to_thread(
            request_json,
            "https://openidconnect.googleapis.com/v1/userinfo",
            None,
            {"Authorization": f"Bearer {token['access_token']}"},
        )
    except (HTTPError, URLError, TimeoutError, OSError, KeyError, json.JSONDecodeError) as error:
        raise HTTPException(status_code=502, detail="Google sign-in could not be completed.") from error


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
