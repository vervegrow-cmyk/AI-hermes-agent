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
      product_schema: {
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
        primaryImageAlt: primaryImage?.altText ?? "",
      },
      offer_schema: {
        "@type": "Offer",
        price: primaryVariant?.price ?? "",
        availability: primaryVariant?.availableForSale
          ? "https://schema.org/InStock"
          : "https://schema.org/OutOfStock",
        itemCondition: "https://schema.org/NewCondition",
        url: `/${product.handle}`,
      },
      faq_schema: {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        mainEntity: analysis.faq_content.map((item) => ({
          "@type": "Question",
          name: item.question,
          acceptedAnswer: {
            "@type": "Answer",
            text: item.answer,
          },
        })),
      },
      breadcrumb_schema: {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        itemListElement: [
          {
            "@type": "ListItem",
            position: 1,
            name: "Home",
            item: "/",
          },
          {
            "@type": "ListItem",
            position: 2,
            name: product.category?.fullName ?? product.productType ?? "Products",
            item: `/${product.handle}`,
          },
        ],
      },
      merchant_return_policy: {
        "@type": "MerchantReturnPolicy",
        status: "projection_only",
      },
      shipping_details: {
        "@type": "OfferShippingDetails",
        status: "projection_only",
      },
    };
  }
}
