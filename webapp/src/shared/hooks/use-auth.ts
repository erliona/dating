"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef } from "react";
import {
  logout as logoutFn,
  redirectToLogin,
  startTokenRefresh,
} from "@/shared/lib/auth";

/**
 * Auth Hook
 *
 * Provides authentication utilities for client components.
 * Manages logout, login redirects, and automatic token refresh.
 */

export function useAuth() {
  const router = useRouter();
  const refreshCleanupRef = useRef<(() => void) | null>(null);

  // Start auto token refresh on mount
  useEffect(() => {
    refreshCleanupRef.current = startTokenRefresh();

    // Cleanup on unmount
    return () => {
      if (refreshCleanupRef.current) {
        refreshCleanupRef.current();
        refreshCleanupRef.current = null;
      }
    };
  }, []);

  const logout = useCallback(async () => {
    // Clear the refresh timer before logout
    if (refreshCleanupRef.current) {
      refreshCleanupRef.current();
      refreshCleanupRef.current = null;
    }

    const success = await logoutFn();
    if (success) {
      router.push("/login");
    }
    return success;
  }, [router]);

  const requireAuth = useCallback((redirectTo?: string) => {
    redirectToLogin(redirectTo);
  }, []);

  return {
    logout,
    requireAuth,
  };
}
