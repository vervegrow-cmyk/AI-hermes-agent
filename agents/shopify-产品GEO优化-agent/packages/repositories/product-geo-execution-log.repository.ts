import { randomUUID } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

import { ProductGeoExecutionLogRecord } from "../agents/product-agentic-geo-agent/product-agentic-geo.types.js";

interface ExecutionLogStore {
  records: ProductGeoExecutionLogRecord[];
}

export class ProductGeoExecutionLogRepository {
  readonly records: ProductGeoExecutionLogRecord[] = [];

  private readonly dataDir = path.resolve(process.cwd(), "runtime-data");
  private readonly storePath = path.join(this.dataDir, "product-geo-execution-logs.json");
  private loaded = false;

  async save(input: Omit<ProductGeoExecutionLogRecord, "id" | "createdAt">): Promise<ProductGeoExecutionLogRecord> {
    await this.load();

    const record: ProductGeoExecutionLogRecord = {
      id: randomUUID(),
      createdAt: new Date().toISOString(),
      ...input,
    };

    this.records.push(record);
    await this.persist();
    return record;
  }

  private async load(): Promise<void> {
    if (this.loaded) {
      return;
    }

    await mkdir(this.dataDir, { recursive: true });

    try {
      const raw = await readFile(this.storePath, "utf8");
      const parsed = JSON.parse(raw) as Partial<ExecutionLogStore>;
      this.records.push(...(parsed.records ?? []));
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
    await writeFile(
      this.storePath,
      JSON.stringify({ records: this.records }, null, 2),
      "utf8",
    );
  }
}
