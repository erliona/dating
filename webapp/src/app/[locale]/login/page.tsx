"use client";

import { useTranslations } from "next-intl";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

/**
 * Login Page
 *
 * Displays Telegram Login Widget and handles authentication flow.
 * After successful login, redirects to the requested page or home.
 */

export default function LoginPage() {
  const t = useTranslations("auth.login");
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Get redirect URL from query params and validate it
  // Only allow relative paths to prevent open redirect attacks
  const validateRedirectUrl = (url: string): string => {
    if (!url) return "/";

    // Only allow relative paths starting with /
    if (url.startsWith("/") && !url.startsWith("//")) {
      return url;
    }

    // Default to home for any suspicious URLs
    return "/";
  };

  const redirectTo = validateRedirectUrl(searchParams.get("redirect") || "/");

  useEffect(() => {
    // Load Telegram Login Widget script
    const script = document.createElement("script");
    script.src = "https://telegram.org/js/telegram-widget.js?22";
    script.async = true;
    script.setAttribute("data-telegram-login", "YOUR_BOT_USERNAME"); // Will be configured via env
    script.setAttribute("data-size", "large");
    script.setAttribute("data-request-access", "write");
    script.setAttribute("data-userpic", "true");
    script.setAttribute("data-radius", "10");
    script.setAttribute("data-onauth", "onTelegramAuth(user)");

    const widgetContainer = document.getElementById("telegram-login-widget");
    if (widgetContainer) {
      widgetContainer.appendChild(script);
    }

    // Define the callback function for Telegram widget
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (window as any).onTelegramAuth = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Get initData from Telegram WebApp if available
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const tg = (window as any).Telegram?.WebApp;
        const initData = tg?.initData || "";

        if (!initData) {
          throw new Error("No Telegram data available");
        }

        // Exchange Telegram data for JWT via our API
        const response = await fetch("/api/auth/tg", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ initData }),
          credentials: "include",
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || "Authentication failed");
        }

        const data = await response.json();

        if (data.success) {
          // Redirect to requested page or home
          router.push(redirectTo);
        } else {
          throw new Error("Login failed");
        }
      } catch (err) {
        console.error("Login error:", err);
        setError(err instanceof Error ? err.message : t("error"));
        setIsLoading(false);
      }
    };

    return () => {
      // Cleanup
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      delete (window as any).onTelegramAuth;
    };
  }, [router, redirectTo, t]);

  return (
    <div className="flex min-h-screen items-center justify-center p-8">
      <div className="w-full max-w-md space-y-8 text-center">
        <div>
          <h1 className="text-3xl font-bold">{t("title")}</h1>
          <p className="text-muted-foreground mt-2">{t("description")}</p>
        </div>

        {searchParams.get("reason") === "unauthorized" && (
          <div className="bg-muted rounded-lg p-4 text-sm">{t("unauthorized")}</div>
        )}

        {error && (
          <div className="bg-destructive/10 text-destructive rounded-lg p-4 text-sm">
            {error}
          </div>
        )}

        <div className="flex flex-col items-center gap-4">
          {isLoading ? (
            <div className="flex items-center gap-2">
              <div className="border-primary h-5 w-5 animate-spin rounded-full border-2 border-t-transparent"></div>
              <span>{t("loading")}</span>
            </div>
          ) : (
            <>
              <div id="telegram-login-widget" className="flex justify-center" />
              <p className="text-muted-foreground text-sm">{t("telegramLogin")}</p>
            </>
          )}
        </div>

        <div className="text-muted-foreground text-xs">
          This app can only be opened in Telegram
        </div>
      </div>
    </div>
  );
}
