import asyncio
import logging

from google import genai
from google.genai import errors

from ..config import settings

logger = logging.getLogger(__name__)

MODEL_FALLBACKS = (
    "gemini-2.5-flash-lite",
    "gemini-2.5-pro",
)


class GeminiServiceError(Exception):
    def __init__(self, message: str, code: str, status_code: int = 503) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class GeminiService:
    @staticmethod
    def _model_candidates() -> tuple[str, ...]:
        return tuple(dict.fromkeys((settings.gemini_model, *MODEL_FALLBACKS)))

    async def generate_reply(self, message: str) -> str:
        if not settings.gemini_api_key:
            raise GeminiServiceError(
                message="Gemini is not configured. Set GEMINI_API_KEY and try again.",
                code="gemini_not_configured",
            )

        try:
            client = genai.Client(api_key=settings.gemini_api_key)
        except Exception as exc:
            logger.exception("Failed to initialize Google GenAI client")
            raise GeminiServiceError(
                message="The AI service is temporarily unavailable. Please try again.",
                code="gemini_request_failed",
            ) from exc

        contents = (
            "You are BharatSetu AI, a concise guide to Indian public services. "
            "Use clear markdown, state uncertainty, and recommend official sources. "
            "Never invent eligibility rules or application links.\n\n"
            f"User question: {message}"
        )
        last_error: errors.APIError | None = None
        for model in self._model_candidates():
            logger.info("Sending Gemini request with model=%s", model)
            try:
                response = await asyncio.wait_for(
                    client.aio.models.generate_content(
                        model=model,
                        contents=contents,
                    ),
                    timeout=20,
                )
                break
            except asyncio.TimeoutError as exc:
                logger.warning("Gemini request timed out with model=%s", model)
                raise GeminiServiceError(
                    message="The AI service took too long to respond. Please try again.",
                    code="gemini_timeout",
                ) from exc
            except errors.APIError as exc:
                last_error = exc
                logger.error(
                    "Google GenAI API request failed: model=%s status_code=%s message=%s",
                    model,
                    exc.code,
                    exc.message or str(exc),
                )
                if exc.code == 404:
                    continue
                raise GeminiServiceError(
                    message="The AI service is temporarily unavailable. Please try again.",
                    code="gemini_request_failed",
                ) from exc
            except Exception as exc:
                logger.exception("Gemini request failed with model=%s", model)
                raise GeminiServiceError(
                    message="The AI service is temporarily unavailable. Please try again.",
                    code="gemini_request_failed",
                ) from exc
        else:
            logger.error("No configured Gemini model was available: %s", last_error)
            raise GeminiServiceError(
                message="No supported Gemini model is available for this API key.",
                code="gemini_model_unavailable",
            ) from last_error

        reply = response.text.strip() if response.text else ""
        if not reply:
            raise GeminiServiceError(
                message="The AI service returned an empty response. Please try again.",
                code="gemini_empty_response",
                status_code=502,
            )

        return reply


gemini_service = GeminiService()