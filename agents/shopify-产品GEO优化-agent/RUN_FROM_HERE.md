# 从当前目录运行

现在这个目录已经包含本地维护用的 `ProductAgenticGEOAgent` TypeScript 核心代码：

- `packages/agents/product-agentic-geo-agent`
- `packages/services`
- `packages/skills/product-agentic-geo`
- `packages/repositories`

环境变量加载顺序：

1. 上层兼容环境变量：`D:\桌面文件下载\AI-hermes-agent\.env`
2. 当前目录环境变量：`D:\桌面文件下载\AI-hermes-agent\agents\shopify-产品GEO优化-agent\.env`
3. 当前目录覆盖环境变量：`D:\桌面文件下载\AI-hermes-agent\agents\shopify-产品GEO优化-agent\.env.local`

推荐后续把这个目录自己的变量维护到本地 `.env`，逐步摆脱对上层 `.env` 的依赖。

在当前目录执行：

```powershell
cd D:\桌面文件下载\AI-hermes-agent\agents\shopify-产品GEO优化-agent
npm install
npm run typecheck
npm run product-geo:run -- --limit=1 --dry-run=true
npm run product-geo:run -- --limit=1 --dry-run=false
npm run product-geo:run -- --limit=50 --dry-run=false
```

说明：

- 当前目录 `package.json` 直接运行本地 `./packages/...` 代码
- 当前目录 `tsconfig.json` 只编译本地 `packages/**/*.ts`
- 当前目录本地安装 `tsx`、`typescript`、`dotenv`
- 以后维护 `ProductAgenticGEOAgent` 时，只修改当前目录下的本地 `packages/`
