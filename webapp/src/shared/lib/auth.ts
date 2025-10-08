/**
 * Auth Utilities
 *
 * Client-side utilities for authentication management.
 * Tokens are stored in httpOnly cookies and managed server-side.
 */

/**
 * Log out the user by clearing auth cookies
 */
export async function logout(): Promise<boolean> {
  try {
    const response = await fetch("/api/auth/logout", {
      method: "POST",
      credentials: "include",
    });

    return response.ok;
  } catch (error) {
    console.error("Logout error:", error);
    return false;
  }
}

/**
 * Check if user is authenticated
 * This makes a call to a protected endpoint to verify the cookie
 */
export async function checkAuth(): Promise<boolean> {
  try {
    // Try to access a protected endpoint via proxy
    const response = await fetch("/api/proxy/profile/check", {
      credentials: "include",
    });

    return response.ok;
  } catch {
    return false;
  }
}

/**
 * Redirect to login page with optional redirect URL
 */
export function redirectToLogin(redirectTo?: string) {
  const params = new URLSearchParams();
  params.set("reason", "unauthorized");

  if (redirectTo) {
    params.set("redirect", redirectTo);
  }

  window.location.href = `/login?${params.toString()}`;
}

/**
 * Handle API errors and redirect on 401/403
 */
export function handleAuthError(status: number, redirectTo?: string) {
  if (status === 401 || status === 403) {
    redirectToLogin(redirectTo || window.location.pathname);
    return true;
  }
  return false;
}

/**
 * Refresh the access token
 */
export async function refreshToken(): Promise<boolean> {
  try {
    const response = await fetch("/api/auth/refresh", {
      method: "POST",
      credentials: "include",
    });

    return response.ok;
  } catch (error) {
    console.error("Token refresh error:", error);
    return false;
  }
}

/**
 * Auto refresh token before expiration
 * Access token TTL is 1 hour, so refresh after 50 minutes to ensure continuity
 */
export function startTokenRefresh() {
  // Refresh token every 50 minutes (10 minutes before 1h expiration)
  const REFRESH_INTERVAL = 50 * 60 * 1000; // 50 minutes in ms

  const refresh = async () => {
    const success = await refreshToken();
    if (!success) {
      // If refresh fails, redirect to login
      redirectToLogin();
    }
  };

  // Initial refresh after interval
  const intervalId = setInterval(refresh, REFRESH_INTERVAL);

  // Return cleanup function
  return () => clearInterval(intervalId);
}
