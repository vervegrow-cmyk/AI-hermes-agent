# Local browser-harness Working Directory

This directory is the shared working root for the local `browser-harness` integration inside `AI-hermes-agent`.

- Runtime wrapper: `..\..\scripts\browser-harness.ps1`
- Hermes client: `..\..\shared\clients\browser_harness.py`
- MCP server: `..\..\tools\mcp\browser_harness_mcp_server.py`
- Detailed docs: `..\..\docs\BROWSER_HARNESS_LOCAL.md`

The executable itself is managed by `uv tool` and currently resolves to:

```text
C:\Users\Administrator\.local\bin\browser-harness.exe
```

This folder stays intentionally lightweight so all Browser Harness calls share the parent `AI-hermes-agent` environment and `.env`.
