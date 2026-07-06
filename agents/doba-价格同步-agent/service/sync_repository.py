from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from models.price_sync import PriceSyncBatch


class JsonStore:
    def __init__(self, path: Path, default_value: Any) -> None:
        self.path = path
        self.default_value = default_value

    def load(self) -> Any:
        if not self.path.exists():
            return self.default_value
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, payload: Any) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


class SyncRepository:
    def __init__(self, root: Path | None = None) -> None:
        base = root or Path(__file__).resolve().parents[1] / "runtime"
        self.root = base
        self.batch_store = JsonStore(base / "batches.json", {})
        self.state_store = JsonStore(base / "state.json", {})

    def ensure_runtime_layout(self) -> None:
        (self.root / "reports").mkdir(parents=True, exist_ok=True)
        (self.root / "logs").mkdir(parents=True, exist_ok=True)
        (self.root / "checkpoints").mkdir(parents=True, exist_ok=True)
        for path, default_value in (
            (self.root / "batches.json", {}),
            (self.root / "state.json", {}),
            (self.root / "mappings.json", []),
            (self.root / "mapping_template.json", []),
        ):
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(default_value, ensure_ascii=True, indent=2), encoding="utf-8")

    def save_batch(self, batch: PriceSyncBatch) -> None:
        payload = self.batch_store.load()
        payload[batch.batch_id] = batch.model_dump(mode="json")
        self.batch_store.save(payload)

    def get_batch(self, batch_id: str) -> dict[str, Any] | None:
        payload = self.batch_store.load()
        return payload.get(batch_id)

    def save_state(self, key: str, state: dict[str, Any]) -> None:
        payload = self.state_store.load()
        payload[key] = state
        self.state_store.save(payload)

    def get_state(self, key: str) -> dict[str, Any] | None:
        payload = self.state_store.load()
        return payload.get(key)

    def list_states(self) -> dict[str, Any]:
        return self.state_store.load()
