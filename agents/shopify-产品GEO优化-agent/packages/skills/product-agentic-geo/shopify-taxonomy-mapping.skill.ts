import { ShopifyProductSnapshot } from "../../agents/product-agentic-geo-agent/product-agentic-geo.types.js";

type TaxonomyRule = {
  match: string[];
  exclude?: string[];
  category: string;
  googleProductCategory: string;
  productType: string;
  supplierCategory: string;
  priority: number;
};

type TaxonomySignal = {
  supplierCategory: string;
  googleProductCategory: string;
  productType: string;
};

export class ShopifyTaxonomyMappingSkill {
  execute(product: ShopifyProductSnapshot): {
    category: string;
    googleProductCategory: string;
    productType: string;
    supplierCategory: string;
    notes: string[];
  } {
    const sourceSignal = this.extractSourceTaxonomySignal(product);
    const semanticText = [
      product.title,
      product.productType,
      product.category?.fullName ?? "",
      sourceSignal.supplierCategory,
      sourceSignal.googleProductCategory,
      sourceSignal.productType,
      ...product.tags,
      ...product.metafields.map((field) => field.value),
    ]
      .join(" ")
      .toLowerCase();

    const rules: TaxonomyRule[] = [
      {
        match: [
          "bathroom vanity",
          "vanity set",
          "makeup vanity",
          "sink cabinet",
          "bathroom sink",
          "single sink vanity",
          "double sink vanity",
          "washstand",
          "vanity",
        ],
        category: "Hardware > Plumbing > Plumbing Fixtures > Sinks",
        googleProductCategory: "Hardware > Plumbing > Plumbing Fixtures > Sinks",
        productType: "Bathroom Vanity",
        supplierCategory: "Bathroom Vanity",
        priority: 120,
      },
      {
        match: [
          "sectional sofa",
          "modular sofa",
          "sofa bed",
          "sleeper sofa",
          "sleeper couch",
          "loveseat sofa",
          "chaise lounge",
          "chaise longue",
          "reclining sofa",
          "boneless sofa",
          "sofa",
          "loveseat",
          "couch",
        ],
        exclude: ["sofa cover", "couch cover", "seat cover"],
        category: "Furniture > Sofas",
        googleProductCategory: "Furniture > Sofas",
        productType: "Sofa",
        supplierCategory: "Sofa",
        priority: 110,
      },
      {
        match: ["chair", "armchair", "dining chair", "barrel chair", "accent chair"],
        category: "Furniture > Chairs",
        googleProductCategory: "Furniture > Chairs",
        productType: "Accent Dining Chair",
        supplierCategory: "Chair",
        priority: 90,
      },
      {
        match: ["bench", "corner bench"],
        category: "Furniture > Benches",
        googleProductCategory: "Furniture > Benches",
        productType: "Corner Bench",
        supplierCategory: "Bench",
        priority: 85,
      },
      {
        match: ["table", "coffee table", "side table"],
        category: "Furniture > Tables",
        googleProductCategory: "Furniture > Tables",
        productType: "Coffee Table",
        supplierCategory: "Table",
        priority: 80,
      },
      {
        match: ["bed", "bed frame", "headboard"],
        category: "Furniture > Beds & Accessories",
        googleProductCategory: "Furniture > Beds & Accessories",
        productType: "Bed Frame",
        supplierCategory: "Bed Frame",
        priority: 70,
      },
      {
        match: [
          "bathroom cabinet",
          "storage cabinet",
          "sideboard",
          "buffet cabinet",
          "dresser",
          "cabinet",
        ],
        exclude: ["vanity", "sink"],
        category: "Furniture > Cabinets & Storage",
        googleProductCategory: "Furniture > Cabinets & Storage",
        productType: "Storage Cabinet",
        supplierCategory: "Cabinet & Storage",
        priority: 60,
      },
      {
        match: ["greenhouse", "polycarbonate panel"],
        category: "Hardware > Building Materials > Glass & Plastic Sheets",
        googleProductCategory: "Hardware > Building Materials > Glass & Plastic Sheets",
        productType: "Polycarbonate Greenhouse Panel",
        supplierCategory: "Greenhouse Panel",
        priority: 50,
      },
    ];

    const matched = rules
      .filter((rule) => {
        const hasMatch = rule.match.some((keyword) => semanticText.includes(keyword));
        if (!hasMatch) {
          return false;
        }

        return !(rule.exclude ?? []).some((keyword) => semanticText.includes(keyword));
      })
      .sort((left, right) => right.priority - left.priority)[0];

    return {
      category:
        matched?.category ??
        sourceSignal.supplierCategory ??
        product.category?.fullName ??
        product.productType,
      googleProductCategory:
        matched?.googleProductCategory ??
        sourceSignal.googleProductCategory ??
        product.category?.fullName ??
        product.productType,
      productType: matched?.productType ?? sourceSignal.productType ?? product.productType,
      supplierCategory:
        matched?.supplierCategory ??
        sourceSignal.supplierCategory ??
        product.category?.fullName ??
        product.productType,
      notes: matched
        ? [`System taxonomy mapped from title/tags to ${matched.productType} with priority ${matched.priority}.`]
        : ["System taxonomy kept current category/productType due to limited evidence."],
    };
  }

  private extractSourceTaxonomySignal(product: ShopifyProductSnapshot): TaxonomySignal {
    const directSupplierCategory =
      product.metafields.find((field) => field.namespace === "geo" && field.key === "supplier_category")
        ?.value ?? "";
    const directGoogleCategory =
      product.metafields.find((field) => field.namespace === "geo" && field.key === "google_product_category")
        ?.value ?? "";

    const sourceSnapshotRaw =
      product.metafields.find((field) => field.namespace === "geo" && field.key === "supplier_source_snapshot")
        ?.value ?? "";

    let snapshot: Record<string, unknown> = {};
    if (sourceSnapshotRaw) {
      try {
        snapshot = JSON.parse(sourceSnapshotRaw) as Record<string, unknown>;
      } catch {
        snapshot = {};
      }
    }

    const supplierCategory =
      directSupplierCategory ||
      this.asText(snapshot.raw_category) ||
      this.asText(snapshot.product_type);
    const googleProductCategory =
      directGoogleCategory || this.asText(snapshot.google_product_category);
    const productType = this.asText(snapshot.product_type) || this.asText(snapshot.raw_category);

    return {
      supplierCategory,
      googleProductCategory,
      productType,
    };
  }

  private asText(value: unknown): string {
    return typeof value === "string" ? value.trim() : "";
  }
}
