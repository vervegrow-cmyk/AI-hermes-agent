from pathlib import Path
import sys

from fastapi.testclient import TestClient

AGENT_ROOT = Path(__file__).resolve().parents[1]
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from api.app import app
from models.price_sync import DobaPriceSnapshot, PriceSyncRequest, ShopifyPriceState, SkuMappingRecord
from service.doba_client import DobaPriceSyncClient
from service.executor import run_price_sync
from service.mapping_repository import MappingRepository
from service.shopify_price_sync_service import ShopifyPriceSyncService
from service.sync_repository import SyncRepository
from shared.config import get_settings


def _mapping_repo(tmp_path):
    return MappingRepository(path=tmp_path / "mappings.json")


def _sync_repo(tmp_path):
    return SyncRepository(root=tmp_path / "runtime")


def _snapshot(sku: str, *, supplier_cost=10.0, shipping_cost=2.0, raw_hash="hash", updated_at="2026-06-30T10:00:00+00:00"):
    return DobaPriceSnapshot(
        store_name="demo-store",
        doba_product_id=f"prod-{sku}",
        doba_sku=sku,
        supplier_cost=supplier_cost,
        shipping_cost=shipping_cost,
        estimated_total_cost=(supplier_cost or 0) + (shipping_cost or 0),
        source_updated_at=updated_at,
        raw_hash=f"{raw_hash}-{sku}",
    )


def _mapping(sku: str, variant: str, product: str = "shopify-product-1"):
    return SkuMappingRecord(
        store_name="demo-store",
        supplier="doba",
        doba_product_id=f"prod-{sku}",
        doba_sku=sku,
        shopify_product_id=product,
        shopify_variant_id=variant,
        shopify_sku=f"SHOP-{sku}",
        mapping_status="active",
    )


def _state(variant: str, price: float):
    return ShopifyPriceState(
        store_name="demo-store",
        shopify_product_id="shopify-product-1",
        shopify_variant_id=variant,
        shopify_sku=f"SHOP-{variant}",
        current_price=price,
    )


def test_routes_are_registered():
    client = TestClient(app)
    paths = client.get("/openapi.json").json()["paths"].keys()
    assert "/health" in paths
    assert "/execute" in paths
    assert "/price-sync/dry-run" in paths
    assert "/price-sync/apply" in paths
    assert "/price-sync/single" in paths
    assert "/price-sync/batches/{batch_id}" in paths
    assert "/price-sync/debug/doba" in paths
    assert "/price-sync/mapping-template" in paths
    assert "/variant-mapping/build" in paths
    assert "/variant-mapping/validate" in paths
    assert "/variant-mapping/stats" in paths
    assert "/variant-mapping/export-review" in paths
    assert "/variant-mapping/import-reviewed" in paths
    assert "/variant-mapping/debug" in paths


def test_dry_run_does_not_write_shopify(tmp_path):
    class _GuardService(ShopifyPriceSyncService):
        def apply_price_updates(self, items):
            raise AssertionError("dry-run should not write Shopify")

    batch = run_price_sync(
        PriceSyncRequest(
            store_name="demo-store",
                sync_scope="full",
                doba_snapshots=[_snapshot("SKU-1")],
                mappings=[_mapping("SKU-1", "var-1")],
                shopify_states=[_state("var-1", 12.0)],
                mode="dry-run",
            ),
        mapping_repository=_mapping_repo(tmp_path),
        sync_repository=_sync_repo(tmp_path),
        shopify_service=_GuardService(force_mode="mock"),
    )
    assert batch.processed_count == 1
    assert batch.items[0].status == "planned"


def test_apply_only_updates_changed_variants(tmp_path):
    calls = []

    class _CaptureService:
        mode = "real"

        def ensure_write_ready(self):
            return None

        def get_price_states(self, **kwargs):
            return [
                _state("var-1", 14.99),
                _state("var-2", 12.0),
            ]

        def apply_price_updates(self, items):
            calls.append([item.doba_sku for item in items])
            return [item.model_copy(update={"status": "synced"}) for item in items]

    batch = run_price_sync(
        PriceSyncRequest(
            store_name="demo-store",
            sync_scope="full",
            doba_snapshots=[_snapshot("SKU-1"), _snapshot("SKU-2")],
            mappings=[_mapping("SKU-1", "var-1"), _mapping("SKU-2", "var-2")],
            mode="apply",
        ),
        mapping_repository=_mapping_repo(tmp_path),
        sync_repository=_sync_repo(tmp_path),
        shopify_service=_CaptureService(),
    )
    assert calls == [["SKU-2"]]
    assert any(item.doba_sku == "SKU-1" and item.status == "skipped" for item in batch.items)
    assert any(item.doba_sku == "SKU-2" and item.status == "synced" for item in batch.items)


