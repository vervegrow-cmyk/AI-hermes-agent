const MOJIBAKE_HINT = /[銆锛浠鍐鍚鍒鍟缁闃璇诲彇鏈€搴忓瓧娈靛洖婧愬晢鍝佹€?]/;
const NORMAL_CHINESE_HINT = /[【】优化商品字段来源结果说明阶段执行真实默认业务写回发布评分成功失败]/;

function countMatches(value: string, pattern: RegExp): number {
  const matches = value.match(new RegExp(pattern.source, "g"));
  return matches?.length ?? 0;
}

function tryRepairUtf8Mojibake(value: string): string {
  if (!value || !MOJIBAKE_HINT.test(value)) {
    return value;
  }

  try {
    const repaired = Buffer.from(value, "latin1").toString("utf8");
    if (!repaired || repaired.includes("\uFFFD")) {
      return value;
    }

    const originalWeird = countMatches(value, MOJIBAKE_HINT);
    const repairedWeird = countMatches(repaired, MOJIBAKE_HINT);
    const originalNormal = countMatches(value, NORMAL_CHINESE_HINT);
    const repairedNormal = countMatches(repaired, NORMAL_CHINESE_HINT);

    if (repairedWeird < originalWeird || repairedNormal > originalNormal) {
      return repaired;
    }
  } catch {
    return value;
  }

  return value;
}

function normalizeConsoleArg(value: unknown): unknown {
  if (typeof value === "string") {
    return tryRepairUtf8Mojibake(value);
  }

  if (Array.isArray(value)) {
    return value.map(normalizeConsoleArg);
  }

  if (value && typeof value === "object") {
    try {
      return JSON.parse(
        JSON.stringify(value, (_key, nested) =>
          typeof nested === "string" ? tryRepairUtf8Mojibake(nested) : nested,
        ),
      );
    } catch {
      return value;
    }
  }

  return value;
}

function patchConsoleMethod<
  T extends (...args: unknown[]) => void,
>(target: Console, method: "log" | "info" | "warn" | "error"): void {
  const original = target[method].bind(target) as T;
  target[method] = ((...args: unknown[]) => {
    original(...args.map(normalizeConsoleArg));
  }) as Console[typeof method];
}

export function configureConsoleEncoding(): void {
  process.env.LANG = process.env.LANG || "en_US.UTF-8";
  process.env.LC_ALL = process.env.LC_ALL || "en_US.UTF-8";
  process.env.PYTHONIOENCODING = process.env.PYTHONIOENCODING || "utf-8";

  process.stdout?.setDefaultEncoding?.("utf8");
  process.stderr?.setDefaultEncoding?.("utf8");

  patchConsoleMethod(console, "log");
  patchConsoleMethod(console, "info");
  patchConsoleMethod(console, "warn");
  patchConsoleMethod(console, "error");
}
