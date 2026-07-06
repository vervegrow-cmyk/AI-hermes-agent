# OpenMontage Integration

This integration keeps OpenMontage installed at:

`D:\桌面文件下载\AI-hermes-agent\external\OpenMontage`

## Setup

Run the setup script from the AI-hermes-agent root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\openmontage_setup.ps1
```

The setup script:

- loads environment variables from the main project `.env`
- checks Python, Node.js, and FFmpeg
- installs OpenMontage Python requirements
- installs `remotion-composer` npm dependencies
- avoids printing secret values

## Create A Video Job

Generate a product video job with:

```powershell
python -m integrations.openmontage.openmontage_adapter
```

You can also provide your own product card JSON:

```powershell
python -m integrations.openmontage.openmontage_adapter --product-card path\to\product_card.json
```

The adapter writes:

- `runtime/openmontage/jobs/{job_id}/brief.md`
- `runtime/openmontage/jobs/{job_id}/product_card.json`

## How Codex Should Execute

1. Open `external/OpenMontage`
2. Read `AGENT_GUIDE.md`
3. Read `PROJECT_CONTEXT.md`
4. Read `CODEX.md`
5. Read the generated `brief.md`
6. Choose the right pipeline
7. Produce a proposal and cost estimate before asset generation
8. Wait for approval before final render
9. Return the final MP4 path

## Environment Variables

- Primary source: `D:\桌面文件下载\AI-hermes-agent\.env`
- Optional additive source: `external/OpenMontage\.env` or `external/OpenMontage\.env.local`
- Secrets are not copied into the OpenMontage repository
- Local OpenMontage env files should only add non-sensitive video-specific settings when needed

## Safety Rules

- Do not auto-publish to any platform
- Do not print secrets
- Require confirmation before any paid API call
- Produce a proposal and cost estimate before video generation
