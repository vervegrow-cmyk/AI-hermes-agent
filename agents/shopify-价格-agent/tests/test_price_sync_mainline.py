from pathlib import Path
import sys

AGENT_ROOT = Path(__file__).resolve().parents[1]
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from models.price_sync import GigaPriceSnapshot, PriceSyncRequest, ShopifyPriceState, SkuMappingRecord
from service.executor import run_price_sync
from service.giga_client import GigaClient
from service.mapping_repository import MappingRepository
from service.shopify_price_sync_service import ShopifyPriceSyncService
from service.sync_repository import SyncRepository


def _mapping_repo(tmp_path):
    return MappingRepository(path=tmp_path / "mappings.json")


def _sync_repo(tmp_path):
    return SyncRepository(root=tmp_path / "runtime")


def test_dry_run_only_returns_changed_skus_for_incremental(tmp_path):
    sync_repo = _sync_repo(tmp_path)
    mapping_repo = _mapping_repo(tmp_path)
    mappings = [
        SkuMappingRecord(
            store_name="demo-store",
            giga_sku="SKU-1",
            shopify_product_id="prod-1",
            shopify_variant_id="var-1",
            shopify_sku="SHOP-1",
            mapping_status="active",
        ),
        SkuMappingRecord(
            store_name="demo-store",
            giga_sku="SKU-2",
            shopify_product_id="prod-1",
            shopify_variant_id="var-2",
            shopify_sku="SHOP-2",
            mapping_status="active",
        ),
    ]
    snapshots = [
        GigaPriceSnapshot(
            store_name="demo-store",
            giga_product_id="g-1",
            giga_sku="SKU-1",
            supplier_cost=10,
            shipping_cost=2,
            source_updated_at="2026-06-22T10:00:00+00:00",
            raw_hash="hash-1",
        ),
        GigaPriceSnapshot(
            store_name="demo-store",
            giga_product_id="g-1",
            giga_sku="SKU-2",
            supplier_cost=12,
            shipping_cost=2,
            source_updated_at="2026-06-22T10:05:00+00:00",
            raw_hash="hash-2",
        ),
    ]
    sync_repo.save_state(
        "demo-store::SKU-1::var-1",
        {
            "store_name": "demo-store",
            "giga_sku": "SKU-1",
            "shopify_variant_id": "var-1",
            "last_source_hash": "hash-1",
            "last_sync_status": "synced",
            "last_source_updated_at": "2026-06-22T10:00:00+00:00",
        },
    )
    command = PriceSyncRequest(
        store_name="demo-store",
        sync_scope="incremental",
        giga_snapshots=snapshots,
        mappings=mappings,
        shopify_states=[
            ShopifyPriceState(store_name="demo-store", shopify_product_id="prod-1", shopify_variant_id="var-1", current_price=30),
            ShopifyPriceState(store_name="demo-store", shopify_product_id="prod-1", shopify_variant_id="var-2", current_price=15),
        ],
        mode="dry-run",
    )
    batch = run_price_sync(
        command,
        mapping_repository=mapping_repo,
        sync_repository=sync_repo,
        shopify_service=ShopifyPriceSyncService(force_mode="mock"),
    )
    assert batch.processed_count == 1
    assert batch.items[0].giga_sku == "SKU-2"
    assert batch.items[0].shopify_variant_id == "var-2"


