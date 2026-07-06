from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import re
import sys
from typing import Any

AGENT_ROOT = Path(__file__).resolve().parents[1]
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from models.category_sync import CategorySyncRequest
from service.category_optimization_service import get_category_optimization_service
from workflow.batch_io import append_jsonl, now_label, read_json, read_jsonl, write_csv, write_json


def _now_label() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _print_line(message: str) -> None:
    print(f"[{_now_label()}] {message}", flush=True)


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (value or "").strip().lower()).strip("-")


def _default_checkpoint_file(args: argparse.Namespace) -> Path:
    runs_dir = AGENT_ROOT / "workflow" / "runs"
    scope = _slugify(args.product_query) if args.product_query else "all-products"
    mode = args.mode or "dry-run"
    return runs_dir / f"category-optimization-{mode}-{scope}.checkpoint.json"


def _load_shopify_suggestions(path_value: str) -> dict[str, Any]:
    if not path_value:
        return {}
    path = Path(path_value).expanduser()
    if not path.is_absolute():
        path = (AGENT_ROOT / path).resolve()
    if not path.exists():
        _print_line(
            f"未找到 Shopify 建议文件：{path}。本次将自动跳过前端建议输入，"
            "改为直接使用 Shopify 数据 + DeepSeek 决策链。"
        )
        return {}
    return read_json(path)


