import {
  DeepSeekGeoAnalysis,
  ShopifyProductSnapshot,
} from "../agents/product-agentic-geo-agent/product-agentic-geo.types.js";

export class OpenAIProductFeedProjectionService {
  buildProjection(
    product: ShopifyProductSnapshot,
    analysis: DeepSeekGeoAnalysis,
  ): Record<string, unknown> {
    const primaryVariant = product.variants[0];
    const primaryImage = product.images[0];

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
      brand: product.vendor,
      image_url: primaryImage?.url ?? "",
      price: primaryVariant?.price ?? "",
      availability: primaryVariant?.availableForSale ? "available" : "unavailable",
      seller_name: process.env.SHOPIFY_STORE ?? process.env.SHOPIFY_SHOP ?? "",
      seller_url: process.env.SHOPIFY_SHOP_DOMAIN ?? process.env.SHOPIFY_STORE ?? "",
      return_policy: "Needs policy enrichment",
      target_countries: ["US"],
      store_country: "US",
      variants: product.variants.map((variant) => ({
        id: variant.id,
        title: variant.title,
        price: variant.price,
        availability: variant.availableForSale,
        options: variant.selectedOptions,
      })),
      shipping: { status: "projection_only" },
      related_products: [],
      geo_availability: ["US"],
    };
  }
}
