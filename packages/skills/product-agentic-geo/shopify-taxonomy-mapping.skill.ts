import { ShopifyProductSnapshot } from "../../agents/product-agentic-geo-agent/product-agentic-geo.types.js";

export class ShopifyTaxonomyMappingSkill {
  execute(product: ShopifyProductSnapshot): { category: string; notes: string[] } {
    return {
      category: product.category?.fullName ?? product.productType,
      notes: ["Phase13A returns taxonomy mapping hints only; no category writeback."],
    };
  }
}
