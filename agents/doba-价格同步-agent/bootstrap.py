from __future__ import annotations

from pathlib import Path
import sys


def ensure_repo_root_on_path() -> Path:
    current = Path(__file__).resolve().parent
    for candidate in (current, *current.parents):
        if candidate.name == "AI-hermes-agent" and (candidate / "shared").exists():
            repo_root = candidate
            if str(repo_root) not in sys.path:
                sys.path.insert(0, str(repo_root))
            return repo_root
    raise RuntimeError("Unable to locate AI-hermes-agent repository root from current agent path.")

