import {
  ProductGeoChannelPublicationRecord,
  ProductSafeWritebackPlan,
  ProductWritebackResult,
} from "../../agents/product-agentic-geo-agent/product-agentic-geo.types.js";
import { ShopifyProductGeoService } from "../../services/shopify-product-geo.service.js";

export class ProductGEOWriteBackSkill {
  constructor(private readonly shopifyProductGeoService: ShopifyProductGeoService) {}

  async execute(input: {
    productId: string;
    plan: ProductSafeWritebackPlan;
    dryRun: boolean;
  }): Promise<ProductWritebackResult> {
    const previewChannelNames = input.plan.salesChannelsToPublish.map(
      (item) => item.name || item.catalogTitle || item.id,
    );

    if (input.dryRun) {
      const checkedAt = new Date().toISOString();
      const channelResults: ProductGeoChannelPublicationRecord[] = input.plan.salesChannelsToPublish.map(
        (item) => ({
          id: "",
          shopifyProductId: input.productId,
          channelName: item.name || item.catalogTitle || item.id,
          publicationId: item.id,
          publishStatus: "published",
          failureReason: "",
          checkedAt,
        }),
      );

      return {
        attempted: true,
        dryRun: true,
        status: "preview_only",
        fieldsWritten: [
          ...input.plan.fieldsToWrite,
          ...(previewChannelNames.length > 0 ? ["sales_channels"] : []),
        ],
        resolvedHandle: input.plan.handle,
        blockedFields: [...input.plan.blockedFields],
        summaryLines: [
          `Dry Run 模式，预览写回字段: ${input.plan.fieldsToWrite.join("、") || "无"}`,
          `Dry Run 模式，预览补发布销售渠道: ${previewChannelNames.join("、") || "无"}`,
        ],
        publishedChannelIds: input.plan.salesChannelsToPublish.map((item) => item.id),
        publishedChannelNames: previewChannelNames,
        channelResults,
      };
    }

    const response = await this.shopifyProductGeoService.writeSafeFields({
      productId: input.productId,
      title: input.plan.title,
      handle: input.plan.handle,
      descriptionHtml: input.plan.descriptionHtml,
      tags: input.plan.tags,
      seoTitle: input.plan.seoTitle,
      seoDescription: input.plan.seoDescription,
      imageAltUpdates: input.plan.imageAltUpdates.map((item) => ({
        id: item.image_id,
        altText: item.alt,
      })),
      metafields: input.plan.metafields,
    });

    const publicationResult = await this.shopifyProductGeoService.ensurePublishedToAllChannels(
      input.productId,
    );

    const fieldsWritten = [...response.writtenFields];
    if (publicationResult.publishedChannelNames.length > 0) {
      fieldsWritten.push("sales_channels");
    }

    return {
      attempted: true,
      dryRun: false,
      status: "written",
      fieldsWritten: [...new Set(fieldsWritten)],
      resolvedHandle: response.resolvedHandle,
      blockedFields: [...input.plan.blockedFields],
      summaryLines: [
        `成功写回字段: ${response.writtenFields.join("、") || "无"}`,
        `新增销售渠道: ${publicationResult.publishedChannelNames.join("、") || "无"}`,
      ],
      publishedChannelIds: publicationResult.publishedChannelIds,
      publishedChannelNames: publicationResult.publishedChannelNames,
      channelResults: publicationResult.channelResults,
    };
  }
}
