import asyncio
import logging

from google import genai

from ..config import settings

logger = logging.getLogger(__name__)


class GeminiServiceError(Exception):
    def __init__(self, message: str, code: str, status_code: int = 503) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class GeminiService:
    async def generate_reply(self, message: str) -> str:
        if not settings.gemini_api_key:
            raise GeminiServiceError(
                message="Gemini is not configured. Set GEMINI_API_KEY and try again.",
                code="gemini_not_configured",
            )

        try:
            client = genai.Client(api_key=settings.gemini_api_key)
            response = await asyncio.wait_for(
                client.aio.models.generate_content(
                    model=settings.gemini_model,
                    contents=(
                        "You are BharatSetu AI, a concise guide to Indian public services. "
                        "Use clear markdown, state uncertainty, and recommend official sources. "
                        "Never invent eligibility rules or application links.\n\n"
                        f"User question: {message}"
                    ),
                ),
                timeout=20,
            )
        except asyncio.TimeoutError as exc:
            logger.warning("Gemini request timed out")
            raise GeminiServiceError(
                message="The AI service took too long to respond. Please try again.",
                code="gemini_timeout",
            ) from exc
        except Exception as exc:
            logger.exception("Gemini request failed")
            raise GeminiServiceError(
                message="The AI service is temporarily unavailable. Please try again.",
                code="gemini_request_failed",
            ) from exc

        reply = response.text.strip() if response.text else ""
        if not reply:
            raise GeminiServiceError(
                message="The AI service returned an empty response. Please try again.",
                code="gemini_empty_response",
                status_code=502,
            )

        return reply


gemini_service = GeminiService()