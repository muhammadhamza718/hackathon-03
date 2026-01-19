/**
 * Compression and Optimization Middleware
 * Implements Brotli/Gzip compression for static assets
 * Task: T134
 *
 * Last Updated: 2026-01-15
 */

import { NextResponse, NextRequest } from 'next/server';

// Compression algorithms
const COMPRESSION_ALGORITHMS = {
  BROTLI: 'br',
  GZIP: 'gzip',
  DEFLATE: 'deflate',
};

// Content types that benefit from compression
const COMPRESSIBLE_CONTENT_TYPES = [
  'text/html',
  'text/css',
  'text/javascript',
  'application/javascript',
  'application/json',
  'application/xml',
  'text/plain',
  'text/xml',
  'image/svg+xml',
  'application/wasm',
];

// Content types to exclude from compression
const EXCLUDED_CONTENT_TYPES = [
  'image/jpeg',
  'image/png',
  'image/gif',
  'image/webp',
  'image/avif',
  'video/mp4',
  'video/webm',
  'audio/mp3',
  'audio/wav',
  'font/woff',
  'font/woff2',
  'font/ttf',
  'font/otf',
];

// File extensions that should be compressed
const COMPRESSIBLE_EXTENSIONS = [
  '.html',
  '.css',
  '.js',
  '.json',
  '.xml',
  '.txt',
  '.svg',
  '.wasm',
];

// Threshold for compression (bytes)
const COMPRESSION_THRESHOLD = 1024; // 1KB

// Compression quality settings
const COMPRESSION_SETTINGS = {
  brotli: {
    quality: 6, // 0-11, 6 is good balance
    lgwindow: 22, // Brotli window size
  },
  gzip: {
    level: 6, // 0-9, 6 is default
  },
};

/**
 * Check if content should be compressed
 */
function shouldCompress(contentType: string, contentLength: number): boolean {
  // Check size threshold
  if (contentLength < COMPRESSION_THRESHOLD) {
    return false;
  }

  // Check content type
  const baseContentType = contentType.split(';')[0].trim().toLowerCase();

  if (EXCLUDED_CONTENT_TYPES.includes(baseContentType)) {
    return false;
  }

  if (COMPRESSIBLE_CONTENT_TYPES.includes(baseContentType)) {
    return true;
  }

  // For unknown types, check if it's text-based
  return baseContentType.startsWith('text/') || baseContentType.includes('xml') || baseContentType.includes('json');
}

/**
 * Check if URL should be optimized
 */
function shouldOptimizeUrl(url: URL): boolean {
  const path = url.pathname.toLowerCase();

  // Skip API routes
  if (path.startsWith('/api/')) {
    return false;
  }

  // Skip dynamic routes
  if (path.includes('_next') && path.includes('data')) {
    return false;
  }

  // Check file extensions
  const extension = path.slice(path.lastIndexOf('.'));
  if (COMPRESSIBLE_EXTENSIONS.includes(extension)) {
    return true;
  }

  // Optimize static assets
  if (path.startsWith('/static/') || path.startsWith('/_next/static/')) {
    return true;
  }

  // Optimize HTML pages
  if (path === '/' || path.endsWith('.html') || !extension) {
    return true;
  }

  return false;
}

/**
 * Simple in-memory compression (for demo purposes)
 * In production, use a proper compression library or CDN
 */
class SimpleCompressor {
  // Note: This is a simplified implementation
  // In production, use libraries like 'compression' or 'brotli-wasm'

  static async compress(content: Buffer, algorithm: string): Promise<Buffer | null> {
    try {
      // For demonstration, we'll just return the content
      // In production, you would implement actual compression here

      if (algorithm === COMPRESSION_ALGORITHMS.BROTLI) {
        // Placeholder: would use 'brotli-wasm' or similar
        return content;
      }

      if (algorithm === COMPRESSION_ALGORITHMS.GZIP) {
        // Placeholder: would use 'pako' or Node.js zlib
        return content;
      }

      return null;
    } catch (error) {
      console.error('Compression error:', error);
      return null;
    }
  }

  static getCompressionRatio(original: number, compressed: number): number {
    if (original === 0) return 0;
    return ((original - compressed) / original) * 100;
  }
}