def test_apply_supports_limit(tmp_path):
    calls = []

    class _CaptureService:
        mode = "real"

        def ensure_write_ready(self):
            return None

        def get_price_states(self, **kwargs):
            price = 12.0
            return [_state(kwargs["mappings"][0].shopify_variant_id, price)]

        def apply_price_updates(self, items):
            calls.extend(item.doba_sku for item in items)
            return [item.model_copy(update={"status": "synced"}) for item in items]

    batch = run_price_sync(
        PriceSyncRequest(
            store_name="demo-store",
            sync_scope="full",
            limit=1,
            doba_snapshots=[_snapshot("SKU-1"), _snapshot("SKU-2")],
            mappings=[_mapping("SKU-1", "var-1"), _mapping("SKU-2", "var-2")],
            mode="apply",
        ),
        mapping_repository=_mapping_repo(tmp_path),
        sync_repository=_sync_repo(tmp_path),
        shopify_service=_CaptureService(),
    )
    assert calls == ["SKU-1"]
    assert batch.processed_count == 1


def test_single_sku_force_recalculate_can_skip_incremental_cache(tmp_path):
    sync_repo = _sync_repo(tmp_path)
    sync_repo.save_state(
        "demo-store::SKU-1::var-1",
        {
            "store_name": "demo-store",
            "doba_sku": "SKU-1",
            "shopify_variant_id": "var-1",
            "last_source_hash": "hash-SKU-1",
            "last_target_price": 13.49,
            "last_sync_status": "synced",
        },
    )
    batch = run_price_sync(
        PriceSyncRequest(
            store_name="demo-store",
            sync_scope="single_sku",
            sku_list=["SKU-1"],
            force_recalculate=True,
            skip_incremental_cache=True,
            doba_snapshots=[_snapshot("SKU-1")],
            mappings=[_mapping("SKU-1", "var-1")],
            shopify_states=[_state("var-1", 10.0)],
            mode="dry-run",
        ),
        mapping_repository=_mapping_repo(tmp_path),
        sync_repository=sync_repo,
        shopify_service=ShopifyPriceSyncService(force_mode="mock"),
    )
    assert batch.processed_count == 1
    assert batch.items[0].doba_sku == "SKU-1"


def test_multi_sku_product_is_processed_per_variant(tmp_path):
    batch = run_price_sync(
        PriceSyncRequest(
            store_name="demo-store",
            sync_scope="full",
            doba_snapshots=[_snapshot("SKU-1"), _snapshot("SKU-2")],
            mappings=[_mapping("SKU-1", "var-1", "prod-1"), _mapping("SKU-2", "var-2", "prod-1")],
            shopify_states=[_state("var-1", 8.0), _state("var-2", 8.0)],
            mode="dry-run",
        ),
        mapping_repository=_mapping_repo(tmp_path),
        sync_repository=_sync_repo(tmp_path),
        shopify_service=ShopifyPriceSyncService(force_mode="mock"),
    )
    assert [item.shopify_variant_id for item in batch.items] == ["var-1", "var-2"]


def test_duplicate_doba_sku_goes_manual_review(tmp_path):
    batch = run_price_sync(
        PriceSyncRequest(
            store_name="demo-store",
            sync_scope="full",
            doba_snapshots=[_snapshot("SKU-1")],
            mappings=[_mapping("SKU-1", "var-1"), _mapping("SKU-1", "var-2")],
            shopify_states=[],
            mode="dry-run",
        ),
        mapping_repository=_mapping_repo(tmp_path),
        sync_repository=_sync_repo(tmp_path),
        shopify_service=ShopifyPriceSyncService(force_mode="mock"),
    )
    assert batch.items[0].status == "manual_review"
    assert "duplicate_source_mapping" in batch.items[0].reason_codes


def test_duplicate_shopify_variant_goes_manual_review(tmp_path):
    batch = run_price_sync(
        PriceSyncRequest(
            store_name="demo-store",
            sync_scope="full",
            doba_snapshots=[_snapshot("SKU-1"), _snapshot("SKU-2")],
            mappings=[_mapping("SKU-1", "var-1"), _mapping("SKU-2", "var-1")],
            shopify_states=[],
            mode="dry-run",
        ),
        mapping_repository=_mapping_repo(tmp_path),
        sync_repository=_sync_repo(tmp_path),
        shopify_service=ShopifyPriceSyncService(force_mode="mock"),
    )
    review_items = [item for item in batch.items if item.status == "manual_review"]
    assert len(review_items) == 2
    assert all("duplicate_target_mapping" in item.reason_codes for item in review_items)


