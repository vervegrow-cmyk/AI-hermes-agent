export interface FetchWithRetryOptions {
  attempts?: number;
  baseDelayMs?: number;
  retryOnStatuses?: number[];
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function shouldRetryStatus(status: number, retryOnStatuses: number[]): boolean {
  return retryOnStatuses.includes(status) || status >= 500;
}

export async function fetchWithRetry(
  input: string | URL,
  init: RequestInit,
  options: FetchWithRetryOptions = {},
): Promise<Response> {
  const attempts = Math.max(1, options.attempts ?? 3);
  const baseDelayMs = Math.max(100, options.baseDelayMs ?? 800);
  const retryOnStatuses = options.retryOnStatuses ?? [408, 409, 425, 429];

  let lastError: unknown;

  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    try {
      const response = await fetch(input, init);
      if (!shouldRetryStatus(response.status, retryOnStatuses) || attempt === attempts) {
        return response;
      }
      await sleep(baseDelayMs * attempt);
    } catch (error) {
      lastError = error;
      if (attempt === attempts) {
        break;
      }
      await sleep(baseDelayMs * attempt);
    }
  }

  throw lastError instanceof Error ? lastError : new Error(String(lastError));
}
