import {
  DeepSeekGeoAnalysis,
  ProductFAQEntry,
} from "../../agents/product-agentic-geo-agent/product-agentic-geo.types.js";

export class ProductFAQTrustSkill {
  execute(analysis: DeepSeekGeoAnalysis): ProductFAQEntry[] {
    return analysis.recommendations.faq;
  }
}
