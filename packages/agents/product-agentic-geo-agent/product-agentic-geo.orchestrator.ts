import { ProductAgenticGEOAgent } from "./product-agentic-geo.agent.js";
import {
  ProductGeoAgentCommand,
  RunActiveProductGEOAuditResult,
} from "./product-agentic-geo.types.js";

export class ProductAgenticGEOOrchestrator {
  constructor(private readonly agent: ProductAgenticGEOAgent) {}

  async handle(command: ProductGeoAgentCommand): Promise<RunActiveProductGEOAuditResult> {
    switch (command.type) {
      case "run-active-product-geo-audit":
        return this.agent.runActiveProductGEOAudit(command.payload);
    }

    throw new Error(`Unsupported command: ${JSON.stringify(command)}`);
  }
}