def test_price_hash_unchanged_skips_item(tmp_path):
    sync_repo = _sync_repo(tmp_path)
    sync_repo.save_state(
        "demo-store::SKU-1::var-1",
        {
            "store_name": "demo-store",
            "doba_sku": "SKU-1",
            "shopify_variant_id": "var-1",
            "last_source_hash": "hash-SKU-1",
            "last_target_price": 11.99,
            "last_sync_status": "synced",
        },
    )
    batch = run_price_sync(
        PriceSyncRequest(
            store_name="demo-store",
                sync_scope="incremental",
                doba_snapshots=[_snapshot("SKU-1")],
                mappings=[_mapping("SKU-1", "var-1")],
                shopify_states=[_state("var-1", 12.0)],
                mode="dry-run",
            ),
        mapping_repository=_mapping_repo(tmp_path),
        sync_repository=sync_repo,
        shopify_service=ShopifyPriceSyncService(force_mode="mock"),
    )
    assert batch.items[0].status == "skipped"


def test_target_price_unchanged_skips_item(tmp_path):
    sync_repo = _sync_repo(tmp_path)
    sync_repo.save_state(
        "demo-store::SKU-1::var-1",
            {
                "store_name": "demo-store",
                "doba_sku": "SKU-1",
                "shopify_variant_id": "var-1",
                "last_source_hash": "older-hash",
                "last_target_price": 14.99,
                "last_sync_status": "synced",
            },
        )
    batch = run_price_sync(
        PriceSyncRequest(
            store_name="demo-store",
                sync_scope="incremental",
                doba_snapshots=[_snapshot("SKU-1")],
                mappings=[_mapping("SKU-1", "var-1")],
                shopify_states=[_state("var-1", 12.0)],
                mode="dry-run",
            ),
        mapping_repository=_mapping_repo(tmp_path),
        sync_repository=sync_repo,
        shopify_service=ShopifyPriceSyncService(force_mode="mock"),
    )
    assert batch.items[0].reason_codes == ["target_price_unchanged"]


def test_shopify_price_already_correct_skips_item(tmp_path):
    batch = run_price_sync(
        PriceSyncRequest(
                store_name="demo-store",
                sync_scope="full",
                doba_snapshots=[_snapshot("SKU-1")],
                mappings=[_mapping("SKU-1", "var-1")],
                shopify_states=[_state("var-1", 14.99)],
                mode="dry-run",
            ),
        mapping_repository=_mapping_repo(tmp_path),
        sync_repository=_sync_repo(tmp_path),
        shopify_service=ShopifyPriceSyncService(force_mode="mock"),
    )
    assert batch.items[0].reason_codes == ["shopify_price_already_correct"]


def test_apply_without_shopify_token_raises_clear_error(tmp_path):
    try:
        run_price_sync(
            PriceSyncRequest(
                store_name="demo-store",
                sync_scope="full",
                doba_snapshots=[_snapshot("SKU-1")],
                mappings=[_mapping("SKU-1", "var-1")],
                shopify_states=[_state("var-1", 8.0)],
                mode="apply",
            ),
            mapping_repository=_mapping_repo(tmp_path),
            sync_repository=_sync_repo(tmp_path),
            shopify_service=ShopifyPriceSyncService(force_mode="mock"),
        )
        raise AssertionError("expected shopify_admin_token_missing")
    except RuntimeError as exc:
        assert str(exc) == "shopify_admin_token_missing"


