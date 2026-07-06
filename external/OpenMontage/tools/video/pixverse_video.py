"""PixVerse video generation via the official PixVerse API."""

from __future__ import annotations

import time
import uuid
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


class PixVerseVideo(BaseTool):
    name = "pixverse_video"
    version = "0.1.0"
    tier = ToolTier.GENERATE
    capability = "video_generation"
    provider = "pixverse"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.API

    dependencies = []
    install_instructions = (
        "Set PIXVERSE_API_KEY to your PixVerse API key.\n"
        "  PixVerse API credits are separate from the web app membership."
    )
    agent_skills = ["ai-video-gen"]

    capabilities = ["text_to_video", "image_to_video"]
    supports = {
        "text_to_video": True,
        "image_to_video": True,
        "aspect_ratio": True,
        "seed": True,
    }
    best_for = [
        "direct PixVerse text-to-video generation",
        "direct PixVerse image-to-video generation",
        "teams already buying PixVerse API credits",
    ]
    not_good_for = ["offline generation"]
    fallback_tools = ["kling_video", "vidu_video", "veo_video"]

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
                "enum": ["v6", "v5.5", "v5"],
                "default": "v6",
            },
            "duration": {
                "type": "integer",
                "enum": [5, 8],
                "default": 5,
            },
            "quality": {
                "type": "string",
                "enum": ["540p", "720p", "1080p"],
                "default": "720p",
            },
            "aspect_ratio": {
                "type": "string",
                "enum": ["16:9", "9:16", "1:1"],
                "default": "16:9",
            },
            "motion_mode": {
                "type": "string",
                "enum": ["normal", "fast"],
                "default": "normal",
            },
            "camera_movement": {"type": "string"},
            "negative_prompt": {"type": "string"},
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
    side_effects = ["writes video file to output_path", "calls PixVerse API"]
    user_visible_verification = ["Watch generated clip for prompt adherence and motion quality"]

    def _get_api_key(self) -> str | None:
        import os

        return os.environ.get("PIXVERSE_API_KEY")

    def get_status(self) -> ToolStatus:
        return ToolStatus.AVAILABLE if self._get_api_key() else ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        quality = str(inputs.get("quality", "720p"))
        duration = int(inputs.get("duration", 5))
        base = {"540p": 0.10, "720p": 0.15, "1080p": 0.25}.get(quality, 0.15)
        return round(base * (duration / 5), 2)

    def estimate_runtime(self, inputs: dict[str, Any]) -> float:
        return 90.0

    @staticmethod
    def _headers(api_key: str) -> dict[str, str]:
        return {
            "API-KEY": api_key,
            "Ai-trace-id": str(uuid.uuid4()),
        }

    def _upload_image(self, api_key: str, image_path: str) -> int:
        import requests

        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        with path.open("rb") as handle:
            response = requests.post(
                "https://app-api.pixverse.ai/openapi/v2/image/upload",
                headers=self._headers(api_key),
                files={"image": (path.name, handle)},
                timeout=120,
            )
        response.raise_for_status()
        payload = response.json()
        if payload.get("ErrCode") != 0:
            raise RuntimeError(f"PixVerse image upload failed: {payload}")
        img_id = payload.get("Resp", {}).get("img_id")
        if img_id is None:
            raise RuntimeError(f"PixVerse image upload returned no img_id: {payload}")
        return int(img_id)

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        api_key = self._get_api_key()
        if not api_key:
            return ToolResult(success=False, error="PIXVERSE_API_KEY not set. " + self.install_instructions)

        import requests

        start = time.time()
        operation = str(inputs.get("operation", "text_to_video"))
        endpoint = "https://app-api.pixverse.ai/openapi/v2/video/text/generate"
        body: dict[str, Any] = {
            "prompt": inputs["prompt"],
            "model": inputs.get("model_variant", "v6"),
            "duration": int(inputs.get("duration", 5)),
            "quality": inputs.get("quality", "720p"),
            "aspect_ratio": inputs.get("aspect_ratio", "16:9"),
            "seed": inputs.get("seed", 0),
        }
        if inputs.get("motion_mode"):
            body["motion_mode"] = inputs["motion_mode"]
        if inputs.get("camera_movement"):
            body["camera_movement"] = inputs["camera_movement"]
        if inputs.get("negative_prompt"):
            body["negative_prompt"] = inputs["negative_prompt"]

        try:
            if operation == "image_to_video":
                endpoint = "https://app-api.pixverse.ai/openapi/v2/video/img/generate"
                if inputs.get("reference_image_path"):
                    body["img_id"] = self._upload_image(api_key, str(inputs["reference_image_path"]))
                elif inputs.get("reference_image_url"):
                    temp_resp = requests.post(
                        "https://app-api.pixverse.ai/openapi/v2/image/upload",
                        headers=self._headers(api_key),
                        data={"image_url": str(inputs["reference_image_url"])},
                        timeout=120,
                    )
                    temp_resp.raise_for_status()
                    temp_payload = temp_resp.json()
                    if temp_payload.get("ErrCode") != 0:
                        return ToolResult(success=False, error=f"PixVerse image upload failed: {temp_payload}")
                    body["img_id"] = temp_payload.get("Resp", {}).get("img_id")
                else:
                    return ToolResult(
                        success=False,
                        error="image_to_video requires reference_image_path or reference_image_url",
                    )

            submit = requests.post(
                endpoint,
                headers={**self._headers(api_key), "Content-Type": "application/json"},
                json=body,
                timeout=60,
            )
            submit.raise_for_status()
            submit_payload = submit.json()
            if submit_payload.get("ErrCode") != 0:
                return ToolResult(success=False, error=f"PixVerse generation failed: {submit_payload}")
            video_id = submit_payload.get("Resp", {}).get("video_id")
            if video_id is None:
                return ToolResult(success=False, error=f"No video_id in PixVerse response: {submit_payload}")

            deadline = time.time() + 900
            last_payload: dict[str, Any] = {}
            status_url = f"https://app-api.pixverse.ai/openapi/v2/video/result/{video_id}"
            while time.time() < deadline:
                poll = requests.get(status_url, headers=self._headers(api_key), timeout=60)
                poll.raise_for_status()
                last_payload = poll.json()
                if last_payload.get("ErrCode") != 0:
                    return ToolResult(success=False, error=f"PixVerse status failed: {last_payload}")
                resp = last_payload.get("Resp", {})
                status = int(resp.get("status", 0))
                if status == 1 and resp.get("url"):
                    output_path = Path(inputs.get("output_path", "pixverse_output.mp4"))
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    download = requests.get(resp["url"], timeout=180)
                    download.raise_for_status()
                    output_path.write_bytes(download.content)
                    return ToolResult(
                        success=True,
                        data={
                            "provider": "pixverse",
                            "model": body["model"],
                            "video_id": video_id,
                            "operation": operation,
                            "prompt": inputs["prompt"],
                            "output": str(output_path),
                            "output_path": str(output_path),
                            "source_url": resp["url"],
                            **probe_output(output_path),
                        },
                        artifacts=[str(output_path)],
                        cost_usd=self.estimate_cost(inputs),
                        duration_seconds=round(time.time() - start, 2),
                        seed=inputs.get("seed"),
                        model=str(body["model"]),
                    )
                if status in {7, 8}:
                    return ToolResult(success=False, error=f"PixVerse generation failed with status={status}: {resp}")
                time.sleep(4)

            return ToolResult(
                success=False,
                error=f"PixVerse generation timed out for video_id={video_id}. Last payload: {last_payload}",
            )
        except Exception as exc:
            return ToolResult(success=False, error=f"PixVerse generation failed: {exc}")
