import {
  DeepSeekGeoAnalysis,
  ShopifyProductSnapshot,
} from "../agents/product-agentic-geo-agent/product-agentic-geo.types.js";
import { DefaultFieldPolicyService } from "./default-field-policy.service.js";

export class GoogleMerchantProjectionService {
  constructor(private readonly defaultFieldPolicyService: DefaultFieldPolicyService) {}

  buildProjection(
    product: ShopifyProductSnapshot,
    analysis: DeepSeekGeoAnalysis,
  ): Record<string, unknown> {
    const primaryVariant = product.variants[0];
    const primaryImage = product.images[0];
    const semanticText = [
      analysis.semantic_profile.what_is_it,
      analysis.product_detail_content.summary,
      ...analysis.product_detail_content.use_cases,
      product.title,
    ]
      .join(" ")
      .toLowerCase();
    const inferredGoogleCategory = semanticText.includes("greenhouse") || semanticText.includes("polycarbonate")
      ? "Hardware > Building Materials > Glass & Plastic Sheets"
      : "";
    const recommendedProductType =
      analysis.recommendations.product_type ||
      (analysis.recommendations.supplier_category as string) ||
      (semanticText.includes("greenhouse") || semanticText.includes("polycarbonate")
        ? "Polycarbonate Greenhouse Panels"
        : product.productType);
    const mappedCategory =
      (analysis.recommendations.google_product_category as string) ||
      (analysis.recommendations.shopify_category as string) ||
      (analysis.recommendations.supplier_category as string) ||
      "";
    const hasGtin = Boolean(primaryVariant?.barcode?.trim());
    const brand = this.defaultFieldPolicyService.resolveBrand(product) || "Unknown Brand";
    const mpn = this.defaultFieldPolicyService.resolveMpn(product);
    const customProduct = this.defaultFieldPolicyService.shouldSetCustomProduct(product);
    const shippingSummary = this.defaultFieldPolicyService.resolveShippingSummary(product);
    const returnPolicySummary = this.defaultFieldPolicyService.resolveReturnPolicySummary();
    const taxHandling = this.defaultFieldPolicyService.resolveTaxHandling();

    return {
      id: product.id,
      title:
        (analysis.google_merchant_projection.title as string) ||
        analysis.recommendations.title ||
        product.title,
      description:
        (analysis.google_merchant_projection.description as string) ||
        analysis.seo_metadata.seo_description ||
        product.seo.description ||
        "",
      link: `/${product.handle}`,
      image_link: primaryImage?.url ?? "",
      availability: primaryVariant?.availableForSale ? "in stock" : "out of stock",
      price: primaryVariant?.price ?? "",
      brand,
      gtin: hasGtin ? primaryVariant?.barcode ?? "" : "",
      mpn,
      custom_product: hasGtin ? false : customProduct,
      condition: "new",
      google_product_category:
        (analysis.google_merchant_projection.google_product_category as string) ||
        analysis.recommendations.google_product_category ||
        mappedCategory ||
        inferredGoogleCategory ||
        product.category?.fullName ||
        "",
      product_type:
        (analysis.google_merchant_projection.product_type as string) ||
        recommendedProductType ||
        (analysis.recommendations.supplier_category as string) ||
        mappedCategory,
      supplier_category: analysis.recommendations.supplier_category || "",
      item_group_id: product.id,
      color: primaryVariant?.selectedOptions.find((option) => option.name.toLowerCase() === "color")?.value ?? "",
      size: primaryVariant?.selectedOptions.find((option) => option.name.toLowerCase() === "size")?.value ?? "",
      material:
        product.metafields.find((field) => field.key.toLowerCase().includes("material"))?.value ?? "",
      shipping: {
        status: "projection_only",
        weight: primaryVariant ? "" : "",
        summary: shippingSummary,
        origin: this.defaultFieldPolicyService.resolveWarehouseOrigin(product),
        tax_handling: taxHandling,
      },
      return_policy: {
        status: "projection_only",
        summary: returnPolicySummary,
      },
    };
  }
}
