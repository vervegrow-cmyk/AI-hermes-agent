import { randomUUID } from "node:crypto";

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

export class ProductGeoSnapshotRepository {
  readonly snapshots: ProductGeoWritebackSnapshotRecord[] = [];

  async createBeforeSnapshot(product: ShopifyProductSnapshot): Promise<ProductGeoWritebackSnapshotRecord> {
    const now = new Date().toISOString();
    const record: ProductGeoWritebackSnapshotRecord = {
      id: randomUUID(),
      shopifyProductId: product.id,
      beforePayload: product as unknown as Record<string, unknown>,
      afterPayload: {},
      changedFields: [],
      writebackStatus: "preview_only",
      rollbackStatus: "not_rolled_back",
      createdAt: now,
      updatedAt: now,
    };
    this.snapshots.push(record);
    return record;
  }

  async attachAfterSnapshot(input: {
    snapshotId: string;
    afterPayload: Record<string, unknown>;
    changedFields: string[];
    writebackStatus?: ProductGeoWritebackSnapshotRecord["writebackStatus"];
  }): Promise<ProductGeoWritebackSnapshotRecord> {
    const snapshot = this.snapshots.find((item) => item.id === input.snapshotId);
    if (!snapshot) {
      throw new Error(`Snapshot not found: ${input.snapshotId}`);
    }
    snapshot.afterPayload = input.afterPayload;
    snapshot.changedFields = input.changedFields;
    if (input.writebackStatus) {
      snapshot.writebackStatus = input.writebackStatus;
    }
    snapshot.updatedAt = new Date().toISOString();
    return snapshot;
  }
}
