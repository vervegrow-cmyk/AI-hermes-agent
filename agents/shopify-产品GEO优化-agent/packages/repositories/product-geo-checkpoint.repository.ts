import { randomUUID } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

import {
  ProductGeoProductCheckpointRecord,
  ProductGeoRunRecord,
} from "../agents/product-agentic-geo-agent/product-agentic-geo.types.js";

interface CheckpointStore {
  runs: ProductGeoRunRecord[];
  productCheckpoints: ProductGeoProductCheckpointRecord[];
}

export class ProductGeoCheckpointRepository {
  readonly runs: ProductGeoRunRecord[] = [];
  readonly productCheckpoints: ProductGeoProductCheckpointRecord[] = [];

  private readonly dataDir = path.resolve(process.cwd(), "runtime-data");
  private readonly storePath = path.join(this.dataDir, "product-geo-checkpoints.json");
  private loaded = false;

  async createRun(input: Omit<ProductGeoRunRecord, "id" | "updatedAt">): Promise<ProductGeoRunRecord> {
    await this.load();
    const record: ProductGeoRunRecord = {
      id: randomUUID(),
      ...input,
      updatedAt: new Date().toISOString(),
    };
    this.runs.push(record);
    await this.persist();
    return record;
  }

  async updateRun(
    runId: string,
    patch: Partial<Omit<ProductGeoRunRecord, "id">>,
  ): Promise<ProductGeoRunRecord | null> {
    await this.load();
    const index = this.runs.findIndex((item) => item.id === runId);
    if (index < 0) return null;
    this.runs[index] = {
      ...this.runs[index],
      ...patch,
      updatedAt: new Date().toISOString(),
    };
    await this.persist();
    return this.runs[index];
  }

  async getRun(runId: string): Promise<ProductGeoRunRecord | null> {
    await this.load();
    return this.runs.find((item) => item.id === runId) ?? null;
  }

  async getLatestResumableRun(): Promise<ProductGeoRunRecord | null> {
    await this.load();
    return (
      [...this.runs]
        .filter((item) => item.resumeEnabled && item.status !== "RUN_COMPLETED")
        .sort((a, b) => b.updatedAt.localeCompare(a.updatedAt))[0] ?? null
    );
  }

  async getLatestRun(): Promise<ProductGeoRunRecord | null> {
    await this.load();
    return [...this.runs].sort((a, b) => b.updatedAt.localeCompare(a.updatedAt))[0] ?? null;
  }

  async upsertProductCheckpoint(
    input: Omit<ProductGeoProductCheckpointRecord, "id" | "updatedAt">,
  ): Promise<ProductGeoProductCheckpointRecord> {
    await this.load();
    const index = this.productCheckpoints.findIndex(
      (item) => item.runId === input.runId && item.shopifyProductId === input.shopifyProductId,
    );
    if (index >= 0) {
      this.productCheckpoints[index] = {
        ...this.productCheckpoints[index],
        ...input,
        updatedAt: new Date().toISOString(),
      };
      await this.persist();
      return this.productCheckpoints[index];
    }

    const record: ProductGeoProductCheckpointRecord = {
      id: randomUUID(),
      ...input,
      updatedAt: new Date().toISOString(),
    };
    this.productCheckpoints.push(record);
    await this.persist();
    return record;
  }

  async getProductCheckpointsByRunId(runId: string): Promise<ProductGeoProductCheckpointRecord[]> {
    await this.load();
    return this.productCheckpoints
      .filter((item) => item.runId === runId)
      .sort((a, b) => a.productIndex - b.productIndex);
  }

  async getProductCheckpoint(
    runId: string,
    shopifyProductId: string,
  ): Promise<ProductGeoProductCheckpointRecord | null> {
    await this.load();
    return (
      this.productCheckpoints.find(
        (item) => item.runId === runId && item.shopifyProductId === shopifyProductId,
      ) ?? null
    );
  }

  async resetIncompleteRuns(): Promise<number> {
    await this.load();
    const targets = this.runs.filter((item) => item.status !== "RUN_COMPLETED");
    for (const run of targets) {
      run.resumeEnabled = false;
      run.status = "RUN_FAILED";
      run.finishedAt = run.finishedAt || new Date().toISOString();
      run.updatedAt = new Date().toISOString();
    }
    await this.persist();
    return targets.length;
  }

  private async load(): Promise<void> {
    if (this.loaded) return;
    await mkdir(this.dataDir, { recursive: true });
    try {
      const raw = await readFile(this.storePath, "utf8");
      const parsed = JSON.parse(raw) as Partial<CheckpointStore>;
      this.runs.push(...(parsed.runs ?? []));
      this.productCheckpoints.push(...(parsed.productCheckpoints ?? []));
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      if (!message.includes("ENOENT")) throw error;
      await this.persist();
    }
    this.loaded = true;
  }

  private async persist(): Promise<void> {
    await mkdir(this.dataDir, { recursive: true });
    await writeFile(
      this.storePath,
      JSON.stringify(
        {
          runs: this.runs,
          productCheckpoints: this.productCheckpoints,
        } satisfies CheckpointStore,
        null,
        2,
      ),
      "utf8",
    );
  }
}
