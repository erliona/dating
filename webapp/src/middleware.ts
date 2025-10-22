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
  // First, apply i18n middleware
  const response = intlMiddleware(request);

  // Check if route requires authentication
  const pathname = request.nextUrl.pathname;
  
  // Check if it's a public route first (including home page)
  const isPublicRoute = PUBLIC_ROUTES.some(
    (route) => pathname === route || pathname.match(/^\/(ru|en)$/)?.[0] === pathname
  );
  
  // Only check for protected routes if it's not a public route
  const isProtectedRoute = !isPublicRoute && PROTECTED_ROUTES.some((route) => pathname.includes(route));

  // Skip auth check for public routes and API routes
  if (isPublicRoute || pathname.startsWith("/api/")) {
    return response;
  }

  // Check for auth token in cookies
  if (isProtectedRoute) {
    const accessToken = request.cookies.get("access_token");

    if (!accessToken) {
      // Redirect to login with the original URL
      // Preserve locale from pathname
      const locale = pathname.startsWith("/ru") ? "ru" : "en";
      const loginUrl = new URL(`/${locale}/login`, request.url);

      loginUrl.searchParams.set("reason", "unauthorized");

      // Preserve full path with query params for redirect after login
      const redirectPath = pathname + (request.nextUrl.search || "");
      loginUrl.searchParams.set("redirect", redirectPath);

      return NextResponse.redirect(loginUrl);
    }
  }

  return response;
}

export const config = {
  // Match only internationalized pathnames
  matcher: ["/", "/(ru|en)/:path*"],
};
