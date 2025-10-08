import { NextResponse } from "next/server";
import { cookies } from "next/headers";

/**
 * Token Refresh API Route
 *
 * Refreshes JWT token using the refresh token from cookies.
 * Updates the access token cookie with a new token.
 *
 * POST /api/auth/refresh
 * Returns: { success: boolean, user_id?: number }
 */

const API_BASE_URL = process.env.API_URL || "http://api-gateway:8080";

export async function POST() {
  try {
    const cookieStore = await cookies();
    const refreshToken = cookieStore.get("refresh_token")?.value;

    if (!refreshToken) {
      return NextResponse.json({ error: "No refresh token found" }, { status: 401 });
    }

    // Call auth service to refresh token
    const authResponse = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${refreshToken}`,
      },
    });

    if (!authResponse.ok) {
      // Refresh token is invalid or expired
      // Clear cookies
      cookieStore.delete("access_token");
      cookieStore.delete("refresh_token");

      return NextResponse.json({ error: "Token refresh failed" }, { status: 401 });
    }

    const authData = await authResponse.json();
    const { token, user_id } = authData;

    if (!token) {
      return NextResponse.json(
        { error: "No token received from auth service" },
        { status: 500 }
      );
    }

    // Update access token cookie with new token
    cookieStore.set("access_token", token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "strict",
      maxAge: 24 * 60 * 60, // 24 hours
      path: "/",
    });

    // Return success response
    return NextResponse.json({
      success: true,
      user_id,
    });
  } catch (error) {
    console.error("Error refreshing token:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
