import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { config as loadDotenv } from "dotenv";
import { configureConsoleEncoding } from "./console-encoding.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, "../../..");
const parentRoot = path.resolve(projectRoot, "../..");

function loadEnvFile(filePath: string, override: boolean): void {
  if (!existsSync(filePath)) {
    return;
  }

  loadDotenv({
    path: filePath,
    override,
  });
}

export function bootstrapEnv(): void {
  configureConsoleEncoding();

  const parentEnvPath = path.join(parentRoot, ".env");
  const localEnvPath = path.join(projectRoot, ".env");
  const localOverrideEnvPath = path.join(projectRoot, ".env.local");

  loadEnvFile(parentEnvPath, false);
  loadEnvFile(localEnvPath, true);
  loadEnvFile(localOverrideEnvPath, true);
}
