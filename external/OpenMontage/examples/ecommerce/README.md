# Ecommerce Examples

This folder contains a runnable TikTok ecommerce example for the beginner foldable drone with a built-in screen remote.

## Included Example

- `drone_tiktok_hard_seed.json`
- `drone_tiktok_hard_seed.py`

## What It Generates

The script always writes a usable short-form campaign package to:

`outputs/ecommerce_drone_tiktok_hard_seed/`

Files:

- `storyboard.md`
- `voiceover.txt`
- `subtitles.srt`
- `shot_prompts.json`
- `tiktok_caption.txt`
- `capcut_package/`
- `rough_cut_preview.mp4` when clip assembly succeeds
- `final_video.mp4` when video generation, TTS, and local FFmpeg finishing all succeed

## Required Environment Keys

The example reads keys from the normal OpenMontage environment loading flow.
It will pick up:

- parent shared env: `../../.env` relative to the OpenMontage repo root
- local env: `.env` in the OpenMontage repo root

Recommended keys:

- `FAL_KEY` or `FAL_AI_API_KEY`
  - Preferred for fal-backed video generation routes such as Seedance
- One TTS key if you want generated narration:
  - `ELEVENLABS_API_KEY`
  - `OPENAI_API_KEY`
  - `GOOGLE_API_KEY`
  - `DOUBAO_SPEECH_API_KEY` / `ARK_API_KEY`

Without provider keys, the script still produces the full planning package and CapCut handoff files.

## Product Image Placement

Put product images here:

`assets/ecommerce/drone/`

Expected files:

- `1.jpg`
- `2.jpg`
- `3.jpg`
- `4.jpg`
- `5.jpg`
- `6.jpg`

If one or more images are missing, the script warns and keeps going.

## How To Run

From the OpenMontage repo root:

```powershell
python .\examples\ecommerce\drone_tiktok_hard_seed.py
```

Planning-only mode, no paid generation:

```powershell
python .\examples\ecommerce\drone_tiktok_hard_seed.py --skip-video-gen --skip-tts
```

Keep planning assets but skip only TTS:

```powershell
python .\examples\ecommerce\drone_tiktok_hard_seed.py --skip-tts
```

## How The Example Chooses Providers

- Video: prefers fal-backed generation when `FAL_KEY` is available
- TTS: prefers whichever configured provider is available first
- Assembly: uses local `ffmpeg` if it is on PATH

If generation fails, the example does not hard-stop the workflow. It still leaves you with prompts, subtitles, script text, and a CapCut-ready package.

## CapCut Handoff

Import these files from:

`outputs/ecommerce_drone_tiktok_hard_seed/capcut_package/`

Suggested workflow:

1. Import generated clips or your own recorded clips.
2. Paste `script.txt` into your VO workflow if you want to re-record manually.
3. Import `subtitles.srt`.
4. Use `shot_list.md` as your cut order.
5. Use `prompts.json` to regenerate or improve individual AI shots.
6. Paste `caption.txt` as the final TikTok post caption.
