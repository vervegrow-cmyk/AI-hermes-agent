from __future__ import annotations

from models.price_sync import GigaPriceSnapshot
from service.giga_client import GigaClient


class GigaPriceSource:
    def __init__(self, client: GigaClient | None = None) -> None:
        self.client = client or GigaClient()

    def load(
        self,
        *,
        store_name: str,
        sync_scope: str,
        updated_since: str = "",
        snapshots_override: list[GigaPriceSnapshot] | list[dict] | None = None,
    ) -> list[GigaPriceSnapshot]:
        return self.client.list_price_snapshots(
            store_name=store_name,
            sync_scope=sync_scope,
            updated_since=updated_since,
            snapshots_override=snapshots_override,
        )
