# API Key Inventory

Last updated: 2026-07-02

This file tracks provider type, balance status, and the latest manual check time.
Do not store real secret values here. Keep real secrets only in `REPO_ROOT/.env`.

Status meanings:

- `free`: free tier or developer quota expected
- `paid-active`: paid account or usage-based account with usable balance/quota
- `paid-empty`: paid account present but balance/quota appears empty
- `unknown`: key exists, but billing/quota status was not confirmed

## Current Inventory

| Provider | Env Var | Capability | Type | Status | Last Checked | Basis |
|---|---|---|---|---|---|---|
| Google AI Studio | `GOOGLE_API_KEY` | Gemini / Google API tools | free | free | 2026-07-02 | User provided Google AI Studio API key; treated as free-tier capable by default |
| Google AI Studio | `GEMINI_API_KEY` | Gemini-compatible fallback alias | free | free | 2026-07-02 | Same key as `GOOGLE_API_KEY`, stored for compatibility |
| fal.ai | `FAL_KEY` | Veo / Kling / MiniMax / FLUX / Recraft / Seedance gateway | paid | unknown | 2026-07-02 | Present in `.env`, but no balance screenshot or quota proof checked today |
| Kling AI | `KLING_API_KEY` | Kling direct platform key | paid | unknown | 2026-07-02 | User provided direct Kling key; enabled status visible, but no balance confirmed |
| Volcengine Ark | `ARK_API_KEY` | Ark platform API access | paid | unknown | 2026-07-02 | User provided Ark key; no quota/balance evidence checked |
| Doubao Speech | `DOUBAO_SPEECH_API_KEY` | Doubao TTS | paid | unknown | 2026-07-02 | Variable reserved, currently not populated in `.env` |
| LibLib AI | `LIBLIB_ACCESS_KEY` | LibLib API access | paid | paid-empty | 2026-07-02 | Screenshot showed remaining points `0` |
| LibLib AI | `LIBLIB_SECRET_KEY` | LibLib API secret | paid | paid-empty | 2026-07-02 | Same account as above; screenshot showed remaining points `0` |
| RunningHub | `RUNNINGHUB_API_KEY` | RunningHub consumer API | paid | paid-active | 2026-07-02 | Screenshot showed account with `R 100`, treated as available balance |
| PixVerse | `PIXVERSE_API_KEY` | PixVerse platform API | paid | unknown | 2026-07-02 | Key creation confirmed, but no balance/quota shown |
| Vidu | `VIDU_API_KEY` | Vidu API | paid | paid-active | 2026-07-02 | Screenshot showed API key status `Active` |
| SiliconFlow | `SILICONFLOW_API_KEY` | SiliconFlow platform API | paid | unknown | 2026-07-02 | Key exists, but no balance/quota confirmation checked |
| Pexels | `PEXELS_API_KEY` | Stock image/video search | free | free | 2026-07-02 | Free API key model |
| Pixabay | `PIXABAY_API_KEY` | Stock image/video search | free | free | 2026-07-02 | Free API key model |

## Notes

- `Status` is an operational label for routing decisions, not a billing truth source.
- Some statuses above are inferred from screenshots you provided on 2026-07-02 and were not re-verified via provider API.
- If a key is exposed in chat, screenshots, or logs, rotate it in the provider console and update `.env`.

## Suggested Routing Policy

### Prefer first

- Free providers with working quotas
- Low-cost paid providers confirmed active

### Use with review

- Paid providers with `unknown` balance status

### Disable by default

- Providers marked `paid-empty`

## Recommended Next Step

Before production use, add one more short column per provider during manual review:

- `Owner`
- `Monthly budget`
- `Primary use`
- `Rotation due`
