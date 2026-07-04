/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Don't let a stray lint warning fail the production build on Vercel.
  eslint: { ignoreDuringBuilds: true },
  // Allow large request bodies are NOT needed: uploads go straight to R2
  // via presigned URLs, so the Vercel function never touches the video.
  experimental: {
    serverComponentsExternalPackages: ["mongodb"],
  },
};

module.exports = nextConfig;
