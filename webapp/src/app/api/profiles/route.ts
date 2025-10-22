import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";

/**
 * Profile Creation API Route
 *
 * Creates a new user profile via the profile-service.
 * Requires authentication via JWT token.
 *
 * POST /api/profiles
 * Body: Profile data from onboarding form
 * Returns: Created profile information
 */

const API_BASE_URL = process.env.API_URL || "http://api-gateway:8080";

export async function POST(request: NextRequest) {
  try {
    // Check authentication
    const cookieStore = await cookies();
    const accessToken = cookieStore.get("access_token");

    console.log("=== Profile Creation API Debug ===");
    console.log("All cookies:", cookieStore.getAll());
    console.log("Access token:", accessToken ? "present" : "missing");

    if (!accessToken) {
      console.log("No access token found, returning 401");
      return NextResponse.json({ error: "Authentication required" }, { status: 401 });
    }

    // Get profile data from request
    const profileData = await request.json();

    // Validate required fields
    const requiredFields = ["name", "birthDate", "gender", "orientation"];
    for (const field of requiredFields) {
      if (!profileData[field]) {
        return NextResponse.json(
          { error: `Missing required field: ${field}` },
          { status: 400 }
        );
      }
    }

    // Decode JWT token to get user_id
    const tokenPayload = JSON.parse(atob(accessToken.value.split('.')[1]));
    const userId = tokenPayload.user_id;

    // Prepare data for profile-service
    const profilePayload = {
      user_id: userId,
      name: profileData.name,
      birth_date: profileData.birthDate,
      gender: profileData.gender,
      orientation: profileData.orientation,
      goal: profileData.goal || "relationship",
      bio: profileData.bio || "",
      city: profileData.city || "",
      is_complete: true,
    };

    // Create profile via profile-service
    const response = await fetch(`${API_BASE_URL}/api/profiles`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${accessToken.value}`,
      },
      body: JSON.stringify(profilePayload),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error("Profile service error:", errorData);
      return NextResponse.json(
        { error: errorData.error || "Failed to create profile" },
        { status: response.status }
      );
    }

    const createdProfile = await response.json();

    return NextResponse.json({
      success: true,
      profile: createdProfile,
    });

  } catch (error) {
    console.error("Error creating profile:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
