import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin();

const nextConfig: NextConfig = {
  output: "standalone",

  // Security headers
  poweredByHeader: false, // Remove X-Powered-By header

  async headers() {
    // Allow API connections based on environment
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://api-gateway:8080";
    const isDev = process.env.NODE_ENV !== "production";

    // Extract domain from API URL for connect-src
    const apiDomain = apiUrl.replace(/^https?:\/\//, "").split(":")[0];
    const connectSrc = isDev
      ? "'self' http://localhost:* https://localhost:* http://api-gateway:* ws://localhost:*" // Dev: allow all localhost
      : `'self' https://${apiDomain} http://${apiDomain}:* wss://${apiDomain}`; // Prod: restrict to API domain

    // Configure script-src based on environment
    // Dev: Allow unsafe-eval and unsafe-inline for Next.js hot reload
    // Prod: Allow unsafe-inline for Next.js inline scripts (required for SSR)
    const scriptSrc = isDev
      ? "'self' 'unsafe-eval' 'unsafe-inline' https://telegram.org https://*.telegram.org"
      : "'self' 'unsafe-inline' https://telegram.org https://oauth.telegram.org";

    // Style-src: unsafe-inline needed for Tailwind in both dev and prod
    const styleSrc = "'self' 'unsafe-inline'";

    // Frame-src: Allow Telegram OAuth and widgets
    const frameSrc =
      "https://oauth.telegram.org https://telegram.org https://*.telegram.org https://t.me";

    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "Content-Security-Policy",
            value: [
              "default-src 'self'",
              `script-src ${scriptSrc}`,
              `style-src ${styleSrc}`,
              "img-src 'self' data: blob: https:",
              "font-src 'self' data:",
              `connect-src ${connectSrc}`,
              `frame-src ${frameSrc}`,
              "frame-ancestors *", // TEMPORARY: Allow all domains for testing
            ].join("; "),
          },
          // X-Frame-Options removed to allow Telegram WebApp embedding (CSP frame-ancestors is used instead)
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
          {
            key: "Referrer-Policy",
            value: "strict-origin-when-cross-origin",
          },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=()",
          },
        ],
      },
    ];
  },
};

export default withNextIntl(nextConfig);
