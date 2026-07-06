import {
  ShopifyMetafield,
  ShopifyProductSnapshot,
  SupplierProductSourceData,
} from "../agents/product-agentic-geo-agent/product-agentic-geo.types.js";
import { DefaultFieldPolicyService } from "./default-field-policy.service.js";

function upsertMetafield(
  metafields: ShopifyMetafield[],
  input: ShopifyMetafield,
): ShopifyMetafield[] {
  const next = [...metafields];
  const index = next.findIndex(
    (item) => item.namespace === input.namespace && item.key === input.key,
  );
  if (index >= 0) {
    next[index] = input;
  } else {
    next.push(input);
  }
  return next;
}

export interface PolicyInjectionResult {
  product: ShopifyProductSnapshot;
  policyLockedSnapshot: Record<string, unknown>;
  lockedPolicyFields: string[];
}

export class BusinessPolicyInjectionService {
  constructor(private readonly defaultFieldPolicyService: DefaultFieldPolicyService) {}

  inject(
    product: ShopifyProductSnapshot,
    sourceData?: SupplierProductSourceData,
  ): PolicyInjectionResult {
    const businessDefaults = this.defaultFieldPolicyService.buildBusinessDefaults(product, sourceData);
    const policyLockedSnapshot = {
      business_defaults: businessDefaults,
      resolved_business_fields: {
        brand: this.defaultFieldPolicyService.resolveBrand(product, sourceData) || "Unbranded",
        mpn: this.defaultFieldPolicyService.resolveMpn(product, sourceData),
        custom_product: this.defaultFieldPolicyService.shouldSetCustomProduct(product, sourceData),
        identifier_exists: !this.defaultFieldPolicyService.shouldSetCustomProduct(product, sourceData),
        shipping_summary: this.defaultFieldPolicyService.resolveShippingSummary(product, sourceData),
        warehouse_origin: this.defaultFieldPolicyService.resolveWarehouseOrigin(product, sourceData),
        return_policy_summary: this.defaultFieldPolicyService.resolveReturnPolicySummary(),
        tax_handling: this.defaultFieldPolicyService.resolveTaxHandling(),
        seller_name: "Clearance Sale Dekuch",
        seller_url: "https://dekuch.com",
        store_country: "US",
        target_countries: ["US"],
      },
      locked_policy_fields: [
        "brand",
        "mpn",
        "custom_product",
        "identifier_exists",
        "shipping_summary",
        "warehouse_origin",
        "return_policy_summary",
        "tax_handling",
        "seller_name",
        "seller_url",
        "store_country",
        "target_countries",
      ],
    };

    const metafields = upsertMetafield(product.metafields, {
      namespace: "geo",
      key: "policy_locked_snapshot",
      type: "json",
      value: JSON.stringify(policyLockedSnapshot),
    });

    return {
      product: {
        ...product,
        metafields,
      },
      policyLockedSnapshot,
      lockedPolicyFields: policyLockedSnapshot.locked_policy_fields,
    };
  }
}
