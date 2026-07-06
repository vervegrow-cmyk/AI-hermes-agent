import {
  DeepSeekGeoAnalysis,
  ShopifyProductSnapshot,
} from "../../agents/product-agentic-geo-agent/product-agentic-geo.types.js";
import { DeepSeekGeoService } from "../../services/deepseek-geo.service.js";

export class ProductGEOAuditSkill {
  constructor(private readonly deepSeekGeoService: DeepSeekGeoService) {}

  async execute(
    product: ShopifyProductSnapshot,
    auditMode: "before" | "preview_after" | "final_after" = "before",
  ): Promise<DeepSeekGeoAnalysis> {
    return this.deepSeekGeoService.analyzeProductGEO({
      auditMode,
      productId: product.id,
      title: product.title,
      descriptionHtml: product.descriptionHtml,
      productType: product.productType,
      vendor: product.vendor,
      tags: product.tags,
      options: product.options,
      variants: product.variants,
      images: product.images,
      metafields: product.metafields,
    });
  }
}
