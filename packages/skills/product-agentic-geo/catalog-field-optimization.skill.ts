import {
  DeepSeekGeoAnalysis,
  ProductGeoRecommendations,
} from "../../agents/product-agentic-geo-agent/product-agentic-geo.types.js";

export class CatalogFieldOptimizationSkill {
  execute(analysis: DeepSeekGeoAnalysis): ProductGeoRecommendations {
    return analysis.recommendations;
  }
}
