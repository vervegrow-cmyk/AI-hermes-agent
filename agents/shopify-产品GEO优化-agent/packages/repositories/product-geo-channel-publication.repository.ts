import { randomUUID } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

import { ProductGeoChannelPublicationRecord } from "../agents/product-agentic-geo-agent/product-agentic-geo.types.js";

interface ChannelPublicationStore {
  records: ProductGeoChannelPublicationRecord[];
}

export class ProductGeoChannelPublicationRepository {
  readonly records: ProductGeoChannelPublicationRecord[] = [];

  private readonly dataDir = path.resolve(process.cwd(), "runtime-data");
  private readonly storePath = path.join(this.dataDir, "product-geo-channel-publications.json");
  private loaded = false;

  async saveMany(
    input: Array<Omit<ProductGeoChannelPublicationRecord, "id">>,
  ): Promise<ProductGeoChannelPublicationRecord[]> {
    await this.load();

    const records = input.map((item) => ({
      id: randomUUID(),
      ...item,
    }));

    this.records.push(...records);
    await this.persist();
    return records;
  }

  private async load(): Promise<void> {
    if (this.loaded) {
      return;
    }

    await mkdir(this.dataDir, { recursive: true });

    try {
      const raw = await readFile(this.storePath, "utf8");
      const parsed = JSON.parse(raw) as Partial<ChannelPublicationStore>;
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
