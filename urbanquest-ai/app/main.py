from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.chat.models import ChatRequest, ChatResponse
from app.chat.service import ChatService
from app.config import get_settings
from app.maps.demo import DemoMapsProvider
from app.planner.service import AdventurePlanner

settings = get_settings()
app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
chat_service = ChatService(
    AdventurePlanner(
        maps_provider=DemoMapsProvider(),
        max_candidates=settings.max_candidates,
    )
)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "service": settings.app_name,
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    return await chat_service.respond(request.message, request.context)
