# Provider Adapter Matrix

This file tracks which parent-project environment variables are already usable by
OpenMontage and which still need first-party tool adapters.

## Implemented in this repo

| Env var | Provider | Current tool | Notes |
|---|---|---|---|
| `ARK_API_KEY` | Volcengine Ark | `tools/video/ark_video.py` | Direct Ark task API adapter, `ARK_BASE_URL` override supported |
| `SILICONFLOW_API_KEY` | SiliconFlow | `tools/video/siliconflow_video.py` | Direct text-to-video via SiliconFlow Wan models |
| `PIXVERSE_API_KEY` | PixVerse | `tools/video/pixverse_video.py` | Direct text-to-video and image-to-video |
| `VIDU_API_KEY` | Vidu | `tools/video/vidu_video.py` | Direct text-to-video and image-to-video |

## Shared in env but not yet implemented here

| Env var(s) | Provider | Status | Why not wired yet |
|---|---|---|---|
| `RUNNINGHUB_API_KEY` | RunningHub | Feasible next | Workflow-oriented gateway, not a single fixed video endpoint |
| `LIBLIB_ACCESS_KEY`, `LIBLIB_SECRET_KEY` | Liblib | Feasible with care | Public references found, but official API surface is less transparent |
| `KLING_API_KEY` | Kling direct | Needs credential clarification | Current repo Kling path uses fal.ai; official Kling docs use AccessKey/SecretKey -> token flow instead of a simple single API key |

## Existing routed alternatives already in repo

| Provider outcome wanted | Existing tool |
|---|---|
| Kling via fal.ai | `kling_video` |
| Seedance via fal.ai | `seedance_video` |
| Veo via fal.ai | `veo_video` |
| Multi-gateway auto routing | `video_selector` |
