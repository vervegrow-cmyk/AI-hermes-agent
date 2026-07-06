# Doba Shopify Agent Common Commands Manual 20260614

## Purpose

This manual records the high-value operational commands for
`agents/doba-shopify-agent`.

The primary command in this version is the full real-publish command for
Shopify products where `vendor == Doba`.

## Command Name

Recommended alias name:

- `cmd:doba-force-publish-deepseek-live-20260614`

Recommended human-readable name:

- `Doba 全量 DeepSeek 优化补齐并真实发布命令 20260614`

Recommended file suffix convention:

- `20260614`

Use the same suffix on:

- command manual file names
- report file names
- live log file names
- operation screenshots or audit notes created on the same version baseline

## Core Command

Run from `agents/doba-shopify-agent`:

```powershell
cd "D:\桌面文件下载\AI-hermes-agent\agents\doba-shopify-agent"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONPATH="D:\桌面文件下载\AI-hermes-agent"
Remove-Item Env:HTTP_PROXY -ErrorAction SilentlyContinue
Remove-Item Env:HTTPS_PROXY -ErrorAction SilentlyContinue
Remove-Item Env:ALL_PROXY -ErrorAction SilentlyContinue
Remove-Item Env:http_proxy -ErrorAction SilentlyContinue
Remove-Item Env:https_proxy -ErrorAction SilentlyContinue
Remove-Item Env:all_proxy -ErrorAction SilentlyContinue
$env:PYTHONDONTWRITEBYTECODE="1"

.\.venv\Scripts\python.exe -m src.app.runners.run_publish_vendor_catalog `
  --vendor Doba `
  --channels "Online Store" "Shop" "Pinterest" "Facebook & Instagram" `
  --report-path "docs/audits/doba-force-publish-report-round26-20260614.json" `
  --stop-on-failure 2>&1 | Tee-Object -FilePath "docs/audits/doba-force-publish-round26-live-20260614.log"
```

## Current Stable Doba -> Shopify Main Pipeline

This is the current real main pipeline command for:

- real Doba API online archiving
- US-focused ship-from filtering
- archive-first candidate pool generation
- stream publish behavior
- immediate candidate refresh after an eligible SPU is archived
- immediate real Shopify publish after candidate qualification
- mapping/checkpoint/report persistence

Important:

- use `DOBA_TRUST_ENV=false`
- this avoids the broken environment-trust path that caused Doba whitelist failures

Run from `agents/doba-shopify-agent`:

```powershell
chcp 65001; [Console]::InputEncoding=[System.Text.UTF8Encoding]::new($false); [Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false); $OutputEncoding=[System.Text.UTF8Encoding]::new($false); $env:PYTHONIOENCODING='utf-8'; $env:PYTHONUTF8='1'; $env:DOBA_TRUST_ENV='false'; .\.venv\Scripts\python.exe -X utf8 -m src.app.runners.run_doba_pipeline --mode archive-and-publish --archive-report-path "docs/audits/doba-online-archive-us-focus-report.json" --archive-checkpoint-path "data/runtime/supplier_archive/doba_online_archive_us_focus_checkpoint.json" --publish-report-path "docs/audits/doba-shopify-live-publish-candidate-only-report.json" --candidate-pool-path "data/runtime/shopify_listing/doba_publish_candidates.json" --target-country US --inventory-threshold 10 --list-min-inventory 11 --eligible-inventory-threshold 10 --page-size 20 --channels Inbox Shop Pinterest "Facebook & Instagram" --incremental --archive-eligible-only --stream-publish
```

### Small Validation Variant

Use this first when you want to verify the pipeline on a tiny batch before a long run:

```powershell
chcp 65001; [Console]::InputEncoding=[System.Text.UTF8Encoding]::new($false); [Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false); $OutputEncoding=[System.Text.UTF8Encoding]::new($false); $env:PYTHONIOENCODING='utf-8'; $env:PYTHONUTF8='1'; $env:DOBA_TRUST_ENV='false'; .\.venv\Scripts\python.exe -X utf8 -m src.app.runners.run_doba_pipeline --mode archive-and-publish --archive-report-path "docs/audits/doba-online-archive-us-focus-report.json" --archive-checkpoint-path "data/runtime/supplier_archive/doba_online_archive_us_focus_checkpoint.json" --publish-report-path "docs/audits/doba-shopify-live-publish-candidate-only-report.json" --candidate-pool-path "data/runtime/shopify_listing/doba_publish_candidates.json" --target-country US --inventory-threshold 10 --list-min-inventory 11 --eligible-inventory-threshold 10 --page-size 20 --channels Inbox Shop Pinterest "Facebook & Instagram" --incremental --archive-eligible-only --stream-publish --max-pages 2 --max-successes 1
```

