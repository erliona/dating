"use client";

import { useAuth } from "@/shared/hooks/use-auth";

/**
 * Profile Page (Protected)
 *
 * User profile page after successful Telegram authentication.
 */

export default function ProfilePage() {
  const { logout } = useAuth();

  const handleLogout = async () => {
    await logout();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 p-4">
      <div className="max-w-md mx-auto pt-8">
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-xl p-6 mb-6">
          <div className="text-center">
            <div className="w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full mx-auto mb-4 flex items-center justify-center">
              <span className="text-white text-3xl font-bold">👤</span>
            </div>
            <h1 className="text-2xl font-bold text-gray-800 mb-2">
              Добро пожаловать!
            </h1>
            <p className="text-gray-600 text-sm">
              Вы успешно авторизованы через Telegram
            </p>
          </div>
        </div>

        {/* Profile Status */}
        <div className="bg-white rounded-2xl shadow-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">
            Статус профиля
          </h2>
          
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Авторизация</span>
              <span className="text-green-600 font-medium">✅ Готово</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Профиль</span>
              <span className="text-yellow-600 font-medium">⚠️ Не заполнен</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Фотографии</span>
              <span className="text-yellow-600 font-medium">⚠️ Не загружены</span>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="space-y-3">
          <button className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold py-3 px-6 rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all duration-200 shadow-lg">
            📝 Заполнить профиль
          </button>
          
          <button className="w-full bg-gradient-to-r from-green-500 to-teal-600 text-white font-semibold py-3 px-6 rounded-lg hover:from-green-600 hover:to-teal-700 transition-all duration-200 shadow-lg">
            🔍 Начать поиск
          </button>
          
          <button
            onClick={handleLogout}
            className="w-full bg-gray-200 text-gray-700 font-semibold py-3 px-6 rounded-lg hover:bg-gray-300 transition-all duration-200"
          >
            🚪 Выйти
          </button>
        </div>

        {/* Footer */}
        <p className="text-xs text-gray-400 text-center mt-6">
          Dating App • Авторизован через Telegram
        </p>
      </div>
    </div>
  );
}
