import {
  ProductGeoAgentCommand,
  RunActiveProductGEOAuditParams,
  RunActiveProductGEOAuditResult,
} from "./product-agentic-geo.types.js";
import { ProductAgenticGEOOrchestrator } from "./product-agentic-geo.orchestrator.js";

export class ProductAgenticGEORouter {
  constructor(private readonly orchestrator: ProductAgenticGEOOrchestrator) {}

  async runActiveProductGEOAudit(
    payload: RunActiveProductGEOAuditParams,
  ): Promise<RunActiveProductGEOAuditResult> {
    const command: ProductGeoAgentCommand = {
      type: "run-active-product-geo-audit",
      payload,
    };
    return this.orchestrator.handle(command);
  }
}
