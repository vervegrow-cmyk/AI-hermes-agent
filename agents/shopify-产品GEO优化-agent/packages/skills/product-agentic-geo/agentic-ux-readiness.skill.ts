import { DeepSeekGeoAnalysis } from "../../agents/product-agentic-geo-agent/product-agentic-geo.types.js";

export class AgenticUXReadinessSkill {
  execute(analysis: DeepSeekGeoAnalysis): { score: number; notes: string[] } {
    return {
      score: analysis.agentic_ux_score,
      notes:
        analysis.agentic_ux_audit.issues.length > 0
          ? analysis.agentic_ux_audit.issues
          : ["Phase13A records the UX score from DeepSeek and defers live journey validation."],
    };
  }
}
