import {
  ShopifyActiveProductRef,
  ShopifyProductSnapshot,
} from "../../agents/product-agentic-geo-agent/product-agentic-geo.types.js";
import { ShopifyProductGeoService } from "../../services/shopify-product-geo.service.js";

export class ShopifyActiveProductScanSkill {
  constructor(private readonly shopifyProductGeoService: ShopifyProductGeoService) {}

  async execute(input: { limit: number }): Promise<ShopifyActiveProductRef[]> {
    return this.shopifyProductGeoService.fetchActiveProductRefs({ limit: input.limit });
  }

  async readProduct(productId: string): Promise<ShopifyProductSnapshot> {
    return this.shopifyProductGeoService.fetchProductById(productId);
  }
}
