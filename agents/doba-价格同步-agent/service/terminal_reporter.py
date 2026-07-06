from __future__ import annotations

from pathlib import Path
from typing import Any

from models.price_sync import PriceSyncBatch, PriceSyncItem


def _line(label: str, value: str) -> str:
    return f"[{label}] {value}"


def build_boot_lines(*, agent_name: str, current_dir: Path, project_root: Path, env_loaded: bool, doba_base_url: str, doba_token_loaded: bool, shopify_store: str, shopify_token_loaded: bool, runtime_dir: Path, registered_routes: list[str]) -> list[str]:
    return [
        _line("BOOT", f"Agent Name: {agent_name}"),
        _line("BOOT", f"Current Dir: {current_dir}"),
        _line("BOOT", f"Project Root: {project_root}"),
        _line("BOOT", f"Shared .env Loaded: {str(env_loaded).lower()}"),
        _line("BOOT", f"Doba Base URL: {doba_base_url}"),
        _line("BOOT", f"Doba Token Loaded: {str(doba_token_loaded).lower()}"),
        _line("BOOT", f"Shopify Store: {shopify_store or 'unconfigured'}"),
        _line("BOOT", f"Shopify Token Loaded: {str(shopify_token_loaded).lower()}"),
        _line("BOOT", f"Runtime Dir: {runtime_dir}"),
        _line("BOOT", f"Registered Routes: {', '.join(registered_routes)}"),
    ]


def build_batch_lines(*, batch: PriceSyncBatch, report_path: str, mapping_summary: dict[str, Any], doba_summary: dict[str, Any], shopify_summary: dict[str, Any], write_results: list[dict[str, Any]] | None = None, single_mode: bool = False) -> list[str]:
    lines: list[str] = []
    tag = "SINGLE" if single_mode else ("APPLY" if batch.mode == "apply" else "DRY-RUN")
    lines.append(_line(tag, f"batch_id={batch.batch_id}"))
    lines.append(_line(tag, f"store_name={batch.store_name}"))
    lines.append(_line(tag, f"sync_scope={mapping_summary.get('sync_scope', '')}"))
    lines.append(
        _line(
            "MAPPING",
            "total={total} / active={active} / duplicate={duplicate} / missing={missing}".format(
                total=mapping_summary.get("total", 0),
                active=mapping_summary.get("active", 0),
                duplicate=mapping_summary.get("duplicate", 0),
                missing=mapping_summary.get("missing", 0),
            ),
        )
    )
    lines.append(
        _line(
            "DOBA",
            "response_items={response_items} / normalized_items={normalized_items} / failed_items={failed_items}".format(
                response_items=doba_summary.get("response_items", 0),
                normalized_items=doba_summary.get("normalized_items", 0),
                failed_items=doba_summary.get("failed_items", 0),
            ),
        )
    )
    lines.append(
        _line(
            "SHOPIFY",
            "variants_requested={variants_requested} / variants_found={variants_found} / variants_missing={variants_missing}".format(
                variants_requested=shopify_summary.get("variants_requested", 0),
                variants_found=shopify_summary.get("variants_found", 0),
                variants_missing=shopify_summary.get("variants_missing", 0),
            ),
        )
    )
    for item in batch.items:
        lines.extend(build_item_lines(item=item, mode=batch.mode, single_mode=single_mode))
    if batch.mode == "apply":
        for result in write_results or []:
            if result.get("status") == "synced":
                lines.append(_line("WRITE-SUCCESS", f"{result['doba_sku']} / {result['shopify_variant_id']} / {result['old_price']} / {result['new_price']}"))
            elif result.get("status") == "failed":
                lines.append(_line("WRITE-FAILED", f"{result['doba_sku']} / {result['shopify_variant_id']} / {result['error_type']} / {result['error_message']}"))
    lines.append(
        _line(
            "SUMMARY",
            "planned={planned} / skipped={skipped} / manual_review={manual_review} / failed={failed} / shopify_writes={writes}".format(
                planned=sum(1 for item in batch.items if item.status == "planned"),
                skipped=batch.skipped_count,
                manual_review=batch.manual_review_count,
                failed=batch.failed_count,
                writes=sum(1 for result in (write_results or []) if result.get("status") == "synced"),
            ),
        )
    )
    lines.append(_line("REPORT", report_path))
    return lines


