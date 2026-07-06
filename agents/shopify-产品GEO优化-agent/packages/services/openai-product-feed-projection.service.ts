import {
  DeepSeekGeoAnalysis,
  ShopifyProductSnapshot,
} from "../agents/product-agentic-geo-agent/product-agentic-geo.types.js";
import { DefaultFieldPolicyService } from "./default-field-policy.service.js";

function firstNonEmpty(...values: Array<string | undefined | null>): string {
  for (const value of values) {
    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
  }
  return "";
}

export class OpenAIProductFeedProjectionService {
  constructor(private readonly defaultFieldPolicyService: DefaultFieldPolicyService) {}

  buildProjection(
    product: ShopifyProductSnapshot,
    analysis: DeepSeekGeoAnalysis,
  ): Record<string, unknown> {
    const primaryVariant = product.variants[0];
    const primaryImage = product.images[0];
    const brand = this.defaultFieldPolicyService.resolveBrand(product);
    const shippingSummary = this.defaultFieldPolicyService.resolveShippingSummary(product);
    const returnPolicySummary = this.defaultFieldPolicyService.resolveReturnPolicySummary();
    const warehouseOrigin = this.defaultFieldPolicyService.resolveWarehouseOrigin(product);
    const taxHandling = this.defaultFieldPolicyService.resolveTaxHandling();
    const mpn = this.defaultFieldPolicyService.resolveMpn(product);
    const customProduct = this.defaultFieldPolicyService.shouldSetCustomProduct(product);
    const mappedProductType =
      analysis.recommendations.product_type ||
      (analysis.recommendations.supplier_category as string) ||
      (analysis.recommendations.shopify_category as string) ||
      product.productType;

    return {
      is_eligible_search: product.status === "ACTIVE" && product.publishedInStore,
      is_eligible_checkout: false,
      item_id: product.id,
      title:
        (analysis.openai_product_feed_projection.title as string) ||
        analysis.recommendations.title ||
        product.title,
      description:
        (analysis.openai_product_feed_projection.description as string) ||
        analysis.product_detail_content.summary ||
        product.descriptionHtml,
      url: `/${product.handle}`,
      brand,
      image_url: primaryImage?.url ?? "",
      price: primaryVariant?.price ?? "",
      availability: primaryVariant?.availableForSale ? "available" : "unavailable",
      seller_name: firstNonEmpty(process.env.SHOPIFY_STORE, process.env.SHOPIFY_SHOP),
      seller_url: firstNonEmpty(process.env.SHOPIFY_SHOP_DOMAIN, process.env.SHOPIFY_STORE),
      return_policy: returnPolicySummary,
      target_countries: ["US"],
      store_country: "US",
      product_type:
        (analysis.openai_product_feed_projection.product_type as string) ||
        mappedProductType,
      supplier_category: analysis.recommendations.supplier_category || "",
      use_cases: analysis.product_detail_content.use_cases,
      key_attributes: [
        brand ? `Brand: ${brand}` : "",
        mpn ? `MPN: ${mpn}` : "",
        customProduct ? "Custom Product: true" : "",
        `Warehouse Origin: ${warehouseOrigin}`,
        `Tax Handling: ${taxHandling}`,
      ].filter(Boolean),
      variants: product.variants.map((variant) => ({
        id: variant.id,
        title: variant.title,
        price: variant.price,
        availability: variant.availableForSale,
        options: variant.selectedOptions,
      })),
      shipping: {
        status: "projection_only",
        summary: shippingSummary,
        origin: warehouseOrigin,
      },
      related_products: [],
      geo_availability: ["US"],
    };
  }
}
