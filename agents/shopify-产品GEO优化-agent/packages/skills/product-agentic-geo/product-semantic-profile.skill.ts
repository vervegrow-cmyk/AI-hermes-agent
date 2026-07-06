import {
  DeepSeekGeoAnalysis,
  ProductSemanticProfile,
} from "../../agents/product-agentic-geo-agent/product-agentic-geo.types.js";

export class ProductSemanticProfileSkill {
  execute(analysis: DeepSeekGeoAnalysis): ProductSemanticProfile {
    return analysis.semantic_profile;
  }
}
