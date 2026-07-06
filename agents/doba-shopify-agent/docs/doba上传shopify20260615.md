# doba上传shopify20260615

## 用途

这份手册记录 Doba 产品真实上传到 Shopify 的常用命令。

当前核心命令用于：

- 扫描 Doba 候选商品
- 真实发布到 Shopify
- 按断点续传继续运行
- 实时输出发布进度与明细

## 核心命令

在 `agents/doba-shopify-agent` 目录下执行：

```powershell
.\.venv\Scripts\python.exe -m src.app.runners.run_doba_shopify_live_publish --report-path docs/audits/doba-shopify-live-publish-report.json --target-country US --page-size 20 --inventory-threshold 10 --list-min-inventory 11
```

## 命令说明

- `--report-path docs/audits/doba-shopify-live-publish-report.json`
  保存断点续传状态、实时结果和失败位置。

- `--target-country US`
  目标销售国家是美国。

- `--page-size 20`
  每次按 20 个候选商品分页扫描。

- `--inventory-threshold 10`
  只有可售库存大于 10 的商品才进入发布流程。

- `--list-min-inventory 11`
  在候选列表层面优先过滤库存小于 11 的商品。

## 当前命令对应的真实发布规则

- 只发布 `Ship From = United States / US` 的商品
- 如果 Doba API 没返回真实发货地，标记为 `UNKNOWN`
- 同一个产品的不同 SKU 要合并到同一个 Shopify Product
- 渠道包含 `Inbox`、`Shop`、`Pinterest`、`Facebook & Instagram`
- 厂商统一写入 `DOBA`
- 加入 `NEW ARRIVALS`
- Shopify 售价按 `Doba sellingPrice * 1.25`

## 续跑说明

这条命令默认支持断点续传。

如果上一次中途失败，再次执行同一条命令，会从 `docs/audits/doba-shopify-live-publish-report.json` 记录的位置继续。

## 建议

后续如果你继续积累常用命令，可以直接沿用这个命名格式：

- `doba上传shopifyYYYYMMDD.md`
