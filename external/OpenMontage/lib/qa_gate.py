"""Publish-ready QA checks for run_workflow and related thin runners."""

from __future__ import annotations

from typing import Any


def evaluate_publish_ready(
    storyboard: list[dict[str, Any]],
    generated_results: list[dict[str, Any]] | None = None,
    *,
    max_static_image_ratio: float = 0.35,
) -> dict[str, Any]:
    """Apply anti-PPT QA rules to a planned or generated workflow."""
    generated_results = generated_results or []

    total_duration = sum(float(shot.get("duration_sec", 0) or 0) for shot in storyboard)
    static_duration = sum(
        float(shot.get("duration_sec", 0) or 0)
        for shot in storyboard
        if bool(shot.get("uses_static_image"))
    )
    static_ratio = (static_duration / total_duration) if total_duration else 1.0

    has_action = any(
        shot.get("shot_type") in {"action", "character_action", "human_action", "complex_creative_gag"}
        or shot.get("has_action")
        for shot in storyboard
    )
    has_product_closeup = any(
        shot.get("shot_type") in {"product_closeup", "product_proof"}
        or shot.get("has_product_closeup")
        for shot in storyboard
    )
    has_cta = any(bool(shot.get("cta")) or bool(shot.get("has_cta")) for shot in storyboard)

    provider_attempted = any(
        result.get("attempted") or result.get("provider") or result.get("tool")
        for result in generated_results
    )
    provider_succeeded = any(result.get("success") for result in generated_results)
    only_product_images = provider_attempted and all(
        result.get("provider") in {"product_image", "real_product_images", "image_only"}
        for result in generated_results
    )

    checks = [
        {
            "name": "static_image_ratio",
            "passed": static_ratio <= max_static_image_ratio,
            "detail": f"{static_ratio:.1%} <= {max_static_image_ratio:.0%}",
        },
        {
            "name": "has_action_shot",
            "passed": has_action,
            "detail": "At least one action/motion shot is required.",
        },
        {
            "name": "has_product_closeup",
            "passed": has_product_closeup,
            "detail": "At least one product closeup/proof shot is required.",
        },
        {
            "name": "has_cta",
            "passed": has_cta,
            "detail": "At least one CTA beat is required.",
        },
        {
            "name": "provider_success_required",
            "passed": provider_succeeded or not provider_attempted,
            "detail": "If providers were attempted, at least one must succeed.",
        },
        {
            "name": "forbid_product_image_only_final",
            "passed": not only_product_images,
            "detail": "A publish-ready final cannot be assembled from product images alone.",
        },
    ]
    publish_ready = all(check["passed"] for check in checks)

    return {
        "publish_ready": publish_ready,
        "static_image_ratio": static_ratio,
        "checks": checks,
    }
