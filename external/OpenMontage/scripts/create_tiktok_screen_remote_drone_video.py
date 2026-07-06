from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.audio.tts_selector import TTSSelector


OUTPUT_DIR = ROOT_DIR / "outputs" / "tiktok_screen_remote_drone"
TEMP_DIR = OUTPUT_DIR / "temp"
ASSET_DIR = ROOT_DIR / "assets" / "products" / "screen_remote_drone"
FINAL_VIDEO_PATH = OUTPUT_DIR / "final_screen_remote_drone_tiktok.mp4"
SCRIPT_PATH = OUTPUT_DIR / "script.md"
STORYBOARD_PATH = OUTPUT_DIR / "storyboard.json"
CAPTIONS_PATH = OUTPUT_DIR / "captions.srt"
CAPTION_TXT_PATH = OUTPUT_DIR / "caption.txt"
RUN_LOG_PATH = OUTPUT_DIR / "run_log.md"
NARRATION_PATH = OUTPUT_DIR / "voiceover.mp3"
MIXED_AUDIO_PATH = OUTPUT_DIR / "voiceover_mixed.wav"
CONCAT_PATH = TEMP_DIR / "concat.txt"
ROUGH_VIDEO_PATH = OUTPUT_DIR / "rough_screen_remote_drone_tiktok.mp4"

WIDTH = 1080
HEIGHT = 1920
FPS = 30
TOTAL_DURATION = 30

FONT_BOLD = Path(r"C:\Windows\Fonts\arialbd.ttf")
FONT_REGULAR = Path(r"C:\Windows\Fonts\arial.ttf")


@dataclass
class Shot:
    shot: int
    start: int
    end: int
    visual: str
    subtitle: str
    voiceover: str
    asset: str
    purpose: str
    visual_style: str
    overlay_mode: str


SHOTS: list[Shot] = [
    Shot(
        shot=1,
        start=0,
        end=3,
        visual="Fast hook shot showing the screen remote and drone product.",
        subtitle="Still using your phone to fly a drone?",
        voiceover="Still using your phone just to fly a drone?",
        asset="assets/products/screen_remote_drone/02_screen_remote.jpg",
        purpose="hook",
        visual_style="fast_push",
        overlay_mode="hook_phone",
    ),
    Shot(
        shot=2,
        start=3,
        end=6,
        visual="Close-up of the built-in screen remote with glow around the LCD area.",
        subtitle="Built-in screen remote",
        voiceover="This one has a built-in screen remote.",
        asset="assets/products/screen_remote_drone/02_screen_remote.jpg",
        purpose="differentiator",
        visual_style="slow_push",
        overlay_mode="screen_glow",
    ),
    Shot(
        shot=3,
        start=6,
        end=9,
        visual="Drone and remote together with a bold no-phone-required callout.",
        subtitle="No phone required",
        voiceover="No phone. No app setup. Just fly.",
        asset="assets/products/screen_remote_drone/06_remote_guide.jpg",
        purpose="pain_point",
        visual_style="pan_right",
        overlay_mode="no_phone",
    ),
    Shot(
        shot=4,
        start=9,
        end=12,
        visual="One-click controls highlighted on the remote guide image.",
        subtitle="One-click takeoff & landing",
        voiceover="One button for takeoff and landing.",
        asset="assets/products/screen_remote_drone/04_one_click.jpg",
        purpose="beginner_friendly",
        visual_style="push_bottom",
        overlay_mode="button_click",
    ),
    Shot(
        shot=5,
        start=12,
        end=15,
        visual="Dual camera module close-up with arrow emphasis and 90 degree cue.",
        subtitle="Dual camera switching",
        voiceover="Switch camera angles right from the remote.",
        asset="assets/products/screen_remote_drone/03_dual_camera.jpg",
        purpose="feature_demo",
        visual_style="slow_push",
        overlay_mode="camera_arrow",
    ),
    Shot(
        shot=6,
        start=15,
        end=18,
        visual="Stable hovering story using the beginner control image with hovering visual treatment.",
        subtitle="Stable hovering for beginners",
        voiceover="Stable hovering makes it easier for beginners.",
        asset="assets/products/screen_remote_drone/04_one_click.jpg",
        purpose="stability",
        visual_style="hover",
        overlay_mode="hover_ring",
    ),
    Shot(
        shot=7,
        start=18,
        end=21,
        visual="Full kit laid out with labels on drone, remote, batteries, carry case, and propellers.",
        subtitle="Comes with the full kit",
        voiceover="You get the drone, screen remote, batteries, propellers, and a carry case.",
        asset="assets/products/screen_remote_drone/01_package.jpg",
        purpose="value",
        visual_style="pan_left",
        overlay_mode="accessory_labels",
    ),
    Shot(
        shot=8,
        start=21,
        end=24,
        visual="Battery module close-up with animated energy-bar feel.",
        subtitle="Extra batteries. More fun.",
        voiceover="Extra batteries mean more flying time and more fun.",
        asset="assets/products/screen_remote_drone/05_battery.jpg",
        purpose="battery_value",
        visual_style="push_right",
        overlay_mode="battery_energy",
    ),
    Shot(
        shot=9,
        start=24,
        end=27,
        visual="Clean family shot of the drone and screen remote framed as a great first drone.",
        subtitle="Great first drone",
        voiceover="If you want a simple first drone, this is a solid pick.",
        asset="assets/products/screen_remote_drone/01_package.jpg",
        purpose="positioning",
        visual_style="hero_push",
        overlay_mode="gift_pick",
    ),
    Shot(
        shot=10,
        start=27,
        end=30,
        visual="Final CTA hero shot with product and a strong tap-to-check-it-out call to action.",
        subtitle="Tap to check it out",
        voiceover="Tap to check it out.",
        asset="assets/products/screen_remote_drone/02_screen_remote.jpg",
        purpose="cta",
        visual_style="hero_push",
        overlay_mode="cta_button",
    ),
]