def test_apply_updates_only_changed_variants_and_persists_state(tmp_path):
    sync_repo = _sync_repo(tmp_path)
    mapping_repo = _mapping_repo(tmp_path)
    snapshots = [
        GigaPriceSnapshot(
            store_name="demo-store",
            giga_product_id="g-1",
            giga_sku="SKU-1",
            supplier_cost=10,
            shipping_cost=2,
            source_updated_at="2026-06-22T10:00:00+00:00",
            raw_hash="hash-1",
        ),
        GigaPriceSnapshot(
            store_name="demo-store",
            giga_product_id="g-1",
            giga_sku="SKU-2",
            supplier_cost=10,
            shipping_cost=2,
            source_updated_at="2026-06-22T10:01:00+00:00",
            raw_hash="hash-2",
        ),
    ]
    mappings = [
        SkuMappingRecord(store_name="demo-store", giga_sku="SKU-1", shopify_product_id="prod-1", shopify_variant_id="var-1", shopify_sku="SHOP-1", mapping_status="active"),
        SkuMappingRecord(store_name="demo-store", giga_sku="SKU-2", shopify_product_id="prod-1", shopify_variant_id="var-2", shopify_sku="SHOP-2", mapping_status="active"),
    ]
    states = [
        ShopifyPriceState(store_name="demo-store", shopify_product_id="prod-1", shopify_variant_id="var-1", current_price=16),
        ShopifyPriceState(store_name="demo-store", shopify_product_id="prod-1", shopify_variant_id="var-2", current_price=13.5),
    ]
    command = PriceSyncRequest(
        store_name="demo-store",
        sync_scope="full",
        giga_snapshots=snapshots,
        mappings=mappings,
        shopify_states=states,
        mode="apply",
    )
    batch = run_price_sync(
        command,
        mapping_repository=mapping_repo,
        sync_repository=sync_repo,
        shopify_service=ShopifyPriceSyncService(force_mode="mock"),
    )
    assert batch.success_count == 1
    assert any(item.giga_sku == "SKU-1" and item.status == "synced" for item in batch.items)
    assert any(item.giga_sku == "SKU-2" and item.status == "skipped" for item in batch.items)
    saved = sync_repo.get_state("demo-store::SKU-1::var-1")
    assert saved is not None
    assert saved["last_sync_status"] == "synced"
    assert saved["last_source_snapshot"]["shipping_cost"] == 2


def test_duplicate_mapping_goes_to_manual_review(tmp_path):
    sync_repo = _sync_repo(tmp_path)
    mapping_repo = _mapping_repo(tmp_path)
    command = PriceSyncRequest(
        store_name="demo-store",
        sync_scope="full",
        giga_snapshots=[
            GigaPriceSnapshot(
                store_name="demo-store",
                giga_product_id="g-1",
                giga_sku="SKU-1",
                supplier_cost=10,
                shipping_cost=2,
                source_updated_at="2026-06-22T10:00:00+00:00",
                raw_hash="hash-1",
            )
        ],
        mappings=[
            SkuMappingRecord(store_name="demo-store", giga_sku="SKU-1", shopify_product_id="prod-1", shopify_variant_id="var-1", mapping_status="active"),
            SkuMappingRecord(store_name="demo-store", giga_sku="SKU-1", shopify_product_id="prod-2", shopify_variant_id="var-2", mapping_status="active"),
        ],
        shopify_states=[],
        mode="dry-run",
    )
    batch = run_price_sync(
        command,
        mapping_repository=mapping_repo,
        sync_repository=sync_repo,
        shopify_service=ShopifyPriceSyncService(force_mode="mock"),
    )
    assert batch.processed_count == 1
    assert batch.items[0].decision == "manual_review"
    assert "duplicate_source_mapping" in batch.items[0].reason_codes


def test_force_single_sku_recalculate_can_bypass_incremental_cache(tmp_path):
    sync_repo = _sync_repo(tmp_path)
    mapping_repo = _mapping_repo(tmp_path)
    sync_repo.save_state(
        "demo-store::SKU-1::var-1",
        {
            "store_name": "demo-store",
            "giga_sku": "SKU-1",
            "shopify_variant_id": "var-1",
            "last_source_hash": "hash-1",
            "last_sync_status": "synced",
            "last_source_updated_at": "2026-06-22T10:00:00+00:00",
        },
    )
    batch = run_price_sync(
        PriceSyncRequest(
            store_name="demo-store",
            sync_scope="single_sku",
            sku_list=["SKU-1"],
            force_recalculate=True,
            skip_incremental_cache=True,
            giga_snapshots=[
                GigaPriceSnapshot(
                    store_name="demo-store",
                    giga_product_id="g-1",
                    giga_sku="SKU-1",
                    supplier_cost=10,
                    shipping_cost=2,
                    source_updated_at="2026-06-22T10:00:00+00:00",
                    raw_hash="hash-1",
                )
            ],
            mappings=[
                SkuMappingRecord(
                    store_name="demo-store",
                    giga_sku="SKU-1",
                    shopify_product_id="prod-1",
                    shopify_variant_id="var-1",
                    shopify_sku="SHOP-1",
                    mapping_status="active",
                )
            ],
            shopify_states=[
                ShopifyPriceState(
                    store_name="demo-store",
                    shopify_product_id="prod-1",
                    shopify_variant_id="var-1",
                    current_price=14,
                )
            ],
            mode="dry-run",
        ),
        mapping_repository=mapping_repo,
        sync_repository=sync_repo,
        shopify_service=ShopifyPriceSyncService(force_mode="mock"),
    )
    assert batch.processed_count == 1
    assert batch.items[0].giga_sku == "SKU-1"


