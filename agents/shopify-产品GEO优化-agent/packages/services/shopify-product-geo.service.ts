import {
  ProductGeoChannelPublicationRecord,
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
import { fetchWithRetry } from "./fetch-retry.service.js";

interface FetchActiveProductsParams {
  limit: number;
}

const SHOPIFY_PRODUCTS_PAGE_SIZE = 250;

interface ShopifyGraphQLResponse {
  data?: Record<string, unknown>;
  errors?: Array<{ message?: string }>;
}

interface TargetChannelDefinition {
  label: string;
  aliases: string[];
}

const TARGET_SALES_CHANNELS: TargetChannelDefinition[] = [
  { label: "在线商店", aliases: ["在线商店", "online store"] },
  { label: "Inbox", aliases: ["inbox"] },
  { label: "Buy Button", aliases: ["buy button"] },
  { label: "Shop", aliases: ["shop"] },
  { label: "GoAffPro Storefront", aliases: ["goaffpro storefront"] },
  { label: "Snapchat Ads", aliases: ["snapchat ads"] },
  { label: "TikTok", aliases: ["tiktok"] },
  { label: "Pinterest", aliases: ["pinterest"] },
  { label: "Facebook & Instagram", aliases: ["facebook & instagram"] },
  { label: "Microsoft Channel", aliases: ["microsoft channel"] },
  { label: "Google & YouTube", aliases: ["google & youtube"] },
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

function firstNonEmpty(...values: Array<string | undefined | null>): string {
  for (const value of values) {
    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
  }
  return "";
}

function normalizeChannelName(value: string): string {
  return value.trim().toLowerCase();
}

function truncateHandle(value: string, maxLength = 255): string {
  return value.length > maxLength ? value.slice(0, maxLength).replace(/-+$/g, "") : value;
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
    this.shopDomain = firstNonEmpty(
      config?.shopDomain,
      process.env.SHOPIFY_SHOP_DOMAIN,
      process.env.SHOPIFY_STORE,
      process.env.SHOPIFY_SHOP,
    );
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

    const collected: ShopifyActiveProductRef[] = [];
    let cursor: string | null = null;
    let hasNextPage = true;

    while (hasNextPage && collected.length < params.limit) {
      const remaining = params.limit - collected.length;
      const first = Math.min(SHOPIFY_PRODUCTS_PAGE_SIZE, remaining);
      const data = await this.query(this.buildActiveProductRefsQuery(), {
        first,
        after: cursor,
        query: "status:active AND published_status:published",
      });

      const products = asRecord(data.products);
      const pageInfo = asRecord(products.pageInfo);
      const pageItems = asArray<{ cursor?: string; node?: Record<string, unknown> }>(products.edges)
        .flatMap((edge) => {
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

      collected.push(...pageItems);
      const edges = asArray<{ cursor?: string }>(products.edges);
      cursor = edges.length > 0 ? asString(edges[edges.length - 1]?.cursor) || null : null;
      hasNextPage = asBoolean(pageInfo.hasNextPage) && Boolean(cursor);
    }

    return collected;
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
    handle?: string;
    descriptionHtml?: string;
    tags?: string[];
    seoTitle?: string;
    seoDescription?: string;
    imageAltUpdates?: ShopifyMediaImage[] | Array<{ id: string; altText: string }>;
    metafields?: ShopifyMetafield[];
  }): Promise<{ writtenFields: string[]; resolvedHandle?: string }> {
    const writtenFields: string[] = [];
    let resolvedHandle = input.handle;

    if (
      input.title !== undefined ||
      input.handle !== undefined ||
      input.descriptionHtml !== undefined ||
      input.tags !== undefined ||
      input.seoTitle !== undefined ||
      input.seoDescription !== undefined
    ) {
      const buildProductPayload = (handleValue?: string) => ({
        id: input.productId,
        ...(input.title !== undefined ? { title: input.title } : {}),
        ...(handleValue !== undefined ? { handle: handleValue } : {}),
        ...(input.descriptionHtml !== undefined ? { descriptionHtml: input.descriptionHtml } : {}),
        ...(input.tags !== undefined ? { tags: input.tags } : {}),
        ...(input.seoTitle !== undefined || input.seoDescription !== undefined
          ? {
              seo: {
                ...(input.seoTitle !== undefined ? { title: input.seoTitle } : {}),
                ...(input.seoDescription !== undefined ? { description: input.seoDescription } : {}),
              },
            }
          : {}),
      });

      const handleCandidates =
        input.handle !== undefined
          ? this.buildHandleCandidates(input.handle, input.productId)
          : [undefined];

      let lastUserErrors: Record<string, unknown>[] = [];
      let succeeded = false;

      for (const handleCandidate of handleCandidates) {
        const data = await this.query(this.buildUpdateProductMutation(), {
          product: buildProductPayload(handleCandidate),
        });
        const updatePayload = asRecord(data.productUpdate);
        const userErrors = this.extractUserErrors(updatePayload);

        if (userErrors.length === 0) {
          resolvedHandle = handleCandidate;
          succeeded = true;
          break;
        }

        lastUserErrors = userErrors;
        if (handleCandidate !== undefined && this.isHandleConflictError(userErrors)) {
          continue;
        }

        this.throwUserErrors(userErrors, "商品字段写回失败");
      }

      if (!succeeded) {
        this.throwUserErrors(lastUserErrors, "商品字段写回失败");
      }

      if (input.title !== undefined) writtenFields.push("title");
      if (resolvedHandle !== undefined) writtenFields.push("handle");
      if (input.descriptionHtml !== undefined) writtenFields.push("description_html");
      if (input.tags !== undefined) writtenFields.push("tags");
      if (input.seoTitle !== undefined) writtenFields.push("seo_title");
      if (input.seoDescription !== undefined) writtenFields.push("seo_description");
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
      resolvedHandle,
    };
  }

  async ensurePublishedToAllChannels(productId: string): Promise<{
    publishedChannelIds: string[];
    publishedChannelNames: string[];
    channelResults: ProductGeoChannelPublicationRecord[];
  }> {
    const statuses = await this.fetchProductPublicationStatuses(productId);
    const availableToPublish = statuses.filter(
      (item) => item.publicationAvailable && !item.isPublished,
    );
    const checkedAt = new Date().toISOString();

    if (availableToPublish.length > 0) {
      const data = await this.query(this.buildPublishToChannelsMutation(), {
        id: productId,
        input: availableToPublish.map((item) => ({
          publicationId: item.id,
        })),
      });

      this.assertUserErrors(asRecord(data.publishablePublish), "销售渠道发布失败");
    }

    const refreshedStatuses = await this.fetchProductPublicationStatuses(productId);
    const newlyPublishedIds = new Set(availableToPublish.map((item) => item.id));
    const channelResults: ProductGeoChannelPublicationRecord[] = refreshedStatuses.map((item) => ({
      id: "",
      shopifyProductId: productId,
      channelName: item.name || item.catalogTitle || item.id,
      publicationId: item.id,
      publishStatus: !item.publicationAvailable
        ? "unavailable"
        : item.isPublished
          ? newlyPublishedIds.has(item.id)
            ? "published"
            : "already_published"
          : "failed",
      failureReason: !item.publicationAvailable
        ? "渠道不存在或不可用"
        : item.isPublished
          ? ""
          : "当前 Shopify 店铺未启用该 publication 或发布失败",
      checkedAt,
    }));

    return {
      publishedChannelIds: availableToPublish.map((item) => item.id),
      publishedChannelNames: availableToPublish.map((item) => item.name || item.catalogTitle || item.id),
      channelResults,
    };
  }

  async alignSalesChannelsToSnapshot(snapshot: ShopifyProductSnapshot): Promise<{
    unpublishedChannelIds: string[];
    unpublishedChannelNames: string[];
  }> {
    const currentStatuses = await this.fetchProductPublicationStatuses(snapshot.id);
    const desiredPublicationIds = new Set(
      snapshot.salesChannels.filter((channel) => channel.isPublished).map((channel) => channel.id),
    );
    const shouldUnpublish = currentStatuses.filter(
      (channel) =>
        channel.publicationAvailable &&
        channel.isPublished &&
        !desiredPublicationIds.has(channel.id),
    );

    if (shouldUnpublish.length === 0) {
      return {
        unpublishedChannelIds: [],
        unpublishedChannelNames: [],
      };
    }

    const data = await this.query(this.buildUnpublishFromChannelsMutation(), {
      id: snapshot.id,
      input: shouldUnpublish.map((item) => ({
        publicationId: item.id,
      })),
    });

    this.assertUserErrors(asRecord(data.publishableUnpublish), "销售渠道回滚失败");

    return {
      unpublishedChannelIds: shouldUnpublish.map((item) => item.id),
      unpublishedChannelNames: shouldUnpublish.map((item) => item.name || item.catalogTitle || item.id),
    };
  }

  async rollbackProductSnapshot(snapshot: ShopifyProductSnapshot): Promise<{
    restoredFields: string[];
    unpublishedChannelNames: string[];
  }> {
    const restoreResult = await this.writeSafeFields({
      productId: snapshot.id,
      title: snapshot.title,
      descriptionHtml: snapshot.descriptionHtml,
      tags: snapshot.tags,
      seoTitle: snapshot.seo.title,
      seoDescription: snapshot.seo.description,
      imageAltUpdates: snapshot.images.map((image) => ({
        id: image.id,
        altText: image.altText,
      })),
      metafields: snapshot.metafields,
    });

    const channelResult = await this.alignSalesChannelsToSnapshot(snapshot);
    return {
      restoredFields: restoreResult.writtenFields,
      unpublishedChannelNames: channelResult.unpublishedChannelNames,
    };
  }

  async fetchProductPublicationStatuses(productId: string): Promise<ShopifyPublication[]> {
    const allPublications = await this.fetchAllPublications();
    const publicationByAlias = new Map<string, ShopifyPublication>();

    for (const publication of allPublications) {
      const possibleAliases = [publication.name, publication.catalogTitle]
        .filter(Boolean)
        .map(normalizeChannelName);

      for (const definition of TARGET_SALES_CHANNELS) {
        if (possibleAliases.some((alias) => definition.aliases.includes(alias))) {
          publicationByAlias.set(definition.label, publication);
        }
      }
    }

    const availablePublications = TARGET_SALES_CHANNELS
      .map((definition) => ({
        definition,
        publication: publicationByAlias.get(definition.label) ?? null,
      }))
      .filter((item) => item.publication !== null) as Array<{
      definition: TargetChannelDefinition;
      publication: ShopifyPublication;
    }>;

    if (availablePublications.length === 0) {
      return TARGET_SALES_CHANNELS.map((definition) => ({
        id: `unavailable:${definition.label}`,
        name: definition.label,
        catalogTitle: definition.label,
        isPublished: false,
        publicationAvailable: false,
      }));
    }

    const aliasMap = availablePublications.map(({ definition, publication }, index) => ({
      alias: `publication_${index}`,
      definition,
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
    const statusMap = new Map<string, ShopifyPublication>();

    for (const { alias, definition, publication } of aliasMap) {
      statusMap.set(definition.label, {
        ...publication,
        name: definition.label,
        catalogTitle: publication.catalogTitle || definition.label,
        isPublished: asBoolean(product[alias]),
        publicationAvailable: true,
      });
    }

    return TARGET_SALES_CHANNELS.map((definition) => {
      const matched = statusMap.get(definition.label);
      if (matched) {
        return matched;
      }

      return {
        id: `unavailable:${definition.label}`,
        name: definition.label,
        catalogTitle: definition.label,
        isPublished: false,
        publicationAvailable: false,
      };
    });
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
        publicationAvailable: true,
      }));
  }

  private async query(query: string, variables: Record<string, unknown>): Promise<Record<string, unknown>> {
    const accessToken = await this.getAccessToken();
    const response = await fetchWithRetry(`https://${this.shopDomain}/admin/api/${this.apiVersion}/graphql.json`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": accessToken,
      },
      body: JSON.stringify({ query, variables }),
    }, { attempts: 4, baseDelayMs: 1000 });

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

      const response = await fetchWithRetry(`https://${this.shopDomain}/admin/oauth/access_token`, {
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
      }, { attempts: 4, baseDelayMs: 1000 });

      if (!response.ok) {
        throw new Error(`Shopify OAuth token request failed: ${response.status} ${await response.text()}`);
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

    const collections: ShopifyCollectionRef[] = asArray<{ node?: Record<string, unknown> }>(collectionsNode.edges)
      .map((edge) => asRecord(edge?.node))
      .filter((item) => asString(item.id).length > 0)
      .map((item) => ({
        id: asString(item.id),
        handle: asString(item.handle),
        title: asString(item.title),
      }));

    const options: ShopifyProductOption[] = asArray<Record<string, unknown>>(node.options).map((option) => ({
      id: asString(option.id),
      name: asString(option.name),
      position: asNumber(option.position),
      values: asArray<Record<string, unknown>>(option.optionValues).map((value) => ({
        id: asString(value.id),
        name: asString(value.name),
      })),
    }));

    const variants: ShopifyProductVariant[] = asArray<{ node?: Record<string, unknown> }>(variantsNode.edges)
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
        selectedOptions: asArray<Record<string, unknown>>(variant.selectedOptions).map((option) => ({
          name: asString(option.name),
          value: asString(option.value),
        })),
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

    const metafields: ShopifyMetafield[] = asArray<{ node?: Record<string, unknown> }>(metafieldsNode.edges)
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
      publishedInStore: salesChannels.some(
        (channel) => channel.name === "在线商店" && channel.isPublished,
      ),
      availableForSale: variants.some((variant) => variant.availableForSale),
      salesChannels,
    };
  }

  private extractUserErrors(payload: Record<string, unknown>): Record<string, unknown>[] {
    return asArray<Record<string, unknown>>(payload.userErrors);
  }

  private isHandleConflictError(userErrors: Record<string, unknown>[]): boolean {
    return userErrors.some((item) => {
      const message = asString(item.message).toLowerCase();
      return message.includes("handle") && (
        message.includes("already in use") ||
        message.includes("must be unique") ||
        message.includes("has already been taken")
      );
    });
  }

  private buildHandleCandidates(handle: string, productId: string): string[] {
    const suffix = productId.split("/").pop()?.slice(-6) || Date.now().toString().slice(-6);
    const base = truncateHandle(handle, 255).replace(/-+$/g, "");
    return [
      base,
      truncateHandle(`${base}-${suffix}`, 255),
      truncateHandle(`${base}-${suffix}-1`, 255),
      truncateHandle(`${base}-${suffix}-2`, 255),
    ];
  }

  private throwUserErrors(userErrors: Record<string, unknown>[], prefix: string): void {
    if (userErrors.length === 0) {
      return;
    }

    const details = userErrors
      .map((item) => asString(item.message) || JSON.stringify(item))
      .join("; ");

    throw new Error(`${prefix}: ${details}`);
  }

  private assertUserErrors(payload: Record<string, unknown>, prefix: string): void {
    this.throwUserErrors(this.extractUserErrors(payload), prefix);
  }

  private buildActiveProductRefsQuery(): string {
    return `
      query ActiveProductRefs($first: Int!, $after: String, $query: String!) {
        products(first: $first, after: $after, query: $query, sortKey: UPDATED_AT) {
          edges {
            cursor
            node {
              id
              title
              handle
            }
          }
          pageInfo {
            hasNextPage
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
          metafields(first: 80) {
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

  private buildUnpublishFromChannelsMutation(): string {
    return `
      mutation UnpublishFromChannels($id: ID!, $input: [PublicationInput!]!) {
        publishableUnpublish(id: $id, input: $input) {
          userErrors {
            field
            message
          }
        }
      }
    `;
  }
}