def test_debug_doba_does_not_leak_secret_values(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("DOBA_ACCESS_TOKEN", "super-secret-token")
    monkeypatch.setenv("DOBA_API_SECRET", "super-secret-secret")
    monkeypatch.setattr(
        DobaPriceSyncClient,
        "list_price_snapshots",
        lambda self, **kwargs: [DobaPriceSnapshot(doba_sku="SKU-1", supplier_cost=10, shipping_cost=2)],
    )
    monkeypatch.setattr(
        DobaPriceSyncClient,
        "probe_endpoints",
        lambda self, **kwargs: [{"endpoint": "/api/goods/doba/stock", "ok": False, "responseMessage": "IP whitelist check failed"}],
    )
    client = TestClient(app)
    result = client.get("/price-sync/debug/doba").json()
    dumped = str(result)
    assert result["ok"] is True
    assert "Authorization" in result["request"]["header_names"]
    assert result["probe_results"][0]["endpoint"] == "/api/goods/doba/stock"
    assert "super-secret-token" not in dumped
    assert "super-secret-secret" not in dumped
    get_settings.cache_clear()


def test_retailer_mainline_uses_updated_stock_and_shipping():
    class _Response:
        def __init__(self, payload, status_code=200):
            self._payload = payload
            self.status_code = status_code
            self.is_success = status_code < 400

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    class _HttpClient:
        def request(self, method, url, headers=None, params=None, json=None):
            if url.endswith("/api/platform/list"):
                return _Response({"businessData": [{"platformId": "shopify-platform", "platformName": "Shopify"}]})
            if url.endswith("/api/goods/doba/updated"):
                return _Response(
                    {
                        "businessData": {
                            "data": {
                                "productUpdateInfoList": [
                                    {
                                        "itemNo": "D0102HPJ8CT",
                                        "updateType": "1",
                                        "updateDetail": "178.79",
                                        "updateTime": "2026-06-30T10:00:00+08:00",
                                    }
                                ]
                            }
                        }
                    }
                )
            if url.endswith("/api/goods/doba/stock"):
                return _Response(
                    {
                        "businessData": {
                            "data": [
                                {
                                    "itemNo": "D0102HPJ8CT",
                                    "sellingPrice": "178.79",
                                    "availableNum": 43,
                                    "currencyId": "USD",
                                }
                            ]
                        }
                    }
                )
            if url.endswith("/api/goods/doba/spu/detail"):
                return _Response(
                    {
                        "businessData": {
                            "data": [
                                {
                                    "spuId": "yzVgqmBGuFDk",
                                    "spuNo": "D0100H5USDX",
                                    "title": "Demo product",
                                    "sellerName": "Demo seller",
                                    "children": [
                                        {
                                            "skuId": "sTvmbYdjPFDo",
                                            "skuCode": "W1170P183257",
                                            "currencyId": "USD",
                                            "stocks": [{"itemNo": "D0102HPJ8CT", "availableNum": 43}],
                                        }
                                    ],
                                }
                            ]
                        }
                    }
                )
            if url.endswith("/api/shipping/doba/cost/goods"):
                return _Response(
                    {
                        "businessData": [
                            {
                                "successful": True,
                                "businessMessage": "Success",
                                "data": {
                                    "itemNo": "D0102HPJ8CT",
                                    "quantity": 1,
                                    "costs": [{"shipFee": 0.0, "currencyId": "USD"}],
                                },
                            }
                        ]
                    }
                )
            raise AssertionError(f"unexpected url {url}")

    snapshots = DobaPriceSyncClient(http_client=_HttpClient()).list_price_snapshots(
        store_name="demo-store",
        sync_scope="incremental",
        updated_since="2026-06-29T00:00:00Z",
    )
    assert len(snapshots) == 1
    assert snapshots[0].doba_sku == "D0102HPJ8CT"
    assert snapshots[0].doba_product_id == "yzVgqmBGuFDk"
    assert snapshots[0].supplier_cost == 178.79
    assert snapshots[0].shipping_cost == 0.0


def test_retailer_full_sync_paginates_spu_list(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("DOBA_PRICE_SYNC_FULL_PAGE_SIZE", "2")
    monkeypatch.setenv("DOBA_ALLOW_FULL_SCAN", "true")

    class _Response:
        def __init__(self, payload, status_code=200):
            self._payload = payload
            self.status_code = status_code
            self.is_success = status_code < 400

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    class _HttpClient:
        def __init__(self):
            self.calls = []

        def request(self, method, url, headers=None, params=None, json=None):
            self.calls.append((url, params, json))
            if url.endswith("/api/platform/list"):
                return _Response({"businessData": [{"platformId": "shopify-platform", "platformName": "Shopify"}]})
            if url.endswith("/api/goods/doba/spu/list"):
                page = int((params or {}).get("pageNumber", 1))
                if page == 1:
                    return _Response(
                        {
                            "businessData": {
                                "data": {
                                    "goodsList": [
                                        {"spuNo": "SPU-1"},
                                        {"spuNo": "SPU-2"},
                                    ]
                                }
                            }
                        }
                    )
                if page == 2:
                    return _Response(
                        {
                            "businessData": {
                                "data": {
                                    "goodsList": [
                                        {"spuNo": "SPU-3"},
                                    ]
                                }
                            }
                        }
                    )
            if url.endswith("/api/goods/doba/spu/detail"):
                requested = str((params or {}).get("spuNo") or "")
                rows = []
                for spu_no in requested.split(","):
                    if not spu_no:
                        continue
                    rows.append(
                        {
                            "spuId": f"{spu_no}-ID",
                            "spuNo": spu_no,
                            "title": f"Title {spu_no}",
                            "sellerName": "Demo seller",
                            "children": [
                                {
                                    "skuId": f"{spu_no}-SKU",
                                    "skuCode": f"{spu_no}-CODE",
                                    "currencyId": "USD",
                                    "stocks": [{"itemNo": f"{spu_no}-ITEM", "availableNum": 5}],
                                }
                            ],
                        }
                    )
                return _Response({"businessData": {"data": rows}})
            if url.endswith("/api/goods/doba/stock"):
                item_nos = str((params or {}).get("itemNo") or "").split(",")
                return _Response(
                    {
                        "businessData": {
                            "data": [
                                {
                                    "itemNo": item_no,
                                    "sellingPrice": "10.00",
                                    "availableNum": 5,
                                    "currencyId": "USD",
                                }
                                for item_no in item_nos
                                if item_no
                            ]
                        }
                    }
                )
            if url.endswith("/api/shipping/doba/cost/goods"):
                goods = list((json or {}).get("goods") or [])
                return _Response(
                    {
                        "businessData": [
                            {
                                "successful": True,
                                "businessMessage": "Success",
                                "data": {
                                    "itemNo": row["itemNo"],
                                    "quantity": 1,
                                    "costs": [{"shipFee": 0.0, "currencyId": "USD"}],
                                },
                            }
                            for row in goods
                        ]
                    }
                )
            raise AssertionError(f"unexpected url {url}")

    http_client = _HttpClient()
    snapshots = DobaPriceSyncClient(http_client=http_client).list_price_snapshots(
        store_name="demo-store",
        sync_scope="full",
    )
    assert [item.doba_sku for item in snapshots] == ["SPU-1-ITEM", "SPU-2-ITEM", "SPU-3-ITEM"]
    list_calls = [call for call in http_client.calls if call[0].endswith("/api/goods/doba/spu/list")]
    assert len(list_calls) == 2
    get_settings.cache_clear()


def test_doba_probe_reports_candidate_endpoint_outcomes():
    class _Response:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload
            self.is_success = status_code < 400

        def json(self):
            return self._payload

    class _HttpClient:
        def request(self, method, url, headers=None, params=None, json=None):
            if url.endswith("/api/category/doba/list"):
                return _Response(403, {"responseCode": "999999", "responseMessage": "IP whitelist check failed"})
            return _Response(404, {"responseCode": "404", "responseMessage": "Not Found"})

    client = DobaPriceSyncClient(http_client=_HttpClient())
    results = client.probe_endpoints(candidates=["/api/category/doba/list", "/api/goods/doba/stock"])
    assert results[0]["endpoint"] == "/api/category/doba/list"
    assert results[0]["responseMessage"] == "IP whitelist check failed"
    assert results[1]["status_code"] == 404


def test_mapping_template_route_writes_template(tmp_path, monkeypatch):
    repo = MappingRepository(path=tmp_path / "mappings.json")
    monkeypatch.setattr("api.app.MappingRepository", lambda: repo)
    client = TestClient(app)
    result = client.post("/price-sync/mapping-template").json()
    assert result["ok"] is True
    content = Path(result["path"]).read_text(encoding="utf-8")
    assert "DOBA-SKU-001" in content


def test_terminal_reporter_prints_dry_run_lines(tmp_path, capsys):
    batch = run_price_sync(
        PriceSyncRequest(
            store_name="demo-store",
            sync_scope="full",
            doba_snapshots=[_snapshot("SKU-1")],
            mappings=[_mapping("SKU-1", "var-1")],
            shopify_states=[_state("var-1", 12.0)],
            print_detail=True,
            mode="dry-run",
        ),
        mapping_repository=_mapping_repo(tmp_path),
        sync_repository=_sync_repo(tmp_path),
        shopify_service=ShopifyPriceSyncService(force_mode="mock"),
    )
    output = capsys.readouterr().out
    assert batch.report_path.endswith(".json")
    assert "[DRY-RUN] batch_id=" in output
    assert "[MAPPING] total=" in output
    assert "[ITEM] SKU-1" in output
    assert "[SUMMARY] planned=" in output