def test_single_sku_uses_real_fetch_paths_when_request_overrides_are_empty(tmp_path):
    mapping_repo = _mapping_repo(tmp_path)
    sync_repo = _sync_repo(tmp_path)

    class _StubGigaClient:
        def list_price_snapshots(self, **kwargs):
            assert kwargs["skus"] == ["SKU-1"]
            assert kwargs["snapshots_override"] is None
            return [
                GigaPriceSnapshot(
                    store_name="demo-store",
                    giga_product_id="g-1",
                    giga_sku="SKU-1",
                    supplier_cost=10,
                    shipping_cost=2,
                    source_updated_at="2026-06-22T10:00:00+00:00",
                    raw_hash="hash-1",
                )
            ]

    class _StubShopifyService:
        def get_price_states(self, **kwargs):
            assert kwargs["states_override"] is None
            return [
                ShopifyPriceState(
                    store_name="demo-store",
                    shopify_product_id="prod-1",
                    shopify_variant_id="var-1",
                    current_price=8,
                )
            ]

        def apply_price_updates(self, items):
            return items

    batch = run_price_sync(
        PriceSyncRequest(
            store_name="demo-store",
            sync_scope="single_sku",
            sku_list=["SKU-1"],
            mappings=[
                SkuMappingRecord(
                    store_name="demo-store",
                    giga_sku="SKU-1",
                    shopify_product_id="prod-1",
                    shopify_variant_id="var-1",
                    shopify_sku="SHOP-1",
                    mapping_status="active",
                )
            ],
            mode="dry-run",
        ),
        giga_client=_StubGigaClient(),
        mapping_repository=mapping_repo,
        sync_repository=sync_repo,
        shopify_service=_StubShopifyService(),
    )

    assert batch.processed_count == 1
    assert batch.items[0].giga_sku == "SKU-1"


def test_large_price_drop_no_longer_forces_manual_review(tmp_path):
    mapping_repo = _mapping_repo(tmp_path)
    sync_repo = _sync_repo(tmp_path)

    batch = run_price_sync(
        PriceSyncRequest(
            store_name="demo-store",
            sync_scope="single_sku",
            sku_list=["SKU-1"],
            giga_snapshots=[
                GigaPriceSnapshot(
                    store_name="demo-store",
                    giga_product_id="g-1",
                    giga_sku="SKU-1",
                    supplier_cost=19.29,
                    shipping_cost=13.96,
                    source_updated_at="2026-06-22T10:00:00+00:00",
                    raw_hash="hash-1",
                )
            ],
            mappings=[
                SkuMappingRecord(
                    store_name="demo-store",
                    giga_sku="SKU-1",
                    shopify_product_id="prod-1",
                    shopify_variant_id="var-1",
                    shopify_sku="SKU-1",
                    mapping_status="active",
                )
            ],
            shopify_states=[
                ShopifyPriceState(
                    store_name="demo-store",
                    shopify_product_id="prod-1",
                    shopify_variant_id="var-1",
                    current_price=61.99,
                )
            ],
            mode="dry-run",
        ),
        mapping_repository=mapping_repo,
        sync_repository=sync_repo,
        shopify_service=ShopifyPriceSyncService(force_mode="mock"),
    )

    assert batch.processed_count == 1
    assert batch.manual_review_count == 0
    assert batch.items[0].decision == "decrease_price"
    assert batch.items[0].status == "planned"