/**
 * Response Optimization Middleware
 */
export async function optimizeResponse(
  request: NextRequest,
  response: NextResponse
): Promise<NextResponse> {
  const url = new URL(request.url);

  // Check if optimization should be applied
  if (!shouldOptimizeUrl(url)) {
    return response;
  }

  const contentType = response.headers.get('content-type') || '';
  const contentLength = parseInt(response.headers.get('content-length') || '0', 10);

  // Check if content should be compressed
  if (!shouldCompress(contentType, contentLength)) {
    return response;
  }

  // Get accepted encoding from request
  const acceptEncoding = request.headers.get('accept-encoding') || '';

  // Determine best compression algorithm
  let compressionAlgorithm: string | null = null;

  if (acceptEncoding.includes(COMPRESSION_ALGORITHMS.BROTLI)) {
    compressionAlgorithm = COMPRESSION_ALGORITHMS.BROTLI;
  } else if (acceptEncoding.includes(COMPRESSION_ALGORITHMS.GZIP)) {
    compressionAlgorithm = COMPRESSION_ALGORITHMS.GZIP;
  }

  if (!compressionAlgorithm) {
    return response;
  }

  // Get response body
  const body = await response.arrayBuffer();
  const bodyBuffer = Buffer.from(body);

  if (bodyBuffer.length < COMPRESSION_THRESHOLD) {
    return response;
  }

  // Compress the body
  const compressed = await SimpleCompressor.compress(bodyBuffer, compressionAlgorithm);

  if (!compressed) {
    return response;
  }

  // Check if compression actually reduced size
  const ratio = SimpleCompressor.getCompressionRatio(bodyBuffer.length, compressed.length);

  if (ratio < 10) { // Only apply if compression reduces size by at least 10%
    return response;
  }

  // Create new response with compressed body
  const optimizedResponse = new NextResponse(compressed, {
    status: response.status,
    statusText: response.statusText,
    headers: new Headers(response.headers),
  });

  // Update headers
  optimizedResponse.headers.set('content-encoding', compressionAlgorithm);
  optimizedResponse.headers.set('content-length', compressed.length.toString());
  optimizedResponse.headers.set('x-compression-ratio', ratio.toFixed(2));
  optimizedResponse.headers.set('x-compression-algorithm', compressionAlgorithm);

  // Remove ETag if present (since content is modified)
  if (optimizedResponse.headers.has('etag')) {
    optimizedResponse.headers.delete('etag');
  }

  // Add vary header for cache correctness
  const vary = optimizedResponse.headers.get('vary') || '';
  const newVary = vary ? `${vary}, Accept-Encoding` : 'Accept-Encoding';
  optimizedResponse.headers.set('vary', newVary);

  // Add cache control for compressed assets
  if (!optimizedResponse.headers.has('cache-control')) {
    optimizedResponse.headers.set(
      'cache-control',
      'public, max-age=31536000, immutable'
    );
  }

  return optimizedResponse;
}

/**
 * Asset Optimization Headers
 */
export function addOptimizationHeaders(
  request: NextRequest,
  response: NextResponse
): NextResponse {
  const url = new URL(request.url);
  const path = url.pathname;

  // Add performance headers for static assets
  if (
    path.startsWith('/_next/static/') ||
    path.startsWith('/static/') ||
    path.startsWith('/public/')
  ) {
    // Enable browser caching for static assets
    if (!response.headers.has('cache-control')) {
      response.headers.set(
        'cache-control',
        'public, max-age=31536000, immutable'
      );
    }

    // Add preload headers for critical assets
    if (path.endsWith('.css') || path.endsWith('.js')) {
      response.headers.set(
        'link',
        `<${path}>; rel=preload; as=${path.endsWith('.css') ? 'style' : 'script'}`
      );
    }
  }

  // Add security headers
  response.headers.set('x-content-type-options', 'nosniff');
  response.headers.set('x-frame-options', 'DENY');
  response.headers.set('x-xss-protection', '1; mode=block');

  return response;
}

/**
 * Progressive Image Loading Header
 */
