import {
  ShopifyMetafield,
  ShopifyProductSnapshot,
  SupplierProductSourceData,
  SupplierSourceType,
} from "../agents/product-agentic-geo-agent/product-agentic-geo.types.js";

function parseJson(value: string): Record<string, unknown> | null {
  try {
    const parsed = JSON.parse(value) as unknown;
    return parsed && typeof parsed === "object" && !Array.isArray(parsed)
      ? (parsed as Record<string, unknown>)
      : null;
  } catch {
    return null;
  }
}

function firstNonEmpty(...values: Array<string | undefined | null>): string {
  for (const value of values) {
    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
  }
  return "";
}

function inferSourceTypeFromVendor(vendor: string): "GIGA" | "DOBA" | "UNKNOWN" {
  const normalized = vendor.trim().toLowerCase();
  if (normalized === "giga" || normalized === "dekuch") {
    return "GIGA";
  }
  if (normalized === "doba") {
    return "DOBA";
  }
  return "UNKNOWN";
}

function readMetafield(metafields: ShopifyMetafield[], namespace: string, key: string): string {
  return (
    metafields.find((field) => field.namespace === namespace && field.key === key)?.value ?? ""
  );
}

function hasCityLevelEvidence(value: string): boolean {
  return /^[A-Za-z .'-]+,\s*[A-Z]{2}(,\s*United States)?$/i.test(value.trim());
}

function normalizeCountryWarehouse(value: string): string {
  const normalized = value.trim().toLowerCase();
  if (!normalized) {
    return "United States warehouse";
  }
  if (
    normalized === "us" ||
    normalized === "usa" ||
    normalized === "united states" ||
    normalized === "united states warehouse" ||
    normalized === "warehouse" ||
    normalized === "default location" ||
    normalized === "online store"
  ) {
    return "United States warehouse";
  }
  return value.trim();
}

export class DefaultFieldPolicyService {
  resolveSourceType(
    product: ShopifyProductSnapshot,
    sourceData?: SupplierProductSourceData,
  ): Exclude<SupplierSourceType, "AUTO"> {
    const explicitSource = firstNonEmpty(
      sourceData?.sourceType,
      readMetafield(product.metafields, "geo", "source_type"),
    ).toUpperCase();

    if (explicitSource === "DOBA") {
      return "DOBA";
    }
    if (explicitSource === "GIGA") {
      return "GIGA";
    }

    const vendorSourceType = inferSourceTypeFromVendor(product.vendor ?? "");
    if (vendorSourceType !== "UNKNOWN") {
      return vendorSourceType;
    }

    return "UNKNOWN";
  }

  resolveBrand(product: ShopifyProductSnapshot, sourceData?: SupplierProductSourceData): string {
    const resolved = firstNonEmpty(product.vendor, sourceData?.brand, sourceData?.vendor);
    if (resolved) {
      return resolved;
    }

    const sourceType = this.resolveSourceType(product, sourceData);
    if (sourceType === "DOBA") {
      return "DOBA";
    }
    if (sourceType === "GIGA") {
      return "Dekuch";
    }

    return "";
  }

  resolveMpn(product: ShopifyProductSnapshot, sourceData?: SupplierProductSourceData): string {
    const sourceSnapshot = parseJson(readMetafield(product.metafields, "geo", "supplier_source_snapshot"));
    const variantSku = product.variants[0]?.sku ?? "";

    return firstNonEmpty(
      sourceData?.mpn,
      typeof sourceSnapshot?.mpn === "string" ? sourceSnapshot.mpn : "",
      variantSku,
      typeof sourceSnapshot?.supplier_sku === "string" ? sourceSnapshot.supplier_sku : "",
      typeof sourceSnapshot?.supplier_product_id === "string" ? sourceSnapshot.supplier_product_id : "",
    );
  }

  resolveWarehouseOrigin(product: ShopifyProductSnapshot, sourceData?: SupplierProductSourceData): string {
    const candidate = firstNonEmpty(
      sourceData?.shippingOrigin,
      sourceData?.warehouse,
      readMetafield(product.metafields, "geo", "warehouse_origin"),
      readMetafield(product.metafields, "geo", "shipping_origin"),
      readMetafield(product.metafields, "supplier", "warehouse"),
      readMetafield(product.metafields, "supplier", "shipping_origin"),
      readMetafield(product.metafields, "custom", "warehouse"),
    );
    if (!candidate) {
      return "United States warehouse";
    }
    if (hasCityLevelEvidence(candidate)) {
      return candidate.includes("United States") ? candidate : `${candidate}, United States`;
    }
    return normalizeCountryWarehouse(candidate);
  }

  resolveShippingSummary(product: ShopifyProductSnapshot, sourceData?: SupplierProductSourceData): string {
    const origin = this.resolveWarehouseOrigin(product, sourceData);
    if (hasCityLevelEvidence(origin)) {
      return `Ships from ${origin}. Free shipping may be available according to the store shipping policy.`;
    }
    return "Ships from a United States warehouse. Free shipping may be available according to the store shipping policy.";
  }

  resolveReturnPolicySummary(): string {
    return "7-day easy return and 30-day after-sales support.";
  }

  resolveTaxHandling(): string {
    return "Taxes are automatically calculated by Shopify at checkout based on store tax settings.";
  }

  buildWarehousePolicySnapshot(
    product: ShopifyProductSnapshot,
    sourceData?: SupplierProductSourceData,
  ): Record<string, unknown> {
    const origin = this.resolveWarehouseOrigin(product, sourceData);
    const cityLevelConfirmed = hasCityLevelEvidence(origin);
    return {
      resolved_warehouse_origin: cityLevelConfirmed ? origin.replace(/,\s*United States$/i, "") : "United States warehouse",
      warehouse_source: sourceData?.shippingOrigin || sourceData?.warehouse ? sourceData?.sourceType ?? "SUPPLIER_API" : "SYSTEM_DEFAULT",
      warehouse_confidence: cityLevelConfirmed ? "high" : "low",
      city_level_confirmed: cityLevelConfirmed,
      country_level_only: !cityLevelConfirmed,
      do_not_invent_city: true,
      fallback_value: "United States warehouse",
    };
  }

  buildBusinessDefaults(
    product: ShopifyProductSnapshot,
    sourceData?: SupplierProductSourceData,
  ): Record<string, unknown> {
    return {
      brand_policy: {
        resolved_brand: this.resolveBrand(product, sourceData) || "Unbranded",
      },
      mpn_policy: {
        resolved_mpn: this.resolveMpn(product, sourceData),
        sku_as_mpn_only: true,
      },
      gtin_policy: {
        allow_sku_as_gtin: false,
        allow_spu_as_gtin: false,
        allow_supplier_sku_as_upc: false,
        use_custom_product_when_gtin_missing: true,
      },
      shipping_policy: {
        resolved_shipping_summary: this.resolveShippingSummary(product, sourceData),
      },
      return_policy: {
        resolved_return_policy_summary: this.resolveReturnPolicySummary(),
      },
      warehouse_policy: this.buildWarehousePolicySnapshot(product, sourceData),
      tax_policy: {
        resolved_tax_handling: this.resolveTaxHandling(),
      },
    };
  }

  shouldSetCustomProduct(
    product: ShopifyProductSnapshot,
    sourceData?: SupplierProductSourceData,
  ): boolean {
    const variantBarcode = product.variants.some((variant) => variant.barcode.trim().length > 0);
    const sourceGtin = Boolean(firstNonEmpty(sourceData?.gtin, sourceData?.barcode));
    return !variantBarcode && !sourceGtin;
  }

  buildDefaultPolicySnapshot(
    product: ShopifyProductSnapshot,
    sourceData?: SupplierProductSourceData,
  ): Record<string, unknown> {
    return {
      business_defaults: this.buildBusinessDefaults(product, sourceData),
      warehouse_policy: this.buildWarehousePolicySnapshot(product, sourceData),
      brand_default_rule: this.resolveBrand(product, sourceData),
      mpn_default_rule: this.resolveMpn(product, sourceData),
      shipping_summary_default_rule: this.resolveShippingSummary(product, sourceData),
      return_policy_summary_default_rule: this.resolveReturnPolicySummary(),
      warehouse_origin_default_rule: this.resolveWarehouseOrigin(product, sourceData),
      tax_handling_default_rule: this.resolveTaxHandling(),
      custom_product_default_rule: this.shouldSetCustomProduct(product, sourceData),
      gtin_missing_fallback_strategy:
        "Do not map SKU/SPU to GTIN/UPC/barcode. Keep GTIN empty and set custom_product=true in merchant/feed projections.",
    };
  }
}
