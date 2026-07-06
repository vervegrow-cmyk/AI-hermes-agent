"""Volcengine / BytePlus Ark chat-completions provider tool.

Supports text chat plus simple multimodal image_url inputs against Ark-hosted
models such as `doubao-seed-evolving`.
"""

from __future__ import annotations

import base64
import mimetypes
import os
import time
from pathlib import Path
from typing import Any

from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ResourceProfile,
    RetryPolicy,
    ToolResult,
    ToolRuntime,
    ToolStability,
    ToolStatus,
    ToolTier,
)


class ArkChat(BaseTool):
    name = "ark_chat"
    version = "0.1.0"
    tier = ToolTier.CORE
    capability = "llm"
    provider = "ark"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.API

    dependencies = []
    install_instructions = (
        "Set ARK_API_KEY to your Volcengine / BytePlus Ark API key.\n"
        "Optional: set ARK_BASE_URL to switch region/base URL.\n"
        "Examples:\n"
        "  https://ark.cn-beijing.volces.com/api/v3\n"
        "  https://ark.ap-southeast.bytepluses.com/api/v3"
    )
    capabilities = [
        "chat_completion",
        "prompt_to_text",
        "multimodal_understanding",
        "image_question_answering",
        "script_writing",
        "storyboard_planning",
    ]
    supports = {
        "system_prompt": True,
        "multimodal_image_url": True,
        "local_image_paths": True,
        "json_output_capture": True,
    }
    best_for = [
        "Doubao Seed Evolving reasoning inside OpenMontage",
        "video scripting, prompt writing, and storyboard planning",
        "product-image understanding before generating ad concepts",
        "multimodal chat against Ark-hosted Doubao models",
    ]
    not_good_for = [
        "direct video generation",
        "streaming token-by-token UX",
    ]
    fallback_tools = []

    input_schema = {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "Convenience alias for a single user text message.",
            },
            "system_prompt": {
                "type": "string",
                "description": "Optional system instruction prepended to the chat.",
            },
            "messages": {
                "type": "array",
                "description": (
                    "Full Ark/OpenAI-style chat messages. If omitted, the tool will "
                    "build a single user message from prompt/image inputs."
                ),
                "items": {"type": "object"},
            },
            "model": {
                "type": "string",
                "default": "doubao-seed-evolving",
                "description": "Ark model id, e.g. doubao-seed-evolving.",
            },
            "image_urls": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Image URLs to attach to the generated user message.",
            },
            "image_paths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Local image paths converted to data URLs and attached to the generated user message.",
            },
            "temperature": {
                "type": "number",
                "default": 0.7,
            },
            "max_tokens": {
                "type": "integer",
                "description": "Optional output token cap passed through when provided.",
            },
            "top_p": {
                "type": "number",
                "description": "Optional nucleus sampling parameter.",
            },
            "output_path": {
                "type": "string",
                "description": "Optional path to save the assistant text response.",
            },
            "raw_output_path": {
                "type": "string",
                "description": "Optional path to save the full JSON response.",
            },
        },
        "oneOf": [
            {"required": ["prompt"]},
            {"required": ["messages"]},
        ],
    }

    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=256, vram_mb=0, disk_mb=20, network_required=True
    )
    retry_policy = RetryPolicy(max_retries=2, retryable_errors=["rate_limit", "timeout", "429", "503"])
    idempotency_key_fields = ["prompt", "system_prompt", "messages", "model", "temperature", "max_tokens", "top_p"]
    side_effects = ["calls Ark chat/completions API", "optionally writes text/json output files"]
    user_visible_verification = ["Review the returned text for factual fit, structure, and prompt quality"]

    def _get_api_key(self) -> str | None:
        return os.environ.get("ARK_API_KEY")

    def _base_url(self) -> str:
        return (
            os.environ.get("ARK_BASE_URL")
            or os.environ.get("ARK_API_BASE")
            or "https://ark.cn-beijing.volces.com/api/v3"
        ).rstrip("/")

    def get_status(self) -> ToolStatus:
        return ToolStatus.AVAILABLE if self._get_api_key() else ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        prompt = str(inputs.get("prompt") or "")
        for message in inputs.get("messages") or []:
            content = message.get("content")
            if isinstance(content, str):
                prompt += content
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        prompt += str(item.get("text") or "")
        # Rough placeholder estimate for planning only.
        return round(max(1, len(prompt)) / 1000 * 0.01, 4)

    @staticmethod
    def _image_to_data_url(path_str: str) -> str:
        path = Path(path_str)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {path_str}")
        mime_type, _ = mimetypes.guess_type(path.name)
        mime_type = mime_type or "application/octet-stream"
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"

    def _build_messages(self, inputs: dict[str, Any]) -> list[dict[str, Any]]:
        if inputs.get("messages"):
            return list(inputs["messages"])

        content: list[dict[str, Any]] = []
        for image_url in inputs.get("image_urls") or []:
            content.append({"type": "image_url", "image_url": {"url": image_url}})
        for image_path in inputs.get("image_paths") or []:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": self._image_to_data_url(str(image_path))},
                }
            )
        if inputs.get("prompt"):
            content.append({"type": "text", "text": inputs["prompt"]})

        if not content:
            raise ValueError("ark_chat requires either messages or prompt/image inputs")

        messages: list[dict[str, Any]] = []
        if inputs.get("system_prompt"):
            messages.append({"role": "system", "content": inputs["system_prompt"]})
        messages.append({"role": "user", "content": content})
        return messages

    @staticmethod
    def _extract_text(payload: dict[str, Any]) -> str:
        choices = payload.get("choices") or []
        if not choices:
            return ""
        message = choices[0].get("message") or {}
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        parts.append(str(item.get("text") or ""))
                    elif "text" in item:
                        parts.append(str(item.get("text") or ""))
            return "\n".join(part for part in parts if part).strip()
        return ""

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        api_key = self._get_api_key()
        if not api_key:
            return ToolResult(success=False, error="ARK_API_KEY not set. " + self.install_instructions)

        import requests

        start = time.time()
        model = str(inputs.get("model", "doubao-seed-evolving"))

        try:
            messages = self._build_messages(inputs)
            payload: dict[str, Any] = {
                "model": model,
                "messages": messages,
            }
            if inputs.get("temperature") is not None:
                payload["temperature"] = inputs["temperature"]
            if inputs.get("max_tokens") is not None:
                payload["max_tokens"] = inputs["max_tokens"]
            if inputs.get("top_p") is not None:
                payload["top_p"] = inputs["top_p"]

            response = requests.post(
                f"{self._base_url()}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=180,
            )
            response.raise_for_status()
            result_json = response.json()
        except Exception as exc:
            return ToolResult(success=False, error=f"Ark chat failed: {exc}")

        text = self._extract_text(result_json)
        artifacts: list[str] = []

        if inputs.get("output_path"):
            output_path = Path(str(inputs["output_path"]))
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(text, encoding="utf-8")
            artifacts.append(str(output_path))

        if inputs.get("raw_output_path"):
            raw_output_path = Path(str(inputs["raw_output_path"]))
            raw_output_path.parent.mkdir(parents=True, exist_ok=True)
            raw_output_path.write_text(__import__("json").dumps(result_json, ensure_ascii=False, indent=2), encoding="utf-8")
            artifacts.append(str(raw_output_path))

        usage = result_json.get("usage") or {}
        return ToolResult(
            success=True,
            data={
                "provider": self.provider,
                "model": model,
                "text": text,
                "messages": messages,
                "usage": usage,
                "raw_response": result_json,
                "output_path": str(inputs["output_path"]) if inputs.get("output_path") else None,
                "raw_output_path": str(inputs["raw_output_path"]) if inputs.get("raw_output_path") else None,
            },
            artifacts=artifacts,
            cost_usd=self.estimate_cost(inputs),
            duration_seconds=round(time.time() - start, 2),
            model=model,
        )
