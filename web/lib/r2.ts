import {
  S3Client,
  GetObjectCommand,
  PutObjectCommand,
  DeleteObjectsCommand,
} from "@aws-sdk/client-s3";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner";

// Cloudflare R2 is S3-compatible, so we use the AWS S3 SDK pointed at the
// R2 endpoint. Region is always "auto" for R2.

const accountId = process.env.R2_ACCOUNT_ID;
const accessKeyId = process.env.R2_ACCESS_KEY_ID;
const secretAccessKey = process.env.R2_SECRET_ACCESS_KEY;
// Optional explicit endpoint — set this to point at a local MinIO (or any other
// S3-compatible store) for local dev. When unset we derive the R2 endpoint from
// the account id exactly as before, so cloud deploys are unaffected.
const endpointOverride = process.env.R2_ENDPOINT;
