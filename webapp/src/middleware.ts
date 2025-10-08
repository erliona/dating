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
  const isProtectedRoute = PROTECTED_ROUTES.some((route) => pathname.includes(route));
  const isPublicRoute = PUBLIC_ROUTES.some(
    (route) => pathname === route || pathname.match(/^\/(ru|en)$/)?.[0] === pathname
  );

  // Skip auth check for public routes and API routes
  if (isPublicRoute || pathname.startsWith("/api/")) {
    return response;
  }

  // Check for auth token in cookies
  if (isProtectedRoute) {
    const accessToken = request.cookies.get("access_token");

    if (!accessToken) {
      // Redirect to login with the original URL
      const loginUrl = new URL(
        `${pathname.startsWith("/ru") ? "/ru" : "/en"}/login`,
        request.url
      );
      loginUrl.searchParams.set("reason", "unauthorized");
      loginUrl.searchParams.set("redirect", pathname);

      return NextResponse.redirect(loginUrl);
    }
  }

  return response;
}

export const config = {
  // Match only internationalized pathnames
  matcher: ["/", "/(ru|en)/:path*"],
};
