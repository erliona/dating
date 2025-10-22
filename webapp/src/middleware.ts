import createMiddleware from "next-intl/middleware";
import { NextRequest, NextResponse } from "next/server";
import { routing } from "./i18n/routing";

// Create i18n middleware
const intlMiddleware = createMiddleware({
  ...routing,
  localeDetection: true, // Enable automatic locale detection from Accept-Language header
});

// Protected routes that require authentication
const PROTECTED_ROUTES = ["/profile", "/matches", "/chat"];

// Public routes that don't require auth
const PUBLIC_ROUTES = ["/", "/login"];

export default async function middleware(request: NextRequest) {
  // TEMPORARILY DISABLED - Only apply i18n middleware
  const response = intlMiddleware(request);
  
  // Skip all auth checks for debugging
  console.log(`[Middleware] TEMPORARILY DISABLED - Allowing all requests to: ${request.nextUrl.pathname}`);
  return response;
}

export const config = {
  // Match only internationalized pathnames
  matcher: ["/", "/(ru|en)/:path*"],
};
