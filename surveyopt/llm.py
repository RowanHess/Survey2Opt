from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from openai import OpenAI


@dataclass(frozen=True)
class LLMRequest:
    task_id: str
    system_prompt: str
    user_prompt: str
    temperature: float
    max_tokens: int
    attempt: int


@dataclass(frozen=True)
class LLMReply:
    text: str
    metadata: dict[str, Any]


class LLMClient(Protocol):
    def complete(self, request: LLMRequest) -> LLMReply:
        ...


class OpenAIChatLLM:
    """
    OpenAI-compatible client.

    This works with the Parley endpoint described in the request, assuming
    the supplied model is available through that endpoint.
    """

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        default_temperature: float = 1,
        default_max_tokens: int = 4_000,
    ) -> None:
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        self.model = model
        self.default_temperature = default_temperature
        self.default_max_tokens = default_max_tokens

    @classmethod
    def from_environment(
        cls,
        *,
        model: str,
        api_key_env: str = "PARLEY_API_KEY",
        base_url_env: str = "PARLEY_BASE_URL",
        default_base_url: str = "https://parley.api.mit.edu/v1",
    ) -> "OpenAIChatLLM":
        api_key = os.environ[api_key_env]
        base_url = os.getenv(base_url_env, default_base_url)

        return cls(
            api_key=api_key,
            base_url=base_url,
            model=model,
        )

    def complete(self, request: LLMRequest) -> LLMReply:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": request.system_prompt,
                },
                {
                    "role": "user",
                    "content": request.user_prompt,
                },
            ],
            max_tokens=request.max_tokens,
        )

        text = response.choices[0].message.content

        if text is None:
            raise RuntimeError("LLM returned an empty response.")

        return LLMReply(
            text=text,
            metadata={
                "provider": "openai_compatible",
                "model": self.model,
                "request_task_id": request.task_id,
            },
        )


class TextFixtureLLM:
    """
    Fake LLM for deterministic tests.

    Responses are stored in text files. For a task with ID:

        person_interests__user_1__interests

    the fixture should be:

        fixtures/person_interests__user_1__interests.txt

    For a repair attempt, the task ID is augmented automatically, e.g.:

        person_interests__user_1__interests__repair_2.txt
    """

    def __init__(self, fixture_directory: str | Path) -> None:
        self.fixture_directory = Path(fixture_directory)

    def complete(self, request: LLMRequest) -> LLMReply:
        safe_task_id = re.sub(
            r"[^A-Za-z0-9_.-]",
            "_",
            request.task_id,
        )

        attempt_file = self.fixture_directory / (
            f"{safe_task_id}__attempt_{request.attempt}.txt"
        )
        default_file = self.fixture_directory / f"{safe_task_id}.txt"

        if attempt_file.exists():
            path = attempt_file
        elif default_file.exists():
            path = default_file
        else:
            raise FileNotFoundError(
                "No fake LLM response found for task "
                f"{request.task_id!r}. Expected {default_file}."
            )

        return LLMReply(
            text=path.read_text(encoding="utf-8"),
            metadata={
                "provider": "text_fixture",
                "fixture_path": str(path),
                "request_task_id": request.task_id,
            },
        )


class LLMRouter:
    """
    Routes ordinary tasks to `standard` and repair / high-stakes tasks to
    `smart`, if configured.
    """

    def __init__(
        self,
        *,
        standard: LLMClient,
        smart: LLMClient | None = None,
    ) -> None:
        self.standard = standard
        self.smart = smart

    def for_profile(self, profile: str) -> LLMClient:
        if profile == "smart" and self.smart is not None:
            return self.smart

        return self.standard

    def repair_client(self) -> LLMClient:
        return self.smart or self.standard