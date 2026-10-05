const rawBackend = (process.env.BACKEND_INTERNAL_URL || process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000').trim().replace(/\/+$/, '');

const nextConfig = {
  reactStrictMode: true,
  typescript: {
    // Avoid Node 24 worker thread resolution issue during build
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${rawBackend}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
