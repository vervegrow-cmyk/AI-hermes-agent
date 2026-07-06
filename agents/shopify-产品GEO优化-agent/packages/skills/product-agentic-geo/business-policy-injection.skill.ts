import { ShopifyProductSnapshot, SupplierProductSourceData } from "../../agents/product-agentic-geo-agent/product-agentic-geo.types.js";
import {
  BusinessPolicyInjectionService,
  PolicyInjectionResult,
} from "../../services/business-policy-injection.service.js";

export class BusinessPolicyInjectionSkill {
  constructor(
    private readonly businessPolicyInjectionService: BusinessPolicyInjectionService,
  ) {}

  execute(
    product: ShopifyProductSnapshot,
    sourceData?: SupplierProductSourceData,
  ): PolicyInjectionResult {
    return this.businessPolicyInjectionService.inject(product, sourceData);
  }
}