def build_mapping_build_lines(*, report: dict[str, Any]) -> list[str]:
    summary = report.get("summary", {})
    match_counts = summary.get("match_type_counts", {})
    outputs = report.get("outputs", {})
    return [
        _line("MAPPING-BUILD", f"batch_id={report.get('batch_id', '')}"),
        _line("MAPPING-BUILD", f"store_name={report.get('store_name', '')}"),
        _line("DOBA", f"total_skus={summary.get('total_doba_skus', 0)}"),
        _line("SHOPIFY", f"total_variants={summary.get('total_shopify_variants', 0)}"),
        _line(
            "MATCH",
            "previous_mapping={previous} / exact_sku={exact} / manual_import={manual}".format(
                previous=match_counts.get("previous_mapping", 0),
                exact=match_counts.get("exact_sku", 0),
                manual=match_counts.get("manual_import", 0),
            ),
        ),
        _line(
            "DUPLICATE",
            "duplicate_source={source} / duplicate_target={target}".format(
                source=summary.get("duplicate_source", 0),
                target=summary.get("duplicate_target", 0),
            ),
        ),
        _line(
            "UNMATCHED",
            "unmatched_doba={doba} / unmatched_shopify={shopify}".format(
                doba=summary.get("unmatched_doba", 0),
                shopify=summary.get("unmatched_shopify", 0),
            ),
        ),
        _line(
            "SUMMARY",
            "active={active} / candidate={candidate} / manual_review={manual_review} / duplicate={duplicate} / unmatched={unmatched}".format(
                active=summary.get("active_mappings", 0),
                candidate=summary.get("candidate_mappings", 0),
                manual_review=summary.get("manual_review", 0),
                duplicate=summary.get("duplicate_source", 0) + summary.get("duplicate_target", 0),
                unmatched=summary.get("unmatched_doba", 0) + summary.get("unmatched_shopify", 0),
            ),
        ),
        _line("OUTPUT", outputs.get("mappings", "")),
        _line("OUTPUT", outputs.get("review_csv", "")),
        _line("REPORT", report.get("report_path", "")),
    ]


def build_mapping_validate_lines(*, validation: dict[str, Any]) -> list[str]:
    return [
        _line("VALIDATE", f"store_name={validation.get('store_name', '')}"),
        _line("VALIDATE", f"mappings_total={validation.get('mappings_total', 0)}"),
        _line("VALIDATE", f"active_total={validation.get('active_total', 0)}"),
        _line("VALIDATE", f"duplicate_source={validation.get('duplicate_source', 0)}"),
        _line("VALIDATE", f"duplicate_target={validation.get('duplicate_target', 0)}"),
        _line("VALIDATE", f"result={validation.get('result', '')}"),
    ]


def build_item_lines(*, item: PriceSyncItem, mode: str, single_mode: bool = False) -> list[str]:
    reason_code = item.reason_codes[0] if item.reason_codes else ""
    if single_mode:
        return [
            _line("SINGLE", f"doba_sku={item.doba_sku}"),
            _line("MAPPING", f"found={str(bool(item.shopify_variant_id)).lower()}"),
            _line("SHOPIFY", f"current_price={item.old_price:.2f}"),
            _line("CALC", f"supplier_cost={item.supplier_cost:.2f} / shipping_cost={item.shipping_cost:.2f} / target_price={item.target_price:.2f}"),
            _line("DECISION", f"decision={item.decision} / reason_code={reason_code}"),
            _line("WILL_UPDATE_SHOPIFY", str(item.will_update_shopify).lower()),
        ]
    base = f"{item.doba_sku} / {item.shopify_variant_id or '-'} / {item.old_price:.2f} / {item.target_price:.2f} / {item.delta:.2f} / {item.decision} / {reason_code}"
    prefix = "WRITE-PLAN" if mode == "apply" and item.will_update_shopify else "ITEM"
    return [_line(prefix, base)]


def emit_lines(lines: list[str]) -> None:
    for line in lines:
        print(line)