def test_run_price_sync_can_auto_discover_mappings_from_shopify(tmp_path):
    mapping_repo = _mapping_repo(tmp_path)
    sync_repo = _sync_repo(tmp_path)

    class _StubGigaClient:
        def list_price_snapshots(self, **kwargs):
            assert kwargs["skus"] == ["SKU-1"]
            return [
                GigaPriceSnapshot(
                    store_name="demo-store",
                    giga_product_id="g-1",
                    giga_sku="SKU-1",
                    supplier_cost=10,
                    shipping_cost=2,
                    source_updated_at="2026-06-22T10:00:00+00:00",
                    raw_hash="hash-1",
                )
            ]

    class _StubShopifyService:
        mode = "real"

        def discover_mappings(self, *, store_name, sku_list=None, progress_callback=None):
            assert store_name == "demo-store"
            assert sku_list is None
            return [
                SkuMappingRecord(
                    store_name="demo-store",
                    giga_sku="SKU-1",
                    shopify_product_id="prod-1",
                    shopify_variant_id="var-1",
                    shopify_sku="SKU-1",
                    mapping_status="active",
                )
            ]

        def get_price_states(self, **kwargs):
            return [
                ShopifyPriceState(
                    store_name="demo-store",
                    shopify_product_id="prod-1",
                    shopify_variant_id="var-1",
                    current_price=8,
                )
            ]

        def apply_price_updates(self, items):
            return items

    batch = run_price_sync(
        PriceSyncRequest(
            store_name="demo-store",
            sync_scope="full",
            mode="dry-run",
        ),
        giga_client=_StubGigaClient(),
        mapping_repository=mapping_repo,
        sync_repository=sync_repo,
        shopify_service=_StubShopifyService(),
    )

    assert batch.processed_count == 1
    saved_mappings = mapping_repo.load_records()
    assert len(saved_mappings) == 1
    assert saved_mappings[0].giga_sku == "SKU-1"


def test_full_sync_refreshes_and_merges_discovered_mappings(tmp_path):
    mapping_repo = _mapping_repo(tmp_path)
    sync_repo = _sync_repo(tmp_path)
    mapping_repo.save_records(
        [
            SkuMappingRecord(
                store_name="demo-store",
                giga_sku="SKU-OLD",
                shopify_product_id="prod-old",
                shopify_variant_id="var-old",
                shopify_sku="SKU-OLD",
                mapping_status="active",
            )
        ]
    )

    class _StubGigaClient:
        def list_price_snapshots(self, **kwargs):
            assert kwargs["skus"] == ["SKU-OLD", "SKU-NEW"]
            return [
                GigaPriceSnapshot(
                    store_name="demo-store",
                    giga_product_id="g-1",
                    giga_sku="SKU-NEW",
                    supplier_cost=10,
                    shipping_cost=2,
                    source_updated_at="2026-06-22T10:00:00+00:00",
                    raw_hash="hash-1",
                )
            ]

    class _StubShopifyService:
        mode = "real"

        def discover_mappings(self, *, store_name, sku_list=None, progress_callback=None):
            return [
                SkuMappingRecord(
                    store_name="demo-store",
                    giga_sku="SKU-NEW",
                    shopify_product_id="prod-new",
                    shopify_variant_id="var-new",
                    shopify_sku="SKU-NEW",
                    mapping_status="active",
                )
            ]

        def get_price_states(self, **kwargs):
            return [
                ShopifyPriceState(
                    store_name="demo-store",
                    shopify_product_id="prod-new",
                    shopify_variant_id="var-new",
                    current_price=8,
                )
            ]

        def apply_price_updates(self, items):
            return items

    batch = run_price_sync(
        PriceSyncRequest(
            store_name="demo-store",
            sync_scope="full",
            mode="dry-run",
        ),
        giga_client=_StubGigaClient(),
        mapping_repository=mapping_repo,
        sync_repository=sync_repo,
        shopify_service=_StubShopifyService(),
    )

    assert batch.processed_count == 1
    saved_mappings = mapping_repo.load_records()
    assert sorted(item.giga_sku for item in saved_mappings) == ["SKU-NEW", "SKU-OLD"]


