import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";

/**
 * Telegram Login API Route
 *
 * Exchanges Telegram WebApp initData for JWT tokens via the API Gateway.
 * Stores tokens in httpOnly cookies for secure storage.
 *
 * POST /api/auth/tg
 * Body: { initData: string }
 * Returns: { success: boolean, user_id: number, username?: string }
 */

const API_BASE_URL = process.env.API_URL || "http://api-gateway:8080";
const BOT_TOKEN = process.env.BOT_TOKEN || "";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { initData } = body;

    if (!initData) {
      return NextResponse.json({ error: "Missing initData" }, { status: 400 });
    }

    if (!BOT_TOKEN) {
      console.error("BOT_TOKEN environment variable is not set");
      return NextResponse.json(
        { error: "Server configuration error" },
        { status: 500 }
      );
    }

    // Exchange Telegram initData for JWT token via auth service
    const authResponse = await fetch(`${API_BASE_URL}/api/auth/validate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        init_data: initData,
        bot_token: BOT_TOKEN,
      }),
    });

    if (!authResponse.ok) {
      const errorData = await authResponse.json().catch(() => ({}));
      console.error("Auth service error:", errorData);
      return NextResponse.json(
        { error: errorData.error || "Authentication failed" },
        { status: authResponse.status }
      );
    }

    const authData = await authResponse.json();
    const { token, user_id, username } = authData;

    if (!token) {
      return NextResponse.json(
        { error: "No token received from auth service" },
        { status: 500 }
      );
    }

    // Set httpOnly cookies for secure token storage
    const cookieStore = await cookies();

    // Access token cookie (shorter TTL for better security)
    // Recommended: 15-60 minutes for access tokens
    cookieStore.set("access_token", token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax", // Lax provides CSRF protection while allowing Telegram widget redirects
      maxAge: 60 * 60, // 1 hour (3600 seconds)
      path: "/",
    });

    // Refresh token cookie (longer TTL for extended sessions)
    // TODO: CRITICAL - Backend must generate a separate refresh token with:
    //   - Different signature/secret
    //   - Longer TTL (7-30 days)
    //   - Token rotation on use
    //   - Different audience/scope
    // Currently using same token as access token - this is a security risk
    cookieStore.set("refresh_token", token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax", // Lax provides CSRF protection while allowing Telegram widget redirects
      maxAge: 7 * 24 * 60 * 60, // 7 days (604800 seconds)
      path: "/",
    });

    // Return success response
    return NextResponse.json({
      success: true,
      user_id,
      username,
    });
  } catch (error) {
    console.error("Error in Telegram auth:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
