import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";

/**
 * Get Profile API Route
 *
 * Gets user profile data from profile-service.
 * Requires authentication via JWT token.
 *
 * GET /api/profiles/[userId]
 * Returns: Profile information
 */

const API_BASE_URL = process.env.API_URL || "http://api-gateway:8080";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ userId: string }> }
) {
  try {
    // Check authentication
    const cookieStore = await cookies();
    const accessToken = cookieStore.get("access_token");

    if (!accessToken) {
      return NextResponse.json({ error: "Authentication required" }, { status: 401 });
    }

    const { userId } = await params;

    // Get profile from profile-service
    const response = await fetch(`${API_BASE_URL}/api/profiles/${userId}`, {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${accessToken.value}`,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error("Profile service error:", errorData);
      return NextResponse.json(
        { error: errorData.error || "Failed to get profile" },
        { status: response.status }
      );
    }

    const profile = await response.json();

    return NextResponse.json({
      success: true,
      profile: profile,
    });

  } catch (error) {
    console.error("Error getting profile:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
