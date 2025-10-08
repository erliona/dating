import { NextResponse } from "next/server";
import { cookies } from "next/headers";

/**
 * Logout API Route
 *
 * Clears authentication cookies to log out the user.
 *
 * POST /api/auth/logout
 * Returns: { success: boolean }
 */

export async function POST() {
  try {
    const cookieStore = await cookies();

    // Clear access token cookie
    cookieStore.delete("access_token");

    // Clear refresh token cookie
    cookieStore.delete("refresh_token");

    return NextResponse.json({
      success: true,
    });
  } catch (error) {
    console.error("Error in logout:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
