from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _run(script_name: str) -> None:
    script_path = REPO_ROOT / "scripts" / script_name
    subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(REPO_ROOT),
        check=True,
    )


def main() -> None:
    for script_name in (
        "register_openhands_mcp.py",
        "register_openhands_yt_dlp_mcp.py",
        "register_openhands_opencli_mcp.py",
        "register_openhands_browser_harness_mcp.py",
    ):
        _run(script_name)


if __name__ == "__main__":
    main()
