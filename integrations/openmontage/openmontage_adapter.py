from __future__ import annotations

import argparse
import json
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .schemas import ProductVideoJob


REPO_ROOT = Path(__file__).resolve().parents[2]
OPENMONTAGE_ROOT = REPO_ROOT / "external" / "OpenMontage"
JOBS_ROOT = REPO_ROOT / "runtime" / "openmontage" / "jobs"
EXAMPLE_JOB_PATH = (
    REPO_ROOT / "integrations" / "openmontage" / "examples" / "product_video_job.example.json"
)


def _command_status(command: list[str], cwd: Path | None = None) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            cwd=cwd or REPO_ROOT,
        )
    except FileNotFoundError:
        return {"available": False, "command": " ".join(command), "detail": "not found"}
    except Exception as exc:  # pragma: no cover - defensive
        return {"available": False, "command": " ".join(command), "detail": str(exc)}

    output = (completed.stdout or completed.stderr).strip()
    return {
        "available": completed.returncode == 0,
        "command": " ".join(command),
        "detail": output,
    }


def _job_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"openmontage-{timestamp}-{uuid.uuid4().hex[:8]}"


def _render_bullets(items: list[str], fallback: str) -> str:
    values = items or [fallback]
    return "\n".join(f"- {item}" for item in values)


def _build_brief(job: ProductVideoJob) -> str:
    product_lines = [
        f"SKU: {job.sku}",
        f"Name: {job.product_name}",
    ]
    if job.warehouse:
        product_lines.append(f"Warehouse: {job.warehouse}")
    if job.quantity is not None:
        product_lines.append(f"Quantity: {job.quantity}")
    if job.target_platforms:
        product_lines.append(f"Target Platforms: {', '.join(job.target_platforms)}")
    if job.destination_url:
        product_lines.append(f"Destination URL: {job.destination_url}")

    required_output = [
        f"{job.video_requirements.resolution} vertical MP4",
        f"{job.video_requirements.language} captions",
        f"{job.video_requirements.language} voiceover" if job.video_requirements.voiceover else "No voiceover unless approved",
        "Product-focused CTA",
        "No exaggerated claims",
        "No unverified claims",
    ]

    workflow_requirements = [
        "Read AGENT_GUIDE.md first.",
        "Select the most appropriate OpenMontage pipeline.",
        "Produce a proposal before generating assets.",
        "Estimate cost before any paid provider call.",
        "Ask for approval before final render.",
        "Save outputs under the provided job directory.",
        "Do not publish to any platform automatically.",
    ]

    return "\n".join(
        [
            "# Product Video Brief",
            "",
            "## Product",
            "\n".join(product_lines),
            "",
            "## Goal",
            "Create a short vertical product video that can be used for TikTok, X, eBay product video, and Shopify landing page.",
            "",
            "## Product Facts",
            _render_bullets(job.product_facts, "Product facts will be provided by the operator."),
            "",
            "## Creative Angle",
            job.creative_angle or "Create a practical, product-led concept that matches the provided product facts.",
            "",
            "## Required Output",
            _render_bullets(required_output, "1080x1920 vertical MP4"),
            "",
            "## Compliance Rules",
            _render_bullets(job.compliance_rules, "Do not make claims that cannot be verified from the product card."),
            "",
            "## Workflow Requirements",
            "\n".join(f"{index}. {item}" for index, item in enumerate(workflow_requirements, start=1)),
        ]
    )


def create_product_video_job(product_card: dict[str, Any]) -> dict[str, Any]:
    job = ProductVideoJob.model_validate(product_card)
    job_id = _job_id()
    job_dir = JOBS_ROOT / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    product_card_path = job_dir / "product_card.json"
    brief_path = job_dir / "brief.md"

    product_card_path.write_text(
        json.dumps(job.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    brief_path.write_text(_build_brief(job), encoding="utf-8")

    return {
        "job_id": job_id,
        "job_dir": str(job_dir),
        "brief_path": str(brief_path),
        "suggested_openmontage_path": str(OPENMONTAGE_ROOT),
        "status": "created",
    }


def build_codex_prompt_for_openmontage(job_id: str) -> str:
    job_dir = JOBS_ROOT / job_id
    brief_path = job_dir / "brief.md"

    if not brief_path.exists():
        return (
            f"OpenMontage job '{job_id}' was not found. "
            f"Expected brief at: {brief_path}"
        )

    return (
        "Open the repository at "
        f"'{OPENMONTAGE_ROOT}'.\n"
        "Read AGENT_GUIDE.md first, then PROJECT_CONTEXT.md, then CODEX.md.\n"
        f"Read the job brief at '{brief_path}'.\n"
        "Choose the most appropriate OpenMontage pipeline for this brief.\n"
        "Before generating any paid assets, provide:\n"
        "1. A proposal with pipeline choice and rationale.\n"
        "2. A cost estimate.\n"
        "3. The render runtime options and your recommendation.\n"
        "Wait for human approval before asset generation or final render.\n"
        "Save all outputs under the provided job directory when possible.\n"
        "Return the final MP4 path and any relevant log/output paths.\n"
        "Do not auto-publish to X, TikTok, eBay, Shopify, or any other platform."
    )


def validate_openmontage_installation() -> dict[str, Any]:
    checks = {
        "openmontage_dir": OPENMONTAGE_ROOT.exists(),
        "readme_md": (OPENMONTAGE_ROOT / "README.md").exists(),
        "agent_guide_md": (OPENMONTAGE_ROOT / "AGENT_GUIDE.md").exists(),
        "requirements_txt": (OPENMONTAGE_ROOT / "requirements.txt").exists(),
        "remotion_package_json": (OPENMONTAGE_ROOT / "remotion-composer" / "package.json").exists(),
    }
    commands = {
        "python": _command_status(["python", "--version"]),
        "node": _command_status(["node", "-v"]),
        "ffmpeg": _command_status(["ffmpeg", "-version"]),
    }
    origin = _command_status(["git", "remote", "get-url", "origin"], cwd=OPENMONTAGE_ROOT)

    return {
        "openmontage_path": str(OPENMONTAGE_ROOT),
        "checks": checks,
        "commands": commands,
        "git_origin": origin,
        "ok": all(checks.values()) and all(item["available"] for item in commands.values()),
    }


def _load_product_card(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Create and validate OpenMontage jobs.")
    parser.add_argument(
        "--action",
        choices=["create-job", "validate-install"],
        default="create-job",
    )
    parser.add_argument(
        "--product-card",
        type=Path,
        default=EXAMPLE_JOB_PATH,
        help="Path to a product card JSON file.",
    )
    parser.add_argument(
        "--job-id",
        help="Existing job id used when building a Codex prompt.",
    )
    args = parser.parse_args()

    if args.action == "validate-install":
        print(json.dumps(validate_openmontage_installation(), ensure_ascii=False, indent=2))
        return

    product_card = _load_product_card(args.product_card)
    created = create_product_video_job(product_card)
    prompt = build_codex_prompt_for_openmontage(created["job_id"])

    output = {
        "created_job": created,
        "codex_prompt": prompt,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
