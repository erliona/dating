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
  const [debugInfo, setDebugInfo] = useState<string[]>([]);

  const addDebugInfo = (message: string) => {
    console.log(message);
    setDebugInfo(prev => [...prev, `${new Date().toLocaleTimeString()}: ${message}`]);
  };

  useEffect(() => {
    const authenticateWithTelegram = async () => {
      try {
        addDebugInfo("Starting authentication...");
        addDebugInfo(`window.Telegram: ${window.Telegram ? 'present' : 'missing'}`);
        
        // Check if we're inside Telegram WebApp
        if (typeof window === "undefined" || !window.Telegram?.WebApp) {
          addDebugInfo("Not running inside Telegram WebApp");
          setIsLoading(false);
          return;
        }

        const tg = window.Telegram.WebApp;
        addDebugInfo(`Telegram WebApp found: initData=${tg.initData ? 'present' : 'missing'}`);
        addDebugInfo(`User Agent: ${navigator.userAgent.substring(0, 50)}...`);
        addDebugInfo(`Referrer: ${document.referrer || 'none'}`);
        addDebugInfo(`Location: ${window.location.href}`);
        
        // Expand the WebApp to full height
        tg.expand();
        addDebugInfo("WebApp expanded");
        
        // Set header color to match theme
        tg.setHeaderColor(tg.themeParams.bg_color || "#ffffff");
        addDebugInfo("Header color set");

        // Get initData from Telegram
        const initData = tg.initData;

        if (!initData) {
          addDebugInfo("No initData from Telegram WebApp");
          addDebugInfo("This usually means the app is not opened from Telegram");
          setIsLoading(false);
          return;
        }
        
        addDebugInfo(`initData received (length): ${initData.length}`);
        addDebugInfo(`initData content: ${initData.substring(0, 100)}...`);

        // Check if already authenticated
        const accessToken = document.cookie
          .split("; ")
          .find((row) => row.startsWith("access_token="))
          ?.split("=")[1];

        if (accessToken) {
          addDebugInfo("Already authenticated");
          setIsLoading(false);
          return;
        }

        // Authenticate with backend
        addDebugInfo("Authenticating with backend...");
        addDebugInfo("Sending POST to /api/auth/tg");
        
        const requestBody = { 
          initData: initData,
        };
        addDebugInfo(`Request body: ${JSON.stringify(requestBody).substring(0, 100)}...`);
            
            const response = await fetch("/api/auth/tg", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(requestBody),
        });

        addDebugInfo(`Response status: ${response.status}`);
        addDebugInfo(`Response headers: ${JSON.stringify(Object.fromEntries(response.headers.entries())).substring(0, 100)}...`);

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          addDebugInfo(`Authentication failed: ${JSON.stringify(errorData)}`);
          throw new Error(
            errorData.error || `Authentication failed: ${response.status}`
          );
        }

        const data = await response.json();
        addDebugInfo(`Authentication successful: ${JSON.stringify(data).substring(0, 100)}...`);

        // Show success feedback
        tg.HapticFeedback.notificationOccurred("success");

        // Redirect to profile or home
        router.push("/ru/profile");
      } catch (err) {
        addDebugInfo(`Telegram authentication error: ${err instanceof Error ? err.message : "Authentication failed"}`);
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
          
          {/* Debug info */}
          {debugInfo.length > 0 && (
            <div className="mt-6 text-xs text-left bg-gray-100 p-3 rounded max-h-40 overflow-y-auto">
              <div className="font-semibold mb-2">Debug Info:</div>
              {debugInfo.map((info, index) => (
                <div key={index} className="mb-1 text-gray-600">{info}</div>
              ))}
            </div>
          )}
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

