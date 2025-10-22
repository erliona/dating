"use client";

import { useRouter } from "next/navigation";

/**
 * Welcome Page
 * 
 * Shown to new users after successful Telegram authentication
 * but before they have created a profile.
 */
export default function WelcomePage() {
  const router = useRouter();

  const handleStartDating = () => {
    router.push("/ru/onboarding");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 text-center">
        {/* Logo/Icon */}
        <div className="w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full mx-auto mb-6 flex items-center justify-center">
          <span className="text-white text-3xl font-bold">💕</span>
        </div>
        
        {/* Title */}
        <h1 className="text-3xl font-bold text-gray-800 mb-4">
          Добро пожаловать в Dating!
        </h1>
        
        {/* Description */}
        <p className="text-gray-600 mb-8 leading-relaxed">
          Найди свою половинку, общайся с интересными людьми и встречайся рядом с тобой
        </p>
        
        {/* Features */}
        <div className="space-y-4 text-left mb-8">
          <div className="flex items-center text-gray-600">
            <span className="text-green-500 mr-3 text-xl">✓</span>
            <span>Безопасная авторизация через Telegram</span>
          </div>
          <div className="flex items-center text-gray-600">
            <span className="text-green-500 mr-3 text-xl">✓</span>
            <span>Поиск людей рядом с тобой</span>
          </div>
          <div className="flex items-center text-gray-600">
            <span className="text-green-500 mr-3 text-xl">✓</span>
            <span>Приватность и безопасность</span>
          </div>
        </div>
        
        {/* Start Button */}
        <button 
          onClick={handleStartDating}
          className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold py-4 px-6 rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all duration-200 shadow-lg text-lg"
        >
          🚀 Начать знакомства
        </button>
        
        {/* Footer */}
        <p className="text-xs text-gray-400 mt-6">
          Открыто через Telegram Mini App
        </p>
      </div>
    </div>
  );
}
