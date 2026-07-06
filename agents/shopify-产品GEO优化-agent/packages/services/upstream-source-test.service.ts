import { createSign, createHmac } from "node:crypto";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

export interface GeoSignalSummary {
  matchedPaths: string[];
  missingSignals: string[];
}

export interface SourceTestReport {
  source: "giga" | "doba";
  endpoint: string;
  method: string;
  ok: boolean;
  status: number;
  request: Record<string, unknown>;
  responsePreview: unknown;
  geoSignalSummary: GeoSignalSummary;
  outputPath: string;
}

function unique<T>(values: T[]): T[] {
  return [...new Set(values)];
}

function normalizePem(value: string): string {
  const normalized = value.replace(/\\n/g, "\n").trim();
  if (!normalized) {
    return normalized;
  }
  if (normalized.includes("BEGIN PRIVATE KEY")) {
    return normalized;
  }
  const chunks = normalized.match(/.{1,64}/g) ?? [normalized];
  return `-----BEGIN PRIVATE KEY-----\n${chunks.join("\n")}\n-----END PRIVATE KEY-----`;
}

function pickFirst(...values: Array<string | undefined>): string {
  for (const value of values) {
    if ((value ?? "").trim()) {
      return value!.trim();
    }
  }
  return "";
}

function toJsonPreview(payload: unknown): unknown {
  if (payload === null || payload === undefined) {
    return payload;
  }
  if (typeof payload !== "object") {
    return payload;
  }
  if (Array.isArray(payload)) {
    return payload.slice(0, 3);
  }

  const entries = Object.entries(payload as Record<string, unknown>).slice(0, 20);
  return Object.fromEntries(entries);
}

function collectPaths(value: unknown, prefix = "", acc: string[] = []): string[] {
  if (value === null || value === undefined) {
    return acc;
  }

  if (Array.isArray(value)) {
    value.slice(0, 5).forEach((item, index) => {
      collectPaths(item, prefix ? `${prefix}[${index}]` : `[${index}]`, acc);
    });
    return acc;
  }

  if (typeof value === "object") {
    for (const [key, child] of Object.entries(value as Record<string, unknown>)) {
      const nextPrefix = prefix ? `${prefix}.${key}` : key;
      acc.push(nextPrefix);
      collectPaths(child, nextPrefix, acc);
    }
  }

  return acc;
}

function summarizeGeoSignals(payload: unknown): GeoSignalSummary {
  const keyPaths = collectPaths(payload).map((item) => item.toLowerCase());
  const signalMatchers: Record<string, string[]> = {
    title: ["title", "productname", "name"],
    description: ["description", "desc", "summary", "feature"],
    category: ["category", "producttype", "taxonomy"],
    brand: ["brand", "vendor", "manufacturer"],
    identifiers: ["sku", "itemno", "spuno", "gtin", "barcode", "mpn"],
    media: ["image", "picture", "photo", "gallery", "video"],
    specs: ["spec", "material", "size", "dimension", "weight", "color"],
    logistics: ["shipping", "return", "warehouse", "delivery"],
    inventory: ["inventory", "stock", "availability", "quantity"],
    pricing: ["price", "cost", "msrp", "sale"],
  };

  const matchedPaths: string[] = [];
  const missingSignals: string[] = [];

  for (const [signal, patterns] of Object.entries(signalMatchers)) {
    const found = keyPaths.filter((path) => patterns.some((pattern) => path.includes(pattern)));
    if (found.length > 0) {
      matchedPaths.push(`${signal}: ${unique(found).slice(0, 5).join(", ")}`);
    } else {
      missingSignals.push(signal);
    }
  }

  return {
    matchedPaths,
    missingSignals,
  };
}

async function persistReport(report: Omit<SourceTestReport, "outputPath">): Promise<string> {
  const outputDir = path.resolve(process.cwd(), "runtime-data", "source-tests");
  await mkdir(outputDir, { recursive: true });
  const safeEndpoint = report.endpoint.replace(/[^\w.-]+/g, "_").slice(0, 80);
  const fileName = `${report.source}-${Date.now()}-${safeEndpoint || "root"}.json`;
  const outputPath = path.join(outputDir, fileName);
  await writeFile(outputPath, JSON.stringify(report, null, 2), "utf8");
  return outputPath;
}

export function buildGigaRuntimeConfig(): {
  baseUrl: string;
  clientId: string;
  clientSecret: string;
} {
  return {
    baseUrl: pickFirst(
      process.env.GIGA_API_BASE_URL,
      process.env.GIGA_PRODUCTION_BASE_URL,
      process.env.GIGA_SANDBOX_BASE_URL,
    ),
    clientId: pickFirst(
      process.env.GIGA_API_KEY,
      process.env.GIGA_PRODUCTION_CLIENT_ID,
      process.env.GIGA_SANDBOX_CLIENT_ID,
    ),
    clientSecret: pickFirst(
      process.env.GIGA_API_SECRET,
      process.env.GIGA_PRODUCTION_APP_SECRET,
      process.env.GIGA_SANDBOX_APP_SECRET,
      process.env.GIGA_SANDBOX_CLIENT_SECRET,
    ),
  };
}

export function buildGigaHeaders(endpoint: string, clientId: string, clientSecret: string): Record<string, string> {
  const nonce = Math.random().toString(36).slice(2, 12);
  const timestamp = String(Date.now());
  const message = `${clientId}&${endpoint}&${timestamp}&${nonce}`;
  const secretKey = `${clientId}&${clientSecret}&${nonce}`;
  const digest = createHmac("sha256", secretKey).update(message).digest("hex");
  const sign = Buffer.from(digest, "utf8").toString("base64");

  return {
    Accept: "application/json",
    "Content-Type": "application/json",
    "client-id": clientId,
    timestamp,
    nonce,
    sign,
  };
}

