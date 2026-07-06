import {
  DeepSeekGeoAnalysis,
  ShopifyProductSnapshot,
} from "../agents/product-agentic-geo-agent/product-agentic-geo.types.js";

export class GoogleMerchantProjectionService {
  buildProjection(
    product: ShopifyProductSnapshot,
    analysis: DeepSeekGeoAnalysis,
  ): Record<string, unknown> {
    const primaryVariant = product.variants[0];
    const primaryImage = product.images[0];

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
      brand: product.vendor,
      gtin: primaryVariant?.barcode ?? "",
      mpn: primaryVariant?.sku ?? "",
      condition: "new",
      google_product_category:
        (analysis.google_merchant_projection.google_product_category as string) ||
        product.category?.fullName ||
        "",
      product_type:
        (analysis.google_merchant_projection.product_type as string) || product.productType,
      item_group_id: product.id,
      color: primaryVariant?.selectedOptions.find((option) => option.name.toLowerCase() === "color")?.value ?? "",
      size: primaryVariant?.selectedOptions.find((option) => option.name.toLowerCase() === "size")?.value ?? "",
      material:
        product.metafields.find((field) => field.key.toLowerCase().includes("material"))?.value ?? "",
      shipping: "Needs merchant policy mapping",
      return_policy: "Needs merchant policy mapping",
    };
  }
}
