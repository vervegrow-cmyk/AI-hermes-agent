import {
  ShopifyProductSnapshot,
  SupplierProductSourceData,
  SupplierSourceResolution,
} from "../agents/product-agentic-geo-agent/product-agentic-geo.types.js";
import {
  buildDobaRuntimeConfig,
  buildDobaSignedParams,
} from "./upstream-source-test.service.js";
import { fetchWithRetry } from "./fetch-retry.service.js";

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
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
      return child
        .map((item) => (typeof item === "string" ? item.trim() : ""))
        .filter(Boolean);
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

export class DobaProductSourceService {
  async fetchProductSource(
    product: ShopifyProductSnapshot,
    resolution: SupplierSourceResolution,
  ): Promise<SupplierProductSourceData | null> {
    const runtime = buildDobaRuntimeConfig();
    if (!runtime.baseUrl || !runtime.appKey || !runtime.privateKey) {
      return null;
    }

    const endpoint = process.env.DOBA_SOURCE_DETAIL_ENDPOINT ?? "/api/goods/doba/spu/detail";
    const query: Record<string, string> = {};
    if (resolution.supplierProductId) {
      query.itemNo = resolution.supplierProductId;
    } else if (resolution.externalSourceId) {
      query.spuId = resolution.externalSourceId;
    } else if (resolution.supplierSku || product.variants.find((item) => item.sku)?.sku) {
      query.skuId = resolution.supplierSku || product.variants.find((item) => item.sku)?.sku || "";
    }

    if (Object.keys(query).length === 0) {
      return null;
    }

    const signed = buildDobaSignedParams(query, runtime);
    const url = new URL(endpoint, runtime.baseUrl.endsWith("/") ? runtime.baseUrl : `${runtime.baseUrl}/`);
    for (const [key, value] of Object.entries(query)) {
      if (value) {
        url.searchParams.set(key, value);
      }
    }

    const headers: Record<string, string> = {
      Accept: "application/json",
      "Content-Type": "application/json",
      appKey: runtime.appKey,
      signType: runtime.signType,
      timestamp: signed.timestamp,
      sign: signed.sign,
    };
    if (runtime.retailerId) {
      headers.retailerId = runtime.retailerId;
    }

    const response = await fetchWithRetry(url, {
      method: "GET",
      headers,
    }, { attempts: 3, baseDelayMs: 1000 });
    const text = await response.text();
    const payload = text ? (JSON.parse(text) as unknown) : {};
    const root = asRecord(payload);
    const data = asRecord(root.data);
    const specifications =
      normalizeRecordFromUnknown(findFirstValue(data, ["specifications", "specs", "attributes"])) || {};
    const dimensionsValue = findFirstValue(data, ["dimensions", "dimension", "sizeinfo"]);
    const packageDimensionsValue = findFirstValue(data, ["packagedimensions", "package_dimensions"]);

    return {
      sourceType: "DOBA",
      supplierProductId: resolution.supplierProductId || asString(data.itemNo),
      supplierSku: resolution.supplierSku || asString(data.skuId),
      title: findFirstString(data, ["title", "productname", "name"]),
      description: findFirstString(data, ["description", "summary", "feature"]),
      brand: findFirstString(data, ["brand", "vendor", "manufacturer"]),
      vendor: findFirstString(data, ["vendor", "brand", "manufacturer"]),
      productType:
        findFirstString(data, ["producttype", "type", "categoryname", "leafcategoryname"]) ||
        findSpecValue(specifications, ["product type", "type", "category"]),
      rawCategory:
        findFirstString(data, ["category", "categoryname", "catname", "categorypath"]) ||
        findSpecValue(specifications, ["category", "supplier category"]),
      googleProductCategory:
        findFirstString(data, ["googleproductcategory", "google_category", "googlecategory"]) ||
        findSpecValue(specifications, ["google product category"]),
      material:
        findFirstString(data, ["material"]) || findSpecValue(specifications, ["material", "fabric"]),
      color: findFirstString(data, ["color"]) || findSpecValue(specifications, ["color", "finish"]),
      size: findFirstString(data, ["size"]) || findSpecValue(specifications, ["size"]),
      dimensions: normalizeRecordFromUnknown(dimensionsValue),
      weight:
        findFirstString(data, ["weight", "grossweight", "netweight"]) ||
        findSpecValue(specifications, ["weight"]),
      packageDimensions: normalizeRecordFromUnknown(packageDimensionsValue),
      packageWeight:
        findFirstString(data, ["packageweight", "shippingweight"]) ||
        findSpecValue(specifications, ["package weight", "shipping weight"]),
      warehouse:
        findFirstString(data, ["warehouse", "warehousecode", "warehouse_name", "stocklocation"]),
      shippingOrigin:
        findFirstString(data, ["shippingorigin", "origin", "warehousecity", "inventorylocation"]),
      shippingTime: findFirstString(data, ["shippingtime", "deliverytime"]),
      returnPolicy: findFirstString(data, ["returnpolicy"]),
      warranty: findFirstString(data, ["warranty"]),
      mpn: findFirstString(data, ["mpn", "model"]) || findSpecValue(specifications, ["mpn", "model"]),
      gtin:
        findFirstString(data, ["gtin", "upc", "ean", "isbn"]) ||
        findSpecValue(specifications, ["gtin", "upc", "ean"]),
      barcode:
        findFirstString(data, ["barcode", "upc", "ean"]) ||
        findSpecValue(specifications, ["barcode", "upc", "ean"]),
      packingList: findStringArray(data, ["packinglist", "packageincludes"]),
      compatibility: findStringArray(data, ["compatibility", "compatiblewith"]),
      specifications,
      usageScenarios: findStringArray(data, ["usagescenarios", "usecases"]),
      images: findStringArray(data, ["images", "imageurls", "gallery"]),
      rawPayload: root,
    };
  }
}
