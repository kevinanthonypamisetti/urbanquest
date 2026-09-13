from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.chat.models import ChatRequest, ChatResponse
from app.chat.service import ChatService
from app.config import get_settings
from app.maps.demo import DemoMapsProvider
from app.maps.google import GoogleMapsProvider
from app.planner.service import AdventurePlanner
from app.auth import router as auth_router
from app.ai_gateway import configure as configure_ai, router as ai_router

settings = get_settings()
app = FastAPI(title=settings.app_name)


@app.exception_handler(Exception)
async def unhandled_error(request: Request, error: Exception) -> JSONResponse:
    print(f"Unhandled request error on {request.url.path}: {error}")
    return JSONResponse(
        status_code=503,
        content={
            "success": False,
            "error": {
                "code": "AI_SERVICE_UNAVAILABLE",
                "message": "Travel planning service is temporarily unavailable.",
            },
        },
    )
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)
maps_provider = (
    GoogleMapsProvider(settings.google_maps_api_key)
    if settings.maps_provider.lower() == "google" and settings.google_maps_api_key
    else DemoMapsProvider()
)
chat_service = ChatService(AdventurePlanner(maps_provider=maps_provider, max_candidates=settings.max_candidates))
configure_ai(chat_service)
app.include_router(auth_router)
app.include_router(ai_router)


@app.api_route("/", methods=["GET", "HEAD"])
async def root() -> dict[str, str]:
    return {
        "service": settings.app_name,
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
    }


@app.api_route("/health", methods=["GET", "HEAD"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "urbanquest-ai"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    return await chat_service.respond(request.message, request.context)
