import {
  DeepSeekGeoAnalysis,
  ShopifyProductSnapshot,
} from "../agents/product-agentic-geo-agent/product-agentic-geo.types.js";

export class SchemaMarkupService {
  buildProjection(
    product: ShopifyProductSnapshot,
    analysis: DeepSeekGeoAnalysis,
  ): Record<string, unknown> {
    const primaryVariant = product.variants[0];
    const primaryImage = product.images[0];

    return {
      "@context": "https://schema.org",
      "@type": product.variants.length > 1 ? "ProductGroup" : "Product",
      productGroupID: product.variants.length > 1 ? product.id : undefined,
      name:
        (analysis.schema_projection.name as string) ||
        analysis.recommendations.title ||
        product.title,
      description:
        (analysis.schema_projection.description as string) ||
        analysis.seo_metadata.seo_description ||
        product.seo.description ||
        "",
      brand: {
        "@type": "Brand",
        name: product.vendor,
      },
      image: product.images.map((image) => image.url),
      category: product.category?.fullName ?? product.productType,
      sku: primaryVariant?.sku ?? "",
      gtin: primaryVariant?.barcode ?? "",
      offers: {
        "@type": "Offer",
        price: primaryVariant?.price ?? "",
        availability: primaryVariant?.availableForSale
          ? "https://schema.org/InStock"
          : "https://schema.org/OutOfStock",
        itemCondition: "https://schema.org/NewCondition",
        url: `/${product.handle}`,
      },
      hasVariant: product.variants.map((variant) => ({
        "@type": "Product",
        sku: variant.sku,
        name: `${product.title} ${variant.title}`.trim(),
        offers: {
          "@type": "Offer",
          price: variant.price,
          availability: variant.availableForSale
            ? "https://schema.org/InStock"
            : "https://schema.org/OutOfStock",
        },
      })),
      faq: analysis.faq_content,
      primaryImageAlt: primaryImage?.altText ?? "",
    };
  }
}
