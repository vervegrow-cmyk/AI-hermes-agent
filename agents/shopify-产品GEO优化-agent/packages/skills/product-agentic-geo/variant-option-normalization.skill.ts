import { ShopifyProductSnapshot } from "../../agents/product-agentic-geo-agent/product-agentic-geo.types.js";

export class VariantOptionNormalizationSkill {
  execute(product: ShopifyProductSnapshot): { suggestions: Array<{ variantId: string; optionName: string; current: string; suggested: string }> } {
    const suggestions = product.variants.flatMap((variant) =>
      variant.selectedOptions.map((option) => ({
        variantId: variant.id,
        optionName: option.name,
        current: option.value,
        suggested: option.value.trim(),
      })),
    );

    return { suggestions };
  }
}
