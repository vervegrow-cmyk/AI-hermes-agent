from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from models.price_sync import PriceSyncBatch


class JsonStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> Any:
        if not self.path.exists():
            return None
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, payload: Any) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


class SyncRepository:
    def __init__(self, root: Path | None = None) -> None:
        base = root or Path(__file__).resolve().parents[1] / "runtime"
        self.root = base
        self.batch_store = JsonStore(base / "batches.json")
        self.state_store = JsonStore(base / "state.json")

    def save_batch(self, batch: PriceSyncBatch) -> None:
        payload = self.batch_store.load() or {}
        payload[batch.batch_id] = batch.model_dump(mode="json")
        self.batch_store.save(payload)

    def get_batch(self, batch_id: str) -> dict[str, Any] | None:
        payload = self.batch_store.load() or {}
        return payload.get(batch_id)

    def save_state(self, key: str, state: dict[str, Any]) -> None:
        payload = self.state_store.load() or {}
        payload[key] = state
        self.state_store.save(payload)

    def get_state(self, key: str) -> dict[str, Any] | None:
        payload = self.state_store.load() or {}
        return payload.get(key)

    def list_states(self) -> dict[str, Any]:
        return self.state_store.load() or {}