class CheckpointStore:
    def __init__(
        self,
        checkpoint_file: Path,
        *,
        mode: str,
        product_query: str,
        max_items: int,
        apply_metafields: bool,
        store_name: str,
    ) -> None:
        self.checkpoint_file = checkpoint_file
        self.result_file = checkpoint_file.with_suffix(".results.jsonl")
        self.review_jsonl_file = checkpoint_file.with_suffix(".review.jsonl")
        self.review_csv_file = checkpoint_file.with_suffix(".review.csv")
        self.failed_jsonl_file = checkpoint_file.with_suffix(".failed.jsonl")
        self.failed_csv_file = checkpoint_file.with_suffix(".failed.csv")
        self.audit_report_file = checkpoint_file.with_suffix(".audit.json")
        self.mode = mode
        self.product_query = product_query
        self.max_items = max_items
        self.apply_metafields = apply_metafields
        self.store_name = store_name
        self.data: dict[str, Any] = {}

    def exists(self) -> bool:
        return self.checkpoint_file.exists()

    def reset(self) -> None:
        for path in [
            self.checkpoint_file,
            self.result_file,
            self.review_jsonl_file,
            self.review_csv_file,
            self.failed_jsonl_file,
            self.failed_csv_file,
            self.audit_report_file,
        ]:
            if path.exists():
                path.unlink()

    def load_or_initialize(self, *, resume: bool) -> dict[str, Any]:
        if resume and self.checkpoint_file.exists():
            self.data = read_json(self.checkpoint_file)
            self._validate_compatibility()
            self.data["status"] = "running"
            self.data["updated_at"] = _now_label()
            self._save()
            return self.data

        self.data = {
            "version": 1,
            "status": "running",
            "mode": self.mode,
            "product_query": self.product_query,
            "max_items": self.max_items,
            "apply_metafields": self.apply_metafields,
            "store_name": self.store_name,
            "started_at": _now_label(),
            "updated_at": _now_label(),
            "processed_count": 0,
            "applied_count": 0,
            "review_count": 0,
            "failed_count": 0,
            "processed_product_ids": [],
            "files": self._files_payload(),
        }
        self._save()
        return self.data

    def processed_product_ids(self) -> list[str]:
        return list(self.data.get("processed_product_ids", []))

    def record_item(self, item: dict[str, Any]) -> None:
        product_id = item.get("product_id", "")
        processed = self.data.setdefault("processed_product_ids", [])
        if product_id and product_id not in processed:
            processed.append(product_id)

        self.data["processed_count"] = len(processed)
        apply_result = item.get("apply_result") or {}
        if apply_result.get("category_updated") or apply_result.get("metafields_updated"):
            self.data["applied_count"] = int(self.data.get("applied_count", 0)) + 1
        if item.get("needs_review"):
            self.data["review_count"] = int(self.data.get("review_count", 0)) + 1
        if self._is_failed_item(item):
            self.data["failed_count"] = int(self.data.get("failed_count", 0)) + 1
        self.data["updated_at"] = _now_label()

        append_jsonl(self.result_file, item)
        if self._is_review_item(item):
            append_jsonl(self.review_jsonl_file, self._build_review_row(item))
        if self._is_failed_item(item):
            append_jsonl(self.failed_jsonl_file, self._build_failed_row(item))

        self._save()

    def mark_interrupted(self) -> None:
        self.data["status"] = "interrupted"
        self.data["updated_at"] = _now_label()
        self.data["summary"] = (
            f"任务已中断，当前已处理 {self.data.get('processed_count', 0)} 个商品，"
            f"成功修改 {self.data.get('applied_count', 0)} 个，需要人工复核 {self.data.get('review_count', 0)} 个，"
            f"写回失败 {self.data.get('failed_count', 0)} 个。"
        )
        self._build_exports()
        self._save()

    def mark_finished(self, summary: str) -> None:
        self.data["status"] = "completed"
        self.data["updated_at"] = _now_label()
        self.data["summary"] = summary
        self._build_exports()
        self._save()

    def _save(self) -> None:
        write_json(self.checkpoint_file, self.data)

    def _validate_compatibility(self) -> None:
        mismatches = []
        if self.data.get("mode") != self.mode:
            mismatches.append("mode")
        if self.data.get("product_query", "") != self.product_query:
            mismatches.append("product_query")
        if int(self.data.get("max_items", 0)) != int(self.max_items):
            mismatches.append("max_items")
        if bool(self.data.get("apply_metafields", True)) != bool(self.apply_metafields):
            mismatches.append("apply_metafields")
        if (self.data.get("store_name") or "") != self.store_name:
            mismatches.append("store_name")
        if mismatches:
            mismatch_text = ", ".join(mismatches)
            raise SystemExit(
                f"检查点文件与当前命令不匹配，冲突字段：{mismatch_text}。"
                f" 如需重跑，请加 --reset-checkpoint，或改用新的 --checkpoint-file。"
            )

    def _files_payload(self) -> dict[str, str]:
        return {
            "checkpoint": str(self.checkpoint_file),
            "results_jsonl": str(self.result_file),
            "review_jsonl": str(self.review_jsonl_file),
            "review_csv": str(self.review_csv_file),
            "failed_jsonl": str(self.failed_jsonl_file),
            "failed_csv": str(self.failed_csv_file),
            "audit_report": str(self.audit_report_file),
        }

    def _build_exports(self) -> None:
        result_items = read_jsonl(self.result_file)
        review_rows = [self._build_review_row(item) for item in result_items if self._is_review_item(item)]
        failed_rows = [self._build_failed_row(item) for item in result_items if self._is_failed_item(item)]
        write_csv(
            self.review_csv_file,
            review_rows,
            [
                "product_id",
                "title",
                "current_category",
                "suggested_category",
                "risk_level",
                "source",
                "decision_reason",
            ],
        )
        write_csv(
            self.failed_csv_file,
            failed_rows,
            [
                "product_id",
                "title",
                "current_category",
                "suggested_category",
                "failure_scope",
                "failure_reason",
                "failure_detail",
            ],
        )
        audit_payload = {
            "generated_at": now_label(),
            "mode": self.mode,
            "store_name": self.store_name,
            "product_query": self.product_query,
            "max_items": self.max_items,
            "summary": self.data.get("summary", ""),
            "counts": {
                "processed": self.data.get("processed_count", 0),
                "applied": self.data.get("applied_count", 0),
                "review": self.data.get("review_count", 0),
                "failed": self.data.get("failed_count", 0),
            },
            "files": self._files_payload(),
            "rollback_source": str(self.result_file),
        }
        write_json(self.audit_report_file, audit_payload)

    def _build_review_row(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "product_id": item.get("product_id", ""),
            "title": item.get("title", ""),
            "current_category": ((item.get("current_category") or {}).get("full_name") or ""),
            "suggested_category": ((item.get("suggested_category") or {}).get("full_name") or ""),
            "risk_level": item.get("risk_level", ""),
            "source": item.get("source", ""),
            "decision_reason": item.get("decision_reason", ""),
        }

    def _build_failed_row(self, item: dict[str, Any]) -> dict[str, Any]:
        apply_result = item.get("apply_result") or {}
        first_error = (apply_result.get("errors") or [{}])[0]
        if not any(first_error.values() if isinstance(first_error, dict) else []):
            first_skipped = next(
                (
                    skipped
                    for skipped in (apply_result.get("skipped_metafields") or [])
                    if skipped.get("reason") in {"shopify_validation_error", "shopify_metafield_exception"}
                ),
                {},
            )
            first_error = {
                "scope": f"metafield:{first_skipped.get('key', '')}" if first_skipped else "",
                "reason": first_skipped.get("reason", ""),
                "detail": first_skipped.get("detail", ""),
            }
        return {
            "product_id": item.get("product_id", ""),
            "title": item.get("title", ""),
            "current_category": ((item.get("current_category") or {}).get("full_name") or ""),
            "suggested_category": ((item.get("suggested_category") or {}).get("full_name") or ""),
            "failure_scope": first_error.get("scope", ""),
            "failure_reason": first_error.get("reason", ""),
            "failure_detail": first_error.get("detail", ""),
        }

    def _is_review_item(self, item: dict[str, Any]) -> bool:
        return bool(item.get("needs_review")) or (item.get("risk_level") == "high")

    def _is_failed_item(self, item: dict[str, Any]) -> bool:
        apply_result = item.get("apply_result") or {}
        if apply_result.get("status") == "apply_failed":
            return True
        return any(
            skipped.get("reason") in {"shopify_validation_error", "shopify_metafield_exception"}
            for skipped in (apply_result.get("skipped_metafields") or [])
        )


