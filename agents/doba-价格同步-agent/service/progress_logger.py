from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter
from typing import Any

from models.price_sync import utc_now_iso


class ProgressLogger:
    def __init__(
        self,
        *,
        root: Path,
        job_type: str,
        batch_id: str,
        print_enabled: bool = True,
    ) -> None:
        self.root = root
        self.job_type = job_type
        self.batch_id = batch_id
        self.print_enabled = print_enabled
        self.logs_dir = self.root / "logs"
        self.checkpoints_dir = self.root / "checkpoints"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.logs_dir / f"{job_type}_{batch_id}.log"
        self.progress_path = self.logs_dir / f"{job_type}_{batch_id}.progress.jsonl"
        self.checkpoint_path = self.checkpoints_dir / f"{job_type}_{batch_id}.json"
        self._step_started_at: dict[str, float] = {}

    def step_start(self, *, phase: str, message: str) -> None:
        self._step_started_at[phase] = perf_counter()
        self._emit_line("STEP-START", f'batch={self.batch_id} phase={phase} message="{message}"')
        self._emit_event(phase=phase, event="step_start", message=message)

    def step_done(self, *, phase: str, message: str, current_step: int = 0, total_steps: int = 0) -> None:
        started = self._step_started_at.get(phase, perf_counter())
        elapsed_ms = int((perf_counter() - started) * 1000)
        self._emit_line("STEP-DONE", f'batch={self.batch_id} phase={phase} elapsed_ms={elapsed_ms} message="{message}"')
        self._emit_event(
            phase=phase,
            event="step_done",
            current_step=current_step,
            total_steps=total_steps,
            message=message,
        )

    def progress(
        self,
        *,
        phase: str,
        current_step: int,
        total_steps: int,
        current_item: int,
        total_items: int,
        ok_count: int,
        skipped_count: int,
        failed_count: int,
        message: str,
    ) -> None:
        percent = 0 if total_items <= 0 else int((current_item / total_items) * 100)
        self._emit_line(
            "PROGRESS",
            (
                f'batch={self.batch_id} phase={phase} step={current_step}/{total_steps} '
                f"item={current_item}/{total_items} percent={percent}% ok={ok_count} "
                f'skipped={skipped_count} failed={failed_count} message="{message}"'
            ),
        )
        self._emit_event(
            phase=phase,
            event="progress",
            current_step=current_step,
            total_steps=total_steps,
            current_item=current_item,
            total_items=total_items,
            percent=percent,
            status="progress",
            message=message,
        )

    def item(
        self,
        *,
        phase: str,
        index: int,
        total: int,
        doba_sku: str = "",
        shopify_variant_id: str = "",
        status: str = "",
        reason_code: str = "",
    ) -> None:
        self._emit_line(
            "ITEM",
            (
                f"batch={self.batch_id} phase={phase} index={index}/{total} "
                f"doba_sku={doba_sku} shopify_variant_id={shopify_variant_id} "
                f"status={status} reason_code={reason_code}"
            ),
        )
        self._emit_event(
            phase=phase,
            event="item",
            current_item=index,
            total_items=total,
            doba_sku=doba_sku,
            shopify_variant_id=shopify_variant_id,
            status=status,
            reason_code=reason_code,
        )

    def error(
        self,
        *,
        phase: str,
        index: int = 0,
        reason_code: str,
        error_message: str,
        doba_sku: str = "",
        shopify_variant_id: str = "",
    ) -> None:
        self._emit_line(
            "ERROR",
            (
                f'batch={self.batch_id} phase={phase} index={index} reason_code={reason_code} '
                f'error="{error_message}"'
            ),
        )
        self._emit_event(
            phase=phase,
            event="error",
            current_item=index,
            doba_sku=doba_sku,
            shopify_variant_id=shopify_variant_id,
            status="failed",
            reason_code=reason_code,
            message=error_message,
        )

    def save_checkpoint(
        self,
        *,
        phase: str,
        index: int,
        total_items: int,
        last_doba_sku: str = "",
        last_shopify_variant_id: str = "",
        last_output_files: list[str] | None = None,
        reason_code: str = "checkpoint_saved",
        reason_text_zh: str = "",
        last_decision: str = "",
        last_reason_code: str = "",
        interrupted: bool = False,
    ) -> str:
        payload = {
            "batch_id": self.batch_id,
            "job_type": self.job_type,
            "interrupted": interrupted,
            "phase": phase,
            "current_step": 0,
            "current_item": index,
            "total_items": total_items,
            "last_doba_sku": last_doba_sku,
            "last_shopify_variant_id": last_shopify_variant_id,
            "last_decision": last_decision,
            "last_reason_code": last_reason_code,
            "last_output_files": list(last_output_files or []),
            "reason_code": reason_code,
            "reason_text_zh": reason_text_zh,
            "created_at": utc_now_iso(),
        }
        self.checkpoint_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        self._emit_line(
            "CHECKPOINT",
            f'batch={self.batch_id} path={self.checkpoint_path.resolve()} phase={phase} index={index} message="checkpoint_saved"',
        )
        self._emit_event(
            phase=phase,
            event="checkpoint",
            current_item=index,
            total_items=total_items,
            doba_sku=last_doba_sku,
            shopify_variant_id=last_shopify_variant_id,
            reason_code=reason_code,
            message="checkpoint_saved",
        )
        return str(self.checkpoint_path.resolve())

    def interrupted(
        self,
        *,
        phase: str,
        index: int,
        total: int,
        reason_code: str,
        last_doba_sku: str = "",
        last_shopify_variant_id: str = "",
        checkpoint_path: str = "",
    ) -> None:
        self._emit_line(
            "INTERRUPTED",
            (
                f"batch={self.batch_id} phase={phase} index={index}/{total} "
                f"last_doba_sku={last_doba_sku} last_shopify_variant_id={last_shopify_variant_id} "
                f"reason_code={reason_code} checkpoint={checkpoint_path}"
            ),
        )
        self._emit_event(
            phase=phase,
            event="interrupted",
            current_item=index,
            total_items=total,
            doba_sku=last_doba_sku,
            shopify_variant_id=last_shopify_variant_id,
            reason_code=reason_code,
            message=checkpoint_path,
        )

    def output(self, path: str) -> None:
        self._emit_line("OUTPUT", path)
        self._emit_event(phase="write_outputs", event="progress", message=path)

    def line(
        self,
        *,
        label: str,
        text: str,
        phase: str = "",
        event: str = "progress",
        doba_sku: str = "",
        shopify_variant_id: str = "",
        reason_code: str = "",
        status: str = "",
        current_item: int = 0,
        total_items: int = 0,
        message: str = "",
    ) -> None:
        self._emit_line(label, text)
        self._emit_event(
            phase=phase,
            event=event,
            current_item=current_item,
            total_items=total_items,
            doba_sku=doba_sku,
            shopify_variant_id=shopify_variant_id,
            reason_code=reason_code,
            status=status,
            message=message or text,
        )

    def _emit_line(self, label: str, text: str) -> None:
        line = f"[{label}] {text}"
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        if self.print_enabled:
            print(line, flush=True)

    def _emit_event(
        self,
        *,
        phase: str,
        event: str,
        current_step: int = 0,
        total_steps: int = 0,
        current_item: int = 0,
        total_items: int = 0,
        percent: int = 0,
        doba_sku: str = "",
        shopify_variant_id: str = "",
        status: str = "",
        reason_code: str = "",
        message: str = "",
    ) -> None:
        payload: dict[str, Any] = {
            "ts": utc_now_iso(),
            "batch_id": self.batch_id,
            "job_type": self.job_type,
            "phase": phase,
            "event": event,
            "current_step": current_step,
            "total_steps": total_steps,
            "current_item": current_item,
            "total_items": total_items,
            "percent": percent,
            "doba_sku": doba_sku,
            "shopify_variant_id": shopify_variant_id,
            "status": status,
            "reason_code": reason_code,
            "message": message,
        }
        with self.progress_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=True) + "\n")
