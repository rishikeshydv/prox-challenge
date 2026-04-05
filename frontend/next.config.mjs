/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/chat",
        destination: "http://localhost:8000/api/chat",
      },
      {
        source: "/api/chat/:path*",
        destination: "http://localhost:8000/api/chat/:path*",
      },
    ];
  },
};

export default nextConfig;
