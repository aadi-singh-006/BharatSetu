import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from google.genai import errors

from app.services.gemini import GeminiService, GeminiServiceError


def api_error(code: int, message: str) -> errors.APIError:
    return errors.APIError(
        code=code,
        response_json={"error": {"code": code, "message": message}},
    )


class GeminiServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.generate_content = AsyncMock()
        self.client = SimpleNamespace(
            aio=SimpleNamespace(
                models=SimpleNamespace(generate_content=self.generate_content),
                aclose=AsyncMock(),
            ),
            close=Mock(),
        )
        self.settings = SimpleNamespace(
            gemini_api_key="test-api-key",
            gemini_model="gemini-3.5-flash-lite",
            gemini_timeout_seconds=1,
        )
        self.client_constructor = patch(
            "app.services.gemini.genai.Client", return_value=self.client
        )
        self.client_constructor_mock = self.client_constructor.start()
        self.settings_patch = patch("app.services.gemini.settings", self.settings)
        self.settings_patch.start()
        self.addCleanup(self.client_constructor.stop)
        self.addCleanup(self.settings_patch.stop)

    async def test_success_logs_model_timing_and_reuses_client(self) -> None:
        self.generate_content.side_effect = [
            SimpleNamespace(text="First reply"),
            SimpleNamespace(text="Second reply"),
        ]
        service = GeminiService()

        with self.assertLogs("app.services.gemini", level="INFO") as logs:
            self.assertEqual(await service.generate_reply("Hello"), "First reply")
            self.assertEqual(await service.generate_reply("Again"), "Second reply")
        await service.close()

        self.assertEqual(self.generate_content.await_count, 2)
        self.assertEqual(self.client_constructor_mock.call_count, 1)
        request_config = self.generate_content.await_args.kwargs["config"]
        self.assertTrue(request_config.automatic_function_calling.disable)
        self.client.aio.aclose.assert_awaited_once()
        self.client.close.assert_called_once()
        self.assertTrue(any("Gemini attempt started" in line for line in logs.output))
        self.assertTrue(any("elapsed_seconds=" in line for line in logs.output))

    async def test_timeout_returns_friendly_error_and_closes_on_shutdown(self) -> None:
        self.settings.gemini_timeout_seconds = 0.01

        async def slow_response(**_kwargs: object) -> SimpleNamespace:
            await asyncio.sleep(1)
            return SimpleNamespace(text="Too late")

        self.generate_content.side_effect = slow_response
        service = GeminiService()
        with self.assertRaises(GeminiServiceError) as raised:
            await service.generate_reply("Hello")
        await service.close()

        self.assertEqual(raised.exception.code, "gemini_timeout")
        self.client.aio.aclose.assert_awaited_once()
        self.client.close.assert_called_once()

    async def test_404_retries_models_in_order_then_closes_on_shutdown(self) -> None:
        self.generate_content.side_effect = [
            api_error(404, "primary model unavailable"),
            api_error(404, "3.6 model unavailable"),
            SimpleNamespace(text="Fallback reply"),
        ]
        service = GeminiService()

        reply = await service.generate_reply("Hello")
        await service.close()

        self.assertEqual(reply, "Fallback reply")
        self.assertEqual(
            [call.kwargs["model"] for call in self.generate_content.await_args_list],
            ["gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-3.7-flash"],
        )
        self.client.aio.aclose.assert_awaited_once()
        self.client.close.assert_called_once()

    async def test_503_retries_same_model_with_backoff_then_succeeds(self) -> None:
        self.generate_content.side_effect = [
            api_error(503, "model is experiencing high demand"),
            SimpleNamespace(text="Primary recovered"),
        ]
        service = GeminiService()

        sleep = AsyncMock()
        with (
            patch("app.services.gemini.asyncio.sleep", sleep),
            self.assertLogs("app.services.gemini", level="WARNING") as logs,
        ):
            reply = await service.generate_reply("Hello")
        await service.close()

        self.assertEqual(reply, "Primary recovered")
        self.assertEqual(
            [call.kwargs["model"] for call in self.generate_content.await_args_list],
            ["gemini-3.5-flash-lite", "gemini-3.5-flash-lite"],
        )
        self.assertTrue(all(
            call.kwargs["config"].automatic_function_calling.disable
            for call in self.generate_content.await_args_list
        ))
        self.assertTrue(any("Retrying temporarily overloaded" in line for line in logs.output))
        sleep.assert_awaited_once_with(0.5)
        self.client.aio.aclose.assert_awaited_once()

    async def test_503_all_models_unavailable_returns_distinct_error(self) -> None:
        service = GeminiService()
        self.settings.gemini_timeout_seconds = 60
        sequence = service._model_candidates()
        self.generate_content.side_effect = [
            api_error(503, "model is experiencing high demand")
            for _ in range(len(sequence) * 3)
        ]
        sleep = AsyncMock()

        with patch("app.services.gemini.asyncio.sleep", sleep):
            with self.assertRaises(GeminiServiceError) as raised:
                await service.generate_reply("Hello")
        await service.close()

        self.assertEqual(raised.exception.code, "gemini_temporarily_unavailable")
        self.assertEqual(raised.exception.status_code, 503)
        self.assertEqual(self.generate_content.await_count, len(sequence) * 3)
        self.assertEqual(sleep.await_count, len(sequence) * 2)
        self.assertEqual(
            [round(call.args[0], 2) for call in sleep.await_args_list],
            [0.5, 1.0] * len(sequence),
        )
        self.client.aio.aclose.assert_awaited_once()

    async def test_all_404s_return_model_unavailable_and_close_on_shutdown(self) -> None:
        self.generate_content.side_effect = [
            api_error(404, "primary unavailable"),
            api_error(404, "3.6 unavailable"),
            api_error(404, "3.7 unavailable"),
            api_error(404, "3.8 unavailable"),
            api_error(404, "3.5 flash unavailable"),
        ]
        service = GeminiService()

        with self.assertRaises(GeminiServiceError) as raised:
            await service.generate_reply("Hello")
        await service.close()

        self.assertEqual(raised.exception.code, "gemini_model_unavailable")
        self.assertEqual(self.generate_content.await_count, 5)
        self.assertEqual(raised.exception.status_code, 404)
        self.client.aio.aclose.assert_awaited_once()

    async def test_429_is_not_retried_as_model_fallback_and_closes_on_shutdown(self) -> None:
        self.generate_content.side_effect = api_error(429, "quota exceeded")
        service = GeminiService()

        with self.assertLogs("app.services.gemini", level="ERROR") as logs:
            with self.assertRaises(GeminiServiceError) as raised:
                await service.generate_reply("Hello")
        await service.close()

        self.assertEqual(raised.exception.code, "gemini_rate_limited")
        self.assertEqual(raised.exception.status_code, 429)
        self.assertEqual(self.generate_content.await_count, 1)
        self.assertTrue(any("code=429" in line and "quota exceeded" in line for line in logs.output))
        self.client.aio.aclose.assert_awaited_once()

    async def test_logs_never_contain_api_key(self) -> None:
        self.generate_content.side_effect = api_error(500, "failed with test-api-key")
        service = GeminiService()

        with self.assertLogs("app.services.gemini", level="ERROR") as logs:
            with self.assertRaises(GeminiServiceError):
                await service.generate_reply("Hello")
        await service.close()

        self.assertNotIn("test-api-key", "\n".join(logs.output))

    async def test_other_api_errors_are_not_reported_as_quota_errors(self) -> None:
        self.generate_content.side_effect = api_error(500, "backend error")
        service = GeminiService()

        with self.assertRaises(GeminiServiceError) as raised:
            await service.generate_reply("Hello")
        await service.close()

        self.assertEqual(raised.exception.code, "gemini_request_failed")
        self.assertEqual(raised.exception.status_code, 503)
        self.client.aio.aclose.assert_awaited_once()

    async def test_authentication_error_has_distinct_response(self) -> None:
        self.generate_content.side_effect = api_error(403, "API key rejected")
        service = GeminiService()

        with self.assertRaises(GeminiServiceError) as raised:
            await service.generate_reply("Hello")
        await service.close()

        self.assertEqual(raised.exception.code, "gemini_authentication_failed")
        self.assertEqual(raised.exception.status_code, 502)
        self.client.aio.aclose.assert_awaited_once()

    async def test_error_logs_redact_full_and_partial_api_key(self) -> None:
        api_key = "fake-gemini-api-key-0123456789"
        self.settings.gemini_api_key = api_key
        self.generate_content.side_effect = RuntimeError(
            f"connection reset: credential={api_key}; fragment={api_key[8:20]}"
        )
        service = GeminiService()

        with self.assertLogs("app.services.gemini", level="ERROR") as logs:
            with self.assertRaises(GeminiServiceError) as raised:
                await service.generate_reply("Hello")
        await service.close()

        self.assertEqual(raised.exception.code, "gemini_request_failed")
        combined_logs = "\n".join(logs.output)
        self.assertIn("RuntimeError", combined_logs)
        self.assertIn("connection reset", combined_logs)
        self.assertIn("[REDACTED]", combined_logs)
        self.assertNotIn(api_key, combined_logs)
        self.assertNotIn(api_key[8:20], combined_logs)
        self.client.aio.aclose.assert_awaited_once()
        self.client.close.assert_called_once()

    async def test_client_initialization_failure_returns_service_error(self) -> None:
        self.client_constructor.stop()
        broken_constructor = patch(
            "app.services.gemini.genai.Client",
            side_effect=ValueError("invalid client configuration"),
        )
        with (
            broken_constructor,
            self.assertLogs("app.services.gemini", level="ERROR"),
        ):
            with self.assertRaises(GeminiServiceError) as raised:
                await GeminiService().generate_reply("Hello")

        self.assertEqual(raised.exception.code, "gemini_request_failed")

    def test_model_candidates_do_not_retry_the_same_model(self) -> None:
        self.settings.gemini_model = "gemini-3.6-flash"
        self.assertEqual(
            GeminiService()._model_candidates(),
            (
                "gemini-3.6-flash",
                "gemini-3.7-flash",
                "gemini-3.8-flash",
                "gemini-3.5-flash",
            ),
        )


if __name__ == "__main__":
    unittest.main()
