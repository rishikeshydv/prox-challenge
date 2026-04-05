/** @type {import('next').NextConfig} */
const backendApiBaseUrl =
  process.env.BACKEND_API_BASE_URL || "http://localhost:8000";

const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/chat",
        destination: `${backendApiBaseUrl}/api/chat`,
      },
      {
        source: "/api/chat/:path*",
        destination: `${backendApiBaseUrl}/api/chat/:path*`,
      },
    ];
  },
};

export default nextConfig;
