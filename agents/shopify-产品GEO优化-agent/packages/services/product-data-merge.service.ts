import {
  EnrichedProductSnapshot,
  ShopifyMetafield,
  ShopifyProductSnapshot,
  SupplierProductSourceData,
  SupplierSourceResolution,
} from "../agents/product-agentic-geo-agent/product-agentic-geo.types.js";
import { DefaultFieldPolicyService } from "./default-field-policy.service.js";

function isGenericProductType(value: string): boolean {
  const normalized = value.trim().toLowerCase();
  return normalized === "" || normalized === "part" || normalized === "other" || normalized === "default title";
}

function upsertMetafield(
  metafields: ShopifyMetafield[],
  input: ShopifyMetafield,
): ShopifyMetafield[] {
  const next = [...metafields];
  const index = next.findIndex(
    (item) => item.namespace === input.namespace && item.key === input.key,
  );
  if (index >= 0) {
    next[index] = input;
  } else {
    next.push(input);
  }
  return next;
}

export class ProductDataMergeService {
  constructor(private readonly defaultFieldPolicyService: DefaultFieldPolicyService) {}

  merge(
    product: ShopifyProductSnapshot,
    sourceData: SupplierProductSourceData,
    resolution: SupplierSourceResolution,
  ): EnrichedProductSnapshot {
    const enrichedFields: string[] = [];
    const unresolvedFields: string[] = [];
    let metafields = [...product.metafields];

    let vendor = product.vendor;
    if (!vendor) {
      vendor = this.defaultFieldPolicyService.resolveBrand(product, sourceData);
    }
    if (vendor && !product.vendor) {
      enrichedFields.push("vendor");
    }

    let productType = product.productType;
    if (isGenericProductType(productType) && (sourceData.productType || sourceData.rawCategory)) {
      productType = sourceData.productType || sourceData.rawCategory;
      enrichedFields.push("productType");
    }

    const sourcePayload = {
      source_type: sourceData.sourceType,
      supplier_product_id: resolution.supplierProductId,
      supplier_sku: resolution.supplierSku,
      brand: sourceData.brand,
      material: sourceData.material,
      dimensions: sourceData.dimensions,
      weight: sourceData.weight,
      package_dimensions: sourceData.packageDimensions,
      package_weight: sourceData.packageWeight,
      shipping_origin: sourceData.shippingOrigin,
      warehouse: sourceData.warehouse,
      shipping_time: sourceData.shippingTime,
      return_policy: sourceData.returnPolicy,
      warranty: sourceData.warranty,
      mpn: sourceData.mpn,
      gtin: sourceData.gtin,
      barcode: sourceData.barcode,
      compatibility: sourceData.compatibility,
      packing_list: sourceData.packingList,
      usage_scenarios: sourceData.usageScenarios,
      images: sourceData.images,
      specifications: sourceData.specifications,
      raw_category: sourceData.rawCategory,
      google_product_category: sourceData.googleProductCategory,
    };

    metafields = upsertMetafield(metafields, {
      namespace: "geo",
      key: "supplier_source_snapshot",
      type: "json",
      value: JSON.stringify(sourcePayload),
    });
    metafields = upsertMetafield(metafields, {
      namespace: "geo",
      key: "source_type",
      type: "single_line_text_field",
      value: sourceData.sourceType,
    });
    if (sourceData.rawCategory || sourceData.productType) {
      metafields = upsertMetafield(metafields, {
        namespace: "geo",
        key: "supplier_category",
        type: "single_line_text_field",
        value: sourceData.rawCategory || sourceData.productType,
      });
    }
    if (sourceData.googleProductCategory) {
      metafields = upsertMetafield(metafields, {
        namespace: "geo",
        key: "google_product_category",
        type: "single_line_text_field",
        value: sourceData.googleProductCategory,
      });
    }
    metafields = upsertMetafield(metafields, {
      namespace: "geo",
      key: "default_field_policy",
      type: "json",
      value: JSON.stringify(
        this.defaultFieldPolicyService.buildDefaultPolicySnapshot(product, sourceData),
      ),
    });

    const sourceSummary = [
      sourceData.description,
      sourceData.material ? `Material: ${sourceData.material}` : "",
      sourceData.weight ? `Weight: ${sourceData.weight}` : "",
      `Shipping: ${this.defaultFieldPolicyService.resolveShippingSummary(product, sourceData)}`,
      `Return Policy: ${sourceData.returnPolicy || this.defaultFieldPolicyService.resolveReturnPolicySummary()}`,
      `Tax Handling: ${this.defaultFieldPolicyService.resolveTaxHandling()}`,
      `Warehouse Origin: ${this.defaultFieldPolicyService.resolveWarehouseOrigin(product, sourceData)}`,
      sourceData.warranty ? `Warranty: ${sourceData.warranty}` : "",
      `MPN: ${this.defaultFieldPolicyService.resolveMpn(product, sourceData)}`,
      sourceData.packingList.length > 0 ? `Packing List: ${sourceData.packingList.join(", ")}` : "",
      sourceData.compatibility.length > 0
        ? `Compatibility: ${sourceData.compatibility.join(", ")}`
        : "",
    ]
      .filter(Boolean)
      .join("\n");

    let descriptionHtml = product.descriptionHtml;
    if (sourceSummary && !product.descriptionHtml.includes("supplier-source-enrichment")) {
      descriptionHtml = `${product.descriptionHtml}\n<!-- supplier-source-enrichment -->\n<p>${sourceSummary.replace(/\n/g, "<br/>")}</p>`;
      enrichedFields.push("descriptionHtml_context");
    }

    if (!sourceData.material) unresolvedFields.push("material");
    if (!sourceData.weight) unresolvedFields.push("weight");
    if (Object.keys(sourceData.dimensions ?? {}).length === 0) unresolvedFields.push("dimensions");
    if (!sourceData.gtin && !sourceData.barcode) unresolvedFields.push("gtin_or_barcode");
    if (!sourceData.rawCategory && !sourceData.productType) unresolvedFields.push("supplier_category");

    return {
      product: {
        ...product,
        vendor,
        productType,
        descriptionHtml,
        metafields,
      },
      sourceType: sourceData.sourceType,
      supplierProductId: resolution.supplierProductId,
      supplierSku: resolution.supplierSku,
      enrichedFields,
      unresolvedFields,
      sourceData,
    };
  }
}
