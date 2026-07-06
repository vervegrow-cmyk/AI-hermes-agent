"""LibTV video provider wrapper via external libtv-skills scripts."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from tools._libtv.client import LibTVClient, LibTVError
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


class LibTVVideo(BaseTool):
    name = "libtv_video"
    version = "0.1.0"
    tier = ToolTier.GENERATE
    capability = "video_generation"
    provider = "libtv"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.API

    dependencies = []
    install_instructions = (
        "Install the official LibTV CLI and set LIBTV_CLI_BINARY if it is not on PATH.\n"
        "Then log in once with:\n"
        "  libtv login web --open\n"
        "Optional env vars: LIBTV_CONFIG_DIR, LIBTV_VIDEO_MODEL"
    )
    agent_skills = ["ai-video-gen"]

    capabilities = ["text_to_video", "image_to_video", "reference_conditioned_video"]
    supports = {
        "text_to_video": True,
        "image_conditioning": True,
        "style_notes": True,
        "external_script_backend": True,
    }
    best_for = [
        "LibTV-driven action or exaggerated viral ad shots",
        "complex creative beats that need the LibTV session flow",
        "provider integration when libtv-skills is already installed locally",
    ]
    not_good_for = [
        "machines without libtv-skills checked out",
        "silent fallback behavior",
    ]
    fallback_tools = ["seedance_video", "kling_video", "runway_video"]

    input_schema = {
        "type": "object",
        "required": ["prompt"],
        "properties": {
            "prompt": {"type": "string"},
            "duration": {"type": "string", "description": "Desired clip duration hint."},
            "aspect_ratio": {"type": "string", "default": "9:16"},
            "product_images": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional local product images to upload as references.",
            },
            "style_notes": {
                "type": "string",
                "description": "Optional extra style or motion guidance appended to the prompt.",
            },
            "output_dir": {
                "type": "string",
                "description": "Directory where LibTV downloads outputs.",
            },
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=512, vram_mb=0, disk_mb=1000, network_required=True
    )
    retry_policy = RetryPolicy(max_retries=1, retryable_errors=["timeout"])
    idempotency_key_fields = ["prompt", "duration", "aspect_ratio", "product_images", "style_notes"]
    side_effects = ["calls external libtv-skills scripts", "downloads generated files into output_dir"]
    user_visible_verification = ["Review the returned LibTV video for motion quality and product fidelity"]

    def __init__(self) -> None:
        self._client = LibTVClient()

    def get_status(self) -> ToolStatus:
        health = self._client.health_check()
        return ToolStatus.AVAILABLE if health.get("ok") else ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        duration = str(inputs.get("duration") or "5")
        try:
            seconds = int(duration)
        except ValueError:
            seconds = 5
        return round(0.20 * (seconds / 5), 2)

    def estimate_runtime(self, inputs: dict[str, Any]) -> float:
        return 180.0

    @staticmethod
    def _build_prompt(inputs: dict[str, Any]) -> str:
        parts = [str(inputs["prompt"]).strip()]
        if inputs.get("duration"):
            parts.append(f"Target duration: {inputs['duration']} seconds.")
        if inputs.get("aspect_ratio"):
            parts.append(f"Aspect ratio: {inputs['aspect_ratio']}.")
        if inputs.get("style_notes"):
            parts.append(f"Style notes: {inputs['style_notes']}")
        return "\n".join(part for part in parts if part)

    @staticmethod
    def _extract_output_files(download_payload: dict[str, Any]) -> list[str]:
        files: list[str] = []
        for key in ("output_files", "files", "artifacts"):
            value = download_payload.get(key)
            if isinstance(value, list):
                files.extend(str(item) for item in value)
        if not files and download_payload.get("output_dir"):
            out_dir = Path(download_payload["output_dir"])
            if out_dir.exists():
                files.extend(
                    str(path)
                    for path in sorted(out_dir.iterdir())
                    if path.is_file()
                )
        return files

    @staticmethod
    def _pick_video_path(output_files: list[str]) -> str | None:
        for file_path in output_files:
            if Path(file_path).suffix.lower() in {".mp4", ".mov", ".webm", ".mkv"}:
                return file_path
        return output_files[0] if output_files else None

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        health = self._client.health_check()
        if not health.get("ok"):
            return ToolResult(
                success=False,
                error=str(health.get("error")) + ". " + self.install_instructions,
                data={
                    "provider": self.provider,
                    "error": health.get("error"),
                    "session_id": None,
                    "project_url": None,
                    "output_files": [],
                },
            )

        start = time.time()
        output_dir = Path(inputs.get("output_dir", "outputs/libtv_video"))
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            response = self._client.create_video(
                self._build_prompt(inputs),
                files=list(inputs.get("product_images") or []),
                output_dir=output_dir,
                poll_interval=int(inputs.get("poll_interval") or 10),
                timeout=int(inputs.get("timeout") or 1800),
                aspect_ratio=str(inputs.get("aspect_ratio") or "9:16"),
                duration=str(inputs.get("duration") or "10"),
                style_notes=str(inputs.get("style_notes") or ""),
            )
        except LibTVError as exc:
            return ToolResult(
                success=False,
                error=f"LibTV video generation failed: {exc}",
                data={
                    "provider": self.provider,
                    "error": str(exc),
                    "session_id": None,
                    "project_url": None,
                    "output_files": [],
                },
            )

        download_payload = dict(response.get("download") or {})
        download_payload.setdefault("output_dir", response.get("output_dir"))
        output_files = self._extract_output_files(download_payload)
        video_path = self._pick_video_path(output_files)
        session_payload = response.get("session") or {}
        model_name = (
            session_payload.get("model")
            or session_payload.get("engine")
            or "libtv-session"
        )

        return ToolResult(
            success=True,
            data={
                "success": True,
                "provider": self.provider,
                "model": model_name,
                "prompt": inputs["prompt"],
                "session_id": response.get("session_id"),
                "project_uuid": response.get("project_uuid"),
                "node_name": response.get("node_name"),
                "project_url": response.get("project_url"),
                "video_path": video_path,
                "output_files": output_files,
                "output_dir": str(output_dir),
                "session": session_payload,
                "download": download_payload,
                "error": None,
            },
            artifacts=output_files,
            cost_usd=self.estimate_cost(inputs),
            duration_seconds=round(time.time() - start, 2),
            model=model_name,
        )
