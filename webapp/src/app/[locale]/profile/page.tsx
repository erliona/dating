"use client";

import { useTranslations } from "next-intl";
import { useAuth } from "@/shared/hooks/use-auth";

/**
 * Profile Page (Protected)
 *
 * Example of a protected page that requires authentication.
 * Middleware will redirect to /login if not authenticated.
 */

export default function ProfilePage() {
  const t = useTranslations("auth.logout");
  const { logout } = useAuth();

  const handleLogout = async () => {
    await logout();
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 p-8">
      <div className="w-full max-w-md space-y-6 text-center">
        <h1 className="text-3xl font-bold">Profile</h1>
        <p className="text-muted-foreground">
          This is a protected page. You should only see this if authenticated.
        </p>

        <button
          onClick={handleLogout}
          className="bg-destructive text-destructive-foreground hover:bg-destructive/90 rounded-lg px-6 py-3 font-semibold transition-colors"
        >
          {t("button")}
        </button>
      </div>
    </div>
  );
}
