/** @type {import('next').NextConfig} */
const nextConfig = {
  // Fully static site: `next build` emits a self-contained ./out directory.
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
  // No server runtime, no DB, no PII collection anywhere in this app.
  reactStrictMode: true,
};

export default nextConfig;