def load_env_files() -> None:
    for env_path in [ROOT_DIR.parent.parent / ".env", ROOT_DIR / ".env"]:
        if env_path.exists():
            load_dotenv(env_path, override=False)


def ensure_dirs() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)


def find_command(*names: str) -> str | None:
    for name in names:
        resolved = shutil.which(name)
        if resolved:
            return resolved
    return None


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True)


def asset_path(rel_path: str) -> Path:
    return ROOT_DIR / rel_path


def required_assets_exist() -> tuple[bool, list[Path]]:
    paths = [asset_path(shot.asset) for shot in SHOTS]
    missing = [path for path in paths if not path.exists()]
    return not missing, missing


def escape_drawtext_text(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", r"\'")
        .replace("%", r"\%")
        .replace(",", r"\,")
    )


def ffmpeg_quote(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/").replace(":", r"\:")


def build_motion_filter(style: str, duration: int) -> str:
    frames = duration * FPS
    if style == "fast_push":
        return (
            "scale=1800:-1,"
            f"zoompan=z='min(1.35,1.02+on*0.004)':"
            "x='iw/2-(iw/zoom/2)':"
            "y='ih/2-(ih/zoom/2)':"
            f"d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS}"
        )
    if style == "slow_push":
        return (
            "scale=1700:-1,"
            f"zoompan=z='min(1.18,1.0+on*0.002)':"
            "x='iw/2-(iw/zoom/2)':"
            "y='ih/2-(ih/zoom/2)':"
            f"d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS}"
        )
    if style == "pan_right":
        return (
            "scale=1900:-1,"
            f"zoompan=z='1.10':"
            "x='min(max(0,on*4),iw-iw/zoom)':"
            "y='ih/2-(ih/zoom/2)':"
            f"d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS}"
        )
    if style == "pan_left":
        return (
            "scale=1900:-1,"
            f"zoompan=z='1.08':"
            "x='max(0,(iw-iw/zoom)-on*4)':"
            "y='ih/2-(ih/zoom/2)':"
            f"d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS}"
        )
    if style == "push_bottom":
        return (
            "scale=1750:-1,"
            f"zoompan=z='min(1.20,1.0+on*0.0025)':"
            "x='iw/2-(iw/zoom/2)':"
            "y='max(0,ih-iH/zoom-on*2)'".replace("iH", "ih") + f":d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS}"
        )
    if style == "push_right":
        return (
            "scale=1750:-1,"
            f"zoompan=z='min(1.18,1.0+on*0.002)':"
            "x='min(max(0,on*2),iw-iw/zoom)':"
            "y='ih/2-(ih/zoom/2)':"
            f"d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS}"
        )
    if style in {"hero_push", "hover"}:
        return (
            "scale=1750:-1,"
            f"zoompan=z='min(1.22,1.0+on*0.0024)':"
            "x='iw/2-(iw/zoom/2)':"
            "y='ih/2-(ih/zoom/2)+sin(on/8)*10':"
            f"d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS}"
        )
    return (
        "scale=1750:-1,"
        f"zoompan=z='1.10':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS}"
    )


def build_overlay_filter(shot: Shot) -> str:
    font_bold = ffmpeg_quote(FONT_BOLD if FONT_BOLD.exists() else FONT_REGULAR)
    font_regular = ffmpeg_quote(FONT_REGULAR if FONT_REGULAR.exists() else FONT_BOLD)
    filters: list[str] = []

    # Common cinematic contrast layer.
    filters.append("eq=contrast=1.04:saturation=1.08:brightness=0.01")
    filters.append("drawbox=x=0:y=0:w=iw:h=ih:color=black@0.10:t=fill")

    if shot.overlay_mode == "hook_phone":
        filters.extend(
            [
                "drawbox=x=70:y=1160:w=940:h=180:color=black@0.38:t=fill",
                f"drawtext=fontfile='{font_bold}':text='Still using your phone?':x=(w-text_w)/2:y=1205:fontsize=62:fontcolor=white:borderw=3:bordercolor=black@0.45",
                "drawbox=x=680:y=350:w=250:h=120:color=red@0.16:t=fill",
                f"drawtext=fontfile='{font_bold}':text='PHONE':x=730:y=386:fontsize=42:fontcolor=yellow:borderw=2:bordercolor=black@0.35",
            ]
        )
    elif shot.overlay_mode == "screen_glow":
        filters.extend(
            [
                "drawbox=x=305:y=790:w=470:h=350:color=0x4CC9F0@0.20:t=fill",
                "drawbox=x=295:y=780:w=490:h=370:color=0x4CC9F0@0.95:t=6",
                "drawbox=x=65:y=1180:w=950:h=150:color=black@0.36:t=fill",
                f"drawtext=fontfile='{font_bold}':text='Built-in screen remote':x=(w-text_w)/2:y=1220:fontsize=58:fontcolor=white:borderw=3:bordercolor=black@0.45",
                f"drawtext=fontfile='{font_bold}':text='SCREEN REMOTE':x=330:y=720:fontsize=40:fontcolor=0x4CC9F0:borderw=2:bordercolor=black@0.35",
            ]
        )
    elif shot.overlay_mode == "no_phone":
        filters.extend(
            [
                "drawbox=x=80:y=1060:w=920:h=160:color=black@0.42:t=fill",
                f"drawtext=fontfile='{font_bold}':text='No phone required':x=(w-text_w)/2:y=1100:fontsize=60:fontcolor=white:borderw=3:bordercolor=black@0.45",
                "drawbox=x=135:y=245:w=520:h=110:color=0xB5179E@0.88:t=fill",
                f"drawtext=fontfile='{font_bold}':text='NO PHONE REQUIRED':x=175:y=277:fontsize=38:fontcolor=white:borderw=1:bordercolor=black@0.25",
            ]
        )
    elif shot.overlay_mode == "button_click":
        filters.extend(
            [
                "drawbox=x=80:y=1085:w=920:h=160:color=black@0.42:t=fill",
                f"drawtext=fontfile='{font_bold}':text='One-click takeoff & landing':x=(w-text_w)/2:y=1125:fontsize=54:fontcolor=white:borderw=3:bordercolor=black@0.45",
                "drawbox=x=520:y=420:w=180:h=180:color=yellow@0.18:t=fill",
                "drawbox=x=510:y=410:w=200:h=200:color=yellow@0.92:t=6",
                f"drawtext=fontfile='{font_bold}':text='CLICK':x=522:y=620:fontsize=42:fontcolor=yellow:borderw=2:bordercolor=black@0.35",
            ]
        )
    elif shot.overlay_mode == "camera_arrow":
        filters.extend(
            [
                "drawbox=x=250:y=1080:w=580:h=160:color=black@0.42:t=fill",
                f"drawtext=fontfile='{font_bold}':text='Dual camera switching':x=(w-text_w)/2:y=1120:fontsize=56:fontcolor=white:borderw=3:bordercolor=black@0.45",
                "drawbox=x=315:y=785:w=255:h=255:color=0x00B4D8@0.88:t=6",
                f"drawtext=fontfile='{font_bold}':text='90°':x=690:y=960:fontsize=74:fontcolor=0xFFD60A:borderw=3:bordercolor=black@0.35",
            ]
        )
    elif shot.overlay_mode == "hover_ring":
        filters.extend(
            [
                "drawbox=x=90:y=1085:w=900:h=160:color=black@0.42:t=fill",
                f"drawtext=fontfile='{font_bold}':text='Stable hovering for beginners':x=(w-text_w)/2:y=1125:fontsize=52:fontcolor=white:borderw=3:bordercolor=black@0.45",
                "drawbox=x=260:y=1260:w=560:h=10:color=0x00F5D4@0.82:t=fill",
                "drawbox=x=535:y=1240:w=10:h=60:color=0x00F5D4@0.82:t=fill",
            ]
        )
    elif shot.overlay_mode == "accessory_labels":
        filters.extend(
            [
                "drawbox=x=90:y=1100:w=900:h=150:color=black@0.42:t=fill",
                f"drawtext=fontfile='{font_bold}':text='Comes with the full kit':x=(w-text_w)/2:y=1140:fontsize=56:fontcolor=white:borderw=3:bordercolor=black@0.45",
                f"drawtext=fontfile='{font_regular}':text='Drone':x=650:y=190:fontsize=34:fontcolor=0xFFD60A:borderw=2:bordercolor=black@0.30",
                f"drawtext=fontfile='{font_regular}':text='Screen Remote':x=270:y=1020:fontsize=34:fontcolor=0x4CC9F0:borderw=2:bordercolor=black@0.30",
                f"drawtext=fontfile='{font_regular}':text='Batteries':x=840:y=1180:fontsize=34:fontcolor=0x00F5D4:borderw=2:bordercolor=black@0.30",
                f"drawtext=fontfile='{font_regular}':text='Carry Case':x=735:y=55:fontsize=34:fontcolor=white:borderw=2:bordercolor=black@0.30",
                f"drawtext=fontfile='{font_regular}':text='Propellers':x=175:y=585:fontsize=34:fontcolor=0xFFD60A:borderw=2:bordercolor=black@0.30",
            ]
        )
    elif shot.overlay_mode == "battery_energy":
        filters.extend(
            [
                "drawbox=x=120:y=1120:w=840:h=150:color=black@0.42:t=fill",
                f"drawtext=fontfile='{font_bold}':text='Extra batteries. More fun.':x=(w-text_w)/2:y=1160:fontsize=56:fontcolor=white:borderw=3:bordercolor=black@0.45",
                "drawbox=x=240:y=1320:w=600:h=34:color=white@0.20:t=fill",
                "drawbox=x=240:y=1320:w=470:h=34:color=0x00F5D4@0.90:t=fill",
                f"drawtext=fontfile='{font_bold}':text='POWER':x=820:y=1310:fontsize=30:fontcolor=0x00F5D4:borderw=2:bordercolor=black@0.30",
            ]
        )
    elif shot.overlay_mode == "gift_pick":
        filters.extend(
            [
                "drawbox=x=110:y=1120:w=860:h=150:color=black@0.42:t=fill",
                f"drawtext=fontfile='{font_bold}':text='Great first drone':x=(w-text_w)/2:y=1160:fontsize=58:fontcolor=white:borderw=3:bordercolor=black@0.45",
                "drawbox=x=330:y=270:w=420:h=90:color=0x4CC9F0@0.82:t=fill",
                f"drawtext=fontfile='{font_bold}':text='EASY FIRST PICK':x=372:y=298:fontsize=34:fontcolor=white:borderw=2:bordercolor=black@0.25",
            ]
        )
    elif shot.overlay_mode == "cta_button":
        filters.extend(
            [
                "drawbox=x=210:y=1105:w=660:h=130:color=0xF72585@0.90:t=fill",
                f"drawtext=fontfile='{font_bold}':text='Tap to check it out':x=(w-text_w)/2:y=1140:fontsize=56:fontcolor=white:borderw=3:bordercolor=black@0.40",
                "drawbox=x=275:y=1260:w=530:h=12:color=white@0.65:t=fill",
            ]
        )

    filters.append("fade=t=in:st=0:d=0.2")
    filters.append("fade=t=out:st=2.7:d=0.3")
    return ",".join(filters)


def render_shot_clip(ffmpeg_cmd: str, shot: Shot) -> Path:
    input_image = asset_path(shot.asset)
    output_clip = TEMP_DIR / f"shot_{shot.shot:02d}.mp4"
    motion = build_motion_filter(shot.visual_style, shot.end - shot.start)
    overlays = build_overlay_filter(shot)
    vf = f"{motion},{overlays}"

    command = [
        ffmpeg_cmd,
        "-y",
        "-loop",
        "1",
        "-i",
        str(input_image),
        "-vf",
        vf,
        "-t",
        str(shot.end - shot.start),
        "-r",
        str(FPS),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-an",
        str(output_clip),
    ]
    proc = run_command(command)
    if proc.returncode != 0 or not output_clip.exists():
        raise RuntimeError(f"Failed rendering shot {shot.shot}: {proc.stderr.strip()}")
    return output_clip


def format_srt_ts(seconds: float) -> str:
    total_ms = int(round(seconds * 1000))
    hours, remainder = divmod(total_ms, 3600000)
    minutes, remainder = divmod(remainder, 60000)
    secs, ms = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{ms:03}"


def write_storyboard() -> None:
    payload = [
        {
            "shot": shot.shot,
            "start": shot.start,
            "end": shot.end,
            "visual": shot.visual,
            "subtitle": shot.subtitle,
            "voiceover": shot.voiceover,
            "asset": shot.asset,
            "purpose": shot.purpose,
        }
        for shot in SHOTS
    ]
    STORYBOARD_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_captions() -> None:
    lines: list[str] = []
    for idx, shot in enumerate(SHOTS, start=1):
        lines.append(str(idx))
        lines.append(f"{format_srt_ts(shot.start)} --> {format_srt_ts(shot.end)}")
        lines.append(shot.subtitle)
        lines.append("")
    CAPTIONS_PATH.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def write_script_md() -> None:
    vo = "\n".join(shot.voiceover for shot in SHOTS)
    subs = "\n".join(shot.subtitle for shot in SHOTS)
    shot_lines = []
    for shot in SHOTS:
        shot_lines.extend(
            [
                f"### Shot {shot.shot} ({shot.start}-{shot.end}s)",
                f"- Asset: `{shot.asset}`",
                f"- Purpose: {shot.purpose}",
                f"- Visual: {shot.visual}",
                f"- Subtitle: {shot.subtitle}",
                f"- Voiceover: {shot.voiceover}",
                "",
            ]
        )

    script = "\n".join(
        [
            "# TikTok Screen Remote Drone Script",
            "",
            "## Video Positioning",
            "A TikTok UGC-style product recommendation video for a beginner-friendly foldable drone with a built-in screen remote.",
            "",
            "## Full English Voiceover",
            vo,
            "",
            "## Full English Subtitles",
            subs,
            "",
            "## 10-Shot Storyboard",
            *shot_lines,
            "## TikTok Caption",
            "Still using your phone to fly a drone? This beginner-friendly drone has a built-in screen remote, one-click takeoff, dual camera switching, and a full accessory kit. Great first drone to try.",
            "",
            "## Hashtags",
            "#BeginnerDrone #DroneTok #TechFinds #CoolGadgets #GiftIdeas #OutdoorGadgets #TikTokMadeMeBuyIt #GadgetFinds",
            "",
            "## Compliance Notes",
            "- Do not claim 4K, GPS, obstacle avoidance, pro drone quality, or long range.",
            "- Keep the positioning centered on beginner ease, no-phone workflow, and kit value.",
            "- Avoid unsafe flight contexts and platform logos.",
        ]
    )
    SCRIPT_PATH.write_text(script + "\n", encoding="utf-8")


def write_caption_txt() -> None:
    CAPTION_TXT_PATH.write_text(
        "\n".join(
            [
                "TikTok Title:",
                "Beginner Drone With Screen Remote Control",
                "",
                "TikTok Caption:",
                "Still using your phone to fly a drone? This beginner-friendly drone has a built-in screen remote, one-click takeoff, dual camera switching, and a full accessory kit. Great first drone to try.",
                "",
                "Hashtags:",
                "#BeginnerDrone #DroneTok #TechFinds #CoolGadgets #GiftIdeas #OutdoorGadgets #TikTokMadeMeBuyIt #GadgetFinds",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def preferred_tts_order() -> list[str]:
    return ["elevenlabs", "openai", "doubao", "google", "piper"]


def generate_tts_narration() -> tuple[Path | None, str, list[str], bool]:
    selector = TTSSelector()
    text = " ".join(shot.voiceover for shot in SHOTS)
    errors: list[str] = []
    for provider in preferred_tts_order():
        result = selector.execute(
            {
                "text": text,
                "preferred_provider": provider,
                "output_path": str(NARRATION_PATH),
                "instructions": "English TikTok tech gadget recommendation, upbeat, clear, friendly, slightly punchy.",
                "speed": 1.03,
            }
        )
        if result.success:
            artifact = next((Path(path) for path in result.artifacts if Path(path).exists()), NARRATION_PATH)
            return artifact, provider, errors, True
        errors.append(f"{provider}: {result.error}")
    return None, "none", errors, False


def render_click_track(ffmpeg_cmd: str) -> Path:
    click_path = TEMP_DIR / "clicks.wav"
    command = [
        ffmpeg_cmd,
        "-y",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=r=48000:cl=stereo",
        "-t",
        str(TOTAL_DURATION),
        "-filter_complex",
        (
            "aevalsrc='if(lt(mod(t,3),0.08),0.25*sin(2*PI*1200*t),0)':d=30[s1];"
            "aevalsrc='if(lt(mod(t+1.5,3),0.05),0.18*sin(2*PI*800*t),0)':d=30[s2];"
            "[s1][s2]amix=inputs=2:normalize=0,afade=t=in:st=0:d=0.1,afade=t=out:st=29.5:d=0.5"
        ),
        str(click_path),
    ]
    proc = run_command(command)
    if proc.returncode != 0 or not click_path.exists():
        raise RuntimeError(f"Failed generating click track: {proc.stderr.strip()}")
    return click_path


def mix_audio(ffmpeg_cmd: str, narration_path: Path | None) -> tuple[Path | None, str]:
    if narration_path is None or not narration_path.exists():
        return None, "No TTS audio available. Final video will be silent."
    click_track = render_click_track(ffmpeg_cmd)
    command = [
        ffmpeg_cmd,
        "-y",
        "-i",
        str(narration_path),
        "-i",
        str(click_track),
        "-filter_complex",
        "[1:a]volume=0.35[sfx];[0:a][sfx]amix=inputs=2:duration=first:normalize=0[aout]",
        "-map",
        "[aout]",
        "-ar",
        "48000",
        str(MIXED_AUDIO_PATH),
    ]
    proc = run_command(command)
    if proc.returncode != 0 or not MIXED_AUDIO_PATH.exists():
        return None, f"Audio mix failed. Using narration-only fallback. {proc.stderr.strip()}"
    return MIXED_AUDIO_PATH, "Narration mixed with simple click/tech accent track."


def concat_clips(ffmpeg_cmd: str, clips: list[Path]) -> None:
    CONCAT_PATH.write_text(
        "\n".join(f"file '{clip.resolve().as_posix()}'" for clip in clips),
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
        str(CONCAT_PATH),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-r",
        str(FPS),
        "-an",
        str(ROUGH_VIDEO_PATH),
    ]
    proc = run_command(command)
    if proc.returncode != 0 or not ROUGH_VIDEO_PATH.exists():
        raise RuntimeError(f"Failed concatenating clips: {proc.stderr.strip()}")


def burn_subtitles_and_mux(ffmpeg_cmd: str, audio_path: Path | None) -> None:
    subtitle_style = (
        "FontName=Arial,FontSize=18,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
        "BackColour=&H64000000,Bold=1,BorderStyle=3,Outline=2,Shadow=0,"
        "MarginV=220,Alignment=2"
    )
    subtitle_filter = f"subtitles='{ffmpeg_quote(CAPTIONS_PATH)}':force_style='{subtitle_style}'"
    command = [ffmpeg_cmd, "-y", "-i", str(ROUGH_VIDEO_PATH)]
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
            "-r",
            str(FPS),
            "-shortest",
        ]
    )
    if audio_path and audio_path.exists():
        command.extend(["-c:a", "aac", "-b:a", "192k"])
    else:
        command.append("-an")
    command.append(str(FINAL_VIDEO_PATH))
    proc = run_command(command)
    if proc.returncode != 0 or not FINAL_VIDEO_PATH.exists():
        raise RuntimeError(f"Failed rendering final video: {proc.stderr.strip()}")


def probe_duration(ffprobe_cmd: str, path: Path) -> str:
    proc = run_command(
        [ffprobe_cmd, "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)]
    )
    if proc.returncode != 0:
        return "unknown"
    return proc.stdout.strip()


def probe_resolution(ffprobe_cmd: str, path: Path) -> str:
    proc = run_command(
        [
            ffprobe_cmd,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "json",
            str(path),
        ]
    )
    if proc.returncode != 0:
        return "unknown"
    try:
        payload = json.loads(proc.stdout)
        stream = (payload.get("streams") or [{}])[0]
        width = stream.get("width")
        height = stream.get("height")
        if width and height:
            return f"{width}x{height}"
    except Exception:
        pass
    return "unknown"


def write_run_log(
    used_ai_video_model: bool,
    used_fallback_ken_burns: bool,
    used_tts: bool,
    tts_provider: str,
    tts_errors: list[str],
    audio_note: str,
    ffprobe_cmd: str,
) -> tuple[str, str]:
    duration = probe_duration(ffprobe_cmd, FINAL_VIDEO_PATH)
    resolution = probe_resolution(ffprobe_cmd, FINAL_VIDEO_PATH)
    missing_keys = []
    import os

    if not (os.environ.get("ELEVENLABS_API_KEY") or os.environ.get("OPENAI_API_KEY") or os.environ.get("DOUBAO_SPEECH_API_KEY") or os.environ.get("GOOGLE_API_KEY")):
        missing_keys.append("No remote TTS API key found")
    if not os.environ.get("FAL_KEY"):
        missing_keys.append("FAL_KEY not used for this render path")

    body = [
        "# Run Log",
        "",
        "## Materials Used",
        *[f"- {shot.asset}" for shot in SHOTS],
        "",
        "## Render Strategy",
        "- Video generation method: Local FFmpeg Ken Burns slideshow with per-shot motion and overlays",
        f"- Used AI video model: {'yes' if used_ai_video_model else 'no'}",
        f"- Used fallback image dynamic composition: {'yes' if used_fallback_ken_burns else 'no'}",
        f"- Used TTS: {'yes' if used_tts else 'no'}",
        f"- TTS provider used: {tts_provider}",
        f"- Audio note: {audio_note}",
        "",
        "## TTS Fallback Errors",
        *([f"- {item}" for item in tts_errors] if tts_errors else ["- none"]),
        "",
        "## Missing API Keys / Capability Notes",
        *([f"- {item}" for item in missing_keys] if missing_keys else ["- none"]),
        "",
        "## Final Output",
        f"- Final video path: {FINAL_VIDEO_PATH}",
        f"- Final video duration: {duration}",
        f"- Final resolution: {resolution}",
        "",
        "## Next Step For Other SKUs",
        "- Replace the 6 product images in assets/products/screen_remote_drone/ with the next SKU set.",
        "- Update the shot asset mapping or duplicate this script with a new product folder.",
        "- Re-run the script to mass-produce another TikTok-ready fallback video.",
    ]
    RUN_LOG_PATH.write_text("\n".join(body) + "\n", encoding="utf-8")
    return duration, resolution


def main() -> int:
    load_env_files()
    ensure_dirs()

    ffmpeg_cmd = find_command("ffmpeg", "ffmpeg.exe")
    ffprobe_cmd = find_command("ffprobe", "ffprobe.exe")
    ok, missing = required_assets_exist()
    if not ok:
        print("请把 6 张无人机产品图放到 assets/products/screen_remote_drone/ 并按 01_package.jpg 到 06_remote_guide.jpg 命名。")
        for path in missing:
            print(f"Missing: {path}")
        return 1
    if not ffmpeg_cmd or not ffprobe_cmd:
        RUN_LOG_PATH.write_text(
            "FFmpeg or ffprobe not found on PATH. Install FFmpeg from https://ffmpeg.org/download.html\n",
            encoding="utf-8",
        )
        print("FFmpeg not found. Install FFmpeg and re-run.")
        return 1

    write_storyboard()
    write_captions()
    write_script_md()
    write_caption_txt()

    clips = [render_shot_clip(ffmpeg_cmd, shot) for shot in SHOTS]
    concat_clips(ffmpeg_cmd, clips)

    narration_path, tts_provider, tts_errors, used_tts = generate_tts_narration()
    mixed_audio, audio_note = mix_audio(ffmpeg_cmd, narration_path)
    burn_subtitles_and_mux(ffmpeg_cmd, mixed_audio if mixed_audio and mixed_audio.exists() else narration_path)

    duration, resolution = write_run_log(
        used_ai_video_model=False,
        used_fallback_ken_burns=True,
        used_tts=used_tts and (mixed_audio is not None or narration_path is not None),
        tts_provider=tts_provider,
        tts_errors=tts_errors,
        audio_note=audio_note,
        ffprobe_cmd=ffprobe_cmd,
    )

    missing_api_keys = []
    import os
    if not os.environ.get("FAL_KEY"):
        missing_api_keys.append("FAL_KEY")
    if not any(os.environ.get(key) for key in ["ELEVENLABS_API_KEY", "OPENAI_API_KEY", "DOUBAO_SPEECH_API_KEY", "GOOGLE_API_KEY"]):
        missing_api_keys.append("TTS_API_KEYS")

    print("DONE")
    print("Final video: outputs/tiktok_screen_remote_drone/final_screen_remote_drone_tiktok.mp4")
    print(f"Duration: {duration}")
    print(f"Resolution: {resolution}")
    print("Used AI video model: no")
    print("Used fallback Ken Burns video: yes")
    print(f"Used TTS: {'yes' if used_tts and (mixed_audio is not None or narration_path is not None) else 'no'}")
    print(f"Missing API keys: {', '.join(missing_api_keys) if missing_api_keys else 'none'}")
    print("Next step: Replace the 6 product images in assets/products/screen_remote_drone/ and re-run this script for the next SKU.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
