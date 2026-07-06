from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import sys

AGENT_ROOT = Path(__file__).resolve().parents[1]
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from service.category_optimization_service import get_category_optimization_service
from workflow.batch_io import read_json, read_jsonl


def _now_label() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _print_line(message: str) -> None:
    print(f"[{_now_label()}] {message}", flush=True)


class RollbackPrinter:
    def __call__(self, event: dict) -> None:
        if event.get("event") != "rollback_item":
            return
        item = event.get("item", {})
        _print_line(
            f"第 {event.get('index', 0)}/{event.get('total', 0)} 个商品回滚完成："
            f"标题：{item.get('title', '')}；"
            f"状态：{item.get('status', '')}；"
            f"类别已恢复：{'是' if item.get('category_restored') else '否'}；"
            f"恢复元字段数：{item.get('metafields_restored', 0)}；"
            f"删除新增元字段数：{item.get('metafields_deleted', 0)}；"
            f"说明：{item.get('detail', '')}。"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rollback a Shopify category optimization batch.")
    parser.add_argument("--source-file", required=True, help="批次审计文件 .audit.json 或结果文件 .results.jsonl")
    parser.add_argument("--limit", type=int, default=0, help="最多回滚多少个商品，0 表示全部")
    return parser


def _load_items(source_file: Path) -> list[dict]:
    if source_file.suffix == ".json":
        payload = read_json(source_file)
        rollback_source = payload.get("rollback_source") or ((payload.get("files") or {}).get("results_jsonl"))
        if not rollback_source:
            raise SystemExit("审计文件中未找到 rollback_source，无法执行回滚。")
        return read_jsonl(Path(rollback_source))
    if source_file.suffix == ".jsonl":
        return read_jsonl(source_file)
    raise SystemExit("仅支持 .audit.json 或 .results.jsonl 文件。")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    source_file = Path(args.source_file).expanduser()
    if not source_file.exists():
        raise SystemExit(f"未找到回滚来源文件：{source_file}")

    items = _load_items(source_file)
    if args.limit and args.limit > 0:
        items = items[: args.limit]

    _print_line(f"开始执行批次回滚，来源文件：{source_file}")
    _print_line(f"本次待回滚商品数：{len(items)}")

    service = get_category_optimization_service()
    printer = RollbackPrinter()
    result = service.rollback_items(items, progress_callback=printer)
    _print_line(result.get("summary", ""))


if __name__ == "__main__":
    main()
