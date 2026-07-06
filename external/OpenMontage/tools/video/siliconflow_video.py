"""SiliconFlow video generation via the official SiliconFlow API.

Supports text-to-video through SiliconFlow's Wan-AI endpoints.
"""

from __future__ import annotations

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


def _extract_first_url(value: Any) -> str | None:
    if isinstance(value, str):
        if value.startswith(("http://", "https://")) and value.lower().endswith((".mp4", ".mov", ".webm", ".mkv")):
            return value
        return None
    if isinstance(value, dict):
        for key in ("url", "video_url", "download_url", "file_url"):
            nested = value.get(key)
            if isinstance(nested, str) and nested.startswith(("http://", "https://")):
                return nested
        for nested in value.values():
            found = _extract_first_url(nested)
            if found:
                return found
        return None
    if isinstance(value, list):
        for item in value:
            found = _extract_first_url(item)
            if found:
                return found
    return None


class SiliconFlowVideo(BaseTool):
    name = "siliconflow_video"
    version = "0.1.0"
    tier = ToolTier.GENERATE
    capability = "video_generation"
    provider = "siliconflow"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.API

    dependencies = []
    install_instructions = (
        "Set SILICONFLOW_API_KEY to your SiliconFlow API key.\n"
        "  Get one from the SiliconFlow console."
    )
    agent_skills = ["ai-video-gen"]

    capabilities = ["text_to_video"]
    supports = {
        "text_to_video": True,
        "aspect_ratio": True,
        "seed": True,
    }
    best_for = [
        "direct Wan-AI video generation on SiliconFlow",
        "teams with prepaid SiliconFlow balance",
        "avoiding third-party gateway lock-in for Wan models",
    ]
    not_good_for = ["image_to_video until SiliconFlow payload details are validated here"]
    fallback_tools = ["wan_video", "seedance_video", "veo_video"]

    input_schema = {
        "type": "object",
        "required": ["prompt"],
        "properties": {
            "prompt": {"type": "string"},
            "operation": {
                "type": "string",
                "enum": ["text_to_video"],
                "default": "text_to_video",
            },
            "model_variant": {
                "type": "string",
                "enum": [
                    "Wan-AI/Wan2.2-T2V-A14B",
                    "Wan-AI/Wan2.1-T2V-14B-720P",
                    "Wan-AI/Wan2.1-T2V-14B-720P-Turbo",
                ],
                "default": "Wan-AI/Wan2.2-T2V-A14B",
            },
            "aspect_ratio": {
                "type": "string",
                "enum": ["16:9", "9:16", "1:1"],
                "default": "16:9",
            },
            "image_size": {
                "type": "string",
                "enum": ["1280x720", "720x1280", "960x960"],
                "description": "Optional explicit size. Overrides aspect_ratio mapping.",
            },
            "negative_prompt": {"type": "string"},
            "seed": {"type": "integer"},
            "output_path": {"type": "string"},
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=512, vram_mb=0, disk_mb=500, network_required=True
    )
    retry_policy = RetryPolicy(max_retries=2, retryable_errors=["rate_limit", "timeout", "503"])
    idempotency_key_fields = ["prompt", "model_variant", "aspect_ratio", "seed"]
    side_effects = ["writes video file to output_path", "calls SiliconFlow API"]
    user_visible_verification = ["Watch generated clip for motion coherence and model fit"]

    def _get_api_key(self) -> str | None:
        import os

        return os.environ.get("SILICONFLOW_API_KEY")

    def get_status(self) -> ToolStatus:
        return ToolStatus.AVAILABLE if self._get_api_key() else ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        variant = str(inputs.get("model_variant", "Wan-AI/Wan2.2-T2V-A14B"))
        if "Turbo" in variant:
            return 0.12
        if "2.2" in variant:
            return 0.20
        return 0.15

    def estimate_runtime(self, inputs: dict[str, Any]) -> float:
        return 90.0

    @staticmethod
    def _image_size(inputs: dict[str, Any]) -> str:
        explicit = inputs.get("image_size")
        if explicit:
            return str(explicit)
        return {
            "16:9": "1280x720",
            "9:16": "720x1280",
            "1:1": "960x960",
        }.get(str(inputs.get("aspect_ratio", "16:9")), "1280x720")

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        api_key = self._get_api_key()
        if not api_key:
            return ToolResult(success=False, error="SILICONFLOW_API_KEY not set. " + self.install_instructions)

        import requests

        start = time.time()
        payload: dict[str, Any] = {
            "model": inputs.get("model_variant", "Wan-AI/Wan2.2-T2V-A14B"),
            "prompt": inputs["prompt"],
            "image_size": self._image_size(inputs),
        }
        if inputs.get("negative_prompt"):
            payload["negative_prompt"] = inputs["negative_prompt"]
        if inputs.get("seed") is not None:
            payload["seed"] = inputs["seed"]

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            submit = requests.post(
                "https://api.siliconflow.com/v1/video/submit",
                headers=headers,
                json=payload,
                timeout=30,
            )
            submit.raise_for_status()
            submit_data = submit.json()
            request_id = submit_data.get("requestId") or submit_data.get("request_id")
            if not request_id:
                return ToolResult(success=False, error=f"No requestId in SiliconFlow response: {submit_data}")

            deadline = time.time() + 900
            last_payload: dict[str, Any] = {}
            while time.time() < deadline:
                poll = requests.post(
                    "https://api.siliconflow.com/v1/video/status",
                    headers=headers,
                    json={"requestId": request_id},
                    timeout=30,
                )
                poll.raise_for_status()
                last_payload = poll.json()
                status_text = str(
                    last_payload.get("status")
                    or last_payload.get("state")
                    or last_payload.get("data", {}).get("status")
                    or ""
                ).lower()
                video_url = _extract_first_url(last_payload)
                if video_url:
                    output_path = Path(inputs.get("output_path", "siliconflow_output.mp4"))
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    download = requests.get(video_url, timeout=180)
                    download.raise_for_status()
                    output_path.write_bytes(download.content)
                    return ToolResult(
                        success=True,
                        data={
                            "provider": "siliconflow",
                            "model": payload["model"],
                            "request_id": request_id,
                            "prompt": inputs["prompt"],
                            "image_size": payload["image_size"],
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
                if status_text in {"failed", "error", "cancelled", "canceled"}:
                    return ToolResult(
                        success=False,
                        error=f"SiliconFlow video generation failed: {last_payload}",
                    )
                time.sleep(5)

            return ToolResult(
                success=False,
                error=f"SiliconFlow video generation timed out for requestId={request_id}. Last payload: {last_payload}",
            )
        except Exception as exc:
            return ToolResult(success=False, error=f"SiliconFlow video generation failed: {exc}")
