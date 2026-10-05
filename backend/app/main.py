import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .routes import router
from .security import redact_secret
from .services.gemini import GeminiServiceError, gemini_service

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    try:
        yield
    finally:
        await gemini_service.close()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Hackathon prototype API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.exception_handler(GeminiServiceError)
async def gemini_error_handler(
    _request: Request,
    exc: GeminiServiceError,
) -> JSONResponse:
    safe_message = redact_secret(exc.message, settings.gemini_api_key)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": safe_message}},
    )


@app.exception_handler(Exception)
async def unexpected_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "Unhandled API error: exception_class=%s message=%s",
        type(exc).__name__,
        redact_secret(exc, settings.gemini_api_key),
    )
    return JSONResponse(
        status_code=503,
        content={
            "error": {
                "code": "service_unavailable",
                "message": "BharatSetu is temporarily unavailable. Please try again.",
            }
        },
    )
