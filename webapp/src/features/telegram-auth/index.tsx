"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

declare global {
  interface Window {
    Telegram?: {
      WebApp: {
        initData: string;
        initDataUnsafe: any;
        themeParams: {
          bg_color: string;
          text_color: string;
          hint_color: string;
          link_color: string;
          button_color: string;
          button_text_color: string;
        };
        expand: () => void;
        setHeaderColor: (color: string) => void;
        HapticFeedback: {
          notificationOccurred: (type: "success" | "warning" | "error") => void;
        };
      };
    };
  }
}

/**
 * TelegramAuth component
 * 
 * Simple debug version to test if component loads correctly
 */
export function TelegramAuth({ children }: { children: React.ReactNode }) {
  const [debugInfo, setDebugInfo] = useState<string[]>([]);

  useEffect(() => {
    const info = [
      "✅ TelegramAuth component loaded successfully",
      "✅ React component is working",
      "✅ Next.js routing is working", 
      "✅ CSS styling is working",
      `🔍 window.Telegram: ${typeof window !== 'undefined' && window.Telegram ? 'present' : 'missing'}`,
      `🔍 WebApp: ${typeof window !== 'undefined' && window.Telegram?.WebApp ? 'present' : 'missing'}`,
      `🔍 initData: ${typeof window !== 'undefined' && window.Telegram?.WebApp?.initData ? 'present' : 'missing'}`,
      `🔍 User Agent: ${typeof window !== 'undefined' ? navigator.userAgent.substring(0, 50) + '...' : 'N/A'}`,
      `🔍 Location: ${typeof window !== 'undefined' ? window.location.href : 'N/A'}`,
    ];
    setDebugInfo(info);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 text-center">
        {/* Logo/Icon */}
        <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full mx-auto mb-6 flex items-center justify-center">
          <span className="text-white text-2xl font-bold">💕</span>
        </div>
        
        {/* Title */}
        <h2 className="text-xl font-semibold text-gray-800 mb-2">
          TelegramAuth Component Loaded!
        </h2>
        <p className="text-gray-600 text-sm mb-6">
          This means the component is working correctly.
        </p>
        
        {/* Debug info */}
        <div className="text-xs text-left bg-gray-100 p-3 rounded max-h-40 overflow-y-auto">
          <div className="font-semibold mb-2">Debug Info:</div>
          {debugInfo.map((info, index) => (
            <div key={index} className="mb-1 text-gray-600">{info}</div>
          ))}
        </div>
        
        {/* Button to continue */}
        <button 
          onClick={() => window.location.reload()}
          className="mt-6 bg-blue-500 hover:bg-blue-600 text-white font-semibold py-2 px-4 rounded"
        >
          Reload Page
        </button>
      </div>
    </div>
  );
}