import { NextRequest, NextResponse } from "next/server";

/**
 * API Proxy Route Handler
 *
 * This route proxies requests to the backend API Gateway while keeping
 * authentication tokens secure (httpOnly cookies, no exposure to browser).
 *
 * Usage from client:
 *   fetch('/api/proxy/profiles/123', { credentials: 'include' })
 *
 * Environment Variables:
 *   API_URL - Backend API Gateway URL (default: http://api-gateway:8080)
 */

const API_BASE_URL = process.env.API_URL || "http://api-gateway:8080";

async function handler(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  const pathname = path.join("/");

  // Construct the target URL
  const url = new URL(`/api/${pathname}`, API_BASE_URL);

  // Forward query parameters
  request.nextUrl.searchParams.forEach((value, key) => {
    url.searchParams.append(key, value);
  });

  try {
    // Forward the request to the backend
    const response = await fetch(url.toString(), {
      method: request.method,
      headers: {
        "Content-Type": "application/json",
        // Forward cookies from the request (for authentication)
        ...(request.headers.get("cookie") && {
          Cookie: request.headers.get("cookie")!,
        }),
        // Forward authorization header if present
        ...(request.headers.get("authorization") && {
          Authorization: request.headers.get("authorization")!,
        }),
      },
      body: request.method !== "GET" ? await request.text() : undefined,
      credentials: "include",
    });

    // Get response data
    const data = await response.text();

    // Create response with same status
    const nextResponse = new NextResponse(data, {
      status: response.status,
      headers: {
        "Content-Type": response.headers.get("Content-Type") || "application/json",
      },
    });

    // Forward Set-Cookie headers (for httpOnly cookies)
    response.headers.forEach((value, key) => {
      if (key.toLowerCase() === "set-cookie") {
        nextResponse.headers.append(key, value);
      }
    });

    return nextResponse;
  } catch (error) {
    console.error("API Proxy error:", error);
    return NextResponse.json(
      { error: "Failed to connect to backend API" },
      { status: 502 }
    );
  }
}

export {
  handler as GET,
  handler as POST,
  handler as PUT,
  handler as DELETE,
  handler as PATCH,
};
