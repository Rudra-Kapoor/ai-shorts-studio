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
