"""Thin REST client for a running ComfyUI server.

Handles the full generation cycle: submit workflow, poll for completion,
download artifacts. Used by comfyui_image, comfyui_video, and custom workflow
runners.
"""

from __future__ import annotations

import copy
import json
import os
import random
import time
from pathlib import Path
from typing import Any

import requests


class ComfyUIError(Exception):
    """Raised when ComfyUI returns an error or times out."""


class ComfyUIClient:
    """Client for the ComfyUI REST API."""

    def __init__(self, server_url: str | None = None) -> None:
        self.server_url = (
            server_url
            or os.environ.get("COMFYUI_BASE_URL")
            or os.environ.get("COMFYUI_SERVER_URL")
            or "http://127.0.0.1:8188"
        ).rstrip("/")
        self.default_output_dir = Path(
            os.environ.get("COMFYUI_OUTPUT_DIR", "D:/ComfyUI/output")
        )

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    @property
    def is_default_url(self) -> bool:
        """True if using the fallback URL (user didn't set a base URL env)."""
        return not (
            os.environ.get("COMFYUI_BASE_URL")
            or os.environ.get("COMFYUI_SERVER_URL")
        )

    def health_check(self) -> dict[str, Any]:
        """Return a structured health result for the configured ComfyUI server."""
        try:
            queue_resp = requests.get(f"{self.server_url}/queue", timeout=5)
            queue_resp.raise_for_status()
            return {
                "ok": True,
                "base_url": self.server_url,
                "queue": queue_resp.json(),
            }
        except Exception as exc:
            return {
                "ok": False,
                "base_url": self.server_url,
                "error": f"ComfyUI is not running at {self.server_url}: {exc}",
            }

    def is_available(self) -> bool:
        """Return True if the ComfyUI server is reachable."""
        return bool(self.health_check().get("ok"))

    def unavailable_reason(self) -> str:
        """Human-readable explanation of why the server can't be reached."""
        if self.is_default_url:
            return (
                f"ComfyUI is not running at {self.server_url}.\n"
                f"Set COMFYUI_BASE_URL in your .env file if your server is at a "
                f"different address."
            )
        return f"ComfyUI is not running at {self.server_url}"

    # ------------------------------------------------------------------
    # Model discovery
    # ------------------------------------------------------------------

    def list_models(self) -> dict[str, list[str]]:
        """Query ComfyUI for available models, grouped by type."""
        node_to_key = {
            "CheckpointLoaderSimple": ("ckpt_name", "checkpoints"),
            "UNETLoader": ("unet_name", "diffusion_models"),
            "VAELoader": ("vae_name", "vae"),
            "CLIPLoader": ("clip_name", "clip"),
            "LoraLoaderModelOnly": ("lora_name", "loras"),
        }
        result: dict[str, list[str]] = {}
        for node_class, (field, group) in node_to_key.items():
            try:
                resp = requests.get(
                    f"{self.server_url}/object_info/{node_class}", timeout=10
                )
                resp.raise_for_status()
                data = resp.json()
                options = (
                    data.get(node_class, {})
                    .get("input", {})
                    .get("required", {})
                    .get(field, [[]])[0]
                )
                if isinstance(options, list):
                    result[group] = options
            except Exception:
                result[group] = []
        return result

    def check_models(
        self, required: list[str]
    ) -> tuple[list[str], list[str]]:
        """Check which of *required* model filenames are available."""
        all_models: set[str] = set()
        for names in self.list_models().values():
            all_models.update(names)

        found = [m for m in required if m in all_models]
        missing = [m for m in required if m not in all_models]
        return found, missing

    # ------------------------------------------------------------------
    # Core cycle
    # ------------------------------------------------------------------

    def queue_prompt(self, workflow: dict) -> str:
        """Queue a workflow for execution. Returns the prompt_id."""
        resp = requests.post(
            f"{self.server_url}/prompt",
            json={"prompt": workflow},
            timeout=30,
        )
        try:
            data = resp.json()
        except ValueError:
            data = {}
        if data.get("node_errors"):
            raise ComfyUIError(f"Node errors: {json.dumps(data['node_errors'])}")
        if data.get("error"):
            raise ComfyUIError(f"Prompt error: {json.dumps(data['error'])}")
        resp.raise_for_status()
        prompt_id = data.get("prompt_id")
        if not prompt_id:
            raise ComfyUIError(f"No prompt_id in response: {data}")
        return prompt_id

    def submit(self, workflow: dict) -> str:
        """Backward-compatible alias for queue_prompt()."""
        return self.queue_prompt(workflow)

    def wait_for_history(
        self,
        prompt_id: str,
        *,
        timeout: int = 600,
        interval: int = 5,
    ) -> dict:
        """Block until *prompt_id* finishes. Returns the history entry."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            resp = requests.get(
                f"{self.server_url}/history/{prompt_id}", timeout=10
            )
            resp.raise_for_status()
            history = resp.json()
            if prompt_id in history:
                entry = history[prompt_id]
                status = entry.get("status", {})
                if status.get("status_str") == "error":
                    msgs = status.get("messages", [])
                    raise ComfyUIError(f"Execution error: {msgs}")
                return entry
            time.sleep(interval)
        raise ComfyUIError(
            f"Prompt {prompt_id} did not complete within {timeout}s"
        )

    def poll(
        self,
        prompt_id: str,
        *,
        timeout: int = 600,
        interval: int = 5,
    ) -> dict:
        """Backward-compatible alias for wait_for_history()."""
        return self.wait_for_history(prompt_id, timeout=timeout, interval=interval)

    def download(
        self,
        filename: str,
        subfolder: str,
        dest: Path,
        folder_type: str = "output",
    ) -> Path:
        """Download an output artifact from the ComfyUI server."""
        resp = requests.get(
            f"{self.server_url}/view",
            params={
                "filename": filename,
                "subfolder": subfolder,
                "type": folder_type,
            },
            timeout=120,
        )
        resp.raise_for_status()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(resp.content)
        return dest

    def collect_outputs(
        self,
        history_entry: dict[str, Any],
        output_dir: str | Path | None = None,
    ) -> list[Path]:
        """Download all artifacts described in a history entry into output_dir."""
        outputs = history_entry.get("outputs", {})
        base_dir = Path(output_dir) if output_dir else self.default_output_dir
        base_dir.mkdir(parents=True, exist_ok=True)

        paths: list[Path] = []
        for node_output in outputs.values():
            items = node_output.get("images", []) or node_output.get("gifs", [])
            for item in items:
                paths.append(
                    self.download(
                        item["filename"],
                        item.get("subfolder", ""),
                        base_dir / item["filename"],
                        item.get("type", "output"),
                    )
                )
        return paths

    def upload_image(self, local_path: Path, name: str) -> str:
        """Upload a local image so it can be referenced by LoadImage nodes."""
        with open(local_path, "rb") as f:
            resp = requests.post(
                f"{self.server_url}/upload/image",
                files={"image": (name, f, "image/png")},
                timeout=30,
            )
        resp.raise_for_status()
        return resp.json()["name"]

    # ------------------------------------------------------------------
    # High-level helper
    # ------------------------------------------------------------------

    def generate(
        self,
        workflow: dict,
        output_node: str,
        dest: Path,
        *,
        timeout: int = 600,
        interval: int = 5,
    ) -> list[Path]:
        """Submit -> wait -> download. Returns list of artifact paths."""
        prompt_id = self.queue_prompt(workflow)
        entry = self.wait_for_history(prompt_id, timeout=timeout, interval=interval)

        outputs = entry.get("outputs", {})
        node_output = outputs.get(output_node, {})

        items = node_output.get("images", []) or node_output.get("gifs", [])
        if not items:
            raise ComfyUIError(
                f"No output artifacts on node {output_node}. "
                f"Available nodes: {list(outputs.keys())}"
            )

        paths: list[Path] = []
        for i, item in enumerate(items):
            suffix = Path(item["filename"]).suffix
            if len(items) == 1:
                target = dest
            else:
                target = dest.with_stem(f"{dest.stem}_{i:03d}").with_suffix(suffix)
            self.download(
                item["filename"],
                item.get("subfolder", ""),
                target,
                item.get("type", "output"),
            )
            paths.append(target)
        return paths

    def run_workflow(
        self,
        workflow_path: str | Path,
        replacements: dict[str, dict[str, Any]],
        output_dir: str | Path | None = None,
        *,
        output_node: str | None = None,
        timeout: int = 600,
        interval: int = 5,
    ) -> dict[str, Any]:
        """Load, patch, queue, wait, and collect outputs for a workflow JSON."""
        workflow = self.load_workflow(Path(workflow_path))
        if replacements:
            workflow = self.patch_workflow(workflow, replacements)
        prompt_id = self.queue_prompt(workflow)
        history = self.wait_for_history(prompt_id, timeout=timeout, interval=interval)
        output_files = self.collect_outputs(history, output_dir)
        result: dict[str, Any] = {
            "prompt_id": prompt_id,
            "history": history,
            "output_files": [str(path) for path in output_files],
        }
        if output_node is not None:
            result["output_node"] = output_node
        return result

    # ------------------------------------------------------------------
    # Workflow helpers
    # ------------------------------------------------------------------

    @staticmethod
    def load_workflow(path: Path) -> dict:
        """Load a workflow JSON template from disk."""
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def patch_workflow(
        workflow: dict, patches: dict[str, dict[str, Any]]
    ) -> dict:
        """Deep-copy *workflow* and apply *patches*."""
        w = copy.deepcopy(workflow)
        for node_id, values in patches.items():
            if node_id not in w:
                raise ComfyUIError(
                    f"Node {node_id!r} not found in workflow. "
                    f"Available: {list(w.keys())}"
                )
            for key, val in values.items():
                w[node_id]["inputs"][key] = val
        return w

    @staticmethod
    def random_seed() -> int:
        """Return a random seed suitable for ComfyUI noise nodes."""
        return random.randint(0, 2**32 - 1)
