from __future__ import annotations

import subprocess
from pathlib import Path

from shared.config import get_settings


class OpenCLIClient:
    def __init__(
        self,
        *,
        wrapper_script: str | Path | None = None,
        root_dir: str | Path | None = None,
    ) -> None:
        settings = get_settings()
        self.wrapper_script = Path(wrapper_script or settings.opencli_cli).resolve()
        self.root_dir = Path(root_dir or settings.opencli_root).resolve()

    def _run(
        self,
        args: list[str],
        *,
        timeout_seconds: float = 300.0,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        if not self.root_dir.exists():
            raise FileNotFoundError(f"OpenCLI root does not exist: {self.root_dir}")
        if not self.wrapper_script.exists():
            raise FileNotFoundError(f"OpenCLI wrapper does not exist: {self.wrapper_script}")

        return subprocess.run(
            ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", str(self.wrapper_script), *args],
            cwd=str(self.root_dir),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=check,
            timeout=timeout_seconds,
        )

    def version(self) -> str:
        result = self._run(["--version"])
        return result.stdout.strip()

    def list_commands(self) -> str:
        result = self._run(["list"])
        return result.stdout

    def doctor(self) -> dict[str, str | int]:
        result = self._run(["doctor"])
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }

    def run_command(
        self,
        args: list[str],
        *,
        timeout_seconds: float = 300.0,
        check: bool = True,
    ) -> dict[str, str | int | list[str]]:
        result = self._run(args, timeout_seconds=timeout_seconds, check=check)
        return {
            "args": args,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
