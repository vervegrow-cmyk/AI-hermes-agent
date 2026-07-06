from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from shared.config import get_settings


class YtDlpClient:
    def __init__(
        self,
        *,
        root_dir: str | Path | None = None,
        downloads_dir: str | Path | None = None,
        python_executable: str | None = None,
    ) -> None:
        settings = get_settings()
        self.root_dir = Path(root_dir or settings.yt_dlp_root).resolve()
        self.downloads_dir = Path(downloads_dir or settings.yt_dlp_downloads_dir).resolve()
        self.python_executable = python_executable or settings.yt_dlp_python

    def _run(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        if not self.root_dir.exists():
            raise FileNotFoundError(f"yt-dlp root does not exist: {self.root_dir}")

        return subprocess.run(
            [self.python_executable, "-m", "yt_dlp", *args],
            cwd=str(self.root_dir),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )

    def version(self) -> str:
        result = self._run(["--version"])
        return result.stdout.strip()

    def extract_info(
        self,
        url: str,
        *,
        flat_playlist: bool = True,
        extra_args: list[str] | None = None,
    ) -> dict[str, Any]:
        args = ["--skip-download", "--dump-single-json"]
        if flat_playlist:
            args.append("--flat-playlist")
        if extra_args:
            args.extend(extra_args)
        args.append(url)

        result = self._run(args)
        return json.loads(result.stdout)

    def download(
        self,
        url: str,
        *,
        destination_dir: str | Path | None = None,
        output_template: str | None = None,
        format_selector: str | None = None,
        audio_only: bool = False,
        write_info_json: bool = True,
        write_thumbnail: bool = False,
        extra_args: list[str] | None = None,
    ) -> dict[str, Any]:
        target_dir = Path(destination_dir or self.downloads_dir).resolve()
        target_dir.mkdir(parents=True, exist_ok=True)

        template = output_template or "%(title)s [%(id)s].%(ext)s"
        args = [
            "--no-progress",
            "--newline",
            "--paths",
            f"home:{target_dir}",
            "--output",
            template,
            "--print",
            "after_move:filepath",
        ]
        if format_selector:
            args.extend(["--format", format_selector])
        if audio_only:
            args.extend(["--extract-audio", "--audio-format", "mp3"])
        if write_info_json:
            args.append("--write-info-json")
        if write_thumbnail:
            args.append("--write-thumbnail")
        if extra_args:
            args.extend(extra_args)
        args.append(url)

        result = self._run(args)
        saved_paths = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return {
            "url": url,
            "destination_dir": str(target_dir),
            "saved_paths": saved_paths,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
