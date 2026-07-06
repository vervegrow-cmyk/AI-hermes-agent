"""Vidu video generation via the official Vidu API."""

from __future__ import annotations

import base64
import mimetypes
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


class ViduVideo(BaseTool):
    name = "vidu_video"
    version = "0.1.0"
    tier = ToolTier.GENERATE
    capability = "video_generation"
    provider = "vidu"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.API

    dependencies = []
    install_instructions = (
        "Set VIDU_API_KEY to your Vidu API key.\n"
        "  Vidu authenticates with Authorization: Token <key>."
    )
    agent_skills = ["ai-video-gen"]

    capabilities = ["text_to_video", "image_to_video"]
    supports = {
        "text_to_video": True,
        "image_to_video": True,
        "native_audio": True,
        "aspect_ratio": True,
        "seed": True,
        "reference_image": True,
    }
    best_for = [
        "direct Vidu q3 text-to-video generation",
        "direct Vidu image-to-video generation",
        "teams with paid Vidu API credits",
    ]
    not_good_for = ["offline generation"]
    fallback_tools = ["pixverse_video", "kling_video", "veo_video"]

    input_schema = {
        "type": "object",
        "required": ["prompt"],
        "properties": {
            "prompt": {"type": "string"},
            "operation": {
                "type": "string",
                "enum": ["text_to_video", "image_to_video"],
                "default": "text_to_video",
            },
            "model_variant": {
                "type": "string",
                "enum": [
                    "viduq3-pro",
                    "viduq3-turbo",
                    "viduq3-pro-fast",
                    "viduq2",
                    "viduq2-pro",
                    "viduq2-pro-fast",
                    "viduq2-turbo",
                    "viduq1",
                    "viduq1-classic",
                    "vidu2.0",
                ],
                "default": "viduq3-pro",
            },
            "duration": {"type": "integer", "default": 5},
            "aspect_ratio": {
                "type": "string",
                "enum": ["16:9", "9:16", "3:4", "4:3", "1:1"],
                "default": "9:16",
            },
            "resolution": {
                "type": "string",
                "enum": ["360p", "540p", "720p", "1080p"],
                "default": "720p",
            },
            "audio": {"type": "boolean", "default": True},
            "audio_type": {
                "type": "string",
                "enum": ["all", "speech_only", "sound_effect_only"],
                "default": "all",
            },
            "bgm": {"type": "boolean", "default": False},
            "seed": {"type": "integer"},
            "reference_image_path": {"type": "string"},
            "reference_image_url": {"type": "string"},
            "output_path": {"type": "string"},
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=512, vram_mb=0, disk_mb=500, network_required=True
    )
    retry_policy = RetryPolicy(max_retries=2, retryable_errors=["rate_limit", "timeout", "429"])
    idempotency_key_fields = ["prompt", "operation", "model_variant", "duration", "seed"]
    side_effects = ["writes video file to output_path", "calls Vidu API"]
    user_visible_verification = ["Watch generated clip and verify the chosen Vidu model behavior"]

    def _get_api_key(self) -> str | None:
        import os

        return os.environ.get("VIDU_API_KEY")

    def get_status(self) -> ToolStatus:
        return ToolStatus.AVAILABLE if self._get_api_key() else ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        variant = str(inputs.get("model_variant", "viduq3-pro"))
        duration = int(inputs.get("duration", 5))
        if "q3-pro" in variant:
            return round(0.30 * (duration / 5), 2)
        if "q3" in variant:
            return round(0.22 * (duration / 5), 2)
        return round(0.15 * (duration / 5), 2)

    def estimate_runtime(self, inputs: dict[str, Any]) -> float:
        return 120.0

    @staticmethod
    def _data_uri(path_str: str) -> str:
        path = Path(path_str)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {path_str}")
        mime_type, _ = mimetypes.guess_type(path.name)
        mime_type = mime_type or "application/octet-stream"
        return f"data:{mime_type};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"

    @staticmethod
    def _headers(api_key: str) -> dict[str, str]:
        return {
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/json",
        }

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        api_key = self._get_api_key()
        if not api_key:
            return ToolResult(success=False, error="VIDU_API_KEY not set. " + self.install_instructions)

        import requests

        start = time.time()
        operation = str(inputs.get("operation", "text_to_video"))
        endpoint = "https://api.vidu.com/ent/v2/text2video"
        payload: dict[str, Any] = {
            "model": inputs.get("model_variant", "viduq3-pro"),
            "prompt": inputs["prompt"],
            "duration": int(inputs.get("duration", 5)),
            "aspect_ratio": inputs.get("aspect_ratio", "9:16"),
            "resolution": inputs.get("resolution", "720p"),
            "audio": bool(inputs.get("audio", True)),
            "bgm": bool(inputs.get("bgm", False)),
        }
        if inputs.get("seed") is not None:
            payload["seed"] = inputs["seed"]

        if operation == "image_to_video":
            endpoint = "https://api.vidu.com/ent/v2/img2video"
            if inputs.get("reference_image_url"):
                payload["images"] = [str(inputs["reference_image_url"])]
            elif inputs.get("reference_image_path"):
                payload["images"] = [self._data_uri(str(inputs["reference_image_path"]))]
            else:
                return ToolResult(
                    success=False,
                    error="image_to_video requires reference_image_path or reference_image_url",
                )
            if payload.get("audio"):
                payload["audio_type"] = inputs.get("audio_type", "all")

        try:
            submit = requests.post(
                endpoint,
                headers=self._headers(api_key),
                json=payload,
                timeout=60,
            )
            submit.raise_for_status()
            submit_payload = submit.json()
            task_id = submit_payload.get("task_id")
            if not task_id:
                return ToolResult(success=False, error=f"No task_id in Vidu response: {submit_payload}")

            status_url = f"https://api.vidu.com/ent/v2/tasks/{task_id}/creations"
            deadline = time.time() + 1200
            last_payload: dict[str, Any] = {}
            while time.time() < deadline:
                poll = requests.get(status_url, headers=self._headers(api_key), timeout=60)
                poll.raise_for_status()
                last_payload = poll.json()
                state = str(last_payload.get("state", "")).lower()
                if state == "success":
                    creations = last_payload.get("creations") or []
                    first = creations[0] if creations else {}
                    video_url = first.get("url")
                    if not video_url:
                        return ToolResult(success=False, error=f"Vidu completed without video URL: {last_payload}")
                    output_path = Path(inputs.get("output_path", "vidu_output.mp4"))
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    download = requests.get(video_url, timeout=180)
                    download.raise_for_status()
                    output_path.write_bytes(download.content)
                    return ToolResult(
                        success=True,
                        data={
                            "provider": "vidu",
                            "model": payload["model"],
                            "task_id": task_id,
                            "operation": operation,
                            "prompt": inputs["prompt"],
                            "output": str(output_path),
                            "output_path": str(output_path),
                            "source_url": video_url,
                            **probe_output(output_path),
                        },
                        artifacts=[str(output_path)],
                        cost_usd=self.estimate_cost(inputs),
                        duration_seconds=round(time.time() - start, 2),
                        seed=inputs.get("seed"),
                        model=str(payload["model"]),
                    )
                if state == "failed":
                    return ToolResult(success=False, error=f"Vidu generation failed: {last_payload}")
                time.sleep(5)

            return ToolResult(
                success=False,
                error=f"Vidu generation timed out for task_id={task_id}. Last payload: {last_payload}",
            )
        except Exception as exc:
            return ToolResult(success=False, error=f"Vidu generation failed: {exc}")
