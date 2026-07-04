import { Redis } from "@upstash/redis";

// Upstash Redis over REST — perfect for serverless (no TCP pool needed).

export const QUEUE_KEY = "ass:jobs";

let _redis: Redis | null = null;

export function redis(): Redis {
  const url = process.env.UPSTASH_REDIS_REST_URL;
  const token = process.env.UPSTASH_REDIS_REST_TOKEN;
  if (!url || !token) throw new Error("Upstash Redis is not configured");
  if (!_redis) _redis = new Redis({ url, token });
  return _redis;
}

export interface JobPayload {
  videoId: string;
  userId: string;
}

/** Push a job onto the queue (left side; worker pops from the right = FIFO). */
export async function enqueueJob(job: JobPayload) {
  await redis().lpush(QUEUE_KEY, JSON.stringify(job));
}

/**
 * Fire a non-blocking HTTP ping at the worker so a sleeping (scaled-to-zero)
 * instance wakes up and drains the queue. We deliberately do NOT await the
 * full processing — we just nudge it and return.
 */
export async function wakeWorker(): Promise<void> {
  const url = process.env.WORKER_URL;
  const secret = process.env.WORKER_SECRET || "";
  if (!url) {
    console.warn("[wakeWorker] WORKER_URL not set — job will wait in queue");
    return;
  }
  try {
    // Short timeout: we only need to land the request, not wait for work.
    const controller = new AbortController();
    const t = setTimeout(() => controller.abort(), 4000);
    await fetch(`${url.replace(/\/$/, "")}/wake`, {
      method: "POST",
      headers: { "x-worker-secret": secret },
      signal: controller.signal,
    }).catch(() => {});
    clearTimeout(t);
  } catch {
    // A cold worker may not answer within 4s — that's fine. It will still
    // have received the connection and will start draining the queue.
  }
}
