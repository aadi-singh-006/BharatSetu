import asyncio
import importlib.metadata
import logging
import time
from datetime import datetime, timezone

from google import genai
from google.genai import errors, types

from ..config import settings
from ..security import redact_secret

logger = logging.getLogger(__name__)
SDK_VERSION = importlib.metadata.version("google-genai")

MODEL_FALLBACKS = (
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-3.8-flash",
    # This model has succeeded with this key before, but recent probes saw
    # intermittent overload; keep it as the last fallback.
    "gemini-3.5-flash",
)
MAX_503_ATTEMPTS = 3  # one initial request plus two bounded retries
_503_RETRY_BASE_DELAY_SECONDS = 0.5
PER_ATTEMPT_TIMEOUT_SECONDS = 20.0


class GeminiServiceError(Exception):
    def __init__(self, message: str, code: str, status_code: int = 503) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class GeminiService:
    def __init__(self) -> None:
        self._client: genai.Client | None = None
        self._client_lock = asyncio.Lock()

    @staticmethod
    def _model_candidates() -> tuple[str, ...]:
        return tuple(dict.fromkeys((settings.gemini_model, *MODEL_FALLBACKS)))

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="milliseconds")

    @staticmethod
    def _safe_error_message(exc: Exception) -> str:
        message = getattr(exc, "message", None) or str(exc)
        return redact_secret(message, settings.gemini_api_key)

    async def _get_client(self) -> genai.Client:
        if self._client is not None:
            return self._client

        async with self._client_lock:
            if self._client is None:
                logger.info("Creating Google GenAI client")
                try:
                    self._client = genai.Client(api_key=settings.gemini_api_key)
                except Exception as exc:
                    logger.error(
                        "Google GenAI client creation failed: sdk_version=%s type=%s message=%s",
                        SDK_VERSION,
                        type(exc).__name__,
                        self._safe_error_message(exc),
                    )
                    raise GeminiServiceError(
                        message="The AI service is temporarily unavailable. Please try again.",
                        code="gemini_request_failed",
                    ) from exc
                logger.info("Google GenAI client created: sdk_version=%s", SDK_VERSION)
        return self._client

    async def close(self) -> None:
        """Close both SDK clients when the application worker shuts down."""
        async with self._client_lock:
            client, self._client = self._client, None
            if client is None:
                return

            try:
                try:
                    await client.aio.aclose()
                except Exception as exc:
                    logger.error("Failed to close Google GenAI async client: type=%s message=%s",
                                 type(exc).__name__, self._safe_error_message(exc))
            finally:
                try:
                    client.close()
                except Exception as exc:
                    logger.error("Failed to close Google GenAI sync client: type=%s message=%s",
                                 type(exc).__name__, self._safe_error_message(exc))

    async def generate_reply(self, message: str) -> str:
        if not settings.gemini_api_key:
            raise GeminiServiceError(
                message="Gemini is not configured. Set GEMINI_API_KEY and try again.",
                code="gemini_not_configured",
            )

        client = await self._get_client()
        contents = (
            "You are BharatSetu AI, a concise guide to Indian public services. "
            "Use clear markdown, state uncertainty, and recommend official sources. "
            "Never invent eligibility rules or application links.\n\n"
            f"User question: {message}"
        )
        candidates = self._model_candidates()
        logger.info("Gemini fallback model sequence=%s sdk_version=%s", candidates, SDK_VERSION)
        last_error: errors.APIError | None = None
        all_errors_were_model_not_found = True
        saw_503 = False
        saw_timeout = False
        deadline = time.monotonic() + settings.gemini_timeout_seconds

        for model in candidates:
            logger.info("Selected Gemini model=%s sdk_version=%s", model, SDK_VERSION)
            for attempt in range(1, MAX_503_ATTEMPTS + 1):
                remaining_seconds = deadline - time.monotonic()
                if remaining_seconds <= 0:
                    logger.error(
                        "Gemini overall request budget exhausted: model=%s sdk_version=%s completed_at_utc=%s elapsed_seconds=%.2f",
                        model,
                        SDK_VERSION,
                        self._utc_now(),
                        settings.gemini_timeout_seconds,
                    )
                    raise GeminiServiceError(
                        message="The AI service took too long to respond. Please try again.",
                        code="gemini_timeout",
                        status_code=504,
                    ) from last_error

                attempt_timeout = min(PER_ATTEMPT_TIMEOUT_SECONDS, remaining_seconds)
                started_at = time.monotonic()
                logger.info(
                    "Gemini attempt started: model=%s sdk_version=%s attempt=%s started_at_utc=%s",
                    model,
                    SDK_VERSION,
                    attempt,
                    self._utc_now(),
                )
                try:
                    response = await asyncio.wait_for(
                        client.aio.models.generate_content(
                            model=model,
                            contents=contents,
                            config=types.GenerateContentConfig(
                                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                                    disable=True
                                )
                            ),
                        ),
                        timeout=attempt_timeout,
                    )
                    elapsed = time.monotonic() - started_at
                    logger.info(
                        "Gemini attempt completed: model=%s sdk_version=%s attempt=%s completed_at_utc=%s elapsed_seconds=%.2f status=success",
                        model,
                        SDK_VERSION,
                        attempt,
                        self._utc_now(),
                        elapsed,
                    )
                    reply = response.text.strip() if response.text else ""
                    if not reply:
                        raise GeminiServiceError(
                            message="The AI service returned an empty response. Please try again.",
                            code="gemini_empty_response",
                            status_code=502,
                        )
                    return reply
                except asyncio.TimeoutError as exc:
                    elapsed = time.monotonic() - started_at
                    saw_timeout = True
                    all_errors_were_model_not_found = False
                    logger.warning(
                        "Gemini attempt timed out: model=%s sdk_version=%s attempt=%s completed_at_utc=%s elapsed_seconds=%.2f status=timeout exception_class=%s message=%s",
                        model,
                        SDK_VERSION,
                        attempt,
                        self._utc_now(),
                        elapsed,
                        type(exc).__name__,
                        self._safe_error_message(exc),
                    )
                    break
                except errors.APIError as exc:
                    elapsed = time.monotonic() - started_at
                    last_error = exc
                    logger.error(
                        "Gemini attempt failed: model=%s sdk_version=%s attempt=%s completed_at_utc=%s elapsed_seconds=%.2f status=%s exception_class=%s api_error_code=%s message=%s",
                        model,
                        SDK_VERSION,
                        attempt,
                        self._utc_now(),
                        elapsed,
                        exc.code,
                        type(exc).__name__,
                        exc.code,
                        self._safe_error_message(exc),
                    )
                    if exc.code == 404:
                        break
                    all_errors_were_model_not_found = False
                    if exc.code == 429:
                        raise GeminiServiceError(
                            message="The AI service is receiving too many requests or has reached its usage limit. Please wait a little and try again.",
                            code="gemini_rate_limited",
                            status_code=429,
                        ) from exc
                    if exc.code in (400, 401, 403):
                        detail = (exc.message or str(exc)).lower()
                        if exc.code in (401, 403) or "api key" in detail or "api_key_invalid" in detail:
                            raise GeminiServiceError(
                                message="Gemini rejected the configured API key. Check GEMINI_API_KEY in the backend environment.",
                                code="gemini_authentication_failed",
                                status_code=502,
                            ) from exc
                    if exc.code == 503:
                        saw_503 = True
                        if attempt < MAX_503_ATTEMPTS:
                            delay = _503_RETRY_BASE_DELAY_SECONDS * (2 ** (attempt - 1))
                            delay = min(delay, max(0.0, deadline - time.monotonic()))
                            logger.warning(
                                "Retrying temporarily overloaded Gemini model: model=%s next_attempt=%s backoff_seconds=%.2f",
                                model,
                                attempt + 1,
                                delay,
                            )
                            await asyncio.sleep(delay)
                            continue
                        break
                    if exc.code == 504:
                        saw_timeout = True
                        break
                    raise GeminiServiceError(
                        message="The AI service is temporarily unavailable. Please try again.",
                        code="gemini_request_failed",
                        status_code=503,
                    ) from exc
                except GeminiServiceError:
                    raise
                except Exception as exc:
                    elapsed = time.monotonic() - started_at
                    all_errors_were_model_not_found = False
                    logger.error(
                        "Gemini attempt failed: model=%s sdk_version=%s attempt=%s completed_at_utc=%s elapsed_seconds=%.2f status=unknown exception_class=%s message=%s",
                        model,
                        SDK_VERSION,
                        attempt,
                        self._utc_now(),
                        elapsed,
                        type(exc).__name__,
                        self._safe_error_message(exc),
                    )
                    raise GeminiServiceError(
                        message="The AI service is temporarily unavailable. Please try again.",
                        code="gemini_request_failed",
                        status_code=503,
                    ) from exc

        logger.warning("Moving to next Gemini fallback model after model=%s", model)

        if all_errors_were_model_not_found:
            raise GeminiServiceError(
                message="No supported Gemini model is available for this API key.",
                code="gemini_model_unavailable",
                status_code=404,
            ) from last_error
        if saw_timeout:
            raise GeminiServiceError(
                message="Gemini did not respond before the request deadline. Please try again.",
                code="gemini_timeout",
                status_code=504,
            ) from last_error
        if saw_503:
            raise GeminiServiceError(
                message="Gemini is temporarily overloaded. Please wait a moment and try again.",
                code="gemini_temporarily_unavailable",
                status_code=503,
            ) from last_error
        raise GeminiServiceError(
            message="The AI service is temporarily unavailable. Please try again.",
            code="gemini_request_failed",
            status_code=503,
        ) from last_error


gemini_service = GeminiService()
