import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8001',
        pathname: '/files/**',
      },
    ],
  },
};

export default nextConfig;
