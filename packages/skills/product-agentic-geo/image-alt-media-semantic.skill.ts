import {
  DeepSeekGeoAnalysis,
  ImageAltRecommendation,
} from "../../agents/product-agentic-geo-agent/product-agentic-geo.types.js";

export class ImageAltMediaSemanticSkill {
  execute(analysis: DeepSeekGeoAnalysis): ImageAltRecommendation[] {
    return analysis.recommendations.image_alt;
  }
}
