/**
 * Next.js Configuration - Minimal and Clean
 * Updated for Next.js 16 compatibility
 *
 * Last Updated: 2026-01-15
 */

/** @type {import('next').NextConfig} */
const nextConfig = {
  // React strict mode
  reactStrictMode: true,

  // Webpack configuration (for compatibility with Monaco Editor)
  webpack: (config, { dev, isServer, nextRuntime }) => {
    // Performance hints
    config.performance = {
      hints: dev ? false : 'warning',
      maxAssetSize: 512000, // 512KB
      maxEntrypointSize: 512000, // 512KB
    };

    // Code splitting optimization
    if (!isServer) {
      config.optimization = {
        ...config.optimization,
        splitChunks: {
          chunks: 'all',
          cacheGroups: {
            // Split large dependencies
            monaco: {
              test: /[\\/]node_modules[\\/]monaco-editor[\\/]/,
              name: 'monaco',
              priority: 30,
              chunks: 'async',
              reuseExistingChunk: true,
            },
            // Vendor chunk for other node_modules
            vendor: {
              test: /[\\/]node_modules[\\/]/,
              name: 'vendor',
              priority: 20,
              chunks: 'all',
              reuseExistingChunk: true,
            },
          },
        },
      };
    }

    // Asset optimization
    config.module.rules.push({
      test: /\.(png|jpe?g|gif|svg|webp)$/i,
      type: 'asset',
      parser: {
        dataUrlCondition: {
          maxSize: 8192, // 8KB limit for inlining
        },
      },
    });

    // Font optimization
    config.module.rules.push({
      test: /\.(woff|woff2|eot|ttf|otf)$/i,
      type: 'asset/resource',
    });

    // Bundle size analysis (only when ANALYZE env is set)
    if (process.env.ANALYZE === 'true') {
      const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');
      config.plugins.push(
        new BundleAnalyzerPlugin({
          analyzerMode: 'static',
          analyzerPort: isServer ? 8888 : 8889,
          openAnalyzer: false,
        })
      );
    }

    return config;
  },

  // Image optimization
  images: {
    formats: ['image/avif', 'image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    minimumCacheTTL: 60, // 60 seconds
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
    ],
  },

  // Compression
  compress: true,

  // Generate source maps only for development
  productionBrowserSourceMaps: false,

  // HTTP/2 and keep-alive
  httpAgentOptions: {
    keepAlive: true,
  },

  // Disable X-Powered-By header for security
  poweredByHeader: false,

  // Server components external packages (moved from experimental)
  serverExternalPackages: ['monaco-editor'],

  // Turbopack configuration (addresses Next.js 16 warnings)
  turbopack: {},

  // Security headers
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=(), interest-cohort=()',
          },
          // Performance headers
          {
            key: 'X-Permitted-Cross-Domain-Policies',
            value: 'none',
          },
          {
            key: 'Cross-Origin-Embedder-Policy',
            value: 'require-corp',
          },
          {
            key: 'Cross-Origin-Opener-Policy',
            value: 'same-origin',
          },
        ],
      },
      {
        source: '/static/(.*)',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
      {
        source: '/api/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'no-store, max-age=0',
          },
        ],
      },
    ];
  },

  // Custom headers for API routes
  async rewrites() {
    return [
      {
        source: '/api/dapr/:path*',
        destination: '/api/dapr/:path*',
      },
      {
        source: '/api/mcp/:path*',
        destination: '/api/mcp/:path*',
      },
    ];
  },
};

export default nextConfig;