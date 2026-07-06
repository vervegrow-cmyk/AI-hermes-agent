import json
import sys
from pathlib import Path

import pytest

AGENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = AGENT_ROOT.parents[1]

for path in (REPO_ROOT, AGENT_ROOT):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


def load_fixture(name: str):
    return json.loads((AGENT_ROOT / "tests" / "fixtures" / name).read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _safe_shopify_test_mode(monkeypatch):
    from shared.config.settings import get_settings

    monkeypatch.setenv("SHOPIFY_PILOT_CREATE_APPROVED", "false")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
