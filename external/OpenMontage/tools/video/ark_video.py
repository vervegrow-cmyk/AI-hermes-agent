"""Official Seedance 2.0 video generation via Volcengine / BytePlus Ark.

Implements the Ark video task flow:
  POST /contents/generations/tasks
  GET  /contents/generations/tasks/{task_id}

This adapter is registered as ``seedance_ark_video`` so OpenMontage can route
official Seedance traffic away from fal.ai when ARK_API_KEY is available.
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
from tools.video._shared import probe_output


def _deep_get(value: Any, keys: tuple[str, ...]) -> Any:
    if not isinstance(value, dict):
        return None
    for key in keys:
        if key in value:
            return value[key]
    return None


def _deep_get_video_url(value: Any) -> str | None:
    if isinstance(value, str):
        if value.startswith(("http://", "https://")) and any(
            token in value.lower() for token in (".mp4", ".mov", ".webm", "video", "download")
        ):
            return value
        return None
    if isinstance(value, dict):
        direct = _deep_get(value, ("video_url", "url", "download_url", "file_url", "output_url"))
        if isinstance(direct, str) and direct.startswith(("http://", "https://")):
            return direct
        for nested in value.values():
            found = _deep_get_video_url(nested)
            if found:
                return found
    if isinstance(value, list):
        for item in value:
            found = _deep_get_video_url(item)
            if found:
                return found
    return None


class SeedanceArkVideo(BaseTool):
    name = "seedance_ark_video"
    version = "0.3.0"
    tier = ToolTier.GENERATE
    capability = "video_generation"
    provider = "seedance"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.API

    dependencies = ["env:ARK_API_KEY"]
    install_instructions = (
        "Set ARK_API_KEY to your official Volcengine / BytePlus Ark API key.\n"
        "Optional: set ARK_BASE_URL to switch region/base URL.\n"
        "Examples:\n"
        "  https://ark.cn-beijing.volces.com/api/v3\n"
        "  https://ark.ap-southeast.bytepluses.com/api/v3"
    )
    agent_skills = ["seedance-2-0", "ai-video-gen"]

    capabilities = ["text_to_video", "image_to_video", "reference_to_video"]
    supports = {
        "text_to_video": True,
        "image_to_video": True,
        "reference_to_video": True,
        "multiple_reference_images": True,
        "reference_image": True,
        "reference_video": True,
        "reference_audio": True,
        "native_audio": True,
        "cinematic_quality": True,
        "aspect_ratio": True,
        "seed": True,
        "task_api": True,
        "official_ark": True,
    }
    best_for = [
        "official Ark-hosted Seedance 2.0 generation without fal.ai",
        "cinematic TikTok / Reels motion shots with native synchronized audio",
        "reference-conditioned Seedance shots using product images",
    ]
    not_good_for = ["offline generation", "zero-config local-only workflows"]
    fallback_tools = ["libtv_video", "seedance_video", "kling_video", "runway_video"]
    quality_score = 0.95

    input_schema = {
        "type": "object",
        "required": ["prompt"],
        "properties": {
            "prompt": {"type": "string"},
            "operation": {
                "type": "string",
                "enum": ["text_to_video", "image_to_video", "reference_to_video"],
                "default": "text_to_video",
            },
            "model_variant": {
                "type": "string",
                "enum": ["mini", "standard", "fast"],
                "default": "mini",
                "description": (
                    "Official Ark Seedance 2.0 model family. "
                    "mini=doubao-seedance-2-0-mini-260615, "
                    "standard=doubao-seedance-2-0-260128, "
                    "fast=doubao-seedance-2-0-fast-260128."
                ),
            },
            "aspect_ratio": {
                "type": "string",
                "enum": ["auto", "21:9", "16:9", "4:3", "1:1", "3:4", "9:16"],
                "default": "9:16",
            },
            "duration": {
                "type": "string",
                "enum": ["auto", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15"],
                "default": "5",
            },
            "resolution": {
                "type": "string",
                "enum": ["480p", "720p", "1080p"],
                "default": "720p",
            },
            "negative_prompt": {"type": "string"},
            "seed": {"type": "integer"},
            "generate_audio": {
                "type": "boolean",
                "default": True,
            },
            "reference_image_url": {"type": "string"},
            "reference_image_path": {"type": "string"},
            "reference_image_urls": {"type": "array", "items": {"type": "string"}},
            "reference_image_paths": {"type": "array", "items": {"type": "string"}},
            "reference_video_urls": {"type": "array", "items": {"type": "string"}},
            "reference_audio_urls": {"type": "array", "items": {"type": "string"}},
            "output_path": {"type": "string"},
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=512, vram_mb=0, disk_mb=500, network_required=True
    )
    retry_policy = RetryPolicy(max_retries=2, retryable_errors=["rate_limit", "timeout", "429", "503"])
    idempotency_key_fields = ["prompt", "operation", "model_variant", "duration", "seed"]
    side_effects = ["writes video file to output_path", "calls Ark video task API"]
    user_visible_verification = ["Watch generated clip and confirm Seedance 2.0 motion quality"]

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
        variant = str(inputs.get("model_variant", "mini"))
        duration = str(inputs.get("duration", "5"))
        secs = 5 if duration == "auto" else int(duration)
        rate = 0.18 if variant == "mini" else (0.24 if variant == "fast" else 0.30)
        return round(rate * secs, 2)

    def estimate_runtime(self, inputs: dict[str, Any]) -> float:
        variant = str(inputs.get("model_variant", "mini"))
        if variant == "fast":
            return 75.0
        if variant == "mini":
            return 105.0
        return 150.0

    @staticmethod
    def _local_to_data_uri(path_str: str) -> str:
        path = Path(path_str)
        if not path.exists():
            raise FileNotFoundError(f"Reference asset not found: {path_str}")
        mime_type, _ = mimetypes.guess_type(path.name)
        mime_type = mime_type or "application/octet-stream"
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"

    @staticmethod
    def _append_media(
        content: list[dict[str, Any]],
        media_type: str,
        urls: list[str],
        role: str | None = None,
    ) -> None:
        for url in urls:
            item: dict[str, Any] = {"type": media_type, media_type: {"url": url}}
            if role:
                item["role"] = role
            content.append(item)

    def _resolve_model(self, variant: str) -> str:
        models = {
            "mini": "doubao-seedance-2-0-mini-260615",
            "standard": "doubao-seedance-2-0-260128",
            "fast": "doubao-seedance-2-0-fast-260128",
        }
        return models[variant]

    def _build_payload(self, inputs: dict[str, Any]) -> dict[str, Any]:
        operation = str(inputs.get("operation", "text_to_video"))
        variant = str(inputs.get("model_variant", "mini"))
        prompt = str(inputs["prompt"]).strip()
        if not prompt:
            raise ValueError("prompt is required")

        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        image_urls = list(inputs.get("reference_image_urls") or [])
        image_paths = list(inputs.get("reference_image_paths") or [])
        if inputs.get("reference_image_url"):
            image_urls.insert(0, str(inputs["reference_image_url"]))
        if inputs.get("reference_image_path"):
            image_paths.insert(0, str(inputs["reference_image_path"]))

        resolved_image_urls = image_urls + [self._local_to_data_uri(path) for path in image_paths]
        if operation == "image_to_video":
            if not resolved_image_urls:
                raise ValueError("image_to_video requires reference_image_url or reference_image_path")
            resolved_image_urls = resolved_image_urls[:1]
        elif operation == "reference_to_video" and len(resolved_image_urls) > 9:
            raise ValueError(f"reference_to_video accepts at most 9 images; got {len(resolved_image_urls)}")

        reference_video_urls = list(inputs.get("reference_video_urls") or [])
        reference_audio_urls = list(inputs.get("reference_audio_urls") or [])
        if len(reference_video_urls) > 3:
            raise ValueError(f"reference_to_video accepts at most 3 reference videos; got {len(reference_video_urls)}")
        if len(reference_audio_urls) > 3:
            raise ValueError(f"reference_to_video accepts at most 3 reference audio clips; got {len(reference_audio_urls)}")

        if operation == "image_to_video":
            self._append_media(content, "image_url", resolved_image_urls[:1])
        else:
            self._append_media(content, "image_url", resolved_image_urls, role="reference_image")
        self._append_media(content, "video_url", reference_video_urls, role="reference_video")
        self._append_media(content, "audio_url", reference_audio_urls, role="reference_audio")

        payload: dict[str, Any] = {
            "model": self._resolve_model(variant),
            "content": content,
            "generate_audio": bool(inputs.get("generate_audio", True)),
            "watermark": False,
        }
        resolution = str(inputs.get("resolution", "720p"))
        if resolution:
            payload["resolution"] = resolution
        aspect_ratio = str(inputs.get("aspect_ratio", "9:16"))
        if aspect_ratio != "auto":
            payload["ratio"] = aspect_ratio
        duration = str(inputs.get("duration", "5"))
        payload["duration"] = 11 if duration == "auto" else int(duration)
        if inputs.get("negative_prompt"):
            payload["negative_prompt"] = str(inputs["negative_prompt"])
        if inputs.get("seed") is not None:
            payload["seed"] = int(inputs["seed"])
        return payload

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        api_key = self._get_api_key()
        if not api_key:
            return ToolResult(success=False, error="ARK_API_KEY not set. " + self.install_instructions)

        import requests

        start = time.time()
        base_url = self._base_url()
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            payload = self._build_payload(inputs)
        except Exception as exc:
            return ToolResult(success=False, error=f"Seedance Ark payload build failed: {exc}")

        try:
            submit = requests.post(
                f"{base_url}/contents/generations/tasks",
                headers=headers,
                json=payload,
                timeout=90,
            )
            if not submit.ok:
                try:
                    submit_error = submit.json()
                except Exception:
                    submit_error = {"status_code": submit.status_code, "text": submit.text[:500]}
                error_meta = submit_error.get("error") if isinstance(submit_error, dict) else {}
                error_code = str(_deep_get(error_meta, ("code",)) or "")
                error_message = str(_deep_get(error_meta, ("message",)) or submit_error)
                if error_code == "ModelNotOpen":
                    return ToolResult(
                        success=False,
                        error=(
                            f"Seedance Ark model {payload['model']} is not activated for this Ark account. "
                            "This account has already been observed to work with "
                            "`doubao-seedance-2-0-mini-260615`, so prefer `model_variant=mini` "
                            "unless you have separately opened the standard/fast variants. "
                            f"Raw response: {error_message}"
                        ),
                    )
                if error_code == "AuthenticationError":
                    return ToolResult(
                        success=False,
                        error=(
                            "Seedance Ark authentication failed. Check ARK_API_KEY and ARK_BASE_URL. "
                            f"Raw response: {error_message}"
                        ),
                    )
                return ToolResult(
                    success=False,
                    error=f"Seedance Ark submit failed ({submit.status_code}): {submit_error}",
                )
            submit_payload = submit.json()
            task_id = (
                submit_payload.get("id")
                or submit_payload.get("task_id")
                or _deep_get(submit_payload.get("data"), ("id", "task_id"))
            )
            if not task_id:
                return ToolResult(
                    success=False,
                    error=f"Seedance Ark submit succeeded but no task id was returned: {submit_payload}",
                )

            deadline = time.time() + 1800
            last_payload: dict[str, Any] = {}
            while time.time() < deadline:
                poll = requests.get(
                    f"{base_url}/contents/generations/tasks/{task_id}",
                    headers=headers,
                    timeout=60,
                )
                poll.raise_for_status()
                last_payload = poll.json()
                status = str(
                    last_payload.get("status")
                    or _deep_get(last_payload.get("data"), ("status",))
                    or ""
                ).lower()
                video_url = _deep_get_video_url(last_payload)
                if video_url:
                    output_path = Path(inputs.get("output_path", "seedance_ark_output.mp4"))
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    download = requests.get(video_url, timeout=300)
                    download.raise_for_status()
                    output_path.write_bytes(download.content)
                    return ToolResult(
                        success=True,
                        data={
                            "provider": "seedance",
                            "tool": self.name,
                            "model": payload["model"],
                            "task_id": task_id,
                            "operation": str(inputs.get("operation", "text_to_video")),
                            "prompt": str(inputs["prompt"]),
                            "base_url": base_url,
                            "source_url": video_url,
                            "output": str(output_path),
                            "output_path": str(output_path),
                            **probe_output(output_path),
                        },
                        artifacts=[str(output_path)],
                        cost_usd=self.estimate_cost(inputs),
                        duration_seconds=round(time.time() - start, 2),
                        seed=payload.get("seed"),
                        model=str(payload["model"]),
                    )
                if status in {"failed", "error", "cancelled", "canceled"}:
                    return ToolResult(
                        success=False,
                        error=f"Seedance Ark generation failed for task_id={task_id}: {last_payload}",
                    )
                time.sleep(8)

            return ToolResult(
                success=False,
                error=f"Seedance Ark generation timed out for task_id={task_id}. Last payload: {last_payload}",
            )
        except Exception as exc:
            return ToolResult(success=False, error=f"Seedance Ark video generation failed: {exc}")
