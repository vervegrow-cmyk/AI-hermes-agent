import {
  DeepSeekGeoAnalysis,
  ShopifyProductSnapshot,
} from "../../agents/product-agentic-geo-agent/product-agentic-geo.types.js";
import { SchemaMarkupService } from "../../services/schema-markup.service.js";

export class ProductSchemaGenerationSkill {
  constructor(private readonly schemaMarkupService: SchemaMarkupService) {}

  execute(product: ShopifyProductSnapshot, analysis: DeepSeekGeoAnalysis): Record<string, unknown> {
    return this.schemaMarkupService.buildProjection(product, analysis);
  }
}
