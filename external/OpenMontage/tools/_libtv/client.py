"""Wrapper around the official LibTV CLI binary.

The older libtv-skills Python scripts are deprecated upstream. OpenMontage now
talks to LibTV through the `libtv` CLI, which drives LibTV canvas projects,
uploads reference assets, creates video nodes, triggers generation, and
downloads outputs.
"""

from __future__ import annotations

import json
import locale
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any


class LibTVError(Exception):
    """Raised when LibTV integration is misconfigured or a CLI command fails."""


class LibTVClient:
    """Thin wrapper around the official LibTV CLI."""

    PROJECT_CANVAS_BASE = "https://www.liblib.tv/canvas?projectId="

    def __init__(
        self,
        cli_binary: str | Path | None = None,
        *,
        config_dir: str | Path | None = None,
        model_name: str | None = None,
    ) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        self.repo_root = repo_root
        self.cli_binary = self._resolve_cli_binary(cli_binary)
        self.config_dir = self._resolve_optional_path(
            config_dir or os.environ.get("LIBTV_CONFIG_DIR")
        )
        self.model_name = model_name or os.environ.get("LIBTV_VIDEO_MODEL") or "Seedance 2.0 VIP"

    @staticmethod
    def _resolve_optional_path(raw: str | Path | None) -> Path | None:
        if not raw:
            return None
        return Path(raw)

    @staticmethod
    def _resolve_cli_binary(cli_binary: str | Path | None) -> Path:
        candidates: list[Path] = []
        if cli_binary:
            candidates.append(Path(cli_binary))

        env_binary = os.environ.get("LIBTV_CLI_BINARY")
        if env_binary:
            candidates.append(Path(env_binary))

        which = shutil.which("libtv")
        if which:
            candidates.append(Path(which))

        user_default = Path.home() / ".libtv" / "libtv.exe"
        local_default = Path("D:/liblib/libtv-cli-bin/libtv-win-x64/libtv.exe")
        candidates.extend([user_default, local_default])

        for candidate in candidates:
            if candidate.exists():
                return candidate

        return candidates[0] if candidates else local_default

    def _cli_env(self) -> dict[str, str]:
        env = os.environ.copy()
        if self.config_dir:
            env["LIBTV_CONFIG_DIR"] = str(self.config_dir)
        return env

    def health_check(self) -> dict[str, Any]:
        if not self.cli_binary.exists():
            return {
                "ok": False,
                "error": (
                    f"LibTV CLI not found at {self.cli_binary}. "
                    "Install the official CLI and set LIBTV_CLI_BINARY."
                ),
                "cli_binary": str(self.cli_binary),
            }

        version_code, version_stdout, version_stderr = self._run_cli(
            ["--version"], allow_failure=True
        )
        version = version_stdout.strip() if version_code == 0 else None

        code, stdout, stderr = self._run_cli(["account", "info"], allow_failure=True)
        if code != 0:
            detail = stderr.strip() or stdout.strip() or "unknown error"
            if "未登录" in detail or "[401]" in detail or "401" in detail:
                return {
                    "ok": False,
                    "error": (
                        "LibTV CLI is installed but not logged in. "
                        f"Run `{self.cli_binary} login web --open` first."
                    ),
                    "cli_binary": str(self.cli_binary),
                    "version": version,
                    "login_required": True,
                }
            return {
                "ok": False,
                "error": f"LibTV CLI health check failed: {detail}",
                "cli_binary": str(self.cli_binary),
                "version": version,
            }

        payload = self._extract_json(stdout)
        return {
            "ok": True,
            "cli_binary": str(self.cli_binary),
            "version": version,
            "account": payload,
            "config_dir": str(self.config_dir) if self.config_dir else None,
        }

    def _run_cli(
        self,
        args: list[str],
        *,
        cwd: str | Path | None = None,
        allow_failure: bool = False,
    ) -> tuple[int, str, str]:
        proc = subprocess.run(
            [str(self.cli_binary), *args],
            cwd=str(cwd) if cwd else None,
            env=self._cli_env(),
            capture_output=True,
        )
        stdout = self._decode_output(proc.stdout)
        stderr = self._decode_output(proc.stderr)
        if proc.returncode != 0 and not allow_failure:
            detail = stderr.strip() or stdout.strip() or "unknown error"
            raise LibTVError(f"libtv {' '.join(args)} failed: {detail}")
        return proc.returncode, stdout, stderr

    def _spawn_cli(
        self,
        args: list[str],
        *,
        cwd: str | Path | None = None,
    ) -> subprocess.Popen[bytes]:
        return subprocess.Popen(
            [str(self.cli_binary), *args],
            cwd=str(cwd) if cwd else None,
            env=self._cli_env(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    @staticmethod
    def _decode_output(data: bytes | str | None) -> str:
        if data is None:
            return ""
        if isinstance(data, str):
            return data
        encodings = [locale.getpreferredencoding(False), "utf-8", "gbk", "cp936"]
        for encoding in encodings:
            if not encoding:
                continue
            try:
                return data.decode(encoding)
            except UnicodeDecodeError:
                continue
        return data.decode("utf-8", errors="replace")

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any]:
        raw = text.strip()
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        for line in reversed(raw.splitlines()):
            candidate = line.strip()
            if not candidate:
                continue
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue

        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                pass
        return {"raw_stdout": raw}

    @staticmethod
    def _infer_media_type(path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}:
            return "image"
        if suffix in {".mp4", ".mov", ".webm", ".mkv"}:
            return "video"
        if suffix in {".mp3", ".wav", ".m4a"}:
            return "audio"
        raise LibTVError(f"Unsupported LibTV upload file type: {path.suffix}")

    @staticmethod
    def _extract_project_uuid(payload: dict[str, Any]) -> str | None:
        for key in ("uuid", "projectUuid", "projectId"):
            value = payload.get(key)
            if value:
                return str(value)
        project_meta = payload.get("projectMeta")
        if isinstance(project_meta, dict):
            for key in ("uuid", "projectUuid", "projectId", "id"):
                value = project_meta.get(key)
                if value:
                    return str(value)
        data = payload.get("data")
        if isinstance(data, dict):
            for key in ("uuid", "projectUuid", "projectId"):
                value = data.get(key)
                if value:
                    return str(value)
        return None

    @staticmethod
    def _extract_media_urls(payload: Any) -> list[str]:
        urls: list[str] = []

        def walk(value: Any) -> None:
            if isinstance(value, dict):
                for item in value.values():
                    walk(item)
                return
            if isinstance(value, list):
                for item in value:
                    walk(item)
                return
            if isinstance(value, str):
                text = value.strip()
                lower = text.lower()
                if text.startswith("http") and lower.endswith(
                    (".mp4", ".mov", ".webm", ".mkv", ".png", ".jpg", ".jpeg", ".webp", ".zip")
                ):
                    urls.append(text)

        walk(payload)
        seen: set[str] = set()
        unique: list[str] = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique.append(url)
        return unique

    @staticmethod
    def _extract_task_info(payload: dict[str, Any]) -> dict[str, Any]:
        data = payload.get("data")
        if isinstance(data, dict):
            task_info = data.get("taskInfo")
            if isinstance(task_info, dict):
                return task_info
        task_info = payload.get("taskInfo")
        return task_info if isinstance(task_info, dict) else {}

    @staticmethod
    def _payload_indicates_failure(payload: Any) -> bool:
        failure_tokens = ("error", "failed", "接口错误", "未登录", "失败")

        def walk(value: Any) -> bool:
            if isinstance(value, dict):
                return any(walk(item) for item in value.values())
            if isinstance(value, list):
                return any(walk(item) for item in value)
            if isinstance(value, str):
                lower = value.lower()
                return any(token in value or token in lower for token in failure_tokens)
            return False

        return walk(payload)

    @staticmethod
    def _duration_setting(duration_hint: str | int | None) -> int:
        try:
            seconds = int(duration_hint or 5)
        except (TypeError, ValueError):
            seconds = 5
        # Seedance example schema in the CLI docs shows 4-5s.
        return 5 if seconds >= 5 else 4

    @staticmethod
    def _resolution_for_aspect(aspect_ratio: str) -> str:
        return "720p"

    def create_project(self, name: str, *, cwd: str | Path | None = None) -> dict[str, Any]:
        _, stdout, _ = self._run_cli(["project", "create", name], cwd=cwd)
        payload = self._extract_json(stdout)
        project_uuid = self._extract_project_uuid(payload)
        if not project_uuid:
            raise LibTVError(f"libtv project create did not return a project UUID: {payload}")
        return payload

    def use_project(self, project_uuid: str, *, cwd: str | Path | None = None) -> dict[str, Any]:
        _, stdout, _ = self._run_cli(["project", "use", project_uuid], cwd=cwd)
        return self._extract_json(stdout)

    def upload_file(
        self,
        local_path: str | Path,
        node_name: str,
        *,
        cwd: str | Path | None = None,
        project_uuid: str | None = None,
    ) -> dict[str, Any]:
        path = Path(local_path).expanduser()
        if not path.is_absolute():
            path = path.resolve()
        if not path.exists():
            raise LibTVError(f"File not found: {path}")
        args = ["upload", node_name, "-t", self._infer_media_type(path), "--resource", str(path)]
        if project_uuid:
            args.extend(["-p", project_uuid])
        _, stdout, _ = self._run_cli(args, cwd=cwd)
        return self._extract_json(stdout)

    def query_node(
        self,
        node_name: str,
        *,
        cwd: str | Path | None = None,
        project_uuid: str | None = None,
    ) -> dict[str, Any]:
        args = ["node", node_name]
        if project_uuid:
            args.extend(["-p", project_uuid])
        _, stdout, _ = self._run_cli(args, cwd=cwd)
        return self._extract_json(stdout)

    def download_node(
        self,
        node_name: str,
        output_dir: str | Path,
        *,
        cwd: str | Path | None = None,
        project_uuid: str | None = None,
    ) -> dict[str, Any]:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        before = {
            path.name: (path.stat().st_size, path.stat().st_mtime)
            for path in out_dir.glob("*")
            if path.is_file()
        }
        args = ["download", "-n", node_name, "-o", str(out_dir)]
        if project_uuid:
            args.extend(["-p", project_uuid])
        _, stdout, _ = self._run_cli(args, cwd=cwd)
        payload = self._extract_json(stdout)
        after_paths = sorted(
            path
            for path in out_dir.glob("*")
            if path.is_file()
            and (
                path.name not in before
                or before[path.name] != (path.stat().st_size, path.stat().st_mtime)
            )
        )
        if not after_paths:
            after_paths = sorted(
                path
                for path in out_dir.glob("*")
                if path.is_file() and path.suffix.lower() in {".mp4", ".mov", ".webm", ".mkv", ".png", ".jpg", ".jpeg", ".webp", ".zip"}
            )
        payload.setdefault("downloaded", [str(path) for path in after_paths])
        payload.setdefault("output_dir", str(out_dir))
        return payload

    def create_video(
        self,
        prompt: str,
        files: list[str] | None = None,
        output_dir: str | Path | None = None,
        *,
        poll_interval: int = 10,
        timeout: int = 1800,
        aspect_ratio: str = "9:16",
        duration: str | int = "10",
        style_notes: str | None = None,
    ) -> dict[str, Any]:
        health = self.health_check()
        if not health.get("ok"):
            raise LibTVError(str(health.get("error")))

        output_root = Path(output_dir) if output_dir else (self.repo_root / "outputs" / "libtv")
        output_root.mkdir(parents=True, exist_ok=True)
        workspace = output_root / ".libtv_workspace"
        workspace.mkdir(parents=True, exist_ok=True)

        project_name = f"OpenMontage {time.strftime('%Y%m%d_%H%M%S')}"
        project_payload = self.create_project(project_name, cwd=workspace)
        project_uuid = self._extract_project_uuid(project_payload)
        if not project_uuid:
            raise LibTVError(f"Failed to determine project UUID: {project_payload}")
        self.use_project(project_uuid, cwd=workspace)

        reference_names: list[str] = []
        for idx, file_path in enumerate(files or [], 1):
            node_name = f"Reference {idx}"
            self.upload_file(file_path, node_name, cwd=workspace, project_uuid=project_uuid)
            reference_names.append(node_name)

        node_name = "OpenMontage Video"
        node_prompt = prompt
        if style_notes:
            node_prompt = f"{node_prompt}\n\nStyle notes: {style_notes}"

        create_args = [
            "node",
            "create",
            node_name,
            "-p",
            project_uuid,
            "-t",
            "video",
            "--prompt",
            node_prompt,
            "--set",
            f"model={self.model_name}",
            "--set",
            f"modeType={'mixed2video' if reference_names else 'text2video'}",
            "--set",
            "count=1",
            "--set",
            f"ratio={aspect_ratio}",
            "--set",
            f"resolution={self._resolution_for_aspect(aspect_ratio)}",
            "--set",
            f"duration={self._duration_setting(duration)}",
            "--set",
            "enableSound=on",
            "--set",
            "search_enabled=1",
        ]
        for ref_name in reference_names:
            create_args.extend(["--left", ref_name])

        _, stdout, _ = self._run_cli(create_args, cwd=workspace)
        node_payload = self._extract_json(stdout)
        node_key = str(node_payload.get("nodeKey") or node_name)

        run_args = ["node", node_key, "-p", project_uuid, "--run"]
        run_proc = self._spawn_cli(run_args, cwd=workspace)

        deadline = time.time() + timeout
        latest = node_payload
        final_run_stdout = ""
        final_run_stderr = ""
        while time.time() < deadline:
            latest = self.query_node(node_key, cwd=workspace, project_uuid=project_uuid)
            if self._payload_indicates_failure(latest):
                run_proc.kill()
                raise LibTVError(f"LibTV node returned an error payload: {latest}")
            media_urls = self._extract_media_urls(latest)
            task_info = self._extract_task_info(latest)
            status = task_info.get("status")
            loading = bool(task_info.get("loading"))

            if media_urls:
                break
            if status in {3, 4, "failed", "error"}:
                run_proc.kill()
                raise LibTVError(f"LibTV node task failed: {latest}")

            if run_proc.poll() is not None:
                final_run_stdout = self._decode_output(run_proc.stdout.read() if run_proc.stdout else b"")
                final_run_stderr = self._decode_output(run_proc.stderr.read() if run_proc.stderr else b"")
                if run_proc.returncode != 0:
                    detail = final_run_stderr.strip() or final_run_stdout.strip() or "unknown error"
                    raise LibTVError(f"LibTV CLI run command failed: {detail}")
                if not loading and not task_info and not media_urls:
                    # The run command finished but the node still has no task/result yet.
                    # Keep polling for a short grace period instead of failing immediately.
                    pass
            time.sleep(poll_interval)
        else:
            run_proc.kill()
            raise LibTVError(f"LibTV node {node_name} did not finish within {timeout}s")

        if run_proc.poll() is None:
            run_proc.terminate()
            try:
                run_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                run_proc.kill()

        run_output_dir = output_root / project_uuid
        run_output_dir.mkdir(parents=True, exist_ok=True)

        download: dict[str, Any] = {}
        output_files: list[str] = []
        download_deadline = time.time() + 300
        while time.time() < download_deadline:
            download = self.download_node(node_key, run_output_dir, cwd=workspace, project_uuid=project_uuid)
            output_files = list(download.get("downloaded") or [])
            if output_files:
                break
            latest = self.query_node(node_key, cwd=workspace, project_uuid=project_uuid)
            media_urls = self._extract_media_urls(latest)
            if not media_urls:
                time.sleep(10)
                continue
            time.sleep(10)
        else:
            raise LibTVError(
                f"LibTV node finished but no downloadable files were retrieved within 300s: {latest}"
            )

        return {
            "project_uuid": project_uuid,
            "project_url": self.PROJECT_CANVAS_BASE + project_uuid,
            "node_name": node_name,
            "node_key": node_key,
            "node": latest,
            "node_create": node_payload,
            "download": download,
            "output_dir": str(run_output_dir),
            "output_files": output_files,
        }
