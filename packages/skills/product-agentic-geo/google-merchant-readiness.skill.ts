import {
  DeepSeekGeoAnalysis,
  ShopifyProductSnapshot,
} from "../../agents/product-agentic-geo-agent/product-agentic-geo.types.js";
import { GoogleMerchantProjectionService } from "../../services/google-merchant-projection.service.js";

export class GoogleMerchantReadinessSkill {
  constructor(private readonly projectionService: GoogleMerchantProjectionService) {}

  execute(product: ShopifyProductSnapshot, analysis: DeepSeekGeoAnalysis): Record<string, unknown> {
    return this.projectionService.buildProjection(product, analysis);
  }
}