export function addImageOptimizationHeaders(
  request: NextRequest,
  response: NextResponse
): NextResponse {
  const url = new URL(request.url);
  const path = url.pathname.toLowerCase();

  // Check if it's an image request
  const imageExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.avif', '.svg'];
  const isImage = imageExtensions.some(ext => path.endsWith(ext));

  if (isImage) {
    // Add image optimization headers
    response.headers.set('accept-ch', 'dpr, width, viewport-width');
    response.headers.set('critical-ch', 'dpr, width, viewport-width');

    // Enable client hints for responsive images
    if (request.headers.has('sec-ch-viewport-width')) {
      response.headers.set(
        'vary',
        `${response.headers.get('vary') || ''}, Sec-CH-Viewport-Width, Sec-CH-DPR`
      );
    }

    // Cache images longer
    if (!response.headers.has('cache-control')) {
      response.headers.set('cache-control', 'public, max-age=31536000, immutable');
    }
  }

  return response;
}

/**
 * WebP/AVIF Format Negotiation
 */
export function negotiateImageFormat(
  request: NextRequest,
  response: NextResponse
): NextResponse {
  const accept = request.headers.get('accept') || '';

  // Check for modern image format support
  const supportsWebP = accept.includes('image/webp');
  const supportsAVIF = accept.includes('image/avif');

  // Add headers to inform the client about supported formats
  if (supportsWebP || supportsAVIF) {
    const formats = [];
    if (supportsAVIF) formats.push('avif');
    if (supportsWebP) formats.push('webp');

    response.headers.set('x-supported-image-formats', formats.join(','));
  }

  return response;
}

/**
 * Main Compression Middleware
 * This would be used in Next.js middleware.ts
 */
export async function compressionMiddleware(
  request: NextRequest
): Promise<NextResponse> {
  // Get the original response (you would call your route handler here)
  // This is a placeholder for the actual response generation

  // For demo purposes, return a basic response
  // In production, you would:
  // 1. Process the request through your route handlers
  // 2. Get the response
  // 3. Apply optimizations

  const response = NextResponse.next();

  // Apply optimizations
  let optimizedResponse = await optimizeResponse(request, response);
  optimizedResponse = addOptimizationHeaders(request, optimizedResponse);
  optimizedResponse = addImageOptimizationHeaders(request, optimizedResponse);
  optimizedResponse = negotiateImageFormat(request, optimizedResponse);

  return optimizedResponse;
}

/**
 * Utility function to get optimal image size based on viewport
 */
export function getOptimalImageSize(
  originalWidth: number,
  viewportWidth: number,
  dpr: number = 1
): number {
  // Never serve images larger than the viewport width * DPR
  const targetWidth = Math.min(originalWidth, viewportWidth * dpr);

  // Round to nearest reasonable size for caching
  const step = 100; // Round to nearest 100px
  return Math.round(targetWidth / step) * step;
}

/**
 * Generate srcset for responsive images
 */
export function generateSrcSet(
  baseUrl: string,
  sizes: number[]
): string {
  return sizes
    .map(size => `${baseUrl}?w=${size}&q=75 ${size}w`)
    .join(', ');
}

/**
 * Generate sizes attribute for responsive images
 */
export function generateSizesAttribute(
  breakpoints: { breakpoint: number; size: string }[]
): string => {
  return breakpoints
    .map(bp => `(max-width: ${bp.breakpoint}px) ${bp.size}`)
    .concat(['100vw']) // Default fallback
    .join(', ');
};

// Predefined size presets
export const IMAGE_PRESETS = {
  thumbnail: {
    width: 150,
    height: 150,
    quality: 75,
  },
  small: {
    width: 320,
    height: 240,
    quality: 80,
  },
  medium: {
    width: 640,
    height: 480,
    quality: 85,
  },
  large: {
    width: 1280,
    height: 720,
    quality: 90,
  },
  full: {
    width: 1920,
    height: 1080,
    quality: 90,
  },
};

// Common breakpoints for responsive images
export const BREAKPOINTS = [
  { width: 320, name: 'mobile-small' },
  { width: 640, name: 'mobile-large' },
  { width: 768, name: 'tablet-small' },
  { width: 1024, name: 'tablet-large' },
  { width: 1280, name: 'desktop-small' },
  { width: 1920, name: 'desktop-large' },
];