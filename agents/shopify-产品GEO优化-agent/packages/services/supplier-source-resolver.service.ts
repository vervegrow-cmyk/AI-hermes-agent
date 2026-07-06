import {
  ShopifyMetafield,
  ShopifyProductSnapshot,
  SupplierSourceResolution,
  SupplierSourceType,
} from "../agents/product-agentic-geo-agent/product-agentic-geo.types.js";

function normalize(value: string): string {
  return value.trim();
}

function inferSourceTypeFromVendor(vendor: string): "GIGA" | "DOBA" | "" {
  const normalized = normalize(vendor).toLowerCase();
  if (normalized === "giga" || normalized === "dekuch") {
    return "GIGA";
  }
  if (normalized === "doba") {
    return "DOBA";
  }
  return "";
}

function normalizeKey(value: string): string {
  return value.trim().toLowerCase().replace(/[\s._-]+/g, "");
}

function readMetafield(metafields: ShopifyMetafield[], keys: string[]): string {
  const lowered = keys.map((item) => item.toLowerCase());
  for (const metafield of metafields) {
    const composite = `${metafield.namespace}.${metafield.key}`.toLowerCase();
    if (lowered.includes(composite) || lowered.includes(metafield.key.toLowerCase())) {
      return normalize(metafield.value);
    }
  }
  return "";
}

function readJsonMetafield(
  metafields: ShopifyMetafield[],
  keys: string[],
): Record<string, unknown> | null {
  const raw = readMetafield(metafields, keys);
  if (!raw) {
    return null;
  }
  try {
    const parsed = JSON.parse(raw) as unknown;
    return parsed && typeof parsed === "object" && !Array.isArray(parsed)
      ? (parsed as Record<string, unknown>)
      : null;
  } catch {
    return null;
  }
}

function readTagValue(tags: string[], keys: string[]): string {
  const normalizedKeys = keys.map((item) => normalizeKey(item));
  for (const rawTag of tags) {
    const tag = normalize(rawTag);
    if (!tag) {
      continue;
    }

    const matched = tag.match(/^([^:=]+)\s*[:=]\s*(.+)$/);
    if (!matched) {
      continue;
    }

    const [, rawKey, rawValue] = matched;
    if (normalizedKeys.includes(normalizeKey(rawKey))) {
      return normalize(rawValue);
    }
  }

  return "";
}

