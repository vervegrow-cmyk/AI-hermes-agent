import {
  DeepSeekGeoAnalysis,
  ShopifyProductSnapshot,
} from "../../agents/product-agentic-geo-agent/product-agentic-geo.types.js";
import { OpenAIProductFeedProjectionService } from "../../services/openai-product-feed-projection.service.js";

export class OpenAIProductFeedProjectionSkill {
  constructor(private readonly projectionService: OpenAIProductFeedProjectionService) {}

  execute(product: ShopifyProductSnapshot, analysis: DeepSeekGeoAnalysis): Record<string, unknown> {
    return this.projectionService.buildProjection(product, analysis);
  }
}