def test_apply_runs_updates_one_item_at_a_time(tmp_path):
    mapping_repo = _mapping_repo(tmp_path)
    sync_repo = _sync_repo(tmp_path)
    calls = []

    class _SequentialShopifyService:
        mode = "real"

        def discover_mappings(self, *, store_name, sku_list=None, progress_callback=None):
            return []

        def get_price_states(self, **kwargs):
            return [
                ShopifyPriceState(store_name="demo-store", shopify_product_id="prod-1", shopify_variant_id="var-1", current_price=8),
                ShopifyPriceState(store_name="demo-store", shopify_product_id="prod-2", shopify_variant_id="var-2", current_price=8),
            ]

        def apply_price_updates(self, items):
            calls.append([item.giga_sku for item in items])
            return [item.model_copy(update={"status": "synced", "error_message": ""}) for item in items]

    batch = run_price_sync(
        PriceSyncRequest(
            store_name="demo-store",
            sync_scope="full",
            giga_snapshots=[
                GigaPriceSnapshot(
                    store_name="demo-store",
                    giga_product_id="g-1",
                    giga_sku="SKU-1",
                    supplier_cost=10,
                    shipping_cost=2,
                    source_updated_at="2026-06-22T10:00:00+00:00",
                    raw_hash="hash-1",
                ),
                GigaPriceSnapshot(
                    store_name="demo-store",
                    giga_product_id="g-2",
                    giga_sku="SKU-2",
                    supplier_cost=11,
                    shipping_cost=2,
                    source_updated_at="2026-06-22T10:01:00+00:00",
                    raw_hash="hash-2",
                ),
            ],
            mappings=[
                SkuMappingRecord(store_name="demo-store", giga_sku="SKU-1", shopify_product_id="prod-1", shopify_variant_id="var-1", shopify_sku="SKU-1", mapping_status="active"),
                SkuMappingRecord(store_name="demo-store", giga_sku="SKU-2", shopify_product_id="prod-2", shopify_variant_id="var-2", shopify_sku="SKU-2", mapping_status="active"),
            ],
            mode="apply",
        ),
        mapping_repository=mapping_repo,
        sync_repository=sync_repo,
        shopify_service=_SequentialShopifyService(),
    )

    assert batch.success_count == 2
    assert calls == [["SKU-1"], ["SKU-2"]]


def test_apply_emits_progress_callback_per_item(tmp_path):
    mapping_repo = _mapping_repo(tmp_path)
    sync_repo = _sync_repo(tmp_path)
    events = []

    class _SequentialShopifyService:
        mode = "real"

        def discover_mappings(self, *, store_name, sku_list=None, progress_callback=None):
            return []

        def get_price_states(self, **kwargs):
            return [
                ShopifyPriceState(store_name="demo-store", shopify_product_id="prod-1", shopify_variant_id="var-1", current_price=8),
                ShopifyPriceState(store_name="demo-store", shopify_product_id="prod-2", shopify_variant_id="var-2", current_price=8),
            ]

        def apply_price_updates(self, items):
            return [item.model_copy(update={"status": "synced", "error_message": ""}) for item in items]

    batch = run_price_sync(
        PriceSyncRequest(
            store_name="demo-store",
            sync_scope="full",
            giga_snapshots=[
                GigaPriceSnapshot(
                    store_name="demo-store",
                    giga_product_id="g-1",
                    giga_sku="SKU-1",
                    supplier_cost=10,
                    shipping_cost=2,
                    source_updated_at="2026-06-22T10:00:00+00:00",
                    raw_hash="hash-1",
                ),
                GigaPriceSnapshot(
                    store_name="demo-store",
                    giga_product_id="g-2",
                    giga_sku="SKU-2",
                    supplier_cost=11,
                    shipping_cost=2,
                    source_updated_at="2026-06-22T10:01:00+00:00",
                    raw_hash="hash-2",
                ),
            ],
            mappings=[
                SkuMappingRecord(store_name="demo-store", giga_sku="SKU-1", shopify_product_id="prod-1", shopify_variant_id="var-1", shopify_sku="SKU-1", mapping_status="active"),
                SkuMappingRecord(store_name="demo-store", giga_sku="SKU-2", shopify_product_id="prod-2", shopify_variant_id="var-2", shopify_sku="SKU-2", mapping_status="active"),
            ],
            mode="apply",
        ),
        mapping_repository=mapping_repo,
        sync_repository=sync_repo,
        shopify_service=_SequentialShopifyService(),
        progress_callback=events.append,
    )

    assert batch.success_count == 2
    item_events = [event for event in events if event.get("event") == "item"]
    assert [event["item"]["giga_sku"] for event in item_events] == ["SKU-1", "SKU-2"]


