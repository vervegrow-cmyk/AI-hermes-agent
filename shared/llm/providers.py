from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from shared.config import get_settings


@dataclass
class BaseLLMClient:
    provider: str
    model: str

    def generate(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        raise NotImplementedError


class OpenAIClient(BaseLLMClient):
    def __init__(self, model: str, api_key: str):
        from openai import OpenAI

        super().__init__(provider="openai", model=model)
        self.client = OpenAI(api_key=api_key)

    def generate(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        response = self.client.responses.create(model=self.model, input=prompt, **kwargs)
        return {"text": response.output_text, "raw": response.model_dump()}


class DeepSeekClient(BaseLLMClient):
    def __init__(self, model: str, api_key: str, base_url: str):
        from openai import OpenAI

        super().__init__(provider="deepseek", model=model)
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def generate(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        request_kwargs = dict(kwargs)
        text_config = request_kwargs.pop("text", None)
        if text_config:
            response_format = (text_config or {}).get("format") or {}
            if response_format.get("type") == "json_object":
                request_kwargs["response_format"] = {"type": "json_object"}
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            **request_kwargs,
        )
        message = response.choices[0].message if response.choices else None
        content = getattr(message, "content", "") or ""
        if isinstance(content, list):
            text = "".join(
                str(part.get("text", ""))
                for part in content
                if isinstance(part, dict)
            )
        else:
            text = str(content)
        return {"text": text, "raw": response.model_dump()}


class AnthropicClient(BaseLLMClient):
    def __init__(self, model: str, api_key: str):
        from anthropic import Anthropic

        super().__init__(provider="anthropic", model=model)
        self.client = Anthropic(api_key=api_key)

    def generate(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=kwargs.pop("max_tokens", 512),
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        )
        text = "".join(
            block.text for block in response.content if getattr(block, "type", "") == "text"
        )
        return {"text": text, "raw": response.model_dump()}


class GeminiClient(BaseLLMClient):
    def __init__(self, model: str, api_key: str):
        from google import genai

        super().__init__(provider="gemini", model=model)
        self.client = genai.Client(api_key=api_key)

    def generate(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        response = self.client.models.generate_content(model=self.model, contents=prompt, **kwargs)
        return {"text": response.text or "", "raw": response.model_dump()}


def get_llm(provider: str | None = None, model: str | None = None) -> BaseLLMClient:
    settings = get_settings()
    provider_name = (provider or settings.default_llm_provider).lower()
    model_name = model or settings.default_llm_model

    if provider_name == "openai":
        return OpenAIClient(model=model_name, api_key=settings.openai_api_key)
    if provider_name == "deepseek":
        return DeepSeekClient(
            model=model or settings.deepseek_model,
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        )
    if provider_name in {"claude", "anthropic"}:
        return AnthropicClient(model=model_name, api_key=settings.anthropic_api_key)
    if provider_name in {"gemini", "google"}:
        return GeminiClient(model=model_name, api_key=settings.google_api_key)
    raise ValueError(f"Unsupported LLM provider: {provider_name}")
