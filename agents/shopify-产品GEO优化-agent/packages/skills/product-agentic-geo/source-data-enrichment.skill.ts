import {
  DeepSeekGeoAnalysis,
  EnrichedProductSnapshot,
  ProductGeoScoreSet,
  ShopifyProductSnapshot,
  SupplierSourceType,
} from "../../agents/product-agentic-geo-agent/product-agentic-geo.types.js";
import { DobaProductSourceService } from "../../services/doba-product-source.service.js";
import { GigaProductSourceService } from "../../services/giga-product-source.service.js";
import { ProductDataMergeService } from "../../services/product-data-merge.service.js";
import { SupplierSourceResolverService } from "../../services/supplier-source-resolver.service.js";

export class SourceDataEnrichmentSkill {
  constructor(
    private readonly gigaProductSourceService: GigaProductSourceService,
    private readonly dobaProductSourceService: DobaProductSourceService,
    private readonly supplierSourceResolverService: SupplierSourceResolverService,
    private readonly productDataMergeService: ProductDataMergeService,
  ) {}

  shouldEnrich(
    product: ShopifyProductSnapshot,
    analysis: DeepSeekGeoAnalysis,
    beforeScores: ProductGeoScoreSet,
  ): boolean {
    return (
      beforeScores.geoScore < 75 ||
      beforeScores.catalogScore < 60 ||
      beforeScores.googleMerchantScore < 60 ||
      beforeScores.openAiFeedScore < 60 ||
      product.productType.trim().toLowerCase() === "part" ||
      analysis.missing_fields.some((field) =>
        ["material", "weight", "dimensions", "brand", "vendor", "barcode", "gtin"].some((keyword) =>
          field.toLowerCase().includes(keyword),
        ),
      ) ||
      analysis.risk_flags.some((flag) =>
        ["category", "taxonomy", "source_data_missing", "missing_supplier_specs"].some((keyword) =>
          flag.toLowerCase().includes(keyword),
        ),
      )
    );
  }

  async execute(input: {
    product: ShopifyProductSnapshot;
    analysis: DeepSeekGeoAnalysis;
    beforeScores: ProductGeoScoreSet;
    preferredSourceType: SupplierSourceType;
  }): Promise<EnrichedProductSnapshot | null> {
    const resolution = this.supplierSourceResolverService.resolve(
      input.product,
      input.preferredSourceType,
    );

    if (resolution.sourceType === "UNKNOWN") {
      return null;
    }

    const sourceData =
      resolution.sourceType === "GIGA"
        ? await this.gigaProductSourceService.fetchProductSource(input.product, resolution)
        : await this.dobaProductSourceService.fetchProductSource(input.product, resolution);

    if (!sourceData) {
      return null;
    }

    return this.productDataMergeService.merge(input.product, sourceData, resolution);
  }
}
