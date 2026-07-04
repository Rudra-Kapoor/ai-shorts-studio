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
