import { randomUUID } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

import {
  ProductGeoWritebackSnapshotRecord,
  ShopifyProductSnapshot,
} from "../agents/product-agentic-geo-agent/product-agentic-geo.types.js";

export const PRODUCT_GEO_WRITEBACK_SNAPSHOTS_TABLE_SQL = `
CREATE TABLE product_geo_writeback_snapshots (
  id UUID PRIMARY KEY,
  shopify_product_id TEXT NOT NULL,
  before_payload_json JSONB NOT NULL,
  after_payload_json JSONB NOT NULL,
  changed_fields_json JSONB NOT NULL,
  writeback_status TEXT,
  rollback_status TEXT DEFAULT 'not_rolled_back',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);`;

interface SnapshotStore {
  snapshots: ProductGeoWritebackSnapshotRecord[];
}

const MAX_PERSISTED_SNAPSHOTS = 200;

function compactSnapshotValue(
  value: unknown,
  options: {
    maxDepth?: number;
    maxKeys?: number;
    maxItems?: number;
    maxStringLength?: number;
  } = {},
): unknown {
  const maxDepth = options.maxDepth ?? 4;
  const maxKeys = options.maxKeys ?? 25;
  const maxItems = options.maxItems ?? 20;
  const maxStringLength = options.maxStringLength ?? 500;
  const seen = new WeakSet<object>();

  const truncate = (input: string): string =>
    input.length > maxStringLength ? `${input.slice(0, maxStringLength)}...` : input;

  const visit = (input: unknown, depth: number): unknown => {
    if (input == null) {
      return input;
    }

    if (typeof input === "string") {
      return truncate(input);
    }

    if (typeof input === "number" || typeof input === "boolean") {
      return input;
    }

    if (depth >= maxDepth) {
      if (Array.isArray(input)) {
        return input.length > 0 ? ["[truncated]"] : [];
      }
      return "[truncated]";
    }

    if (Array.isArray(input)) {
      return input.slice(0, maxItems).map((item) => visit(item, depth + 1));
    }

    if (typeof input === "object") {
      if (seen.has(input)) {
        return "[circular]";
      }
      seen.add(input);

      return Object.fromEntries(
        Object.entries(input)
          .slice(0, maxKeys)
          .map(([key, nested]) => [key, visit(nested, depth + 1)]),
      );
    }

    return String(input);
  };

  return visit(value, 0);
}

export class ProductGeoSnapshotRepository {
  readonly snapshots: ProductGeoWritebackSnapshotRecord[] = [];

  private readonly dataDir = path.resolve(process.cwd(), "runtime-data");
  private readonly storePath = path.join(this.dataDir, "product-geo-snapshots.json");
  private loaded = false;

  async createBeforeSnapshot(
    product: ShopifyProductSnapshot,
  ): Promise<ProductGeoWritebackSnapshotRecord> {
    await this.load();

    const now = new Date().toISOString();
    const record: ProductGeoWritebackSnapshotRecord = {
      id: randomUUID(),
      shopifyProductId: product.id,
      beforePayload: compactSnapshotValue(product as unknown as Record<string, unknown>, {
        maxDepth: 4,
        maxKeys: 30,
        maxItems: 20,
        maxStringLength: 600,
      }) as Record<string, unknown>,
      afterPayload: {},
      changedFields: [],
      writebackStatus: "preview_only",
      rollbackStatus: "not_rolled_back",
      createdAt: now,
      updatedAt: now,
    };

    this.snapshots.push(record);
    await this.persist();
    return record;
  }

  async attachAfterSnapshot(input: {
    snapshotId: string;
    afterPayload: Record<string, unknown>;
    changedFields: string[];
    writebackStatus?: ProductGeoWritebackSnapshotRecord["writebackStatus"];
  }): Promise<ProductGeoWritebackSnapshotRecord> {
    await this.load();

    const snapshot = this.snapshots.find((item) => item.id === input.snapshotId);
    if (!snapshot) {
      throw new Error(`Snapshot not found: ${input.snapshotId}`);
    }

    snapshot.afterPayload = compactSnapshotValue(input.afterPayload, {
      maxDepth: 4,
      maxKeys: 30,
      maxItems: 20,
      maxStringLength: 600,
    }) as Record<string, unknown>;
    snapshot.changedFields = [...input.changedFields];
    if (input.writebackStatus) {
      snapshot.writebackStatus = input.writebackStatus;
    }
    snapshot.updatedAt = new Date().toISOString();

    await this.persist();
    return snapshot;
  }

  async getSnapshot(snapshotId: string): Promise<ProductGeoWritebackSnapshotRecord | null> {
    await this.load();
    return this.snapshots.find((item) => item.id === snapshotId) ?? null;
  }

  async getLatestSnapshotByProductId(
    shopifyProductId: string,
  ): Promise<ProductGeoWritebackSnapshotRecord | null> {
    await this.load();
    return (
      this.snapshots
        .filter((item) => item.shopifyProductId === shopifyProductId)
        .sort((left, right) => right.createdAt.localeCompare(left.createdAt))[0] ?? null
    );
  }

  async markRolledBack(
    snapshotId: string,
    rollbackStatus: ProductGeoWritebackSnapshotRecord["rollbackStatus"],
  ): Promise<ProductGeoWritebackSnapshotRecord> {
    await this.load();

    const snapshot = this.snapshots.find((item) => item.id === snapshotId);
    if (!snapshot) {
      throw new Error(`Snapshot not found: ${snapshotId}`);
    }

    snapshot.rollbackStatus = rollbackStatus;
    snapshot.updatedAt = new Date().toISOString();
    await this.persist();
    return snapshot;
  }

  private async load(): Promise<void> {
    if (this.loaded) {
      return;
    }

    await mkdir(this.dataDir, { recursive: true });

    try {
      const raw = await readFile(this.storePath, "utf8");
      const parsed = JSON.parse(raw) as Partial<SnapshotStore>;
      this.snapshots.push(
        ...(parsed.snapshots ?? []).map((snapshot) => this.normalizeSnapshot(snapshot)),
      );
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      if (!message.includes("ENOENT")) {
        throw error;
      }
      await this.persist();
    }

    this.loaded = true;
  }

  private async persist(): Promise<void> {
    await mkdir(this.dataDir, { recursive: true });
    const store: SnapshotStore = {
      snapshots: this.snapshots
        .map((snapshot) => this.normalizeSnapshot(snapshot))
        .sort((left, right) => right.updatedAt.localeCompare(left.updatedAt))
        .slice(0, MAX_PERSISTED_SNAPSHOTS),
    };
    this.snapshots.length = 0;
    this.snapshots.push(...store.snapshots);
    await writeFile(this.storePath, JSON.stringify(store, null, 2), "utf8");
  }

  private normalizeSnapshot(
    snapshot: ProductGeoWritebackSnapshotRecord,
  ): ProductGeoWritebackSnapshotRecord {
    return {
      ...snapshot,
      beforePayload: compactSnapshotValue(snapshot.beforePayload, {
        maxDepth: 4,
        maxKeys: 30,
        maxItems: 20,
        maxStringLength: 600,
      }) as Record<string, unknown>,
      afterPayload: compactSnapshotValue(snapshot.afterPayload, {
        maxDepth: 4,
        maxKeys: 30,
        maxItems: 20,
        maxStringLength: 600,
      }) as Record<string, unknown>,
      changedFields: [...(snapshot.changedFields ?? [])].slice(0, 50),
    };
  }
}
