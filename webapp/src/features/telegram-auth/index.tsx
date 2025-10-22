"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

/**
 * TelegramAuth component
 * 
 * Automatically authenticates users via Telegram WebApp initData
 * when the app is opened inside Telegram.
 */
export function TelegramAuth({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const authenticateWithTelegram = async () => {
      try {
        console.log("[TelegramAuth] Starting authentication...");
        console.log("[TelegramAuth] window.Telegram:", window.Telegram);
        
        // Check if we're inside Telegram WebApp
        if (typeof window === "undefined" || !window.Telegram?.WebApp) {
          console.log("[TelegramAuth] Not running inside Telegram WebApp");
          setIsLoading(false);
          return;
        }

        const tg = window.Telegram.WebApp;
        console.log("[TelegramAuth] Telegram WebApp found:", {
          initData: tg.initData ? "present" : "missing",
          initDataUnsafe: tg.initDataUnsafe,
          themeParams: tg.themeParams,
        });
        
        // Expand the WebApp to full height
        tg.expand();
        console.log("[TelegramAuth] WebApp expanded");
        
        // Set header color to match theme
        tg.setHeaderColor(tg.themeParams.bg_color || "#ffffff");
        console.log("[TelegramAuth] Header color set");

        // Get initData from Telegram
        const initData = tg.initData;

        if (!initData) {
          console.warn("[TelegramAuth] No initData from Telegram WebApp");
          console.warn("[TelegramAuth] This usually means the app is not opened from Telegram");
          setIsLoading(false);
          return;
        }
        
        console.log("[TelegramAuth] initData received (length):", initData.length);

        // Check if already authenticated
        const accessToken = document.cookie
          .split("; ")
          .find((row) => row.startsWith("access_token="))
          ?.split("=")[1];

        if (accessToken) {
          console.log("Already authenticated");
          setIsLoading(false);
          return;
        }

        // Authenticate with backend
        console.log("[TelegramAuth] Authenticating with backend...");
        console.log("[TelegramAuth] Sending POST to /api/auth/tg");
        
            const response = await fetch("/api/auth/validate", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ 
            init_data: initData,
            bot_token: "8302871321:AAGDRnSDYdYHeEOqtEoKZVYLCbBlI2GBYMM"
          }),
        });

        console.log("[TelegramAuth] Response status:", response.status);
        console.log("[TelegramAuth] Response headers:", Object.fromEntries(response.headers.entries()));

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          console.error("[TelegramAuth] Authentication failed:", errorData);
          throw new Error(
            errorData.error || `Authentication failed: ${response.status}`
          );
        }

        const data = await response.json();
        console.log("[TelegramAuth] Authentication successful:", data);

        // Show success feedback
        tg.HapticFeedback.notificationOccurred("success");

        // Redirect to profile or home
        router.push("/ru/profile");
      } catch (err) {
        console.error("Telegram authentication error:", err);
        setError(err instanceof Error ? err.message : "Authentication failed");
        
        // Show error feedback
        if (window.Telegram?.WebApp) {
          window.Telegram.WebApp.HapticFeedback.notificationOccurred("error");
        }
      } finally {
        setIsLoading(false);
      }
    };

    authenticateWithTelegram();
  }, [router]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 text-center">
          {/* Logo/Icon */}
          <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full mx-auto mb-6 flex items-center justify-center">
            <span className="text-white text-2xl font-bold">💕</span>
          </div>
          
          {/* Loading spinner */}
          <div className="mb-6">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-500 border-r-transparent" />
          </div>
          
          {/* Loading text */}
          <h2 className="text-xl font-semibold text-gray-800 mb-2">
            Подключение к Telegram...
          </h2>
          <p className="text-gray-600 text-sm">
            Проверяем авторизацию и загружаем ваш профиль
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center p-4">
        <div className="max-w-md text-center">
          <h2 className="mb-2 text-xl font-semibold text-red-600">
            Ошибка авторизации
          </h2>
          <p className="text-muted-foreground">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="bg-primary text-primary-foreground hover:bg-primary/90 mt-4 rounded-lg px-4 py-2"
          >
            Попробовать снова
          </button>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

// Extend Window interface to include Telegram WebApp
declare global {
  interface Window {
    Telegram?: {
      WebApp: {
        initData: string;
        initDataUnsafe: {
          user?: {
            id: number;
            first_name: string;
            last_name?: string;
            username?: string;
            language_code?: string;
          };
        };
        themeParams: {
          bg_color?: string;
          text_color?: string;
          hint_color?: string;
          link_color?: string;
          button_color?: string;
          button_text_color?: string;
        };
        expand: () => void;
        close: () => void;
        setHeaderColor: (color: string) => void;
        HapticFeedback: {
          impactOccurred: (style: "light" | "medium" | "heavy" | "rigid" | "soft") => void;
          notificationOccurred: (type: "error" | "success" | "warning") => void;
          selectionChanged: () => void;
        };
      };
    };
  }
}

