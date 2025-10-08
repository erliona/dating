"use client";

import { useRouter } from "next/navigation";
import { useCallback } from "react";
import { logout as logoutFn, redirectToLogin } from "@/shared/lib/auth";

/**
 * Auth Hook
 *
 * Provides authentication utilities for client components.
 * Manages logout and login redirects.
 */

export function useAuth() {
  const router = useRouter();

  const logout = useCallback(async () => {
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
