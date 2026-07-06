import {
  DeepSeekGeoAnalysis,
  SearchIntentProjection,
} from "../../agents/product-agentic-geo-agent/product-agentic-geo.types.js";

export class AgenticSearchIntentSkill {
  execute(analysis: DeepSeekGeoAnalysis): SearchIntentProjection {
    return analysis.recommendations.search_intents;
  }
}