class ProgressPrinter:
    def __init__(self, checkpoint: CheckpointStore | None = None) -> None:
        self.checkpoint = checkpoint
        self.processed = 0
        self.applied = 0
        self.review = 0

    def __call__(self, event: dict) -> None:
        if event.get("event") == "stage":
            self._print_stage(event)
            return
        self._print_item(event)

    def _print_stage(self, event: dict) -> None:
        stage = event.get("stage", "")
        if stage == "start":
            max_items = event.get("max_items") or "不限"
            product_query = event.get("product_query") or "未提供"
            _print_line(
                f"开始执行分类优化任务，模式：{event.get('mode')}，店铺：{event.get('store')}，"
                f"筛选条件：{product_query}，最大处理数：{max_items}"
            )
            return
        if stage == "products_loaded":
            _print_line(f"已加载待处理商品 {event.get('count', 0)} 个。")
            return
        if stage == "scan_progress":
            mode_label = "全店扫描" if event.get("mode") == "all_products" else "筛选扫描"
            _print_line(
                f"{mode_label}进行中：第 {event.get('page', 0)} 页，本页读取 {event.get('page_count', 0)} 个，"
                f"当前累计已加载 {event.get('loaded_count', 0)} 个商品。"
            )
            return
        if stage == "finished":
            _print_line(
                f"任务完成：共处理 {event.get('processed_count', 0)} 个商品，"
                f"成功修改 {event.get('applied_count', 0)} 个，需要人工复核 {event.get('review_count', 0)} 个。"
            )
            return
        _print_line(f"阶段更新：{stage}")

    def _print_item(self, event: dict) -> None:
        item = event.get("item", {})
        self.processed += 1
        apply_result = item.get("apply_result") or {}
        category_updated = bool(apply_result.get("category_updated"))
        metafields_updated = int(apply_result.get("metafields_updated", 0) or 0)
        if category_updated or metafields_updated:
            self.applied += 1
        if item.get("needs_review"):
            self.review += 1
        if self.checkpoint is not None:
            self.checkpoint.record_item(item)

        current_category = (item.get("current_category") or {}).get("full_name") or "未设置"
        suggested_category = (item.get("suggested_category") or {}).get("full_name") or "未生成"
        metafield_count = len(item.get("suggested_metafields") or [])
        status = apply_result.get("status", "")

        if status == "applied":
            result_text = (
                f"已成功优化并写回 Shopify（类别已更新：{'是' if category_updated else '否'}，"
                f"元字段写回数：{metafields_updated}）"
            )
        elif status == "unchanged":
            result_text = "已检查完成，无需修改"
        elif status == "apply_failed":
            result_text = "写回未完成，已记录错误并继续处理后续商品"
        elif status == "review_required":
            result_text = "已识别为高风险，待人工复核"
        elif status == "dry_run":
            result_text = "dry-run 已生成建议，未写回"
        else:
            result_text = status or "未知状态"

        _print_line(
            f"第 {event.get('index', 0)}/{event.get('total', 0)} 个商品处理完成："
            f"标题：{item.get('title', '')}；"
            f"当前类别：{current_category}；"
            f"建议类别：{suggested_category}；"
            f"建议来源：{item.get('source', '')}；"
            f"风险等级：{item.get('risk_level', '')}；"
            f"建议元字段数：{metafield_count}；"
            f"执行结果：{result_text}。"
        )
        _print_line(f"中文决策说明：{item.get('decision_reason', '') or '无'}")
        for error in apply_result.get("errors") or []:
            _print_line(
                f"写回错误：范围：{error.get('scope', 'unknown')}；"
                f"原因：{error.get('reason', 'unknown')}；"
                f"详情：{error.get('detail', '无')}。"
            )
        for skipped in apply_result.get("skipped_metafields") or []:
            if skipped.get("reason") in {"shopify_validation_error", "shopify_metafield_exception"}:
                _print_line(
                    f"元字段跳过：字段：{skipped.get('key', '')}；"
                    f"原因：{skipped.get('reason', 'unknown')}；"
                    f"详情：{skipped.get('detail', '无')}。"
                )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Shopify category optimization with Chinese terminal details.")
    parser.add_argument("--mode", choices=["dry-run", "apply"], default="dry-run", help="执行模式")
    parser.add_argument("--product-query", default="", help="Shopify 商品筛选 query")
    parser.add_argument("--candidate-category", default="", help="可选的候选类目提示")
    parser.add_argument("--max-items", type=int, default=0, help="最大处理商品数，0 表示全店全部商品")
    parser.add_argument("--product-id", action="append", default=[], help="指定 Shopify Product GID，可重复传入")
    parser.add_argument("--store-name", default="", help="店铺域名，默认使用共享环境变量")
    parser.add_argument("--no-apply-metafields", action="store_true", help="apply 模式下不写回元字段")
    parser.add_argument("--force-apply-review-items", action="store_true", help="高风险或原本待人工复核的后端决策也直接写回 Shopify，不再进入人工复核")
    parser.add_argument("--checkpoint-file", default="", help="检查点文件路径，默认自动生成")
    parser.add_argument("--no-resume", action="store_true", help="本次执行不读取已有检查点")
    parser.add_argument("--reset-checkpoint", action="store_true", help="执行前重置检查点和结果文件")
    parser.add_argument("--shopify-suggestions-file", default="", help="前端建议抓取结果 JSON 文件")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    checkpoint_file = Path(args.checkpoint_file).expanduser() if args.checkpoint_file else _default_checkpoint_file(args)
    checkpoint = CheckpointStore(
        checkpoint_file,
        mode=args.mode,
        product_query=args.product_query,
        max_items=args.max_items,
        apply_metafields=not args.no_apply_metafields,
        store_name=args.store_name,
    )
    if args.reset_checkpoint:
        checkpoint.reset()

    checkpoint_data = checkpoint.load_or_initialize(resume=not args.no_resume)
    resumed_count = len(checkpoint.processed_product_ids())

    _print_line(f"检查点文件：{checkpoint.checkpoint_file}")
    _print_line(f"结果明细文件：{checkpoint.result_file}")
    _print_line(f"复核清单文件：{checkpoint.review_csv_file}")
    _print_line(f"失败清单文件：{checkpoint.failed_csv_file}")
    _print_line(f"审计报告文件：{checkpoint.audit_report_file}")
    if resumed_count:
        _print_line(f"检测到历史进度，已完成 {resumed_count} 个商品，本次将从断点继续执行。")
    else:
        _print_line("未检测到可恢复进度，本次将从头开始执行。")

    request = CategorySyncRequest(
        store_name=args.store_name,
        mode=args.mode,
        product_query=args.product_query,
        candidate_category=args.candidate_category,
        max_items=args.max_items,
        product_ids=args.product_id,
        exclude_product_ids=checkpoint.processed_product_ids(),
        shopify_suggestions=_load_shopify_suggestions(args.shopify_suggestions_file),
        apply_metafields=not args.no_apply_metafields,
        force_apply_review_items=args.force_apply_review_items,
    )

    service = get_category_optimization_service()
    printer = ProgressPrinter(checkpoint=checkpoint)
    try:
        result = service.run(
            request,
            task="category-optimization-cli",
            progress_callback=printer,
        )
    except KeyboardInterrupt:
        checkpoint.mark_interrupted()
        _print_line(
            f"用户已中断执行。已处理 {printer.processed} 个商品，"
            f"已成功修改 {printer.applied} 个，需要人工复核 {printer.review} 个。"
        )
        _print_line("检查点已保存，下次使用相同命令可继续执行。")
        raise SystemExit(130)

    checkpoint.mark_finished(result.get("summary", ""))
    _print_line(f"任务摘要：{result.get('summary', '')}")
    _print_line("检查点已更新完成。如需重新从头跑，请在命令后加 --reset-checkpoint。")


if __name__ == "__main__":
    main()
