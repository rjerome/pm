import json
from dataclasses import dataclass
from typing import Any, Optional
from urllib import error, request

from backend.app.config import (
    OPENROUTER_API_URL,
    OPENROUTER_APP_TITLE,
    OPENROUTER_CONNECTIVITY_PROMPT,
    OPENROUTER_HTTP_REFERER,
    OPENROUTER_MODEL,
    OPENROUTER_TIMEOUT_SECONDS,
    get_openrouter_api_key,
)


class MissingOpenRouterApiKeyError(RuntimeError):
    pass


class OpenRouterRequestError(RuntimeError):
    pass


@dataclass(frozen=True)
class ConnectivityCheckResult:
    model: str
    reply: str


class OpenRouterClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: str = OPENROUTER_API_URL,
        model: str = OPENROUTER_MODEL,
        timeout_seconds: int = OPENROUTER_TIMEOUT_SECONDS,
    ) -> None:
        self.api_key = get_openrouter_api_key() if api_key is None else api_key
        self.api_url = api_url
        self.model = model
        self.timeout_seconds = timeout_seconds

    def run_connectivity_check(self) -> ConnectivityCheckResult:
        if not self.api_key:
            raise MissingOpenRouterApiKeyError(
                "OPENROUTER_API_KEY is not configured."
            )

        response_payload = self._post(
            {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": OPENROUTER_CONNECTIVITY_PROMPT,
                    }
                ],
            }
        )

        return ConnectivityCheckResult(
            model=str(response_payload.get("model") or self.model),
            reply=_extract_reply_text(response_payload),
        )

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        raw_payload = json.dumps(payload).encode("utf-8")
        http_request = request.Request(
            self.api_url,
            data=raw_payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": OPENROUTER_HTTP_REFERER,
                "X-Title": OPENROUTER_APP_TITLE,
            },
        )

        try:
            with request.urlopen(http_request, timeout=self.timeout_seconds) as response:
                raw_response = response.read().decode("utf-8")
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise OpenRouterRequestError(_build_http_error_message(exc.code, body)) from exc
        except error.URLError as exc:
            raise OpenRouterRequestError(
                f"Could not reach OpenRouter: {exc.reason}"
            ) from exc

        try:
            return json.loads(raw_response)
        except json.JSONDecodeError as exc:
            raise OpenRouterRequestError(
                "OpenRouter returned a non-JSON response."
            ) from exc


def _build_http_error_message(status_code: int, response_body: str) -> str:
    response_text = response_body.strip()

    if status_code in {401, 403}:
        return "OpenRouter rejected the API key."

    if response_text:
        try:
            payload = json.loads(response_text)
        except json.JSONDecodeError:
            return f"OpenRouter request failed with status {status_code}."

        error_message = payload.get("error", {}).get("message")
        if error_message:
            return f"OpenRouter request failed: {error_message}"

    return f"OpenRouter request failed with status {status_code}."


def _extract_reply_text(response_payload: dict[str, Any]) -> str:
    choices = response_payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise OpenRouterRequestError("OpenRouter response did not include any choices.")

    message = choices[0].get("message")
    if not isinstance(message, dict):
        raise OpenRouterRequestError(
            "OpenRouter response did not include an assistant message."
        )

    content = message.get("content")
    if isinstance(content, str):
        reply = content.strip()
        if reply:
            return reply

    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if isinstance(part, dict):
                text = part.get("text")
                if isinstance(text, str) and text.strip():
                    parts.append(text.strip())

        if parts:
            return "\n".join(parts)

    raise OpenRouterRequestError(
        "OpenRouter response did not include assistant text."
    )
