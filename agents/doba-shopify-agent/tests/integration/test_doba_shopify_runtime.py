from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from src.app.runners.run_doba_shopify_runtime import build_parser
from src.modules.doba_pipeline.application.production_runtime import run_doba_shopify_runtime
from src.modules.supplier_archive.application.online_archive_runtime import run_doba_online_archive


def test_runtime_runner_cli_argument_parsing() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "--mode",
            "full-runtime",
            "--target-country",
            "US",
            "--inventory-threshold",
            "10",
            "--stream-publish",
            "--incremental",
            "--archive-eligible-only",
            "--channels",
            "shop,inbox,pinterest,facebook",
        ]
    )
    assert args.mode == "full-runtime"
    assert args.target_country == "US"
    assert args.stream_publish is True
    assert args.incremental is True
    assert args.archive_eligible_only is True
    assert args.channels == "shop,inbox,pinterest,facebook"


def test_online_archive_stops_when_stream_hook_requests_stop(tmp_path: Path, monkeypatch) -> None:
    import src.modules.supplier_archive.application.online_archive_runtime as runtime

    monkeypatch.setattr(runtime, "_fetch_platform_id", lambda _client: "shopify-platform")
    monkeypatch.setattr(runtime, "_fetch_spu_page", lambda *_args, **_kwargs: (1, [{"spuNo": "SPU-1", "spuId": "PID-1", "title": "Test Product"}]))
    monkeypatch.setattr(runtime, "_fetch_spu_details", lambda *_args, **_kwargs: {"SPU-1": {"spuNo": "SPU-1", "spuId": "PID-1", "title": "Test Product", "busiId": "SUP-1"}})
    monkeypatch.setattr(runtime, "_collect_item_nos", lambda _details: [])
    monkeypatch.setattr(runtime, "_fetch_stock_map", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(runtime, "_fetch_shipping_map", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(runtime, "_fetch_seller_info", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(
        runtime,
        "_build_archive_inputs_from_detail",
        lambda **_kwargs: [
            type(
                "ArchiveInput",
                (),
                {
                    "ship_from_country": "United States",
                    "inventory": 25,
                    "sku": "SKU-1",
                    "sku_code": "CODE-1",
                    "title": "Test Product",
                    "cost": 12.5,
                    "shipping_cost": 0,
                    "seller_name": "Seller",
                    "category_name": "Category",
                },
            )()
        ],
    )
    monkeypatch.setattr(
        runtime,
        "archive_supplier_products",
        lambda products, _repo: type("ArchiveResult", (), {"model_dump": lambda self: {"archived_products": len(products), "warnings": []}})(),
    )
    monkeypatch.setattr(runtime, "DobaClient", type("DobaClient", (), {"from_settings": staticmethod(lambda: object())}))

    result = run_doba_online_archive(
        report_path=str(tmp_path / "archive-report.json"),
        checkpoint_path=str(tmp_path / "archive-checkpoint.json"),
        archive_eligible_only=True,
        eligible_inventory_threshold=10,
        resume=False,
        post_archive_hook=lambda _products, context: {
            "stop_archive": True,
            "stop_reason": "publish_failed",
            "last_failure": {
                "failed_spu_no": context["spu_no"],
                "failed_doba_product_id": context["spu_id"],
                "failed_reason": "publish_failed",
            },
        },
    )

    assert result["stopped_reason"] == "publish_failed"
    assert result["last_failure"]["failed_spu_no"] == "SPU-1"


def test_runtime_archive_only_generates_report_and_chinese_logs(tmp_path: Path, monkeypatch, capsys) -> None:
    import src.modules.doba_pipeline.application.production_runtime as runtime

    monkeypatch.setattr(
        runtime,
        "run_doba_online_archive",
        lambda **_kwargs: {
            "progress": {"processed_spu": 3, "archived_sku": 5, "eligible_spu": 2},
            "completed": True,
        },
    )

    result = run_doba_shopify_runtime(
        {
            "mode": "archive-only",
            "target_country": "US",
            "archive_report_path": str(tmp_path / "archive.json"),
            "archive_checkpoint_path": str(tmp_path / "archive-checkpoint.json"),
            "publish_report_path": str(tmp_path / "publish.json"),
            "publish_checkpoint_path": str(tmp_path / "publish-checkpoint.json"),
            "candidate_pool_path": str(tmp_path / "candidate.json"),
            "runtime_report_path": str(tmp_path / "runtime-report.md"),
        }
    )

    stdout = capsys.readouterr().out
    assert "Doba-Shopify-Agent V2 Commerce Runtime" in stdout
    assert "目标市场：US" in stdout
    assert Path(result["runtime_report_path"]).exists()
    assert result["summary"]["scanned"] == 3


def test_full_runtime_rolls_back_publish_when_risk_blocks(tmp_path: Path, monkeypatch) -> None:
    import src.modules.doba_pipeline.application.production_runtime as runtime

    rollback_calls: list[dict[str, object]] = []

    def fake_archive(**kwargs):
        hook = kwargs["post_archive_hook"]
        products = [
            SimpleNamespace(
                inventory=34,
                category_metafields={"shopify_category_id": "gid://shopify/TaxonomyCategory/test"},
                ship_from_country="United States",
            )
        ]
        hook_result = hook(
            products,
            {
                "spu_no": "SPU-ROLLBACK-1",
                "spu_id": "PID-ROLLBACK-1",
                "title": "Rollback Test Product",
                "total_spu": 1,
            },
        )
        return {
            "progress": {"processed_spu": 1, "archived_sku": 1, "eligible_spu": 1},
            "completed": False,
            "stopped_reason": hook_result.get("stop_reason"),
            "last_failure": hook_result.get("last_failure"),
        }

    monkeypatch.setattr(runtime, "run_doba_online_archive", fake_archive)
    monkeypatch.setattr(
        runtime,
        "_collect_spu_context",
        lambda **_kwargs: {"screening_inputs": [SimpleNamespace(supplier_sku="SKU-ROLLBACK-1")]},
    )
    monkeypatch.setattr(
        runtime,
        "run_rule_engine",
        lambda *_args, **_kwargs: SimpleNamespace(
            pre_filtered_products=[SimpleNamespace(supplier_sku="SKU-ROLLBACK-1")],
            model_dump=lambda: {"pre_filtered_products": 1},
        ),
    )
    monkeypatch.setattr(
        runtime,
        "run_deepseek_scoring",
        lambda *_args, **_kwargs: SimpleNamespace(total_scored_products=1, ai_product_scores=[{"sku": "SKU-ROLLBACK-1"}]),
    )
    monkeypatch.setattr(
        runtime,
        "run_candidate_pool",
        lambda *_args, **_kwargs: SimpleNamespace(
            approved_for_listing_count=1,
            listing_candidates=[SimpleNamespace(status="approved_for_listing", overall_score=92)],
        ),
    )
    monkeypatch.setattr(
        runtime,
        "build_doba_publish_candidate_pool",
        lambda **_kwargs: {
            "summary": {"qualified_count": 1},
            "qualified_candidates": [
                {
                    "spu_no": "SPU-ROLLBACK-1",
                    "content_enrichment": {"geo_score": {"score": 96, "eligible": True}},
                }
            ],
        },
    )
    monkeypatch.setattr(
        runtime,
        "publish_doba_products_live",
        lambda **_kwargs: {
            "completed": True,
            "summary": {"published_count": 1},
            "results": [
                {
                    "doba_spu_no": "SPU-ROLLBACK-1",
                    "action": "published",
                    "reason": "",
                    "shopify_product_id": "gid://shopify/Product/rollback-test",
                    "published_channels": ["Shop", "Inbox"],
                    "variant_count": 1,
                    "sku_list": ["SKU-ROLLBACK-1"],
                    "cost_prices": [20.0],
                    "sale_prices": [30.0],
                    "variant_details": [{"sku": "SKU-ROLLBACK-1"}],
                }
            ],
        },
    )
    monkeypatch.setattr(runtime, "_shopify_states_from_result", lambda *_args, **_kwargs: ([SimpleNamespace(inventory=34)], [SimpleNamespace()]))
    monkeypatch.setattr(runtime, "build_inventory_sync_command_from_archive", lambda **_kwargs: {"kind": "inventory"})
    monkeypatch.setattr(
        runtime,
        "run_inventory_sync_runtime",
        lambda _command: SimpleNamespace(report=SimpleNamespace(successful_syncs=1, failed_syncs=0), records=[]),
    )
    monkeypatch.setattr(runtime, "build_price_sync_command_from_archive", lambda **_kwargs: {"kind": "price"})
    monkeypatch.setattr(
        runtime,
        "run_price_sync_runtime",
        lambda _command: SimpleNamespace(
            report=SimpleNamespace(successful_syncs=1, failed_syncs=0),
            records=[],
            decisions=[],
        ),
    )
    monkeypatch.setattr(runtime, "build_risk_control_command_from_archive", lambda **_kwargs: {"kind": "risk"})
    monkeypatch.setattr(
        runtime,
        "run_risk_control",
        lambda _command: SimpleNamespace(
            risk_events=[SimpleNamespace(level="HIGH")],
            approval_queue=[],
            blocked_products=[SimpleNamespace(supplier_sku="SKU-ROLLBACK-1", reason="critical_risk_detected")],
        ),
    )
    monkeypatch.setattr(
        runtime,
        "rollback_shopify_product_publications",
        lambda **kwargs: rollback_calls.append(dict(kwargs)) or {
            "shopify_product_id": str(kwargs["product_id"]),
            "unpublished_channels": list(kwargs.get("channels") or []),
            "shopify_status": "DRAFT",
            "published_channels": [],
        },
    )

    result = run_doba_shopify_runtime(
        {
            "mode": "full-runtime",
            "target_country": "US",
            "inventory_threshold": 10,
            "list_min_inventory": 11,
            "eligible_inventory_threshold": 10,
            "page_size": 20,
            "stream_publish": True,
            "incremental": True,
            "archive_eligible_only": True,
            "channels": "shop,inbox",
            "archive_report_path": str(tmp_path / "archive.json"),
            "archive_checkpoint_path": str(tmp_path / "archive-checkpoint.json"),
            "publish_report_path": str(tmp_path / "publish.json"),
            "publish_checkpoint_path": str(tmp_path / "publish-checkpoint.json"),
            "candidate_pool_path": str(tmp_path / "candidate.json"),
            "runtime_report_path": str(tmp_path / "runtime-report.md"),
        }
    )

    assert result["ok"] is False
    assert result["last_failure"]["failed_reason"] == "critical_risk_detected"
    assert result["last_failure"]["rollback_summary"]["shopify_status"] == "DRAFT"
    assert rollback_calls == [
        {
            "product_id": "gid://shopify/Product/rollback-test",
            "channels": ["Shop", "Inbox"],
            "set_draft": True,
        }
    ]


def test_full_runtime_skips_shopify_publish_when_spu_not_in_candidate_pool(tmp_path: Path, monkeypatch) -> None:
    import src.modules.doba_pipeline.application.production_runtime as runtime

    def fake_archive(**kwargs):
        hook = kwargs["post_archive_hook"]
        products = [
            SimpleNamespace(
                inventory=34,
                category_metafields={"shopify_category_id": "gid://shopify/TaxonomyCategory/test"},
                ship_from_country="United States",
            )
        ]
        hook_result = hook(
            products,
            {
                "spu_no": "SPU-SKIP-1",
                "spu_id": "PID-SKIP-1",
                "title": "Candidate Pool Skip Product",
                "total_spu": 1,
            },
        )
        return {
            "progress": {"processed_spu": 1, "archived_sku": 1, "eligible_spu": 1},
            "completed": True,
            "last_stream_publish": hook_result,
        }

    monkeypatch.setattr(runtime, "run_doba_online_archive", fake_archive)
    monkeypatch.setattr(
        runtime,
        "_collect_spu_context",
        lambda **_kwargs: {"screening_inputs": [SimpleNamespace(supplier_sku="SKU-SKIP-1")]},
    )
    monkeypatch.setattr(
        runtime,
        "run_rule_engine",
        lambda *_args, **_kwargs: SimpleNamespace(
            pre_filtered_products=[SimpleNamespace(supplier_sku="SKU-SKIP-1")],
            model_dump=lambda: {"pre_filtered_products": 1},
        ),
    )
    monkeypatch.setattr(
        runtime,
        "run_deepseek_scoring",
        lambda *_args, **_kwargs: SimpleNamespace(total_scored_products=1, ai_product_scores=[{"sku": "SKU-SKIP-1"}]),
    )
    monkeypatch.setattr(
        runtime,
        "run_candidate_pool",
        lambda *_args, **_kwargs: SimpleNamespace(
            approved_for_listing_count=1,
            listing_candidates=[SimpleNamespace(status="approved_for_listing", overall_score=88)],
        ),
    )
    monkeypatch.setattr(
        runtime,
        "build_doba_publish_candidate_pool",
        lambda **_kwargs: {
            "summary": {"qualified_count": 0, "skipped_by_reason": {"already_successfully_published": 1}},
            "qualified_candidates": [],
        },
    )
    monkeypatch.setattr(
        runtime,
        "publish_doba_products_live",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("publish_doba_products_live should not be called")),
    )

    result = run_doba_shopify_runtime(
        {
            "mode": "full-runtime",
            "target_country": "US",
            "inventory_threshold": 10,
            "list_min_inventory": 11,
            "eligible_inventory_threshold": 10,
            "page_size": 20,
            "stream_publish": True,
            "incremental": True,
            "archive_eligible_only": True,
            "channels": "shop,inbox",
            "archive_report_path": str(tmp_path / "archive.json"),
            "archive_checkpoint_path": str(tmp_path / "archive-checkpoint.json"),
            "publish_report_path": str(tmp_path / "publish.json"),
            "publish_checkpoint_path": str(tmp_path / "publish-checkpoint.json"),
            "candidate_pool_path": str(tmp_path / "candidate.json"),
            "runtime_report_path": str(tmp_path / "runtime-report.md"),
        }
    )

    assert result["ok"] is True
    assert result["summary"]["skipped"] == 1
    assert result["summary"]["duplicate_skipped"] == 1
