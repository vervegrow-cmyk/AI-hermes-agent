from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.audio.tts_selector import TTSSelector
from tools.video.video_selector import VideoSelector

CONFIG_PATH = Path(__file__).resolve().with_suffix(".json")
OUTPUT_DIR = ROOT_DIR / "outputs" / "ecommerce_drone_tiktok_hard_seed"
CLIPS_DIR = OUTPUT_DIR / "clips"
CAPCUT_DIR = OUTPUT_DIR / "capcut_package"


def load_shared_env() -> None:
    env_files = [
        ROOT_DIR.parent.parent / ".env",
        ROOT_DIR / ".env",
    ]
    for env_file in env_files:
        if env_file.exists():
            load_dotenv(env_file, override=False)


def read_config(config_path: Path) -> dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def ensure_output_dirs() -> None:
    for path in [OUTPUT_DIR, CLIPS_DIR, CAPCUT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def find_command(*names: str) -> str | None:
    for name in names:
        resolved = shutil.which(name)
        if resolved:
            return resolved
    return None


def format_srt_timestamp(seconds: float) -> str:
    millis = int(round(seconds * 1000))
    hours, remainder = divmod(millis, 3600000)
    minutes, remainder = divmod(remainder, 60000)
    secs, ms = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{ms:03}"


def collect_asset_status(config: dict[str, Any]) -> tuple[list[Path], list[str]]:
    warnings: list[str] = []
    resolved: list[Path] = []
    for rel_path in config["product_assets"]["images"]:
        path = ROOT_DIR / rel_path
        if path.exists():
            resolved.append(path)
        else:
            warnings.append(f"Missing product image: {path}")
    return resolved, warnings


def build_storyboard(config: dict[str, Any]) -> str:
    lines = [
        "# TikTok Hard Seeding Video - Beginner Screen Remote Drone",
        "",
        "## Product Positioning",
        "This is a beginner-friendly foldable drone positioned as an easy first drone for casual users.",
        "The core angle is low-friction flying: built-in screen remote, no phone needed, one-click takeoff, and a full ready-to-fly kit.",
        "",
        "## Shot List",
        "| Time | Scene | Visual | Subtitle | Voiceover | Purpose |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for shot in config["shot_list"]:
        lines.append(
            f"| {shot['start']}-{shot['end']}s | {shot['scene']} | {shot['visual']} | "
            f"{shot['subtitle'].replace(chr(10), ' / ')} | {shot['voiceover']} | {shot['purpose']} |"
        )
    lines.extend(
        [
            "",
            "## Editing Notes",
            "- Cut every 2-3 seconds to maintain TikTok pacing.",
            "- Keep subtitles large, high-contrast, and centered in the safe area.",
            "- Use quick push-ins, punchy reveals, and direct ecommerce framing.",
            "- Prioritize product clarity over abstract cinematic styling.",
            "- If real motion clips are unavailable, use the generated prompts, voiceover, and subtitles for CapCut finishing.",
            "",
            "## Compliance Notes",
            "- Do not claim 4K, GPS, obstacle avoidance, long range, or professional aerial performance.",
            "- Do not use fake scarcity or unverifiable discount language.",
            "- Keep claims anchored to visible product features: screen remote, no phone workflow, one-click takeoff, dual camera switching, included accessories.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_voiceover_text(config: dict[str, Any]) -> str:
    return "\n".join(config["voiceover"]) + "\n"


def build_srt(config: dict[str, Any]) -> str:
    lines: list[str] = []
    for index, item in enumerate(config["subtitles"], start=1):
        lines.append(str(index))
        lines.append(f"{format_srt_timestamp(item['start'])} --> {format_srt_timestamp(item['end'])}")
        lines.append(item["text"])
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def build_caption(config: dict[str, Any]) -> str:
    hashtags = " ".join(config["hashtags"])
    return f"{config['final_caption']}\n\n{hashtags}\n"


def build_shot_list_markdown(config: dict[str, Any]) -> str:
    lines = ["# Shot List", ""]
    for shot in config["shot_list"]:
        lines.extend(
            [
                f"## {shot['id']}",
                f"- Time: {shot['start']}-{shot['end']}s",
                f"- Scene: {shot['scene']}",
                f"- Visual: {shot['visual']}",
                f"- Subtitle: {shot['subtitle']}",
                f"- Voiceover: {shot['voiceover']}",
                f"- Purpose: {shot['purpose']}",
                "",
            ]
        )
    return "\n".join(lines)


def preferred_video_provider() -> str:
    if any(key in __import__("os").environ for key in ["FAL_KEY", "FAL_AI_API_KEY"]):
        return "seedance"
    return "auto"


def preferred_tts_provider() -> str:
    env = __import__("os").environ
    if "ELEVENLABS_API_KEY" in env:
        return "elevenlabs"
    if "OPENAI_API_KEY" in env:
        return "openai"
    if "GOOGLE_API_KEY" in env:
        return "google"
    if "DOUBAO_SPEECH_API_KEY" in env or "ARK_API_KEY" in env:
        return "doubao"
    return "auto"


def generate_video_clips(
    config: dict[str, Any],
    image_paths: list[Path],
    skip_video_gen: bool,
) -> tuple[list[dict[str, Any]], list[str], float]:
    warnings: list[str] = []
    results: list[dict[str, Any]] = []
    total_cost = 0.0

    if skip_video_gen:
        warnings.append("Video generation skipped by flag.")
        return results, warnings, total_cost

    selector = VideoSelector()
    if not image_paths:
        warnings.append("No product images found, skipped video generation.")
        return results, warnings, total_cost

    prompt_map = {item["shot_id"]: item["prompt"] for item in config["ai_video_prompts"]}
    asset_cycle = image_paths if image_paths else []
    for index, shot in enumerate(config["shot_list"]):
        clip_path = CLIPS_DIR / f"{shot['id']}.mp4"
        prompt = prompt_map.get(shot["id"], shot["visual"])
        duration = max(1, int(shot["end"] - shot["start"]))
        primary_image = asset_cycle[min(index, len(asset_cycle) - 1)]
        inputs: dict[str, Any] = {
            "prompt": prompt,
            "preferred_provider": preferred_video_provider(),
            "aspect_ratio": config["aspect_ratio"],
            "duration": str(duration),
            "operation": "image_to_video",
            "reference_image_path": str(primary_image),
            "output_path": str(clip_path),
        }

        if len(asset_cycle) >= 2:
            window = asset_cycle[max(0, index - 1): min(len(asset_cycle), index + 2)]
            inputs["operation"] = "reference_to_video"
            inputs["reference_image_paths"] = [str(path) for path in window]
            inputs.pop("reference_image_path", None)

        result = selector.execute(inputs)
        item = {
            "shot_id": shot["id"],
            "success": result.success,
            "selected_provider": result.data.get("selected_provider"),
            "selected_tool": result.data.get("selected_tool"),
            "error": result.error,
            "cost_usd": result.cost_usd,
            "artifacts": result.artifacts,
            "output_path": str(clip_path),
        }
        total_cost += result.cost_usd
        if result.success:
            actual_output = next((Path(path) for path in result.artifacts if Path(path).suffix.lower() == ".mp4"), clip_path)
            item["output_path"] = str(actual_output)
        else:
            warnings.append(f"{shot['id']}: {result.error}")
        results.append(item)
    return results, warnings, total_cost


def generate_voiceover_audio(config: dict[str, Any], skip_tts: bool) -> tuple[Path | None, str | None, float]:
    if skip_tts:
        return None, "TTS generation skipped by flag.", 0.0

    selector = TTSSelector()
    output_path = OUTPUT_DIR / "voiceover.mp3"
    result = selector.execute(
        {
            "text": " ".join(config["voiceover"]),
            "preferred_provider": preferred_tts_provider(),
            "output_path": str(output_path),
            "instructions": "Fast-paced TikTok ecommerce UGC voiceover, clear, confident, upbeat, natural.",
            "speed": 1.02,
        }
    )
    if not result.success:
        return None, result.error, result.cost_usd
    actual_output = next((Path(path) for path in result.artifacts if Path(path).suffix.lower() in {".mp3", ".wav", ".m4a"}), output_path)
    return actual_output, None, result.cost_usd


def concat_clips_ffmpeg(clip_paths: list[Path], output_path: Path) -> str | None:
    ffmpeg_cmd = find_command("ffmpeg", "ffmpeg.exe")
    if not ffmpeg_cmd:
        return "ffmpeg not found on PATH, skipped final video assembly."
    if not clip_paths:
        return "No generated clips were available for assembly."

    concat_file = OUTPUT_DIR / "clips.txt"
    concat_file.write_text(
        "\n".join(f"file '{path.resolve().as_posix()}'" for path in clip_paths),
        encoding="utf-8",
    )
    command = [
        ffmpeg_cmd,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_file),
        "-c",
        "copy",
        str(output_path),
    ]
    proc = subprocess.run(command, capture_output=True, text=True)
    if proc.returncode == 0 and output_path.exists():
        return None

    command = [
        ffmpeg_cmd,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_file),
        "-vf",
        "scale=1080:1920:force_original_aspect_ratio=cover,crop=1080:1920",
        "-r",
        "30",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-an",
        str(output_path),
    ]
    proc = subprocess.run(command, capture_output=True, text=True)
    if proc.returncode != 0 or not output_path.exists():
        return proc.stderr.strip() or "ffmpeg concat failed."
    return None


def mux_audio_and_subtitles(video_path: Path, audio_path: Path | None, subtitle_path: Path, final_output: Path) -> str | None:
    ffmpeg_cmd = find_command("ffmpeg", "ffmpeg.exe")
    if not ffmpeg_cmd:
        return "ffmpeg not found on PATH, skipped subtitle burn and audio mux."
    if not video_path.exists():
        return "Base preview video missing, skipped final mux."

    subtitle_filter_path = subtitle_path.resolve().as_posix().replace(":", "\\:")
    subtitle_filter = f"subtitles='{subtitle_filter_path}'"
    command = [ffmpeg_cmd, "-y", "-i", str(video_path)]
    if audio_path and audio_path.exists():
        command.extend(["-i", str(audio_path)])
    command.extend(
        [
            "-vf",
            subtitle_filter,
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-shortest",
        ]
    )
    if audio_path and audio_path.exists():
        command.extend(["-c:a", "aac", "-b:a", "192k"])
    else:
        command.append("-an")
    command.append(str(final_output))
    proc = subprocess.run(command, capture_output=True, text=True)
    if proc.returncode != 0 or not final_output.exists():
        return proc.stderr.strip() or "ffmpeg subtitle burn failed."
    return None


def write_outputs(config: dict[str, Any], video_results: list[dict[str, Any]], warnings: list[str]) -> dict[str, str]:
    shot_prompts = {
        "product_name": config["product_name"],
        "style": config["style"],
        "aspect_ratio": config["aspect_ratio"],
        "prompts": config["ai_video_prompts"],
        "generation_results": video_results,
        "warnings": warnings,
    }
    files = {
        "storyboard": OUTPUT_DIR / "storyboard.md",
        "voiceover": OUTPUT_DIR / "voiceover.txt",
        "subtitles": OUTPUT_DIR / "subtitles.srt",
        "shot_prompts": OUTPUT_DIR / "shot_prompts.json",
        "caption": OUTPUT_DIR / "tiktok_caption.txt",
        "capcut_script": CAPCUT_DIR / "script.txt",
        "capcut_subtitles": CAPCUT_DIR / "subtitles.srt",
        "capcut_caption": CAPCUT_DIR / "caption.txt",
        "capcut_shot_list": CAPCUT_DIR / "shot_list.md",
        "capcut_prompts": CAPCUT_DIR / "prompts.json",
    }
    files["storyboard"].write_text(build_storyboard(config), encoding="utf-8")
    files["voiceover"].write_text(build_voiceover_text(config), encoding="utf-8")
    files["subtitles"].write_text(build_srt(config), encoding="utf-8")
    files["shot_prompts"].write_text(json.dumps(shot_prompts, indent=2, ensure_ascii=False), encoding="utf-8")
    files["caption"].write_text(build_caption(config), encoding="utf-8")
    files["capcut_script"].write_text(build_voiceover_text(config), encoding="utf-8")
    files["capcut_subtitles"].write_text(build_srt(config), encoding="utf-8")
    files["capcut_caption"].write_text(build_caption(config), encoding="utf-8")
    files["capcut_shot_list"].write_text(build_shot_list_markdown(config), encoding="utf-8")
    files["capcut_prompts"].write_text(json.dumps(config["ai_video_prompts"], indent=2, ensure_ascii=False), encoding="utf-8")
    return {key: str(value) for key, value in files.items()}


def write_run_report(
    config: dict[str, Any],
    assets_found: list[Path],
    warnings: list[str],
    video_results: list[dict[str, Any]],
    voiceover_audio: Path | None,
    total_cost_usd: float,
    final_video: Path | None,
) -> Path:
    report = {
        "product_name": config["product_name"],
        "platform": config["platform"],
        "assets_found": [str(path) for path in assets_found],
        "warnings": warnings,
        "video_results": video_results,
        "voiceover_audio": str(voiceover_audio) if voiceover_audio else None,
        "final_video": str(final_video) if final_video else None,
        "total_cost_usd": round(total_cost_usd, 4),
    }
    report_path = OUTPUT_DIR / "run_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a TikTok hard-sell ecommerce package for the beginner drone demo."
    )
    parser.add_argument("--config", default=str(CONFIG_PATH), help="Path to JSON config.")
    parser.add_argument("--skip-video-gen", action="store_true", help="Only build planning assets, skip video generation.")
    parser.add_argument("--skip-tts", action="store_true", help="Skip voiceover audio generation.")
    args = parser.parse_args(argv)

    load_shared_env()
    ensure_output_dirs()

    config = read_config(Path(args.config))
    assets_found, warnings = collect_asset_status(config)
    output_files = write_outputs(config, [], warnings)

    video_results, video_warnings, video_cost = generate_video_clips(config, assets_found, args.skip_video_gen)
    warnings.extend(video_warnings)
    output_files = write_outputs(config, video_results, warnings)

    voiceover_audio, tts_error, tts_cost = generate_voiceover_audio(config, args.skip_tts)
    if tts_error:
        warnings.append(tts_error)

    rough_cut_path = OUTPUT_DIR / "rough_cut_preview.mp4"
    final_video_path = OUTPUT_DIR / "final_video.mp4"
    clip_paths = [
        Path(item["output_path"])
        for item in video_results
        if item.get("success") and Path(item["output_path"]).exists()
    ]

    assembly_error = concat_clips_ffmpeg(clip_paths, rough_cut_path)
    if assembly_error:
        warnings.append(assembly_error)

    final_error = None
    if rough_cut_path.exists():
        final_error = mux_audio_and_subtitles(rough_cut_path, voiceover_audio, Path(output_files["subtitles"]), final_video_path)
        if final_error:
            warnings.append(final_error)

    total_cost_usd = video_cost + tts_cost
    report_path = write_run_report(
        config=config,
        assets_found=assets_found,
        warnings=warnings,
        video_results=video_results,
        voiceover_audio=voiceover_audio,
        total_cost_usd=total_cost_usd,
        final_video=final_video_path if final_video_path.exists() else None,
    )

    print(f"[OpenMontage] Output directory: {OUTPUT_DIR}")
    print(f"[OpenMontage] Storyboard: {output_files['storyboard']}")
    print(f"[OpenMontage] Voiceover text: {output_files['voiceover']}")
    print(f"[OpenMontage] Subtitles: {output_files['subtitles']}")
    print(f"[OpenMontage] Shot prompts: {output_files['shot_prompts']}")
    print(f"[OpenMontage] TikTok caption: {output_files['caption']}")
    print(f"[OpenMontage] CapCut package: {CAPCUT_DIR}")
    if rough_cut_path.exists():
        print(f"[OpenMontage] Rough cut preview: {rough_cut_path}")
    if final_video_path.exists():
        print(f"[OpenMontage] Final video: {final_video_path}")
    if voiceover_audio and voiceover_audio.exists():
        print(f"[OpenMontage] Voiceover audio: {voiceover_audio}")
    print(f"[OpenMontage] Run report: {report_path}")
    print(f"[OpenMontage] Estimated/actual tool cost logged: ${total_cost_usd:.2f}")

    if warnings:
        print("[OpenMontage] Warnings:")
        for warning in warnings:
            print(f"  - {warning}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
