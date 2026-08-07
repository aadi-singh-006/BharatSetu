from fastapi import APIRouter

from .config import settings
from .schemas import ChatRequest, ChatResponse, ErrorResponse
from .services.gemini import gemini_service
from .services.knowledge_base import knowledge_base_service

router = APIRouter()


@router.get("/")
async def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "message": "BharatSetu AI backend is running.",
    }


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env}


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        502: {"model": ErrorResponse, "description": "Gemini returned an invalid response"},
        503: {"model": ErrorResponse, "description": "Gemini is unavailable or not configured"},
    },
)
async def chat(payload: ChatRequest) -> ChatResponse:
    entry = knowledge_base_service.search(payload.message)
    if entry:
        return ChatResponse(
            reply=(
                f"## {entry['title']}\n\n{entry['description']}\n\n"
                f"### Eligibility\n{entry['eligibility']}\n\n"
                "### Required documents\n" + "\n".join(
                    f"- {document}" for document in entry["required_documents"]
                ) + "\n\n### Application steps\n" + "\n".join(
                    f"{index}. {step}" for index, step in enumerate(entry["application_steps"], 1)
                ) + f"\n\n**Official source:** [Open the official website]({entry['official_website']})"
            ),
            model="knowledge_base",
        )
    reply = await gemini_service.generate_reply(payload.message)
    return ChatResponse(reply=reply, model=settings.gemini_model)