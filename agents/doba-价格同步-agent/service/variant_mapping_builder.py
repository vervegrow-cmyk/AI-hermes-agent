from __future__ import annotations

import json
from uuid import uuid4

from models.price_sync import DobaPriceSnapshot, utc_now_iso
from models.variant_mapping import ShopifyVariantSnapshot, VariantMappingBuildRequest, VariantMappingRecord
from service.doba_client import DobaPriceSyncClient
from service.mapping_repository import MappingRepository
from service.progress_logger import ProgressLogger
from service.shopify_variant_reader import ShopifyVariantReader


class VariantMappingBuilder:
    def __init__(
        self,
        *,
        doba_client: DobaPriceSyncClient | None = None,
        shopify_reader: ShopifyVariantReader | None = None,
        repository: MappingRepository | None = None,
    ) -> None:
        self.doba_client = doba_client or DobaPriceSyncClient()
        self.shopify_reader = shopify_reader or ShopifyVariantReader()
        self.repository = repository or MappingRepository()

    def build(self, request: VariantMappingBuildRequest | dict) -> dict:
        request = request if isinstance(request, VariantMappingBuildRequest) else VariantMappingBuildRequest.model_validate(request)
        store_name = request.store_name
        self.repository.ensure_layout()
        batch_id = str(uuid4())
        logger = ProgressLogger(
            root=self.repository.root,
            job_type="mapping_build",
            batch_id=batch_id,
            print_enabled=request.print_detail,
        )
        started_at = utc_now_iso()
        output_files: list[str] = []
        report: dict = {
            "batch_id": batch_id,
            "store_name": store_name,
            "started_at": started_at,
            "completed_at": "",
            "interrupted": False,
            "checkpoint_path": "",
            "summary": {},
            "items": [],
            "duplicates": [],
            "unmatched_doba": [],
            "unmatched_shopify": [],
            "errors": [],
            "outputs": {},
        }
        try:
            logger.step_start(phase="load_previous_mappings", message="load previous mappings")
            previous_records = self.repository.load_variant_records()
            logger.step_done(phase="load_previous_mappings", message="previous mappings loaded", current_step=1, total_steps=6)

            logger.step_start(phase="fetch_shopify_variants", message="fetch Shopify DOBA variants")
            shopify_variants = self.shopify_reader.list_variants(
                store_name=store_name,
                variants_override=request.shopify_variants or None,
            )
            logger.progress(
                phase="fetch_shopify_variants",
                current_step=2,
                total_steps=6,
                current_item=len(shopify_variants),
                total_items=len(shopify_variants),
                ok_count=len(shopify_variants),
                skipped_count=0,
                failed_count=0,
                message="shopify variants fetched",
            )
            logger.step_done(phase="fetch_shopify_variants", message="shopify variants fetched", current_step=2, total_steps=6)

            candidate_skus = self._collect_candidate_skus(store_name=store_name, shopify_variants=shopify_variants, previous_records=previous_records)
            logger.step_start(phase="fetch_doba_candidates", message="fetch Doba by Shopify candidate SKUs")
            doba_snapshots = self.doba_client.list_price_snapshots(
                store_name=store_name,
                sync_scope="single_sku",
                skus=candidate_skus,
                snapshots_override=request.doba_snapshots or None,
            )
            logger.progress(
                phase="fetch_doba_candidates",
                current_step=3,
                total_steps=6,
                current_item=len(doba_snapshots),
                total_items=len(candidate_skus),
                ok_count=len(doba_snapshots),
                skipped_count=max(len(candidate_skus) - len(doba_snapshots), 0),
                failed_count=0,
                message="doba candidate lookup finished",
            )
            logger.step_done(phase="fetch_doba_candidates", message="doba candidate lookup finished", current_step=3, total_steps=6)

            built_records = self._build_records(
                store_name=store_name,
                shopify_variants=shopify_variants,
                previous_records=previous_records,
                doba_snapshots=doba_snapshots,
                logger=logger,
            )

            logger.step_start(phase="write_outputs", message="write mapping runtime outputs")
            mapping_path = self.repository.save_variant_records(built_records)
            output_files.append(mapping_path)
            review_rows = [record.model_dump(mode="json") for record in built_records if record.mapping_status != "active"]
            candidates_path = self.repository.save_candidates(review_rows)
            output_files.append(candidates_path)
            review_path = self.repository.save_review_rows(review_rows)
            output_files.append(review_path)
            unmatched_doba_rows = [record.model_dump(mode="json") for record in built_records if record.mapping_status == "unmatched_doba"]
            unmatched_doba_path = self.repository.save_unmatched_doba(unmatched_doba_rows)
            output_files.append(unmatched_doba_path)
            unmatched_shopify_rows = [record.model_dump(mode="json") for record in built_records if record.mapping_status == "unmatched_shopify"]
            unmatched_shopify_path = self.repository.save_unmatched_shopify(unmatched_shopify_rows)
            output_files.append(unmatched_shopify_path)
            duplicates = {
                "duplicate_source": [record.model_dump(mode="json") for record in built_records if record.mapping_status == "duplicate_source"],
                "duplicate_target": [record.model_dump(mode="json") for record in built_records if record.mapping_status == "duplicate_target"],
            }
            duplicates_path = self.repository.save_duplicates(duplicates)
            output_files.append(duplicates_path)
            for path in output_files:
                logger.output(path)
            summary = self.repository.build_mapping_stats(
                store_name=store_name,
                records=built_records,
                total_shopify_variants=len(shopify_variants),
                total_doba_skus=len(candidate_skus),
            )
            summary["match_type_counts"] = self._count_match_types(built_records)
            report.update(
                {
                    "completed_at": utc_now_iso(),
                    "summary": summary,
                    "items": [record.model_dump(mode="json") for record in built_records],
                    "duplicates": duplicates["duplicate_source"] + duplicates["duplicate_target"],
                    "unmatched_doba": unmatched_doba_rows,
                    "unmatched_shopify": unmatched_shopify_rows,
                    "outputs": {
                        "mappings": mapping_path,
                        "candidates": candidates_path,
                        "review_csv": review_path,
                        "unmatched_doba": unmatched_doba_path,
                        "unmatched_shopify": unmatched_shopify_path,
                        "duplicates": duplicates_path,
                    },
                }
            )
            report_path = self._write_report(batch_id=batch_id, report=report)
            report["report_path"] = report_path
            logger.output(report_path)
            logger.step_done(phase="write_outputs", message="mapping outputs written", current_step=6, total_steps=6)
            return report
        except KeyboardInterrupt:
            checkpoint_path = logger.save_checkpoint(phase="interrupted", index=0, total_items=0, last_output_files=output_files, reason_code="interrupted_by_user", interrupted=True)
            logger.interrupted(phase="interrupted", index=0, total=0, reason_code="interrupted_by_user", checkpoint_path=checkpoint_path)
            report.update({"completed_at": utc_now_iso(), "interrupted": True, "checkpoint_path": checkpoint_path, "errors": ["interrupted_by_user"]})
            report["report_path"] = self._write_report(batch_id=batch_id, report=report)
            raise
        except Exception as exc:
            logger.error(phase="runtime_exception", reason_code="runtime_exception", error_message=str(exc))
            checkpoint_path = logger.save_checkpoint(phase="runtime_exception", index=0, total_items=0, last_output_files=output_files, reason_code="runtime_exception", interrupted=False)
            report.update({"completed_at": utc_now_iso(), "checkpoint_path": checkpoint_path, "errors": [str(exc)]})
            report["report_path"] = self._write_report(batch_id=batch_id, report=report)
            raise

    def _collect_candidate_skus(
        self,
        *,
        store_name: str,
        shopify_variants: list[ShopifyVariantSnapshot],
        previous_records: list[VariantMappingRecord],
    ) -> list[str]:
        values: list[str] = []
        for variant in shopify_variants:
            if variant.shopify_sku.strip():
                values.append(variant.shopify_sku.strip())
            if variant.doba_sku_metafield.strip():
                values.append(variant.doba_sku_metafield.strip())
        for record in previous_records:
            if record.store_name == store_name and record.doba_sku:
                values.append(record.doba_sku.strip())
        deduped: list[str] = []
        seen: set[str] = set()
        for value in values:
            if not value or value in seen:
                continue
            seen.add(value)
            deduped.append(value)
        return deduped

    def _build_records(
        self,
        *,
        store_name: str,
        shopify_variants: list[ShopifyVariantSnapshot],
        previous_records: list[VariantMappingRecord],
        doba_snapshots: list[DobaPriceSnapshot],
        logger: ProgressLogger,
    ) -> list[VariantMappingRecord]:
        records: list[VariantMappingRecord] = []
        snapshots_by_sku = {item.doba_sku: item for item in doba_snapshots}
        previous_by_variant = {
            item.shopify_variant_id: item
            for item in previous_records
            if item.store_name == store_name and item.mapping_status == "active" and item.shopify_variant_id
        }
        source_counts: dict[str, int] = {}
        target_counts: dict[str, int] = {}

        logger.step_start(phase="match_previous_mapping", message="match previous mappings")
        for index, variant in enumerate(shopify_variants, start=1):
            previous = previous_by_variant.get(variant.shopify_variant_id)
            if previous:
                candidate_skus = [value for value in [variant.doba_sku_metafield.strip(), variant.shopify_sku.strip()] if value]
                conflicts = [value for value in candidate_skus if value in snapshots_by_sku and value != previous.doba_sku]
                if conflicts:
                    previous_record = VariantMappingRecord(
                        store_name=store_name,
                        supplier="doba",
                        doba_product_id=previous.doba_product_id,
                        doba_sku=previous.doba_sku,
                        shopify_product_id=variant.shopify_product_id,
                        shopify_variant_id=variant.shopify_variant_id,
                        shopify_sku=variant.shopify_sku,
                        shopify_product_title=variant.shopify_product_title,
                        shopify_variant_title=variant.shopify_variant_title,
                        match_type="previous_mapping",
                        match_confidence=0,
                        mapping_status="duplicate_target",
                        reason_code="duplicate_target_mapping",
                        last_price_hash=previous.last_price_hash,
                        last_doba_updated_at=previous.last_doba_updated_at,
                    )
                    records.append(previous_record)
                    logger.item(phase="match_previous_mapping", index=index, total=len(shopify_variants), doba_sku=previous_record.doba_sku, shopify_variant_id=previous_record.shopify_variant_id, status=previous_record.mapping_status, reason_code=previous_record.reason_code)
                    for conflict_sku in conflicts:
                        snapshot = snapshots_by_sku[conflict_sku]
                        record = VariantMappingRecord(
                            store_name=store_name,
                            supplier="doba",
                            doba_product_id=snapshot.doba_product_id,
                            doba_sku=snapshot.doba_sku,
                            shopify_product_id=variant.shopify_product_id,
                            shopify_variant_id=variant.shopify_variant_id,
                            shopify_sku=variant.shopify_sku,
                            shopify_product_title=variant.shopify_product_title,
                            shopify_variant_title=variant.shopify_variant_title,
                            match_type="duplicate",
                            match_confidence=0,
                            mapping_status="duplicate_target",
                            reason_code="duplicate_target_mapping",
                            last_price_hash=snapshot.raw_hash,
                            last_doba_updated_at=snapshot.source_updated_at,
                        )
                        records.append(record)
                        logger.item(phase="match_previous_mapping", index=index, total=len(shopify_variants), doba_sku=record.doba_sku, shopify_variant_id=record.shopify_variant_id, status=record.mapping_status, reason_code=record.reason_code)
                    continue
                record = VariantMappingRecord(
                    store_name=store_name,
                    supplier="doba",
                    doba_product_id=previous.doba_product_id,
                    doba_sku=previous.doba_sku,
                    shopify_product_id=variant.shopify_product_id,
                    shopify_variant_id=variant.shopify_variant_id,
                    shopify_sku=variant.shopify_sku,
                    shopify_product_title=variant.shopify_product_title,
                    shopify_variant_title=variant.shopify_variant_title,
                    match_type="previous_mapping",
                    match_confidence=100,
                    mapping_status="active",
                    reason_code="matched_by_previous_mapping",
                    last_price_hash=previous.last_price_hash,
                    last_doba_updated_at=previous.last_doba_updated_at,
                )
                records.append(record)
                source_counts[record.doba_sku] = source_counts.get(record.doba_sku, 0) + 1
                target_counts[record.shopify_variant_id] = target_counts.get(record.shopify_variant_id, 0) + 1
                logger.item(phase="match_previous_mapping", index=index, total=len(shopify_variants), doba_sku=record.doba_sku, shopify_variant_id=record.shopify_variant_id, status=record.mapping_status, reason_code=record.reason_code)
        logger.step_done(phase="match_previous_mapping", message="previous mapping pass finished", current_step=4, total_steps=6)

        logger.step_start(phase="match_exact_sku", message="match Shopify candidates to Doba SKUs")
        existing_targets = {item.shopify_variant_id for item in records}
        for index, variant in enumerate(shopify_variants, start=1):
            if variant.shopify_variant_id in existing_targets:
                continue
            candidate_skus = [value for value in [variant.doba_sku_metafield.strip(), variant.shopify_sku.strip()] if value]
            matched_snapshots = [snapshots_by_sku[value] for value in candidate_skus if value in snapshots_by_sku]
            if len(matched_snapshots) == 1:
                snapshot = matched_snapshots[0]
                record = VariantMappingRecord(
                    store_name=store_name,
                    supplier="doba",
                    doba_product_id=snapshot.doba_product_id,
                    doba_sku=snapshot.doba_sku,
                    shopify_product_id=variant.shopify_product_id,
                    shopify_variant_id=variant.shopify_variant_id,
                    shopify_sku=variant.shopify_sku,
                    shopify_product_title=variant.shopify_product_title,
                    shopify_variant_title=variant.shopify_variant_title,
                    match_type="exact_sku" if snapshot.doba_sku == variant.shopify_sku else "metafield_doba_sku",
                    match_confidence=100,
                    mapping_status="active",
                    reason_code="matched_by_exact_sku" if snapshot.doba_sku == variant.shopify_sku else "matched_by_metafield_doba_sku",
                    last_price_hash=snapshot.raw_hash,
                    last_doba_updated_at=snapshot.source_updated_at,
                )
            elif len(matched_snapshots) > 1:
                snapshot = matched_snapshots[0]
                record = VariantMappingRecord(
                    store_name=store_name,
                    supplier="doba",
                    doba_product_id=snapshot.doba_product_id,
                    doba_sku=snapshot.doba_sku,
                    shopify_product_id=variant.shopify_product_id,
                    shopify_variant_id=variant.shopify_variant_id,
                    shopify_sku=variant.shopify_sku,
                    shopify_product_title=variant.shopify_product_title,
                    shopify_variant_title=variant.shopify_variant_title,
                    match_type="duplicate",
                    match_confidence=0,
                    mapping_status="duplicate_source",
                    reason_code="duplicate_source_mapping",
                )
            else:
                if candidate_skus:
                    record = VariantMappingRecord(
                        store_name=store_name,
                        supplier="doba",
                        doba_sku=candidate_skus[0],
                        shopify_product_id=variant.shopify_product_id,
                        shopify_variant_id=variant.shopify_variant_id,
                        shopify_sku=variant.shopify_sku,
                        shopify_product_title=variant.shopify_product_title,
                        shopify_variant_title=variant.shopify_variant_title,
                        match_type="unknown",
                        match_confidence=0,
                        mapping_status="unmatched_doba",
                        reason_code="doba_lookup_endpoint_missing",
                    )
                else:
                    record = VariantMappingRecord(
                        store_name=store_name,
                        supplier="doba",
                        doba_sku="",
                        shopify_product_id=variant.shopify_product_id,
                        shopify_variant_id=variant.shopify_variant_id,
                        shopify_sku=variant.shopify_sku,
                        shopify_product_title=variant.shopify_product_title,
                        shopify_variant_title=variant.shopify_variant_title,
                        match_type="unknown",
                        match_confidence=0,
                        mapping_status="unmatched_shopify",
                        reason_code="unmatched_shopify",
                    )
            records.append(record)
            source_counts[record.doba_sku] = source_counts.get(record.doba_sku, 0) + (1 if record.doba_sku else 0)
            target_counts[record.shopify_variant_id] = target_counts.get(record.shopify_variant_id, 0) + 1
            logger.item(phase="match_exact_sku", index=index, total=len(shopify_variants), doba_sku=record.doba_sku, shopify_variant_id=record.shopify_variant_id, status=record.mapping_status, reason_code=record.reason_code)
        logger.step_done(phase="match_exact_sku", message="shopify-driven matching finished", current_step=5, total_steps=6)

        self._mark_duplicates(records=records, source_counts=source_counts, target_counts=target_counts, logger=logger)
        self._append_unmatched_shopify(records=records, shopify_variants=shopify_variants, logger=logger)
        return records

    def _mark_duplicates(
        self,
        *,
        records: list[VariantMappingRecord],
        source_counts: dict[str, int],
        target_counts: dict[str, int],
        logger: ProgressLogger,
    ) -> None:
        for item in records:
            if item.mapping_status != "active":
                continue
            if item.doba_sku and source_counts.get(item.doba_sku, 0) > 1:
                item.mapping_status = "duplicate_source"
                item.reason_code = "duplicate_source_mapping"
                item.match_confidence = 0
                logger.item(phase="detect_unmatched", index=0, total=0, doba_sku=item.doba_sku, shopify_variant_id=item.shopify_variant_id, status=item.mapping_status, reason_code=item.reason_code)
            elif item.shopify_variant_id and target_counts.get(item.shopify_variant_id, 0) > 1:
                item.mapping_status = "duplicate_target"
                item.reason_code = "duplicate_target_mapping"
                item.match_confidence = 0
                logger.item(phase="detect_unmatched", index=0, total=0, doba_sku=item.doba_sku, shopify_variant_id=item.shopify_variant_id, status=item.mapping_status, reason_code=item.reason_code)

    def _append_unmatched_shopify(
        self,
        *,
        records: list[VariantMappingRecord],
        shopify_variants: list[ShopifyVariantSnapshot],
        logger: ProgressLogger,
    ) -> None:
        logger.step_start(phase="detect_unmatched", message="detect unmatched Shopify variants")
        existing_targets = {item.shopify_variant_id for item in records if item.shopify_variant_id}
        count = 0
        for variant in shopify_variants:
            if variant.shopify_variant_id in existing_targets:
                continue
            count += 1
            record = VariantMappingRecord(
                store_name=variant.store_name,
                supplier="doba",
                doba_sku="",
                shopify_product_id=variant.shopify_product_id,
                shopify_variant_id=variant.shopify_variant_id,
                shopify_sku=variant.shopify_sku,
                shopify_product_title=variant.shopify_product_title,
                shopify_variant_title=variant.shopify_variant_title,
                match_type="unknown",
                match_confidence=0,
                mapping_status="unmatched_shopify",
                reason_code="unmatched_shopify",
            )
            records.append(record)
            logger.item(phase="detect_unmatched", index=count, total=max(len(shopify_variants), 1), doba_sku="", shopify_variant_id=record.shopify_variant_id, status=record.mapping_status, reason_code=record.reason_code)
        logger.step_done(phase="detect_unmatched", message="unmatched detection finished", current_step=6, total_steps=6)

    def _count_match_types(self, records: list[VariantMappingRecord]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for record in records:
            counts[record.match_type] = counts.get(record.match_type, 0) + 1
        return counts

    def _write_report(self, *, batch_id: str, report: dict) -> str:
        reports_root = self.repository.root / "reports"
        reports_root.mkdir(parents=True, exist_ok=True)
        path = reports_root / f"mapping_build_{batch_id}.json"
        path.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
        return str(path.resolve())
