import {
  ShopifyProductSnapshot,
  SupplierProductSourceData,
  SupplierSourceResolution,
} from "../agents/product-agentic-geo-agent/product-agentic-geo.types.js";
import {
  buildGigaHeaders,
  buildGigaRuntimeConfig,
} from "./upstream-source-test.service.js";
import { fetchWithRetry } from "./fetch-retry.service.js";

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function asString(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

function isNonEmptyRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function findFirstString(value: unknown, keys: string[]): string {
  if (value === null || value === undefined) {
    return "";
  }
  if (Array.isArray(value)) {
    for (const item of value) {
      const found = findFirstString(item, keys);
      if (found) return found;
    }
    return "";
  }
  if (typeof value !== "object") {
    return "";
  }

  const record = value as Record<string, unknown>;
  for (const [key, child] of Object.entries(record)) {
    if (keys.includes(key.toLowerCase())) {
      const stringValue = asString(child);
      if (stringValue) return stringValue;
    }
  }
  for (const child of Object.values(record)) {
    const found = findFirstString(child, keys);
    if (found) return found;
  }
  return "";
}

function findStringArray(value: unknown, keys: string[]): string[] {
  if (value === null || value === undefined || typeof value !== "object") {
    return [];
  }
  const record = value as Record<string, unknown>;
  for (const [key, child] of Object.entries(record)) {
    if (keys.includes(key.toLowerCase()) && Array.isArray(child)) {
      return child.map((item) => asString(item)).filter(Boolean);
    }
  }
  for (const child of Object.values(record)) {
    const found = findStringArray(child, keys);
    if (found.length > 0) return found;
  }
  return [];
}

function findFirstValue(value: unknown, keys: string[]): unknown {
  if (value === null || value === undefined) return undefined;
  if (Array.isArray(value)) {
    for (const item of value) {
      const found = findFirstValue(item, keys);
      if (found !== undefined && found !== null && found !== "") return found;
    }
    return undefined;
  }
  if (typeof value !== "object") return undefined;

  const record = value as Record<string, unknown>;
  for (const [key, child] of Object.entries(record)) {
    if (keys.includes(key.toLowerCase())) {
      if (child !== undefined && child !== null && child !== "") return child;
    }
  }
  for (const child of Object.values(record)) {
    const found = findFirstValue(child, keys);
    if (found !== undefined && found !== null && found !== "") return found;
  }
  return undefined;
}

function normalizeRecordFromUnknown(value: unknown): Record<string, unknown> {
  if (isNonEmptyRecord(value)) {
    return value;
  }
  if (typeof value === "string" && value.trim()) {
    return { value: value.trim() };
  }
  return {};
}

function findSpecValue(value: unknown, labels: string[]): string {
  const normalizedLabels = labels.map((item) => item.toLowerCase());
  if (Array.isArray(value)) {
    for (const item of value) {
      const found = findSpecValue(item, labels);
      if (found) return found;
    }
    return "";
  }
  if (!isNonEmptyRecord(value)) {
    return "";
  }

  const record = value as Record<string, unknown>;
  const name = asString(record.name ?? record.label ?? record.key).toLowerCase();
  const valueText = asString(record.value ?? record.content ?? record.description);
  if (name && valueText && normalizedLabels.some((label) => name.includes(label))) {
    return valueText;
  }

  for (const [key, child] of Object.entries(record)) {
    if (normalizedLabels.some((label) => key.toLowerCase().includes(label))) {
      const direct = asString(child);
      if (direct) return direct;
    }
  }

  for (const child of Object.values(record)) {
    const found = findSpecValue(child, labels);
    if (found) return found;
  }

  return "";
}

export class GigaProductSourceService {
  async fetchProductSource(
    product: ShopifyProductSnapshot,
    resolution: SupplierSourceResolution,
  ): Promise<SupplierProductSourceData | null> {
    const runtime = buildGigaRuntimeConfig();
    const sku = resolution.supplierSku || product.variants.find((item) => item.sku)?.sku || "";
    if (!runtime.baseUrl || !runtime.clientId || !runtime.clientSecret || !sku) {
      return null;
    }

    const endpoint =
      process.env.GIGA_SOURCE_DETAIL_ENDPOINT ??
      "/b2b-overseas-api/v1/buyer/inventory/quantity/v2";
    const url = new URL(endpoint, runtime.baseUrl.endsWith("/") ? runtime.baseUrl : `${runtime.baseUrl}/`);
    const response = await fetchWithRetry(url, {
      method: "POST",
      headers: buildGigaHeaders(endpoint, runtime.clientId, runtime.clientSecret),
      body: JSON.stringify({ skus: [sku] }),
    }, { attempts: 3, baseDelayMs: 1000 });

    const text = await response.text();
    const payload = text ? (JSON.parse(text) as unknown) : {};
    const root = asRecord(payload);
    const specifications =
      normalizeRecordFromUnknown(findFirstValue(root, ["specifications", "specs", "attributes"])) || {};
    const dimensionsValue = findFirstValue(root, ["dimensions", "dimension", "sizeinfo"]);
    const packageDimensionsValue = findFirstValue(root, ["packagedimensions", "package_dimensions"]);

    return {
      sourceType: "GIGA",
      supplierProductId: resolution.supplierProductId,
      supplierSku: sku,
      title: findFirstString(root, ["title", "productname", "name"]),
      description: findFirstString(root, ["description", "summary", "feature"]),
      brand: findFirstString(root, ["brand", "vendor", "manufacturer"]),
      vendor: findFirstString(root, ["vendor", "brand", "manufacturer"]),
      productType:
        findFirstString(root, ["producttype", "type", "categoryname", "leafcategoryname"]) ||
        findSpecValue(specifications, ["product type", "type", "category"]),
      rawCategory:
        findFirstString(root, ["category", "categoryname", "catname", "categorypath"]) ||
        findSpecValue(specifications, ["category", "supplier category"]),
      googleProductCategory:
        findFirstString(root, ["googleproductcategory", "google_category", "googlecategory"]) ||
        findSpecValue(specifications, ["google product category"]),
      material:
        findFirstString(root, ["material"]) || findSpecValue(specifications, ["material", "fabric"]),
      color: findFirstString(root, ["color"]) || findSpecValue(specifications, ["color", "finish"]),
      size: findFirstString(root, ["size"]) || findSpecValue(specifications, ["size"]),
      dimensions: normalizeRecordFromUnknown(dimensionsValue),
      weight:
        findFirstString(root, ["weight", "grossweight", "netweight"]) ||
        findSpecValue(specifications, ["weight"]),
      packageDimensions: normalizeRecordFromUnknown(packageDimensionsValue),
      packageWeight:
        findFirstString(root, ["packageweight", "shippingweight"]) ||
        findSpecValue(specifications, ["package weight", "shipping weight"]),
      warehouse:
        findFirstString(root, ["warehouse", "warehousecode", "warehouse_name", "stocklocation"]),
      shippingOrigin:
        findFirstString(root, ["shippingorigin", "origin", "warehousecity", "inventorylocation"]),
      shippingTime: findFirstString(root, ["shippingtime", "deliverytime"]),
      returnPolicy: findFirstString(root, ["returnpolicy"]),
      warranty: findFirstString(root, ["warranty"]),
      mpn: findFirstString(root, ["mpn", "model"]) || findSpecValue(specifications, ["mpn", "model"]),
      gtin:
        findFirstString(root, ["gtin", "upc", "ean", "isbn"]) ||
        findSpecValue(specifications, ["gtin", "upc", "ean"]),
      barcode:
        findFirstString(root, ["barcode", "upc", "ean"]) ||
        findSpecValue(specifications, ["barcode", "upc", "ean"]),
      packingList: findStringArray(root, ["packinglist", "packageincludes"]),
      compatibility: findStringArray(root, ["compatibility", "compatiblewith"]),
      specifications,
      usageScenarios: findStringArray(root, ["usagescenarios", "usecases"]),
      images: findStringArray(root, ["images", "imageurls", "gallery"]),
      rawPayload: root,
    };
  }
}
