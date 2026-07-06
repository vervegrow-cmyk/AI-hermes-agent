from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
from typing import Any

from src.modules.shopify_listing.application.live_publish_runtime import (
    DEFAULT_CANDIDATE_POOL_PATH,
    build_doba_publish_candidate_pool,
    publish_doba_products_live,
)
from src.modules.supplier_archive.application.online_archive_runtime import run_doba_online_archive
from src.shared.repositories import (
    SQLiteCandidatePoolRepository,
    SQLitePublishMappingRepository,
    SQLiteSupplierArchiveRepository,
)


DEFAULT_ARCHIVE_REPORT_PATH = "docs/audits/doba-online-archive-us-focus-report.json"
DEFAULT_ARCHIVE_CHECKPOINT_PATH = "data/runtime/supplier_archive/doba_online_archive_us_focus_checkpoint.json"
DEFAULT_PUBLISH_REPORT_PATH = "docs/audits/doba-shopify-live-publish-candidate-only-report.json"


def _make_stream_publish_hook(
    *,
    candidate_pool_path: str,
    publish_report_path: str,
    target_country: str,
    inventory_threshold: int,
    list_min_inventory: int | None,
    page_size: int,
    channels: list[str],
    resume: bool,
) -> Any:
    def _hook(products: list[Any], context: dict[str, Any]) -> dict[str, Any]:
        current_spu_no = str(context.get("spu_no") or "").strip()
        candidate_result = build_doba_publish_candidate_pool(
            candidate_pool_path=candidate_pool_path,
            target_country=target_country,
            inventory_threshold=inventory_threshold,
            incremental=True,
            incremental_spu_nos=([current_spu_no] if current_spu_no else None),
        )
        publish_result = publish_doba_products_live(
            report_path=publish_report_path,
            target_country=target_country,
            channels=channels,
            page_size=page_size,
            inventory_threshold=inventory_threshold,
            list_min_inventory=(int(list_min_inventory) if list_min_inventory is not None else None),
            candidate_pool_path=candidate_pool_path,
            prefer_candidate_pool=True,
            refresh_candidate_pool=False,
            resume=resume,
            candidate_spu_nos=([current_spu_no] if current_spu_no else None),
            max_successes=1,
        )
        return {
            "spu_no": current_spu_no,
            "title": str(context.get("title") or ""),
            "candidate_pool_summary": dict(candidate_result.get("summary") or {}),
            "publish_summary": dict(publish_result.get("summary") or {}),
            "publish_completed": bool(publish_result.get("completed")),
        }

    return _hook


def _load_json(path: str | Path) -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        return {}
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _validate_runtime_state(
    *,
    candidate_pool_path: str,
    publish_report_path: str,
) -> dict[str, Any]:
    archive_repository = SQLiteSupplierArchiveRepository()
    publish_mapping_repository = SQLitePublishMappingRepository()
    candidate_repository = SQLiteCandidatePoolRepository()
    candidate_payload = _load_json(candidate_pool_path)
    publish_report = _load_json(publish_report_path)
    mappings = publish_mapping_repository.list_publish_mappings()
    mapping_issues: list[dict[str, Any]] = []
    duplicates = Counter((record.supplier_product_id, record.supplier_sku) for record in mappings)
    for record in mappings:
        issues: list[str] = []
        if str(record.status or "").strip().lower() == "published":
            if not str(record.shopify_product_id or "").strip():
                issues.append("missing_shopify_product_id")
            if not str(record.shopify_variant_id or "").strip():
                issues.append("missing_shopify_variant_id")
        if duplicates[(record.supplier_product_id, record.supplier_sku)] > 1:
            issues.append("duplicate_mapping_key")
        if issues:
            mapping_issues.append(
                {
                    "supplier_spu_no": record.supplier_spu_no,
                    "supplier_sku": record.supplier_sku,
                    "issues": issues,
                }
            )
    return {
        "ok": len(mapping_issues) == 0,
        "mode": "validate-only",
        "archive_supplier_products": len(archive_repository.list_supplier_products()),
        "candidate_pool_entries": len(candidate_repository.list_qualified_candidates()),
        "candidate_pool_generated_at": str(candidate_payload.get("generated_at") or ""),
        "publish_mappings": len(mappings),
        "last_publish_completed": bool(publish_report.get("completed")),
        "mapping_issues": mapping_issues,
    }