export class SupplierSourceResolverService {
  resolve(
    product: ShopifyProductSnapshot,
    preferredSourceType: SupplierSourceType = "AUTO",
  ): SupplierSourceResolution {
    if (preferredSourceType === "GIGA") {
      return this.buildForcedResolution(product, "GIGA");
    }
    if (preferredSourceType === "DOBA") {
      return this.buildForcedResolution(product, "DOBA");
    }

    const gigaProductId = readMetafield(product.metafields, [
      "geo.giga_product_id",
      "source.giga_product_id",
      "integration.giga_product_id",
      "giga_product_id",
      "external_source_id",
    ]);
    const dobaProductId = readMetafield(product.metafields, [
      "geo.doba_product_id",
      "source.doba_product_id",
      "integration.doba_product_id",
      "doba_product_id",
      "external_source_id",
    ]);
    const supplierSku = readMetafield(product.metafields, [
      "geo.supplier_sku",
      "source.supplier_sku",
      "integration.supplier_sku",
      "supplier_sku",
    ]);
    const sourceTypeMetafield = readMetafield(product.metafields, [
      "geo.source_type",
      "product_geo.source_type",
      "source.source_type",
      "source_type",
    ]).toUpperCase();
    const sourceSnapshot = readJsonMetafield(product.metafields, [
      "geo.supplier_source_snapshot",
      "product_geo.supplier_source_snapshot",
      "source.supplier_source_snapshot",
      "supplier_source_snapshot",
    ]);
    const vendor = normalize(product.vendor ?? "");
    const vendorLower = vendor.toLowerCase();
    const tagString = product.tags.join(" ").toLowerCase();
    const tagSourceType = readTagValue(product.tags, [
      "source_type",
      "source",
      "supplier_source",
      "vendor_source",
    ]).toUpperCase();
    const tagSupplierProductId = readTagValue(product.tags, [
      "giga_product_id",
      "doba_product_id",
      "supplier_product_id",
      "supplier_productid",
      "external_source_id",
      "item_no",
      "itemno",
      "spu_id",
      "spuid",
      "spu_no",
      "spuno",
      "product_id",
    ]);
    const tagSupplierSku = readTagValue(product.tags, [
      "supplier_sku",
      "suppliersku",
      "source_sku",
      "vendorsku",
      "sku_id",
      "skuid",
    ]);
    const firstSku = normalize(product.variants.find((item) => item.sku)?.sku ?? "");
    const snapshotSourceType = normalize(String(sourceSnapshot?.source_type ?? "")).toUpperCase();
    const snapshotProductId = normalize(
      String(sourceSnapshot?.supplier_product_id ?? sourceSnapshot?.external_source_id ?? ""),
    );
    const snapshotSupplierSku = normalize(String(sourceSnapshot?.supplier_sku ?? ""));
    const externalSourceId = readMetafield(product.metafields, [
      "geo.external_source_id",
      "product_geo.external_source_id",
      "source.external_source_id",
      "external_source_id",
    ]);
    const inferredVendorSourceType = inferSourceTypeFromVendor(vendor);

    if (
      sourceTypeMetafield === "GIGA" ||
      snapshotSourceType === "GIGA" ||
      tagSourceType === "GIGA" ||
      inferredVendorSourceType === "GIGA"
    ) {
      return {
        sourceType: "GIGA",
        supplierProductId: gigaProductId || tagSupplierProductId || snapshotProductId || externalSourceId,
        supplierSku: supplierSku || tagSupplierSku || snapshotSupplierSku || firstSku,
        externalSourceId: gigaProductId || tagSupplierProductId || snapshotProductId || externalSourceId,
        matchedBy: [
          ...(sourceTypeMetafield === "GIGA" ? ["metafield:source_type"] : []),
          ...(snapshotSourceType === "GIGA" ? ["metafield:supplier_source_snapshot"] : []),
          ...(tagSourceType === "GIGA" ? ["tag:source_type"] : []),
          ...(inferredVendorSourceType === "GIGA" ? [`vendor:${vendor}`] : []),
        ],
      };
    }

    if (
      sourceTypeMetafield === "DOBA" ||
      snapshotSourceType === "DOBA" ||
      tagSourceType === "DOBA" ||
      inferredVendorSourceType === "DOBA"
    ) {
      return {
        sourceType: "DOBA",
        supplierProductId: dobaProductId || tagSupplierProductId || snapshotProductId || externalSourceId,
        supplierSku: supplierSku || tagSupplierSku || snapshotSupplierSku || firstSku,
        externalSourceId: dobaProductId || tagSupplierProductId || snapshotProductId || externalSourceId,
        matchedBy: [
          ...(sourceTypeMetafield === "DOBA" ? ["metafield:source_type"] : []),
          ...(snapshotSourceType === "DOBA" ? ["metafield:supplier_source_snapshot"] : []),
          ...(tagSourceType === "DOBA" ? ["tag:source_type"] : []),
          ...(inferredVendorSourceType === "DOBA" ? [`vendor:${vendor}`] : []),
        ],
      };
    }

    if (
      !vendorLower &&
      (gigaProductId || tagString.includes("giga") || firstSku.startsWith("GIGA"))
    ) {
      return {
        sourceType: "GIGA",
        supplierProductId: gigaProductId || tagSupplierProductId || externalSourceId,
        supplierSku: supplierSku || tagSupplierSku || firstSku,
        externalSourceId: gigaProductId || tagSupplierProductId || externalSourceId,
        matchedBy: [
          ...(gigaProductId ? ["metafield:giga_product_id"] : []),
          ...(tagString.includes("giga") ? ["tag:giga"] : []),
          ...(firstSku.startsWith("GIGA") ? ["sku-prefix:GIGA"] : []),
          ...(tagSupplierProductId ? ["tag:supplier_product_id"] : []),
        ],
      };
    }

    if (
      !vendorLower &&
      (dobaProductId || tagString.includes("doba") || firstSku.startsWith("DOBA"))
    ) {
      return {
        sourceType: "DOBA",
        supplierProductId: dobaProductId || tagSupplierProductId || externalSourceId,
        supplierSku: supplierSku || tagSupplierSku || firstSku,
        externalSourceId: dobaProductId || tagSupplierProductId || externalSourceId,
        matchedBy: [
          ...(dobaProductId ? ["metafield:doba_product_id"] : []),
          ...(tagString.includes("doba") ? ["tag:doba"] : []),
          ...(firstSku.startsWith("DOBA") ? ["sku-prefix:DOBA"] : []),
          ...(tagSupplierProductId ? ["tag:supplier_product_id"] : []),
        ],
      };
    }

    if (!vendorLower && externalSourceId && tagString.includes("doba")) {
      return {
        sourceType: "DOBA",
        supplierProductId: dobaProductId || externalSourceId,
        supplierSku: supplierSku || snapshotSupplierSku || firstSku,
        externalSourceId,
        matchedBy: ["metafield:external_source_id", "tag:doba"],
      };
    }
    if (!vendorLower && externalSourceId && tagString.includes("giga")) {
      return {
        sourceType: "GIGA",
        supplierProductId: gigaProductId || externalSourceId,
        supplierSku: supplierSku || snapshotSupplierSku || firstSku,
        externalSourceId,
        matchedBy: ["metafield:external_source_id", "tag:giga"],
      };
    }

    return {
      sourceType: "UNKNOWN",
      supplierProductId: "",
      supplierSku: supplierSku || firstSku,
      externalSourceId: "",
      matchedBy: [],
    };
  }

  private buildForcedResolution(
    product: ShopifyProductSnapshot,
    sourceType: "GIGA" | "DOBA",
  ): SupplierSourceResolution {
    const supplierProductId = readMetafield(product.metafields, [
      `geo.${sourceType.toLowerCase()}_product_id`,
      `source.${sourceType.toLowerCase()}_product_id`,
      `${sourceType.toLowerCase()}_product_id`,
      "external_source_id",
    ]);
    const tagSupplierProductId = readTagValue(product.tags, [
      `${sourceType.toLowerCase()}_product_id`,
      "supplier_product_id",
      "external_source_id",
      "item_no",
      "itemno",
      "spu_id",
      "spuid",
      "spu_no",
      "spuno",
      "product_id",
    ]);
    const supplierSku =
      readMetafield(product.metafields, ["geo.supplier_sku", "source.supplier_sku", "supplier_sku"]) ||
      readTagValue(product.tags, ["supplier_sku", "suppliersku", "source_sku", "vendorsku", "sku_id", "skuid"]) ||
      normalize(product.variants.find((item) => item.sku)?.sku ?? "");

    return {
      sourceType,
      supplierProductId: supplierProductId || tagSupplierProductId,
      supplierSku,
      externalSourceId: supplierProductId || tagSupplierProductId,
      matchedBy: ["forced"],
    };
  }
}