## What This Command Does

This command performs a real end-to-end run for all Shopify products where
`vendor == Doba`.

Main capabilities:

- loads all Shopify publications needed for the target channels
- scans the full Shopify catalog for products matching `vendor:Doba`
- processes products one by one instead of bulk blind writes
- calls DeepSeek for every product using title, tags, and description context
- attempts to optimize and fill Shopify category
- attempts to optimize and fill `productType`
- attempts to optimize and fill Hermes metafields related to category decisions
- writes LLM suggestion metadata such as status, confidence, reason, and payload
- applies real publication to:
  - `Online Store`
  - `Shop`
  - `Pinterest`
  - `Facebook & Instagram`
- adds each processed product to the `NEW ARRIVALS` collection
- writes a structured JSON report
- writes a live console log file
- stops immediately if `--stop-on-failure` hits a hard failure

## Real-Time Output You Will See

Typical progress output includes:

- `loading publications for vendor=Doba`
- `deepseek_status=enabled:model=deepseek-chat`
- `fetching product page N for query=vendor:Doba`
- `X/821 optimizing gid://shopify/Product/...`
- `detail category=... -> ...`
- `detail llm=parsed pt=... label=... conf=...`
- `detail collection=yes | published=... | missing=-`
- `done action=category_applied collection=yes publish_error=no source_error=no`

## Output Files

JSON report:

- `docs/audits/doba-force-publish-report-round26-20260614.json`

Live log:

- `docs/audits/doba-force-publish-round26-live-20260614.log`

## Parameter Notes

- `--vendor Doba`
  Filters the run to Shopify products whose vendor field equals `Doba`.

- `--channels "Online Store" "Shop" "Pinterest" "Facebook & Instagram"`
  Forces publication to the four required channels.

- `--report-path "...json"`
  Saves the structured run result for later audit and analysis.

- `--stop-on-failure`
  Stops the full run when a hard failure occurs so the operator can inspect the
  reason before continuing.

## Safety and Behavior Notes

- This is a real publish command, not a dry run.
- It can modify Shopify category, `productType`, tags, Hermes metafields, and
  channel publication state.
- It is designed to prefer safe review downgrade over writing obviously wrong
  taxonomy when confidence is too low.
- Even when Shopify category is not safely writable, the command can still fill
  `productType`, tags, and Hermes metafields.
- Proxy environment variables are cleared before execution to reduce DeepSeek
  connection issues.

## Recommended Naming Rule For Future Runs

Use this pattern:

- report: `doba-force-publish-report-roundNN-20260614.json`
- live log: `doba-force-publish-roundNN-live-20260614.log`

Example:

- `doba-force-publish-report-round27-20260614.json`
- `doba-force-publish-round27-live-20260614.log`

## Common Follow-Up Checks

Check the latest log tail:

```powershell
Get-Content "D:\桌面文件下载\AI-hermes-agent\agents\doba-shopify-agent\docs\audits\doba-force-publish-round26-live-20260614.log" -Tail 80
```

Filter review, no-match, and error items:

```powershell
Select-String -Path "D:\桌面文件下载\AI-hermes-agent\agents\doba-shopify-agent\docs\audits\doba-force-publish-round26-live-20260614.log" -Pattern "publish_error=yes|source_error=yes|category_suggested_review|llm_suggested_review|no_match" -Context 0,3
```

Filter high-risk sample products:

```powershell
Select-String -Path "D:\桌面文件下载\AI-hermes-agent\agents\doba-shopify-agent\docs\audits\doba-force-publish-round26-live-20260614.log" -Pattern "Party Tent|Pergola|Garden Dining|Refrigerant Recovery Tank|Zero Gravity|Grass Trimmer|Hand Sanitizer|Duffel|Dog Bathtub|Teapot" -Context 0,4
```

## Operator Guidance

Use this command when the goal is:

- full Doba catalog optimization
- DeepSeek-assisted category enrichment
- real channel publication
- live operational visibility
- immediate stop on hard failure

Do not use this command when the goal is:

- a dry run only
- taxonomy rule development without touching Shopify
- low-risk sample validation on only one or two products
