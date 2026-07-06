from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from shared.config import get_settings


class AgentReachClient:
    def __init__(
        self,
        *,
        root_dir: str | Path | None = None,
        python_executable: str | None = None,
        cli_executable: str | None = None,
    ) -> None:
        settings = get_settings()
        self.root_dir = Path(root_dir or settings.agent_reach_root).resolve()
        self.python_executable = python_executable or settings.agent_reach_python
        self.cli_executable = cli_executable or settings.agent_reach_cli

    @property
    def _venv_scripts_dir(self) -> Path:
        if self.cli_executable.endswith(".exe"):
            return Path(self.cli_executable).resolve().parent
        return Path(self.python_executable).resolve().parent

    def _build_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env["PATH"] = f"{self._venv_scripts_dir}{os.pathsep}{env.get('PATH', '')}"
        env.setdefault("PYTHONIOENCODING", "utf-8")
        return env

    def _run(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        if not self.root_dir.exists():
            raise FileNotFoundError(f"Agent Reach root does not exist: {self.root_dir}")

        cli_path = Path(self.cli_executable)
        if not cli_path.is_absolute():
            cli_path = self._venv_scripts_dir / self.cli_executable

        return subprocess.run(
            [str(cli_path), *args],
            cwd=str(self.root_dir),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
            env=self._build_env(),
        )

    def version(self) -> str:
        result = self._run(["version"])
        return result.stdout.strip()

    def doctor(self) -> dict[str, Any]:
        result = self._run(["doctor", "--json"])
        return json.loads(result.stdout)

    def check_update(self) -> dict[str, Any]:
        result = self._run(["check-update", "--json"])
        return json.loads(result.stdout)

    def transcribe(
        self,
        source: str,
        *,
        provider: str = "auto",
        output_path: str | Path | None = None,
    ) -> str:
        args = ["transcribe", source, "--provider", provider]
        if output_path is not None:
            args.extend(["-o", str(output_path)])
        result = self._run(args)
        return result.stdout