export async function runGigaSourceTest(input: {
  endpoint: string;
  method: string;
  body?: unknown;
}): Promise<SourceTestReport> {
  const runtime = buildGigaRuntimeConfig();
  if (!runtime.baseUrl || !runtime.clientId || !runtime.clientSecret) {
    throw new Error("缺少 GIGA 运行配置，请检查 GIGA_API_BASE_URL / GIGA_API_KEY / GIGA_API_SECRET。");
  }

  const url = new URL(input.endpoint, runtime.baseUrl.endsWith("/") ? runtime.baseUrl : `${runtime.baseUrl}/`);
  const headers = buildGigaHeaders(input.endpoint, runtime.clientId, runtime.clientSecret);
  const response = await fetch(url, {
    method: input.method,
    headers,
    body: input.body === undefined ? undefined : JSON.stringify(input.body),
  });

  const text = await response.text();
  let payload: unknown = text;
  try {
    payload = text ? JSON.parse(text) : null;
  } catch {
    payload = text;
  }

  const reportWithoutPath = {
    source: "giga" as const,
    endpoint: input.endpoint,
    method: input.method,
    ok: response.ok,
    status: response.status,
    request: {
      url: url.toString(),
      body: input.body ?? null,
      headerNames: Object.keys(headers),
    },
    responsePreview: toJsonPreview(payload),
    geoSignalSummary: summarizeGeoSignals(payload),
  };
  const outputPath = await persistReport(reportWithoutPath);

  return {
    ...reportWithoutPath,
    outputPath,
  };
}

export function buildDobaRuntimeConfig(): {
  baseUrl: string;
  appKey: string;
  signType: string;
  privateKey: string;
  retailerId: string;
} {
  return {
    baseUrl: pickFirst(process.env.DOBA_API_BASE_URL),
    appKey: pickFirst(process.env.DOBA_APP_KEY),
    signType: pickFirst(process.env.DOBA_SIGN_TYPE, "RSA2"),
    privateKey: normalizePem(pickFirst(process.env.DOBA_PRIVATE_KEY)),
    retailerId: pickFirst(process.env.DOBA_RETAILER_ID),
  };
}

function buildDobaCanonical(params: Record<string, string>): string {
  return Object.entries(params)
    .filter(([, value]) => value !== "")
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([key, value]) => `${key}=${value}`)
    .join("&");
}

export function buildDobaSignedParams(
  extraParams: Record<string, string>,
  runtime = buildDobaRuntimeConfig(),
): Record<string, string> {
  if (!runtime.appKey || !runtime.privateKey) {
    throw new Error("缺少 DOBA 签名配置，请检查 DOBA_APP_KEY / DOBA_PRIVATE_KEY。");
  }

  const authParams: Record<string, string> = {
    appKey: runtime.appKey,
    signType: runtime.signType || "RSA2",
    timestamp: String(Date.now()),
    ...extraParams,
  };

  const signer = createSign("RSA-SHA256");
  signer.update(buildDobaCanonical(authParams), "utf8");
  signer.end();
  const sign = signer.sign(runtime.privateKey, "base64");

  return {
    ...authParams,
    sign,
  };
}

export async function runDobaSourceTest(input: {
  endpoint: string;
  method: string;
  query?: Record<string, string>;
}): Promise<SourceTestReport> {
  const runtime = buildDobaRuntimeConfig();
  if (!runtime.baseUrl || !runtime.appKey || !runtime.privateKey) {
    throw new Error("缺少 DOBA 运行配置，请检查 DOBA_API_BASE_URL / DOBA_APP_KEY / DOBA_PRIVATE_KEY。");
  }

  const businessQuery = { ...(input.query ?? {}) };
  const signedParams = buildDobaSignedParams(businessQuery, runtime);
  const url = new URL(input.endpoint, runtime.baseUrl.endsWith("/") ? runtime.baseUrl : `${runtime.baseUrl}/`);
  for (const [key, value] of Object.entries(businessQuery)) {
    if (value !== "") {
      url.searchParams.set(key, value);
    }
  }

  const headers: Record<string, string> = {
    Accept: "application/json",
    "Content-Type": "application/json",
    appKey: runtime.appKey,
    signType: runtime.signType || "RSA2",
    timestamp: signedParams.timestamp,
    sign: signedParams.sign,
  };

  if (runtime.retailerId) {
    headers.retailerId = runtime.retailerId;
  }

  const response = await fetch(url, {
    method: input.method,
    headers,
  });

  const text = await response.text();
  let payload: unknown = text;
  try {
    payload = text ? JSON.parse(text) : null;
  } catch {
    payload = text;
  }

  const reportWithoutPath = {
    source: "doba" as const,
    endpoint: input.endpoint,
    method: input.method,
    ok: response.ok,
    status: response.status,
    request: {
      url: url.toString(),
      query: businessQuery,
      signPayload: Object.fromEntries(
        Object.entries(signedParams).filter(([key]) => key !== "sign"),
      ),
      headerNames: Object.keys(headers),
    },
    responsePreview: toJsonPreview(payload),
    geoSignalSummary: summarizeGeoSignals(payload),
  };
  const outputPath = await persistReport(reportWithoutPath);

  return {
    ...reportWithoutPath,
    outputPath,
  };
}
