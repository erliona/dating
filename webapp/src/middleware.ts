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
const PUBLIC_ROUTES = ["/", "/login", "/welcome", "/onboarding"];

export default async function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;
  
  // Apply i18n middleware first
  const response = intlMiddleware(request);
  
  // Check if this is a protected route
  const isProtectedRoute = PROTECTED_ROUTES.some(route => 
    pathname.includes(route) || pathname.endsWith(route)
  );
  
  // Check if this is a public route
  const isPublicRoute = PUBLIC_ROUTES.some(route => 
    pathname.includes(route) || pathname.endsWith(route)
  );
  
  // Skip auth check for public routes
  if (isPublicRoute) {
    console.log(`[Middleware] Public route - allowing: ${pathname}`);
    return response;
  }
  
  // Skip auth check for API routes
  if (pathname.startsWith('/api/')) {
    console.log(`[Middleware] API route - allowing: ${pathname}`);
    return response;
  }
  
  // For protected routes, check authentication
  if (isProtectedRoute) {
    const accessToken = request.cookies.get("access_token");
    
    if (!accessToken) {
      console.log(`[Middleware] No access token for protected route: ${pathname}`);
      return NextResponse.redirect(new URL("/ru/login", request.url));
    }
    
    console.log(`[Middleware] Access token found for protected route: ${pathname}`);
  }
  
  console.log(`[Middleware] Allowing request to: ${pathname}`);
  return response;
}

export const config = {
  // Match only internationalized pathnames
  matcher: ["/", "/(ru|en)/:path*"],
};