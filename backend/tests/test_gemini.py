import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

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
                models=SimpleNamespace(generate_content=self.generate_content)
            )
        )
        self.settings = SimpleNamespace(
            gemini_api_key="test-api-key",
            gemini_model="configured-model",
        )

    async def test_retries_404s_with_required_models_in_order(self) -> None:
        self.generate_content.side_effect = [
            api_error(404, "configured model unavailable"),
            api_error(404, "flash-lite unavailable"),
            SimpleNamespace(text="Fallback reply"),
        ]

        with (
            patch("app.services.gemini.settings", self.settings),
            patch("app.services.gemini.genai.Client", return_value=self.client),
            self.assertLogs("app.services.gemini", level="INFO") as logs,
        ):
            reply = await GeminiService().generate_reply("Hello")

        self.assertEqual(reply, "Fallback reply")
        self.assertEqual(
            [call.kwargs["model"] for call in self.generate_content.await_args_list],
            ["configured-model", "gemini-2.5-flash-lite", "gemini-2.5-pro"],
        )
        for model in ("configured-model", "gemini-2.5-flash-lite", "gemini-2.5-pro"):
            self.assertTrue(any(f"model={model}" in entry for entry in logs.output))

    async def test_non_404_api_error_logs_details_without_retry(self) -> None:
        self.generate_content.side_effect = api_error(429, "quota exceeded")

        with (
            patch("app.services.gemini.settings", self.settings),
            patch("app.services.gemini.genai.Client", return_value=self.client),
            self.assertLogs("app.services.gemini", level="ERROR") as logs,
        ):
            with self.assertRaises(GeminiServiceError) as raised:
                await GeminiService().generate_reply("Hello")

        self.assertEqual(raised.exception.code, "gemini_request_failed")
        self.assertEqual(self.generate_content.await_count, 1)
        self.assertTrue(any(
            "status_code=429" in entry and "message=quota exceeded" in entry
            for entry in logs.output
        ))

    async def test_all_404s_return_model_unavailable(self) -> None:
        self.generate_content.side_effect = [
            api_error(404, "configured unavailable"),
            api_error(404, "flash-lite unavailable"),
            api_error(404, "pro unavailable"),
        ]

        with (
            patch("app.services.gemini.settings", self.settings),
            patch("app.services.gemini.genai.Client", return_value=self.client),
        ):
            with self.assertRaises(GeminiServiceError) as raised:
                await GeminiService().generate_reply("Hello")

        self.assertEqual(raised.exception.code, "gemini_model_unavailable")
        self.assertEqual(self.generate_content.await_count, 3)

    async def test_success_uses_only_configured_model_and_logs_it(self) -> None:
        self.generate_content.return_value = SimpleNamespace(text="Configured reply")

        with (
            patch("app.services.gemini.settings", self.settings),
            patch("app.services.gemini.genai.Client", return_value=self.client),
            self.assertLogs("app.services.gemini", level="INFO") as logs,
        ):
            reply = await GeminiService().generate_reply("Hello")

        self.assertEqual(reply, "Configured reply")
        self.assertEqual(self.generate_content.await_count, 1)
        self.assertEqual(
            self.generate_content.await_args.kwargs["model"],
            "configured-model",
        )
        self.assertTrue(any("model=configured-model" in entry for entry in logs.output))

    async def test_client_initialization_failure_uses_service_error(self) -> None:
        with (
            patch("app.services.gemini.settings", self.settings),
            patch(
                "app.services.gemini.genai.Client",
                side_effect=ValueError("invalid client configuration"),
            ),
        ):
            with self.assertRaises(GeminiServiceError) as raised:
                await GeminiService().generate_reply("Hello")

        self.assertEqual(raised.exception.code, "gemini_request_failed")

    def test_model_candidates_do_not_retry_the_same_model(self) -> None:
        self.settings.gemini_model = "gemini-2.5-flash-lite"

        with patch("app.services.gemini.settings", self.settings):
            candidates = GeminiService()._model_candidates()

        self.assertEqual(
            candidates,
            ("gemini-2.5-flash-lite", "gemini-2.5-pro"),
        )


if __name__ == "__main__":
    unittest.main()