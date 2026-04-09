import json
import socket
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib import error, request

from backend.app.config import (
    OPENROUTER_API_URL,
    OPENROUTER_APP_TITLE,
    OPENROUTER_CONNECTIVITY_PROMPT,
    OPENROUTER_HTTP_REFERER,
    OPENROUTER_MODEL,
    OPENROUTER_MAX_RETRIES,
    OPENROUTER_TIMEOUT_SECONDS,
    get_openrouter_api_key,
)
from backend.app.models import AIAssistantPayload, AIConversationMessage


class MissingOpenRouterApiKeyError(RuntimeError):
    pass


class OpenRouterRequestError(RuntimeError):
    pass


@dataclass(frozen=True)
class ConnectivityCheckResult:
    model: str
    reply: str


@dataclass(frozen=True)
class BoardAssistantResult:
    model: str
    reply: str
    operations: List[dict]


class OpenRouterClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: str = OPENROUTER_API_URL,
        model: str = OPENROUTER_MODEL,
        timeout_seconds: int = OPENROUTER_TIMEOUT_SECONDS,
        max_retries: int = OPENROUTER_MAX_RETRIES,
    ) -> None:
        self.api_key = get_openrouter_api_key() if api_key is None else api_key
        self.api_url = api_url
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

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

    def run_board_assistant(
        self,
        board_snapshot: dict,
        message: str,
        history: List[AIConversationMessage],
    ) -> BoardAssistantResult:
        if not self.api_key:
            raise MissingOpenRouterApiKeyError(
                "OPENROUTER_API_KEY is not configured."
            )

        request_payload = {
            "model": self.model,
            "messages": _build_board_assistant_messages(
                board_snapshot=board_snapshot,
                message=message,
                history=history,
            ),
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "board_assistant_response",
                    "strict": True,
                    "schema": AIAssistantPayload.model_json_schema(),
                },
            },
            "plugins": [{"id": "response-healing"}],
            "temperature": 0,
            "max_tokens": 300,
        }

        last_error: Optional[OpenRouterRequestError] = None
        for attempt in range(self.max_retries + 1):
            response_payload = self._post(request_payload)

            try:
                assistant_payload = _parse_assistant_payload(response_payload)
            except OpenRouterRequestError as exc:
                last_error = exc
                if not _is_retryable_structured_output_error(exc) or attempt >= self.max_retries:
                    raise
                time.sleep(0.4 * (attempt + 1))
                continue

            return BoardAssistantResult(
                model=str(response_payload.get("model") or self.model),
                reply=assistant_payload.reply,
                operations=[operation.model_dump() for operation in assistant_payload.operations],
            )

        if last_error is not None:
            raise last_error

        raise OpenRouterRequestError("OpenRouter request failed before a valid response was returned.")

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
        except socket.timeout as exc:
            raise OpenRouterRequestError(
                "OpenRouter timed out before returning a response."
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


def _build_board_assistant_messages(
    board_snapshot: Dict[str, object],
    message: str,
    history: List[AIConversationMessage],
) -> List[dict]:
    messages: List[dict] = [
        {
            "role": "system",
            "content": (
                "You are an assistant for a kanban board. "
                "Reply naturally to the user and include zero or more focused board operations. "
                "Only use these operations when needed: rename_column, create_card, update_card, "
                "move_card, delete_card. "
                "Do not invent columns or cards that are not present in the provided board snapshot. "
                "Use zero operations when no board change is needed."
            ),
        }
    ]

    for history_message in history:
        messages.append(history_message.model_dump())

    messages.append(
        {
            "role": "user",
            "content": (
                "Current board snapshot:\n"
                f"{json.dumps(board_snapshot, ensure_ascii=True)}\n\n"
                "User request:\n"
                f"{message}"
            ),
        }
    )

    return messages


def _parse_assistant_payload(response_payload: dict[str, Any]) -> AIAssistantPayload:
    raw_content = _extract_reply_text(response_payload)

    try:
        parsed_content = _parse_json_text(raw_content)
    except json.JSONDecodeError as exc:
        raise OpenRouterRequestError(
            "OpenRouter returned invalid JSON for the structured assistant response."
        ) from exc

    try:
        return AIAssistantPayload.model_validate(parsed_content)
    except Exception as exc:
        raise OpenRouterRequestError(
            "OpenRouter returned a structured assistant response that did not match the expected schema."
        ) from exc


def _parse_json_text(raw_content: str) -> dict:
    try:
        return json.loads(raw_content)
    except json.JSONDecodeError:
        cleaned_content = raw_content.strip()

        if cleaned_content.startswith("```"):
            fenced_lines = cleaned_content.splitlines()
            if len(fenced_lines) >= 3 and fenced_lines[-1].strip() == "```":
                return json.loads("\n".join(fenced_lines[1:-1]))

        first_object_start = cleaned_content.find("{")
        last_object_end = cleaned_content.rfind("}")
        if first_object_start != -1 and last_object_end != -1 and last_object_end > first_object_start:
            return json.loads(cleaned_content[first_object_start : last_object_end + 1])

        raise


def _is_retryable_structured_output_error(error_value: OpenRouterRequestError) -> bool:
    return str(error_value) in {
        "OpenRouter response did not include assistant text.",
        "OpenRouter returned invalid JSON for the structured assistant response.",
        "OpenRouter returned a structured assistant response that did not match the expected schema.",
    }