def _repair_runtime_state(
    *,
    candidate_pool_path: str,
    target_country: str,
    inventory_threshold: int,
) -> dict[str, Any]:
    publish_mapping_repository = SQLitePublishMappingRepository()
    repaired_records = 0
    touched_spu_nos: set[str] = set()
    for record in publish_mapping_repository.list_publish_mappings():
        if str(record.status or "").strip().lower() == "published" and (
            not str(record.shopify_product_id or "").strip() or not str(record.shopify_variant_id or "").strip()
        ):
            record.status = "repair_required"
            record.last_error = "auto_repair_marked_missing_shopify_ids"
            publish_mapping_repository.save_publish_mapping(record)
            repaired_records += 1
            if str(record.supplier_spu_no or "").strip():
                touched_spu_nos.add(str(record.supplier_spu_no).strip())
    candidate_result = build_doba_publish_candidate_pool(
        candidate_pool_path=candidate_pool_path,
        target_country=target_country,
        inventory_threshold=inventory_threshold,
        incremental=True,
    )
    return {
        "ok": True,
        "mode": "repair-only",
        "repaired_mapping_records": repaired_records,
        "touched_spu_nos": sorted(touched_spu_nos),
        "candidate_pool_summary": dict(candidate_result.get("summary") or {}),
    }


