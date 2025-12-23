import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  experimental: {
    reactCompiler: true, // <--- This enables the magic
  },
};

export default nextConfig;
