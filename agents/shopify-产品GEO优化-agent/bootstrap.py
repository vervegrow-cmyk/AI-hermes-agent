from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

AGENT_ROOT = Path(__file__).resolve().parent
REPO_ROOT = AGENT_ROOT.parents[1]


def ensure_project_paths() -> None:
    for path in (REPO_ROOT, AGENT_ROOT):
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


def load_shared_environment() -> None:
    repo_env = REPO_ROOT / ".env"
    agent_env = AGENT_ROOT / ".env"

    if repo_env.exists():
        load_dotenv(repo_env, override=False, encoding="utf-8")
    if agent_env.exists():
        load_dotenv(agent_env, override=True, encoding="utf-8")

    os.environ.setdefault("AGENT_ROOT", str(AGENT_ROOT))
    os.environ.setdefault("REPO_ROOT", str(REPO_ROOT))


ensure_project_paths()
load_shared_environment()
