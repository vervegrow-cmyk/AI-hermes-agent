import {
  ShopifyActiveProductRef,
  ShopifyCategoryRef,
  ShopifyCollectionRef,
  ShopifyMediaImage,
  ShopifyMetafield,
  ShopifyProductOption,
  ShopifyProductSnapshot,
  ShopifyProductVariant,
  ShopifyPublication,
} from "../agents/product-agentic-geo-agent/product-agentic-geo.types.js";

interface FetchActiveProductsParams {
  limit: number;
}

interface ShopifyGraphQLResponse {
  data?: Record<string, unknown>;
  errors?: Array<{ message?: string }>;
}

const TARGET_SALES_CHANNEL_NAMES = [
  "在线商店",
  "Online Store",
  "Inbox",
  "Buy Button",
  "Shop",
  "GoAffPro Storefront",
  "Snapchat Ads",
  "TikTok",
  "Pinterest",
  "Facebook & Instagram",
  "Microsoft Channel",
  "Google & YouTube",
];

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function asArray<T = unknown>(value: unknown): T[] {
  return Array.isArray(value) ? (value as T[]) : [];
}

function asString(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function asBoolean(value: unknown): boolean {
  return typeof value === "boolean" ? value : false;
}

function asNumber(value: unknown): number {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}

function normalizeChannelName(value: string): string {
  return value.trim().toLowerCase();
}

export class ShopifyProductGeoService {
  private readonly shopDomain: string;
  private readonly adminToken: string;
  private readonly apiVersion: string;
  private readonly clientId: string;
  private readonly clientSecret: string;
  private readonly authMode: string;
  private cachedAccessToken: string | null = null;

  constructor(config?: { shopDomain?: string; adminToken?: string; apiVersion?: string }) {
    this.shopDomain =
      config?.shopDomain ??
      process.env.SHOPIFY_SHOP_DOMAIN ??
      process.env.SHOPIFY_STORE ??
      process.env.SHOPIFY_SHOP ??
      "";
    this.adminToken =
      config?.adminToken ??
      process.env.SHOPIFY_ADMIN_ACCESS_TOKEN ??
      process.env.SHOPIFY_TOKEN ??
      "";
    this.apiVersion = config?.apiVersion ?? process.env.SHOPIFY_API_VERSION ?? "2026-01";
    this.clientId = process.env.SHOPIFY_CLIENT_ID ?? "";
    this.clientSecret = process.env.SHOPIFY_CLIENT_SECRET ?? "";
    this.authMode = (process.env.SHOPIFY_AUTH_MODE ?? "custom_admin_token").trim().toLowerCase();
  }

  async fetchActiveProductRefs(params: FetchActiveProductsParams): Promise<ShopifyActiveProductRef[]> {
    if (!this.shopDomain) {
      throw new Error("Missing Shopify shop domain");
    }

    const data = await this.query(this.buildActiveProductRefsQuery(), {
      first: params.limit,
      query: "status:active AND published_status:published",
    });

    const products = asRecord(data.products);

    return asArray<{ node?: Record<string, unknown> }>(products.edges).flatMap((edge) => {
      const node = asRecord(edge?.node);
      if (!asString(node.id)) {
        return [];
      }

      return [
        {
          id: asString(node.id),
          handle: asString(node.handle),
          title: asString(node.title),
        },
      ];
    });
  }

  async fetchProductById(productId: string): Promise<ShopifyProductSnapshot> {
    const data = await this.query(this.buildProductByIdQuery(), { id: productId });
    const product = asRecord(data.product);

    if (!asString(product.id)) {
      throw new Error(`Shopify product not found: ${productId}`);
    }

    const salesChannels = await this.fetchProductPublicationStatuses(productId);
    return this.mapProductSnapshot(product, salesChannels);
  }

  async writeSafeFields(input: {
    productId: string;
    title?: string;
    descriptionHtml?: string;
    tags?: string[];
    seoTitle?: string;
    seoDescription?: string;
    imageAltUpdates?: ShopifyMediaImage[] | Array<{ id: string; altText: string }>;
    metafields?: ShopifyMetafield[];
  }): Promise<{ writtenFields: string[] }> {
    const writtenFields: string[] = [];

    if (
      input.title !== undefined ||
      input.descriptionHtml !== undefined ||
      input.tags !== undefined ||
      input.seoTitle !== undefined ||
      input.seoDescription !== undefined
    ) {
      const data = await this.query(this.buildUpdateProductMutation(), {
        product: {
          id: input.productId,
          ...(input.title !== undefined ? { title: input.title } : {}),
          ...(input.descriptionHtml !== undefined
            ? { descriptionHtml: input.descriptionHtml }
            : {}),
          ...(input.tags !== undefined ? { tags: input.tags } : {}),
          ...(input.seoTitle !== undefined || input.seoDescription !== undefined
            ? {
                seo: {
                  ...(input.seoTitle !== undefined ? { title: input.seoTitle } : {}),
                  ...(input.seoDescription !== undefined
                    ? { description: input.seoDescription }
                    : {}),
                },
              }
            : {}),
        },
      });

      this.assertUserErrors(asRecord(data.productUpdate), "商品字段写回失败");

      if (input.title !== undefined) {
        writtenFields.push("title");
      }
      if (input.descriptionHtml !== undefined) {
        writtenFields.push("description_html");
      }
      if (input.tags !== undefined) {
        writtenFields.push("tags");
      }
      if (input.seoTitle !== undefined) {
        writtenFields.push("seo_title");
      }
      if (input.seoDescription !== undefined) {
        writtenFields.push("seo_description");
      }
    }

    if (input.imageAltUpdates && input.imageAltUpdates.length > 0) {
      const files = input.imageAltUpdates
        .map((image) => ({
          id: image.id,
          alt: "altText" in image ? image.altText : "",
        }))
        .filter((image) => image.id);

      if (files.length > 0) {
        const data = await this.query(this.buildUpdateImageAltMutation(), { files });
        this.assertUserErrors(asRecord(data.fileUpdate), "图片 Alt 写回失败");
        writtenFields.push("image_alt");
      }
    }

    if (input.metafields && input.metafields.length > 0) {
      const metafields = input.metafields
        .filter((field) => field.namespace && field.key && field.type)
        .map((field) => ({
          ownerId: input.productId,
          namespace: field.namespace,
          key: field.key,
          type: field.type,
          value: field.value,
        }));

      if (metafields.length > 0) {
        const data = await this.query(this.buildMetafieldsSetMutation(), { metafields });
        this.assertUserErrors(asRecord(data.metafieldsSet), "Metafields 写回失败");
        writtenFields.push("metafields");
      }
    }

    return {
      writtenFields: [...new Set(writtenFields)],
    };
  }

  async ensurePublishedToAllChannels(productId: string): Promise<{
    publishedChannelIds: string[];
    publishedChannelNames: string[];
  }> {
    const statuses = await this.fetchProductPublicationStatuses(productId);
    const unpublished = statuses.filter((item) => !item.isPublished);

    if (unpublished.length === 0) {
      return {
        publishedChannelIds: [],
        publishedChannelNames: [],
      };
    }

    const data = await this.query(this.buildPublishToChannelsMutation(), {
      id: productId,
      input: unpublished.map((item) => ({
        publicationId: item.id,
      })),
    });

    this.assertUserErrors(asRecord(data.publishablePublish), "销售渠道发布失败");

    return {
      publishedChannelIds: unpublished.map((item) => item.id),
      publishedChannelNames: unpublished.map((item) => item.name || item.catalogTitle || item.id),
    };
  }

  async fetchProductPublicationStatuses(productId: string): Promise<ShopifyPublication[]> {
    const targetPublications = await this.fetchTargetPublications();

    if (targetPublications.length === 0) {
      throw new Error("未找到任何目标销售渠道，请先确认商店已经启用这些销售渠道。");
    }

    const aliasMap = targetPublications.map((publication, index) => ({
      alias: `publication_${index}`,
      publication,
    }));

    const query = `
      query ProductPublicationStatuses($id: ID!) {
        product(id: $id) {
          id
          ${aliasMap
            .map(
              ({ alias, publication }) =>
                `${alias}: publishedOnPublication(publicationId: "${publication.id}")`,
            )
            .join("\n          ")}
        }
      }
    `;

    const data = await this.query(query, { id: productId });
    const product = asRecord(data.product);

    return aliasMap.map(({ alias, publication }) => ({
      ...publication,
      isPublished: asBoolean(product[alias]),
    }));
  }

  private async fetchTargetPublications(): Promise<ShopifyPublication[]> {
    const allPublications = await this.fetchAllPublications();
    const desiredNames = new Set(TARGET_SALES_CHANNEL_NAMES.map(normalizeChannelName));

    const matched = allPublications.filter((publication) => {
      const displayNames = [publication.name, publication.catalogTitle]
        .filter(Boolean)
        .map(normalizeChannelName);

      return displayNames.some((item) => desiredNames.has(item));
    });

    if (matched.length === 0) {
      throw new Error("未匹配到目标销售渠道，请检查 Publication 查询结果和渠道名称。");
    }

    return matched;
  }

  private async fetchAllPublications(): Promise<ShopifyPublication[]> {
    const data = await this.query(this.buildPublicationsQuery(), { first: 100 });
    const publications = asRecord(data.publications);

    return asArray<{ node?: Record<string, unknown> }>(publications.edges)
      .map((edge) => asRecord(edge?.node))
      .filter((item) => asString(item.id).length > 0)
      .map((item) => ({
        id: asString(item.id),
        name: asString(item.name),
        catalogTitle: asString(asRecord(item.catalog).title),
        isPublished: false,
      }));
  }

  private async query(query: string, variables: Record<string, unknown>): Promise<Record<string, unknown>> {
    const accessToken = await this.getAccessToken();
    const response = await fetch(
      `https://${this.shopDomain}/admin/api/${this.apiVersion}/graphql.json`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Shopify-Access-Token": accessToken,
        },
        body: JSON.stringify({ query, variables }),
      },
    );

    if (!response.ok) {
      throw new Error(`Shopify GraphQL request failed: ${response.status} ${await response.text()}`);
    }

    const payload = (await response.json()) as ShopifyGraphQLResponse;
    if (payload.errors?.length) {
      throw new Error(
        `Shopify GraphQL returned errors: ${payload.errors
          .map((error) => error.message ?? "unknown")
          .join("; ")}`,
      );
    }

    return asRecord(payload.data);
  }

  private async getAccessToken(): Promise<string> {
    if (this.adminToken) {
      return this.adminToken;
    }

    if (this.cachedAccessToken) {
      return this.cachedAccessToken;
    }

    if (this.authMode === "client_credentials") {
      if (!this.clientId || !this.clientSecret) {
        throw new Error("Missing Shopify OAuth client credentials");
      }

      const response = await fetch(`https://${this.shopDomain}/admin/oauth/access_token`, {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({
          client_id: this.clientId,
          client_secret: this.clientSecret,
          grant_type: "client_credentials",
        }),
      });

      if (!response.ok) {
        throw new Error(
          `Shopify OAuth token request failed: ${response.status} ${await response.text()}`,
        );
      }

      const payload = asRecord(await response.json());
      const accessToken = asString(payload.access_token);

      if (!accessToken) {
        throw new Error("Shopify OAuth token response missing access_token");
      }

      this.cachedAccessToken = accessToken;
      return accessToken;
    }

    throw new Error(
      "Missing Shopify admin access token. Current configuration also does not yield a client_credentials OAuth token.",
    );
  }

  private mapProductSnapshot(
    node: Record<string, unknown>,
    salesChannels: ShopifyPublication[],
  ): ShopifyProductSnapshot {
    const seo = asRecord(node.seo);
    const category = asRecord(node.category);
    const collectionsNode = asRecord(node.collections);
    const variantsNode = asRecord(node.variants);
    const metafieldsNode = asRecord(node.metafields);
    const mediaNode = asRecord(node.media);

    const collections: ShopifyCollectionRef[] = asArray<{ node?: Record<string, unknown> }>(
      collectionsNode.edges,
    )
      .map((edge) => asRecord(edge?.node))
      .filter((item) => asString(item.id).length > 0)
      .map((item) => ({
        id: asString(item.id),
        handle: asString(item.handle),
        title: asString(item.title),
      }));

    const options: ShopifyProductOption[] = asArray<Record<string, unknown>>(node.options).map(
      (option) => ({
        id: asString(option.id),
        name: asString(option.name),
        position: asNumber(option.position),
        values: asArray<Record<string, unknown>>(option.optionValues).map((value) => ({
          id: asString(value.id),
          name: asString(value.name),
        })),
      }),
    );

    const variants: ShopifyProductVariant[] = asArray<{ node?: Record<string, unknown> }>(
      variantsNode.edges,
    )
      .map((edge) => asRecord(edge?.node))
      .filter((item) => asString(item.id).length > 0)
      .map((variant) => ({
        id: asString(variant.id),
        title: asString(variant.title),
        sku: asString(variant.sku),
        barcode: asString(variant.barcode),
        price: asString(variant.price),
        compareAtPrice: asString(variant.compareAtPrice),
        inventoryQuantity: asNumber(variant.inventoryQuantity),
        availableForSale: asBoolean(variant.availableForSale),
        selectedOptions: asArray<Record<string, unknown>>(variant.selectedOptions).map(
          (option) => ({
            name: asString(option.name),
            value: asString(option.value),
          }),
        ),
      }));

    const images: ShopifyMediaImage[] = asArray<{ node?: Record<string, unknown> }>(mediaNode.edges)
      .map((edge) => asRecord(edge?.node))
      .filter((item) => asString(item.id).length > 0)
      .map((image, index) => ({
        id: asString(image.id),
        url: asString(asRecord(image.image).url),
        altText: asString(asRecord(image.image).altText),
        mediaContentType: asString(image.mediaContentType),
        position: index + 1,
      }));

    const metafields: ShopifyMetafield[] = asArray<{ node?: Record<string, unknown> }>(
      metafieldsNode.edges,
    )
      .map((edge) => asRecord(edge?.node))
      .filter((item) => asString(item.key).length > 0)
      .map((field) => ({
        namespace: asString(field.namespace),
        key: asString(field.key),
        type: asString(field.type),
        value: asString(field.value),
      }));

    const categoryRef: ShopifyCategoryRef | null = asString(category.id)
      ? {
          id: asString(category.id),
          fullName: asString(category.fullName),
        }
      : null;

    return {
      id: asString(node.id),
      title: asString(node.title),
      handle: asString(node.handle),
      status: asString(node.status),
      vendor: asString(node.vendor),
      productType: asString(node.productType),
      tags: asArray<string>(node.tags).filter((tag): tag is string => typeof tag === "string"),
      descriptionHtml: asString(node.descriptionHtml),
      seo: {
        title: asString(seo.title),
        description: asString(seo.description),
      },
      options,
      variants,
      images,
      metafields,
      category: categoryRef,
      collections,
      publishedInStore: true,
      availableForSale: variants.some((variant) => variant.availableForSale),
      salesChannels,
    };
  }

  private assertUserErrors(payload: Record<string, unknown>, prefix: string): void {
    const userErrors = asArray<Record<string, unknown>>(payload.userErrors);
    if (userErrors.length === 0) {
      return;
    }

    const details = userErrors
      .map((item) => asString(item.message) || JSON.stringify(item))
      .join("; ");

    throw new Error(`${prefix}: ${details}`);
  }

  private buildActiveProductRefsQuery(): string {
    return `
      query ActiveProductRefs($first: Int!, $query: String!) {
        products(first: $first, query: $query, sortKey: UPDATED_AT) {
          edges {
            node {
              id
              title
              handle
            }
          }
        }
      }
    `;
  }

  private buildProductByIdQuery(): string {
    return `
      query ProductById($id: ID!) {
        product(id: $id) {
          id
          title
          handle
          status
          vendor
          productType
          tags
          descriptionHtml
          seo {
            title
            description
          }
          category {
            id
            fullName
          }
          collections(first: 20) {
            edges {
              node {
                id
                handle
                title
              }
            }
          }
          options {
            id
            name
            position
            optionValues {
              id
              name
            }
          }
          variants(first: 50) {
            edges {
              node {
                id
                title
                sku
                barcode
                price
                compareAtPrice
                inventoryQuantity
                availableForSale
                selectedOptions {
                  name
                  value
                }
              }
            }
          }
          media(first: 20) {
            edges {
              node {
                ... on MediaImage {
                  id
                  mediaContentType
                  image {
                    url
                    altText
                  }
                }
              }
            }
          }
          metafields(first: 50) {
            edges {
              node {
                namespace
                key
                type
                value
              }
            }
          }
        }
      }
    `;
  }

  private buildPublicationsQuery(): string {
    return `
      query Publications($first: Int!) {
        publications(first: $first) {
          edges {
            node {
              id
              name
              catalog {
                ... on AppCatalog {
                  title
                }
              }
            }
          }
        }
      }
    `;
  }

  private buildUpdateProductMutation(): string {
    return `
      mutation UpdateProduct($product: ProductUpdateInput!) {
        productUpdate(product: $product) {
          product {
            id
            title
            descriptionHtml
            tags
            seo {
              title
              description
            }
          }
          userErrors {
            field
            message
          }
        }
      }
    `;
  }

  private buildUpdateImageAltMutation(): string {
    return `
      mutation UpdateFileAlt($files: [FileUpdateInput!]!) {
        fileUpdate(files: $files) {
          files {
            id
          }
          userErrors {
            field
            message
          }
        }
      }
    `;
  }

  private buildMetafieldsSetMutation(): string {
    return `
      mutation SetProductMetafields($metafields: [MetafieldsSetInput!]!) {
        metafieldsSet(metafields: $metafields) {
          metafields {
            key
            namespace
          }
          userErrors {
            field
            message
          }
        }
      }
    `;
  }

  private buildPublishToChannelsMutation(): string {
    return `
      mutation PublishToChannels($id: ID!, $input: [PublicationInput!]!) {
        publishablePublish(id: $id, input: $input) {
          publishable {
            ... on Product {
              id
            }
          }
          userErrors {
            field
            message
          }
        }
      }
    `;
  }
}
