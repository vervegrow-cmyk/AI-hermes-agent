from __future__ import annotations

import sys
from pathlib import Path

AGENT_ROOT = Path(__file__).resolve().parent
REPO_ROOT = AGENT_ROOT.parents[1]

for path in (REPO_ROOT, AGENT_ROOT):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)
