# LibTV Integration

This repo treats LibTV as a `video_generation` provider, not as a separate
workflow system.

## Files

- `tools/_libtv/client.py`
- `tools/video/libtv_video.py`
- `scripts/test_libtv_video.py`

## Required environment variables

Add these to the shared `.env` used by OpenMontage:

```env
LIBTV_ACCESS_KEY=your-key
OPENAPI_IM_BASE=https://...
IM_BASE_URL=https://...
LIBTV_SKILLS_DIR=external/libtv-skills/skills/libtv-skill
```

`LIBTV_SKILLS_DIR` defaults to:

```text
external/libtv-skills/skills/libtv-skill
```

## Required checkout

Clone the external skills repo to:

```text
external/libtv-skills/
```

The integration expects these scripts inside `LIBTV_SKILLS_DIR`:

- `upload_file.py`
- `create_session.py`
- `query_session.py`
- `download_results.py`

## Provider behavior

`libtv_video` accepts:

- `prompt`
- `duration`
- `aspect_ratio`
- `product_images`
- `output_dir`
- `style_notes`

It shells out to the external LibTV scripts in this order:

1. `upload_file.py` for each local product image
2. `create_session.py`
3. `query_session.py` until complete
4. `download_results.py`

## Test command

```powershell
python scripts/test_libtv_video.py --prompt "Create a 10-second vertical TikTok UGC product video for a solar fan hat in a hot soccer stadium."
```

## Failure modes

- Missing `LIBTV_ACCESS_KEY`
  - `libtv_video` returns a clear error and does not silently fallback
- Missing `external/libtv-skills`
  - error tells you to clone the repo first
- Missing helper scripts
  - error lists the missing script paths
- External script failure
  - stderr or JSON error payload is surfaced in the tool result