def test_mapping_repository_can_write_template(tmp_path):
    repo = MappingRepository(path=tmp_path / "mappings.json")
    path = repo.write_template()
    assert Path(path).exists()
    content = Path(path).read_text(encoding="utf-8")
    assert "GIGA-SKU-001" in content


def test_giga_debug_uses_override_free_runtime_shape():
    class _Response:
        status_code = 200
        text = '{"items":[{"sku":"SKU-1","price":10,"normal_shipping_fee":2}]}'

        def raise_for_status(self):
            return None

        def json(self):
            return {"items": [{"sku": "SKU-1", "price": 10, "normal_shipping_fee": 2}]}

    class _HttpClient:
        def get(self, *args, **kwargs):
            return _Response()

    client = GigaClient(http_client=_HttpClient())
    result = client.debug_price_snapshots(store_name="demo-store", sync_scope="full")
    assert result["ok"] is True
    assert result["response"]["item_count"] == 1
    assert result["response"]["normalized_preview"][0]["giga_sku"] == "SKU-1"


def test_giga_debug_supports_endpoint_override_and_probe():
    class _Response:
        status_code = 404
        text = '{"success":false,"code":"404","msg":"Not Found"}'
        is_success = False

        def raise_for_status(self):
            import httpx

            request = httpx.Request("GET", "https://openapi.gigab2b.com/api/v1/products/prices")
            response = httpx.Response(404, request=request, text=self.text)
            raise httpx.HTTPStatusError("not found", request=request, response=response)

        def json(self):
            return {"success": False, "code": "404", "msg": "Not Found"}

    class _HttpClient:
        def get(self, *args, **kwargs):
            return _Response()

    client = GigaClient(http_client=_HttpClient())
    debug = client.debug_price_snapshots(
        store_name="demo-store",
        sync_scope="full",
        endpoint_override="/api/v1/products/prices",
    )
    assert debug["ok"] is False
    assert debug["request"]["endpoint"] == "/api/v1/products/prices"

    probe = client.probe_endpoints(
        store_name="demo-store",
        sync_scope="full",
        candidates=["/api/v1/products/prices"],
    )
    assert probe["results"][0]["endpoint"] == "/api/v1/products/prices"


def test_giga_client_uses_real_price_query_payload():
    captured = {}

    class _Response:
        status_code = 200
        text = '{"success":true,"code":"200","data":[{"sku":"SKU-1","price":10,"shippingFee":2,"currency":"USD"}]}'

        def raise_for_status(self):
            return None

        def json(self):
            return {"success": True, "code": "200", "data": [{"sku": "SKU-1", "price": 10, "shippingFee": 2, "currency": "USD"}]}

    class _HttpClient:
        def post(self, url, headers=None, json=None):
            captured["url"] = url
            captured["json"] = json
            return _Response()

    client = GigaClient(http_client=_HttpClient())
    snapshots = client.list_price_snapshots(
        store_name="demo-store",
        sync_scope="full",
        skus=["SKU-1"],
    )
    assert captured["url"].endswith("/b2b-overseas-api/v1/buyer/product/price/v1")
    assert captured["json"] == {"skus": ["SKU-1"]}
    assert snapshots[0].giga_sku == "SKU-1"
    assert snapshots[0].shipping_cost == 2


def test_giga_frontend_debug_detects_captcha():
    class _Response:
        status_code = 200
        text = "<html><title>Verification</title><script>AliyunCaptcha</script></html>"
        url = "https://www.gigab2b.com/index.php?route=safe/captcha"

    class _HttpClient:
        def get(self, *args, **kwargs):
            return _Response()

    client = GigaClient(http_client=_HttpClient())
    client.settings.giga_buyer_site_base_url = "https://www.gigab2b.com"
    client.settings.giga_frontend_product_list_route = "/index.php?route=/product/list/list"
    result = client.debug_frontend_access()
    assert result["ok"] is True
    assert result["response"]["blocked_by_captcha"] is True
