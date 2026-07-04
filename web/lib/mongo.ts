import { MongoClient, Db } from "mongodb";

// Serverless-safe singleton. On Vercel, functions are reused across
// invocations, so we cache the client on the global object to avoid
// opening a new connection pool on every request.

const uri = process.env.MONGODB_URI;
const dbName = process.env.MONGODB_DB || "ai_shorts";

if (!uri) {
  // Don't throw at import time during build; throw when actually used.
  console.warn("[mongo] MONGODB_URI is not set");
}

const globalWithMongo = global as typeof globalThis & {
  _mongoClient?: MongoClient;
  _mongoPromise?: Promise<MongoClient>;
};

export async function getDb(): Promise<Db> {
  if (!uri) throw new Error("MONGODB_URI is not configured");

  if (!globalWithMongo._mongoPromise) {
    const client = new MongoClient(uri, {
      maxPoolSize: 5,
    });
    globalWithMongo._mongoClient = client;
    globalWithMongo._mongoPromise = client.connect();
  }
  const client = await globalWithMongo._mongoPromise;
  return client.db(dbName);
}

export const Collections = {
  videos: "videos",
  clips: "clips",
  users: "users",
} as const;
