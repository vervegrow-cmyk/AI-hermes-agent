from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from lib.checkpoint import write_checkpoint
from lib.pipeline_loader import load_pipeline
from lib.qa_gate import evaluate_publish_ready
from tools.base_tool import ToolResult
from tools.tool_registry import registry


PRODUCT_CLOSEUP_WORKFLOW = ROOT_DIR / "assets" / "workflows" / "comfyui" / "product_closeup_workflow_api.json"
KEYFRAME_LOCK_WORKFLOW = ROOT_DIR / "assets" / "workflows" / "comfyui" / "keyframe_lock_workflow_api.json"


def slugify(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in value.strip())
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-") or "product"


def load_json(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict[str, Any] | list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def resolve_relative_path(raw: str | None, base_dir: Path) -> Path | None:
    if not raw:
        return None
    path = Path(str(raw))
    if not path.is_absolute():
        path = (base_dir / path).resolve()
    return path


def resolve_storyboard(product: dict[str, Any], product_path: Path) -> list[dict[str, Any]]:
    if isinstance(product.get("storyboard"), list):
        return list(product["storyboard"])
    storyboard_path = product.get("storyboard_path")
    if storyboard_path:
        candidate = Path(storyboard_path)
        if not candidate.is_absolute():
            candidate = product_path.parent / candidate
        payload = load_json(candidate)
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            if isinstance(payload.get("shots"), list):
                return list(payload["shots"])
            if isinstance(payload.get("storyboard"), list):
                return list(payload["storyboard"])
    return []


def resolve_product_images(product: dict[str, Any], product_path: Path) -> list[str]:
    candidates = (
        product.get("product_images")
        or product.get("image_paths")
        or product.get("images")
        or ((product.get("assets") or {}).get("product_images") if isinstance(product.get("assets"), dict) else None)
        or []
    )
    resolved: list[str] = []
    for item in candidates:
        raw = item.get("path") if isinstance(item, dict) else item
        if not raw:
            continue
        path = Path(str(raw))
        if not path.is_absolute():
            path = (product_path.parent / path).resolve()
        if path.exists():
            resolved.append(str(path))
    return resolved


def resolve_model_reference_images(product: dict[str, Any], product_path: Path) -> list[str]:
    candidates = product.get("model_reference_images") or []
    resolved: list[str] = []
    for item in candidates:
        raw = item.get("path") if isinstance(item, dict) else item
        path = resolve_relative_path(str(raw), product_path.parent) if raw else None
        if path and path.exists():
            resolved.append(str(path))
    return resolved


def resolve_keyframe_plan(product: dict[str, Any], product_path: Path) -> list[dict[str, Any]]:
    if isinstance(product.get("keyframe_prompts"), list):
        return list(product["keyframe_prompts"])
    keyframe_plan_path = product.get("keyframe_prompt_plan")
    if not keyframe_plan_path:
        return []
    candidate = resolve_relative_path(str(keyframe_plan_path), product_path.parent)
    if not candidate or not candidate.exists():
        return []
    payload = load_json(candidate)
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        if isinstance(payload.get("prompts"), list):
            return list(payload["prompts"])
        if isinstance(payload.get("keyframe_prompts"), list):
            return list(payload["keyframe_prompts"])
    return []


def shot_bucket(shot: dict[str, Any]) -> str:
    shot_type = str(shot.get("shot_type") or shot.get("type") or "").lower()
    purpose = str(shot.get("purpose") or "").lower()
    if shot_type in {"complex_creative_gag", "complex", "complex_narrative"} or "fly" in purpose:
        return "complex_creative_gag"
    if shot_type in {"product_closeup", "product_proof", "product"} or shot.get("must_use_real_product"):
        return "product_closeup"
    return "action_or_character_motion"


def tool_names_to_providers(tool_names: list[str]) -> list[str]:
    providers: list[str] = []
    for tool_name in tool_names:
        tool = registry.get(tool_name)
        if tool:
            providers.append(tool.provider)
    return providers


def shot_duration_seconds(shot: dict[str, Any]) -> float:
    if shot.get("duration_sec") is not None:
        return float(shot.get("duration_sec") or 0)
    if shot.get("duration") is not None:
        return float(shot.get("duration") or 0)
    start = shot.get("start_seconds", shot.get("start"))
    end = shot.get("end_seconds", shot.get("end"))
    if start is not None and end is not None:
        return max(0.0, float(end) - float(start))
    return 4.0


def shot_prompt(shot: dict[str, Any], fallback: str) -> str:
    return str(
        shot.get("visual_prompt")
        or shot.get("prompt")
        or shot.get("goal")
        or shot.get("visual")
        or shot.get("description")
        or fallback
    )


def shot_text(shot: dict[str, Any]) -> str:
    return str(shot.get("subtitle") or shot.get("subtitle_text") or shot.get("voiceover") or shot.get("text") or "")


def rank_video_shot(shot: dict[str, Any], tool_names: list[str]) -> dict[str, Any]:
    selector = registry.get("video_selector")
    if selector is None:
        return {"error": "video_selector not available", "rankings": []}
    allowed_providers = tool_names_to_providers(tool_names)
    result = selector.execute(
        {
            "operation": "rank",
            "target_operation": "text_to_video",
            "prompt": shot_prompt(shot, "Video shot"),
            "allowed_providers": allowed_providers,
            "aspect_ratio": shot.get("aspect_ratio", "9:16"),
            "duration": str(int(round(shot_duration_seconds(shot))) or 5),
        }
    )
    return result.data if result.success else {"error": result.error, "rankings": []}


def rank_image_shot(shot: dict[str, Any], tool_names: list[str]) -> dict[str, Any]:
    selector = registry.get("image_selector")
    if selector is None:
        return {"error": "image_selector not available", "rankings": []}
    allowed_providers = tool_names_to_providers(tool_names)
    result = selector.execute(
        {
            "operation": "rank",
            "prompt": shot_prompt(shot, "Product closeup image"),
            "allowed_providers": allowed_providers,
            "aspect_ratio": shot.get("aspect_ratio", "9:16"),
        }
    )
    return result.data if result.success else {"error": result.error, "rankings": []}


def rank_voiceover(text: str, tool_names: list[str]) -> dict[str, Any]:
    selector = registry.get("tts_selector")
    if selector is None:
        return {"error": "tts_selector not available", "rankings": []}
    allowed_providers = tool_names_to_providers(tool_names)
    result = selector.execute(
        {
            "operation": "rank",
            "text": text,
            "allowed_providers": allowed_providers,
        }
    )
    return result.data if result.success else {"error": result.error, "rankings": []}


def write_markdown(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def prepare_product_assets(
    product: dict[str, Any],
    product_images: list[str],
    generated_dir: Path,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    output_dir = generated_dir / "product_assets"
    output_dir.mkdir(parents=True, exist_ok=True)
    comfyui_tool = registry.get("comfyui_image")

    for index, source_path in enumerate(product_images, start=1):
        source = Path(source_path)
        target = output_dir / f"{index:02d}_{source.stem}.png"
        prompt = (
            f"Prepare this product image for TikTok vertical editing. Preserve the exact product identity. "
            f"Product: {product.get('title') or product.get('name') or 'product'}."
        )

        if comfyui_tool and comfyui_tool.get_status().value in {"available", "degraded"}:
            result = comfyui_tool.execute(
                {
                    "prompt": prompt,
                    "generation_mode": "edit",
                    "image_path": str(source),
                    "workflow_path": str(PRODUCT_CLOSEUP_WORKFLOW),
                    "output_node": "13",
                    "width": 1080,
                    "height": 1920,
                    "upscale_method": "lanczos",
                    "output_path": str(target),
                    "workflow_name": "product_closeup_workflow_api",
                    "workflow_model": "image_scale_vertical_product_prep",
                }
            )
            if result.success:
                output_path = Path(result.data.get("output") or result.artifacts[0])
                results.append(
                    {
                        "success": True,
                        "provider": "comfyui",
                        "tool": "comfyui_image",
                        "source_path": str(source),
                        "output_path": str(output_path),
                        "error": None,
                    }
                )
                continue
            fallback_error = result.error
        else:
            fallback_error = "comfyui_image unavailable"

        fallback_target = output_dir / f"{index:02d}_{source.stem}{source.suffix.lower()}"
        shutil.copy2(source, fallback_target)
        results.append(
            {
                "success": True,
                "provider": "product_image",
                "tool": "product_image",
                "source_path": str(source),
                "output_path": str(fallback_target),
                "error": fallback_error,
            }
        )
    return results


def choose_keyframe_source_image(
    prompt_def: dict[str, Any],
    product_path: Path,
    model_reference_images: list[str],
    product_images: list[str],
) -> str | None:
    explicit = (
        prompt_def.get("source_image")
        or prompt_def.get("source_path")
        or prompt_def.get("reference_image")
        or prompt_def.get("reference_image_path")
    )
    resolved_explicit = (
        resolve_relative_path(str(explicit), product_path.parent) if explicit else None
    )
    if resolved_explicit and resolved_explicit.exists():
        return str(resolved_explicit)

    shot_id = str(prompt_def.get("shot_id") or prompt_def.get("id") or "").lower()
    purpose = str(prompt_def.get("purpose") or "").lower()

    if any(token in shot_id or token in purpose for token in ("activate", "wear", "relief", "pain")):
        if model_reference_images:
            return model_reference_images[0]
    if "reveal" in shot_id or "reveal" in purpose:
        if model_reference_images:
            return model_reference_images[0]
        if product_images:
            return product_images[0]

    if model_reference_images:
        return model_reference_images[0]
    if product_images:
        return product_images[0]
    return None


def generate_keyframe_assets(
    *,
    product: dict[str, Any],
    product_path: Path,
    keyframe_plan: list[dict[str, Any]],
    model_reference_images: list[str],
    product_images: list[str],
    generated_dir: Path,
) -> list[dict[str, Any]]:
    if not keyframe_plan:
        return []

    comfyui_tool = registry.get("comfyui_image")
    results: list[dict[str, Any]] = []
    output_dir = generated_dir / "keyframes"
    output_dir.mkdir(parents=True, exist_ok=True)

    for index, prompt_def in enumerate(keyframe_plan, start=1):
        keyframe_id = str(prompt_def.get("id") or f"keyframe_{index:02d}")
        shot_id = str(prompt_def.get("shot_id") or "")
        prompt = str(prompt_def.get("prompt") or prompt_def.get("target_frame_description") or keyframe_id)
        source_image = choose_keyframe_source_image(
            prompt_def,
            product_path,
            model_reference_images,
            product_images,
        )
        output_path = output_dir / f"{slugify(keyframe_id)}.png"

        if comfyui_tool and source_image and comfyui_tool.get_status().value in {"available", "degraded"}:
            result = comfyui_tool.execute(
                {
                    "prompt": prompt,
                    "generation_mode": "edit",
                    "image_path": str(source_image),
                    "workflow_path": str(KEYFRAME_LOCK_WORKFLOW),
                    "output_node": "13",
                    "width": 1080,
                    "height": 1920,
                    "upscale_method": "lanczos",
                    "output_path": str(output_path),
                    "workflow_name": "keyframe_lock_workflow_api",
                    "workflow_model": "keyframe_lock_reference_prep",
                }
            )
            if result.success:
                results.append(
                    {
                        "success": True,
                        "keyframe_id": keyframe_id,
                        "shot_id": shot_id,
                        "provider": "comfyui",
                        "tool": "comfyui_image",
                        "prompt": prompt,
                        "source_path": str(source_image),
                        "output_path": str(result.data.get("output") or result.artifacts[0]),
                        "error": None,
                        "notes": prompt_def.get("match_notes") or [],
                    }
                )
                continue
            fallback_error = result.error
        else:
            fallback_error = "comfyui_image unavailable or no source image"

        if source_image:
            shutil.copy2(source_image, output_path)
            results.append(
                {
                    "success": True,
                    "keyframe_id": keyframe_id,
                    "shot_id": shot_id,
                    "provider": "reference_image",
                    "tool": "reference_image",
                    "prompt": prompt,
                    "source_path": str(source_image),
                    "output_path": str(output_path),
                    "error": fallback_error,
                    "notes": prompt_def.get("match_notes") or [],
                }
            )
        else:
            results.append(
                {
                    "success": False,
                    "keyframe_id": keyframe_id,
                    "shot_id": shot_id,
                    "provider": None,
                    "tool": None,
                    "prompt": prompt,
                    "source_path": None,
                    "output_path": None,
                    "error": "No source image available for keyframe generation.",
                    "notes": prompt_def.get("match_notes") or [],
                }
            )

    return results


def _looks_like_real_person_reference(path_str: str) -> bool:
    path = Path(str(path_str))
    stem = path.stem.lower()
    parts = [part.lower() for part in path.parts]
    risky_tokens = {
        "model",
        "stadium",
        "portrait",
        "selfie",
        "person",
        "wearing",
        "keyframe",
        "pain",
        "relief",
        "activate",
        "reveal",
    }
    if any(token in stem for token in risky_tokens):
        return True
    if "keyframes" in parts:
        return True
    return False


def split_seedance_reference_images(
    keyframe_reference_images: list[str],
    product_images: list[str],
) -> tuple[list[str], list[str]]:
    candidate_paths = list(keyframe_reference_images) + list(product_images)
    safe_paths: list[str] = []
    risky_paths: list[str] = []
    for path_str in candidate_paths:
        if str(path_str).startswith(("http://", "https://")):
            safe_paths.append(str(path_str))
            continue
        if _looks_like_real_person_reference(str(path_str)):
            risky_paths.append(str(path_str))
        else:
            safe_paths.append(str(path_str))
    return safe_paths, risky_paths


def build_seedance_text_only_prompt(
    shot: dict[str, Any],
    base_prompt: str,
    risky_reference_images: list[str],
) -> str:
    details = [
        "Photorealistic vertical UGC video.",
        "Keep exact product identity: beige wide-brim solar fan hat, dual black side-mounted fans, visible small solar panels, black chin strap.",
        "Same sunny crowded soccer stadium environment.",
        "Same brunette woman in a fitted black T-shirt.",
        "No text overlay, no infographic layout, no poster composition.",
    ]
    if risky_reference_images:
        details.append(
            "Do not rely on any real-person uploaded photo as reference; recreate the composition from prompt only while preserving product identity."
        )
    return f"{base_prompt.strip()} {' '.join(details)}"


def execute_motion_tool(
    tool_name: str,
    shot: dict[str, Any],
    product_images: list[str],
    keyframe_reference_images: list[str],
    output_dir: Path,
) -> ToolResult:
    try:
        tool = registry.get(tool_name)
        if tool is None:
            return ToolResult(success=False, error=f"{tool_name} not registered")

        requested_duration = int(round(shot_duration_seconds(shot))) or 5
        generation_duration = str(max(4, requested_duration))
        aspect_ratio = str(shot.get("aspect_ratio") or "9:16")
        prompt = shot_prompt(shot, "Dynamic product video shot")
        reference_image_paths = list(keyframe_reference_images) + list(product_images)
        safe_reference_image_paths, risky_reference_image_paths = split_seedance_reference_images(
            keyframe_reference_images,
            product_images,
        )
        public_reference_images = [
            image for image in safe_reference_image_paths if str(image).startswith(("http://", "https://"))
        ]
        public_reference_images.extend(list(shot.get("reference_image_urls") or []))

        if tool_name == "libtv_video":
            return tool.execute(
                {
                    "prompt": prompt,
                    "duration": generation_duration,
                    "aspect_ratio": aspect_ratio,
                    "product_images": reference_image_paths,
                    "style_notes": str(shot.get("style_notes") or shot.get("purpose") or ""),
                    "output_dir": str(output_dir),
                    "timeout": int(shot.get("timeout") or 1800),
                    "poll_interval": int(shot.get("poll_interval") or 10),
                }
            )

        if tool_name == "seedance_ark_video":
            operation = "reference_to_video" if safe_reference_image_paths else "text_to_video"
            primary_inputs = {
                "prompt": prompt,
                "operation": operation,
                "duration": generation_duration,
                "aspect_ratio": aspect_ratio,
                "reference_image_paths": safe_reference_image_paths,
                "reference_image_urls": public_reference_images,
                "generate_audio": False,
                "output_path": str(output_dir / f"{slugify(str(shot.get('shot_id') or 'shot'))}.mp4"),
            }
            result = tool.execute(primary_inputs)
            if result.success:
                return result
            privacy_blocked = "InputImageSensitiveContentDetected.PrivacyInformation" in str(result.error or "")
            if operation == "reference_to_video" and (privacy_blocked or risky_reference_image_paths):
                fallback_prompt = build_seedance_text_only_prompt(
                    shot,
                    prompt,
                    risky_reference_image_paths,
                )
                fallback_inputs = {
                    "prompt": fallback_prompt,
                    "operation": "text_to_video",
                    "duration": generation_duration,
                    "aspect_ratio": aspect_ratio,
                    "generate_audio": False,
                    "output_path": str(output_dir / f"{slugify(str(shot.get('shot_id') or 'shot'))}.mp4"),
                }
                fallback_result = tool.execute(fallback_inputs)
                if fallback_result.success:
                    fallback_result.data["fallback_from_reference_mode"] = True
                    fallback_result.data["initial_error"] = result.error
                    fallback_result.data["dropped_reference_images"] = risky_reference_image_paths
                    return fallback_result
                fallback_result.error = (
                    f"{fallback_result.error} | initial_reference_error={result.error}"
                )
                return fallback_result
            return result

        if tool_name == "seedance_video":
            operation = "reference_to_video" if reference_image_paths else "text_to_video"
            return tool.execute(
                {
                    "prompt": prompt,
                    "operation": operation,
                    "duration": generation_duration,
                    "aspect_ratio": aspect_ratio,
                    "reference_image_paths": reference_image_paths,
                    "generate_audio": False,
                    "output_path": str(output_dir / f"{slugify(str(shot.get('shot_id') or 'shot'))}.mp4"),
                }
            )

        selector = registry.get("video_selector")
        if selector is None:
            return ToolResult(success=False, error="video_selector not available for fallback routing")
        provider = tool.provider
        operation = "reference_to_video" if reference_image_paths else "text_to_video"
        return selector.execute(
            {
                "prompt": prompt,
                "operation": operation,
                "preferred_provider": provider,
                "allowed_providers": [provider],
                "duration": generation_duration,
                "aspect_ratio": aspect_ratio,
                "reference_image_paths": reference_image_paths,
                "output_path": str(output_dir / f"{slugify(str(shot.get('shot_id') or provider))}.mp4"),
            }
        )
    except Exception as exc:
        return ToolResult(success=False, error=f"{tool_name} execution crashed: {exc}")


def generate_motion_asset(
    shot: dict[str, Any],
    preferred_tools: list[str],
    product_images: list[str],
    keyframe_assets: list[dict[str, Any]],
    generated_dir: Path,
) -> dict[str, Any]:
    shot_id = str(shot.get("shot_id") or slugify(shot_prompt(shot, "shot")))
    shot_dir = generated_dir / "motion" / shot_id
    shot_dir.mkdir(parents=True, exist_ok=True)
    attempts: list[dict[str, Any]] = []
    keyframe_reference_images = [
        str(item.get("output_path"))
        for item in keyframe_assets
        if item.get("success") and str(item.get("shot_id") or "") == shot_id and item.get("output_path")
    ]

    for tool_name in preferred_tools:
        tool = registry.get(tool_name)
        if tool is None:
            attempts.append({"tool": tool_name, "status": "missing"})
            continue
        status = tool.get_status().value
        if status == "unavailable":
            attempts.append({"tool": tool_name, "provider": tool.provider, "status": status})
            continue

        result = execute_motion_tool(tool_name, shot, product_images, keyframe_reference_images, shot_dir)
        attempts.append(
            {
                "tool": tool_name,
                "provider": tool.provider,
                "status": "success" if result.success else "failed",
                "error": result.error,
                "keyframe_refs": keyframe_reference_images,
            }
        )
        if result.success:
            video_path = (
                result.data.get("video_path")
                or result.data.get("output")
                or (result.artifacts[0] if result.artifacts else None)
            )
            return {
                "success": True,
                "provider": result.data.get("selected_provider") or result.data.get("provider") or tool.provider,
                "tool": result.data.get("selected_tool") or tool_name,
                "asset_type": "video",
                "path": str(video_path) if video_path else None,
                "attempts": attempts,
                "data": result.data,
                "error": None,
                "keyframe_reference_images": keyframe_reference_images,
            }

    return {
        "success": False,
        "provider": None,
        "tool": None,
        "asset_type": "video",
        "path": None,
        "attempts": attempts,
        "data": {},
        "error": "All motion providers failed or were unavailable.",
        "keyframe_reference_images": keyframe_reference_images,
    }


def generate_shot_assets(
    storyboard: list[dict[str, Any]],
    routing_meta: dict[str, Any],
    product_assets: list[dict[str, Any]],
    product_images: list[str],
    keyframe_assets: list[dict[str, Any]],
    generated_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    shot_results: list[dict[str, Any]] = []
    generated_results: list[dict[str, Any]] = []
    product_cursor = 0

    for shot in storyboard:
        bucket = shot_bucket(shot)
        preferred_tools = list((routing_meta.get(bucket) or {}).get("preferred_tools") or [])
        ranking = (
            rank_image_shot(shot, [name for name in preferred_tools if name != "product_image"])
            if bucket == "product_closeup"
            else rank_video_shot(shot, preferred_tools)
        )

        if bucket == "product_closeup":
            if product_assets:
                selected = product_assets[product_cursor % len(product_assets)]
                product_cursor += 1
                shot_result = {
                    "shot_id": shot.get("shot_id"),
                    "bucket": bucket,
                    "preferred_tools": preferred_tools,
                    "selector_rankings": ranking.get("rankings", []),
                    "selector_error": ranking.get("error"),
                    "result": {
                        "success": True,
                        "provider": selected["provider"],
                        "tool": selected["tool"],
                        "asset_type": "image",
                        "path": selected["output_path"],
                        "attempts": [],
                        "data": {"source_path": selected["source_path"]},
                        "error": selected["error"],
                    },
                }
                generated_results.append(
                    {
                        "success": True,
                        "provider": selected["provider"],
                        "tool": selected["tool"],
                        "shot_id": shot.get("shot_id"),
                        "attempted": True,
                    }
                )
            else:
                shot_result = {
                    "shot_id": shot.get("shot_id"),
                    "bucket": bucket,
                    "preferred_tools": preferred_tools,
                    "selector_rankings": ranking.get("rankings", []),
                    "selector_error": ranking.get("error"),
                    "result": {
                        "success": False,
                        "provider": None,
                        "tool": None,
                        "asset_type": "image",
                        "path": None,
                        "attempts": [],
                        "data": {},
                        "error": "No product images were provided.",
                    },
                }
            shot_results.append(shot_result)
            continue

        motion_result = generate_motion_asset(shot, preferred_tools, product_images, keyframe_assets, generated_dir)
        shot_results.append(
            {
                "shot_id": shot.get("shot_id"),
                "bucket": bucket,
                "preferred_tools": preferred_tools,
                "selector_rankings": ranking.get("rankings", []),
                "selector_error": ranking.get("error"),
                "result": motion_result,
            }
        )
        generated_results.append(
            {
                "success": motion_result["success"],
                "provider": motion_result["provider"],
                "tool": motion_result["tool"],
                "shot_id": shot.get("shot_id"),
                "attempted": bool(motion_result.get("attempts")),
            }
        )

    return shot_results, generated_results


def build_asset_manifest(
    storyboard: list[dict[str, Any]],
    shot_results: list[dict[str, Any]],
) -> dict[str, Any]:
    assets: list[dict[str, Any]] = []
    total_cost = 0.0

    results_by_shot = {str(item.get("shot_id")): item for item in shot_results}
    for index, shot in enumerate(storyboard, start=1):
        shot_id = str(shot.get("shot_id") or f"shot_{index:02d}")
        routed = results_by_shot.get(shot_id, {})
        result = routed.get("result") or {}
        asset_path = result.get("path")
        if not asset_path:
            continue
        asset_type = "image" if result.get("asset_type") == "image" else "video"
        assets.append(
            {
                "id": f"asset_{index:02d}_{slugify(shot_id)}",
                "type": asset_type,
                "path": str(asset_path),
                "source_tool": str(result.get("tool") or "unknown"),
                "scene_id": shot_id,
                "prompt": shot_prompt(shot, ""),
                "model": str((result.get("data") or {}).get("model") or (result.get("data") or {}).get("selected_tool") or ""),
                "cost_usd": float((result.get("data") or {}).get("cost_usd") or 0.0),
                "duration_seconds": shot_duration_seconds(shot),
                "resolution": "1080x1920",
                "format": Path(str(asset_path)).suffix.lstrip("."),
                "provider": result.get("provider"),
                "subtype": shot_bucket(shot),
                "generation_summary": f"{shot_bucket(shot)} routed to {result.get('tool') or result.get('provider')}",
            }
        )
        total_cost += float((result.get("data") or {}).get("cost_usd") or 0.0)

    return {
        "version": "1.0",
        "assets": assets,
        "total_cost_usd": round(total_cost, 4),
        "metadata": {
            "asset_count": len(assets),
        },
    }


def build_edit_decisions(
    storyboard: list[dict[str, Any]],
    asset_manifest: dict[str, Any],
    render_runtime: str | None,
) -> dict[str, Any] | None:
    if not render_runtime:
        return None

    asset_by_scene = {asset["scene_id"]: asset for asset in asset_manifest.get("assets", [])}
    cuts: list[dict[str, Any]] = []
    cursor = 0.0
    for index, shot in enumerate(storyboard, start=1):
        shot_id = str(shot.get("shot_id") or f"shot_{index:02d}")
        asset = asset_by_scene.get(shot_id)
        if not asset:
            continue
        duration = max(0.1, shot_duration_seconds(shot))
        cut: dict[str, Any] = {
            "id": f"cut_{index:02d}_{slugify(shot_id)}",
            "source": asset["path"],
            "source_asset_id": asset["id"],
            "in_seconds": 0.0,
            "out_seconds": duration,
            "layer": "primary",
            "reason": f"{shot_bucket(shot)} via {asset['source_tool']}",
        }
        if asset["type"] == "image":
            cut["transform"] = {
                "scale": 1.0,
                "position": "center",
                "animation": "ken-burns-slow-zoom",
            }
        cuts.append(cut)
        cursor += duration

    return {
        "version": "1.0",
        "cuts": cuts,
        "render_runtime": render_runtime,
        "renderer_family": "product-reveal",
        "composition_mode": "templated",
        "metadata": {
            "total_timeline_seconds": round(cursor, 2),
            "shot_count": len(cuts),
        },
    }


def maybe_compose_final(
    *,
    edit_decisions: dict[str, Any] | None,
    asset_manifest: dict[str, Any],
    storyboard: list[dict[str, Any]],
    output_path: Path,
) -> dict[str, Any]:
    if not edit_decisions:
        return {
            "success": False,
            "error": "render_runtime missing in product.json; compose skipped intentionally.",
            "output_path": str(output_path),
        }

    composer = registry.get("video_compose")
    if composer is None:
        return {
            "success": False,
            "error": "video_compose is not registered.",
            "output_path": str(output_path),
        }

    result = composer.execute(
        {
            "operation": "render",
            "edit_decisions": edit_decisions,
            "asset_manifest": asset_manifest,
            "scene_plan": storyboard,
            "output_path": str(output_path),
        }
    )
    return {
        "success": result.success,
        "error": result.error,
        "output_path": str(output_path),
        "data": result.data,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Shot-routed OpenMontage workflow runner.")
    parser.add_argument("--pipeline", required=True, help="Pipeline id in pipeline_defs/, e.g. exaggerated_viral_ad")
    parser.add_argument("--product", required=True, help="Path to product.json")
    args = parser.parse_args()

    manifest = load_pipeline(args.pipeline)
    product_path = Path(args.product).resolve()
    product = load_json(product_path)
    product_id = slugify(str(product.get("product_id") or product.get("id") or product_path.stem))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = ROOT_DIR / "runs" / args.pipeline / f"{product_id}_{timestamp}"
    generated_dir = run_dir / "generated"
    temp_dir = run_dir / "temp"
    logs_dir = run_dir / "logs"
    qa_dir = run_dir / "qa"
    final_dir = run_dir / "final"
    for directory in (generated_dir, temp_dir, logs_dir, qa_dir, final_dir):
        directory.mkdir(parents=True, exist_ok=True)

    registry.ensure_discovered()
    storyboard = resolve_storyboard(product, product_path)
    product_images = resolve_product_images(product, product_path)
    model_reference_images = resolve_model_reference_images(product, product_path)
    keyframe_plan = resolve_keyframe_plan(product, product_path)
    routing_meta = (manifest.get("metadata") or {}).get("provider_routing") or {}
    render_runtime = str(product.get("render_runtime") or "").strip().lower() or None

    product_assets = prepare_product_assets(product, product_images, generated_dir)
    keyframe_assets = generate_keyframe_assets(
        product=product,
        product_path=product_path,
        keyframe_plan=keyframe_plan,
        model_reference_images=model_reference_images,
        product_images=product_images,
        generated_dir=generated_dir,
    )
    shot_results, generated_results = generate_shot_assets(
        storyboard=storyboard,
        routing_meta=routing_meta,
        product_assets=product_assets,
        product_images=product_images,
        keyframe_assets=keyframe_assets,
        generated_dir=generated_dir,
    )

    voiceover_text = str(product.get("voiceover") or product.get("script") or "")
    voice_tools = list((routing_meta.get("voiceover") or {}).get("preferred_tools") or [])
    voiceover_plan = rank_voiceover(voiceover_text, voice_tools) if voiceover_text else {}

    asset_manifest = build_asset_manifest(storyboard, shot_results)
    edit_decisions = build_edit_decisions(storyboard, asset_manifest, render_runtime)
    compose_result = maybe_compose_final(
        edit_decisions=edit_decisions,
        asset_manifest=asset_manifest,
        storyboard=storyboard,
        output_path=final_dir / "final.mp4",
    )

    qa_storyboard: list[dict[str, Any]] = []
    for shot_item in shot_results:
        shot = next(
            (candidate for candidate in storyboard if str(candidate.get("shot_id")) == str(shot_item.get("shot_id"))),
            {},
        )
        result = shot_item.get("result") or {}
        qa_storyboard.append(
            {
                **shot,
                "duration_sec": shot_duration_seconds(shot),
                "uses_static_image": result.get("asset_type") == "image",
                "has_action": bool(shot.get("has_action")) or shot_bucket(shot) != "product_closeup",
                "has_product_closeup": bool(shot.get("has_product_closeup")) or shot_bucket(shot) == "product_closeup",
                "has_cta": bool(shot.get("cta") or shot.get("has_cta")),
            }
        )

    qa = evaluate_publish_ready(
        qa_storyboard,
        generated_results=generated_results,
        max_static_image_ratio=float(
            ((manifest.get("metadata") or {}).get("qa_rules") or {}).get("max_static_image_ratio", 0.35)
        ),
    )

    routing_plan = {
        "pipeline": args.pipeline,
        "product_id": product_id,
        "run_dir": str(run_dir),
        "storyboard_count": len(storyboard),
        "product_images": product_images,
        "model_reference_images": model_reference_images,
        "keyframe_plan_count": len(keyframe_plan),
        "keyframe_assets": keyframe_assets,
        "product_asset_preprocess": product_assets,
        "shot_routes": shot_results,
        "voiceover_plan": voiceover_plan,
        "final_output_path": str(final_dir / "final.mp4"),
        "compose_result": compose_result,
    }
    write_json(generated_dir / "routing_plan.json", routing_plan)
    write_json(generated_dir / "asset_manifest.json", asset_manifest)
    if edit_decisions:
        write_json(generated_dir / "edit_decisions.json", edit_decisions)

    write_checkpoint(
        pipeline_dir=run_dir / "pipeline",
        project_id=product_id,
        stage="assets",
        status="completed",
        artifacts={"asset_manifest": asset_manifest},
        pipeline_type=args.pipeline,
        metadata={
            "run_dir": str(run_dir),
            "product_json": str(product_path),
            "created_by": "scripts/run_workflow.py",
        },
    )

    (qa_dir / "qa_report.md").write_text(
        "# QA Report\n\n"
        + "\n".join(
            f"- {check['name']}: {'pass' if check['passed'] else 'fail'} ({check['detail']})"
            for check in qa["checks"]
        )
        + f"\n\n- publish_ready: {'yes' if qa['publish_ready'] else 'no'}\n",
        encoding="utf-8",
    )

    if not qa["publish_ready"]:
        missing_reasons = [check["name"] for check in qa["checks"] if not check["passed"]]
        write_markdown(
            qa_dir / "missing_assets.md",
            [
                "# Missing Assets",
                "",
                "Publish-ready output is blocked by the following unmet checks:",
                *[f"- {reason}" for reason in missing_reasons],
            ],
        )

    write_markdown(
        logs_dir / "run_log.md",
        [
            "# Run Log",
            "",
            f"- Pipeline: `{args.pipeline}`",
            f"- Product JSON: `{product_path}`",
            f"- Run dir: `{run_dir}`",
            f"- Storyboard shots discovered: `{len(storyboard)}`",
            f"- Product images discovered: `{len(product_images)}`",
            f"- Model reference images discovered: `{len(model_reference_images)}`",
            f"- Keyframe prompts discovered: `{len(keyframe_plan)}`",
            f"- Keyframes prepared: `{len([item for item in keyframe_assets if item.get('success')])}`",
            f"- Product assets prepared: `{len(product_assets)}`",
            f"- Routed shots executed: `{len(shot_results)}`",
            f"- Render runtime: `{render_runtime or 'not-set'}`",
            f"- Final output path: `{final_dir / 'final.mp4'}`",
            f"- Compose success: `{'yes' if compose_result.get('success') else 'no'}`",
            f"- Publish-ready: `{'yes' if qa['publish_ready'] else 'no'}`",
        ],
    )

    print(
        json.dumps(
            {
                "run_dir": str(run_dir),
                "routing_plan": str(generated_dir / "routing_plan.json"),
                "asset_manifest": str(generated_dir / "asset_manifest.json"),
                "edit_decisions": str(generated_dir / "edit_decisions.json") if edit_decisions else None,
                "run_log": str(logs_dir / "run_log.md"),
                "qa_report": str(qa_dir / "qa_report.md"),
                "missing_assets": str(qa_dir / "missing_assets.md") if not qa["publish_ready"] else None,
                "final_output_path": str(final_dir / "final.mp4"),
                "compose_success": compose_result.get("success"),
                "compose_error": compose_result.get("error"),
                "publish_ready": qa["publish_ready"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