def run_doba_pipeline(payload: dict[str, Any]) -> dict[str, Any]:
    mode = str(payload.get("mode") or "archive-and-publish").strip().lower()
    archive_report_path = str(payload.get("archive_report_path") or DEFAULT_ARCHIVE_REPORT_PATH)
    archive_checkpoint_path = str(payload.get("archive_checkpoint_path") or DEFAULT_ARCHIVE_CHECKPOINT_PATH)
    publish_report_path = str(payload.get("publish_report_path") or DEFAULT_PUBLISH_REPORT_PATH)
    candidate_pool_path = str(payload.get("candidate_pool_path") or DEFAULT_CANDIDATE_POOL_PATH)
    target_country = str(payload.get("target_country") or "US")
    inventory_threshold = int(payload.get("inventory_threshold") or 10)
    list_min_inventory = payload.get("list_min_inventory", 11)
    page_size = int(payload.get("page_size") or 20)
    channels = list(payload.get("channels") or ["Inbox", "Shop", "Pinterest", "Facebook & Instagram"])
    stream_publish = bool(payload.get("stream_publish", False))
    resume_enabled = not bool(payload.get("no_resume", False))
    post_archive_hook = (
        _make_stream_publish_hook(
            candidate_pool_path=candidate_pool_path,
            publish_report_path=publish_report_path,
            target_country=target_country,
            inventory_threshold=inventory_threshold,
            list_min_inventory=list_min_inventory,
            page_size=page_size,
            channels=channels,
            resume=resume_enabled,
        )
        if stream_publish
        else None
    )

    if mode == "validate-only":
        return _validate_runtime_state(
            candidate_pool_path=candidate_pool_path,
            publish_report_path=publish_report_path,
        )
    if mode == "repair-only":
        return _repair_runtime_state(
            candidate_pool_path=candidate_pool_path,
            target_country=target_country,
            inventory_threshold=inventory_threshold,
        )
    if mode == "candidate-only":
        return build_doba_publish_candidate_pool(
            candidate_pool_path=candidate_pool_path,
            target_country=target_country,
            inventory_threshold=inventory_threshold,
            incremental=bool(payload.get("incremental", True)),
        )
    if mode == "archive-only":
        return run_doba_online_archive(
            report_path=archive_report_path,
            checkpoint_path=archive_checkpoint_path,
            page_size=page_size,
            target_country=target_country,
            min_inventory=(int(list_min_inventory) if list_min_inventory is not None else None),
            archive_eligible_only=bool(payload.get("archive_eligible_only", True)),
            eligible_inventory_threshold=int(payload.get("eligible_inventory_threshold") or inventory_threshold),
            resume=resume_enabled,
            max_pages=payload.get("max_pages"),
            post_archive_hook=post_archive_hook,
        )
    if mode == "publish-only":
        return publish_doba_products_live(
            report_path=publish_report_path,
            target_country=target_country,
            channels=channels,
            page_size=page_size,
            inventory_threshold=inventory_threshold,
            list_min_inventory=(int(list_min_inventory) if list_min_inventory is not None else None),
            candidate_pool_path=candidate_pool_path,
            prefer_candidate_pool=not bool(payload.get("no_candidate_pool", False)),
            refresh_candidate_pool=bool(payload.get("refresh_candidate_pool", False)),
            resume=resume_enabled,
            max_successes=payload.get("max_successes"),
        )
    if mode == "dry-run":
        candidate_result = build_doba_publish_candidate_pool(
            candidate_pool_path=candidate_pool_path,
            target_country=target_country,
            inventory_threshold=inventory_threshold,
            incremental=bool(payload.get("incremental", True)),
        )
        return {
            "ok": True,
            "mode": "dry-run",
            "candidate_pool_summary": dict(candidate_result.get("summary") or {}),
            "publish_would_use_candidate_pool": not bool(payload.get("no_candidate_pool", False)),
            "publish_report_path": publish_report_path,
        }

    archive_result = run_doba_online_archive(
        report_path=archive_report_path,
        checkpoint_path=archive_checkpoint_path,
        page_size=page_size,
        target_country=target_country,
        min_inventory=(int(list_min_inventory) if list_min_inventory is not None else None),
        archive_eligible_only=bool(payload.get("archive_eligible_only", True)),
        eligible_inventory_threshold=int(payload.get("eligible_inventory_threshold") or inventory_threshold),
        resume=resume_enabled,
        max_pages=payload.get("max_pages"),
        post_archive_hook=post_archive_hook,
    )
    if stream_publish:
        last_stream_publish = dict(archive_result.get("last_stream_publish") or {})
        return {
            "ok": True,
            "mode": "archive-stream-publish",
            "archive_result": archive_result,
            "candidate_pool_result": {
                "summary": dict(last_stream_publish.get("candidate_pool_summary") or {}),
                "source": "stream_publish_hook",
            },
            "publish_result": {
                "summary": dict(last_stream_publish.get("publish_summary") or {}),
                "completed": bool(last_stream_publish.get("publish_completed")),
                "source": "stream_publish_hook",
            },
        }
    candidate_result = build_doba_publish_candidate_pool(
        candidate_pool_path=candidate_pool_path,
        target_country=target_country,
        inventory_threshold=inventory_threshold,
        incremental=bool(payload.get("incremental", True)),
    )
    publish_result = publish_doba_products_live(
        report_path=publish_report_path,
        target_country=target_country,
        channels=channels,
        page_size=page_size,
        inventory_threshold=inventory_threshold,
        list_min_inventory=(int(list_min_inventory) if list_min_inventory is not None else None),
        candidate_pool_path=candidate_pool_path,
        prefer_candidate_pool=not bool(payload.get("no_candidate_pool", False)),
        refresh_candidate_pool=False,
        resume=resume_enabled,
        max_successes=payload.get("max_successes"),
    )
    return {
        "ok": True,
        "mode": "archive-and-publish",
        "archive_result": archive_result,
        "candidate_pool_result": candidate_result,
        "publish_result": publish_result,
    }
