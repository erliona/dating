"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

interface Profile {
  user_id: number;
  name: string;
  age: number;
  gender: string;
  city: string;
  bio: string;
  photos: string[];
}

/**
 * Profile Page (Protected)
 *
 * Profile page for registered users - shows real profile data.
 */
export default function ProfilePage() {
  const router = useRouter();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadProfile = async () => {
      try {
        // Get user_id from JWT token
        const accessToken = document.cookie
          .split("; ")
          .find((row) => row.startsWith("access_token="))
          ?.split("=")[1];

        if (!accessToken) {
          setError("No access token found");
          setLoading(false);
          return;
        }

        // Decode JWT to get user_id
        const tokenPayload = JSON.parse(atob(accessToken.split('.')[1]));
        const userId = tokenPayload.user_id;

        // Fetch profile data
        const response = await fetch(`/api/profiles/${userId}`);
        
        if (!response.ok) {
          if (response.status === 404) {
            setError("Profile not found");
          } else {
            setError("Failed to load profile");
          }
          setLoading(false);
          return;
        }

        const data = await response.json();
        setProfile(data.profile);
      } catch (err) {
        console.error("Error loading profile:", err);
        setError("Failed to load profile");
      } finally {
        setLoading(false);
      }
    };

    loadProfile();
  }, []);

  const handleEditProfile = () => {
    router.push("/ru/onboarding");
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 text-center">
          <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full mx-auto mb-6 flex items-center justify-center">
            <span className="text-white text-2xl font-bold">💕</span>
          </div>
          
          <div className="mb-6">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-500 border-r-transparent" />
          </div>
          
          <h2 className="text-xl font-semibold text-gray-800 mb-2">
            Загрузка профиля...
          </h2>
          <p className="text-gray-600 text-sm">
            Получаем информацию о вашем профиле
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 text-center">
          <div className="w-16 h-16 bg-gradient-to-r from-red-500 to-pink-600 rounded-full mx-auto mb-6 flex items-center justify-center">
            <span className="text-white text-2xl font-bold">⚠️</span>
          </div>
          
          <h2 className="text-xl font-semibold text-gray-800 mb-2">
            Ошибка загрузки
          </h2>
          <p className="text-gray-600 text-sm mb-6">
            {error}
          </p>
          
          <button
            onClick={() => window.location.reload()}
            className="w-full bg-blue-500 hover:bg-blue-600 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 shadow-lg"
          >
            Попробовать снова
          </button>
        </div>
      </div>
    );
  }

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
              Мой профиль
            </h1>
            <p className="text-gray-600 text-sm">
              Управляй своим профилем и настройками
            </p>
          </div>
        </div>

        {/* Profile Info */}
        <div className="bg-white rounded-2xl shadow-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">
            Информация о профиле
          </h2>
          
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Имя</span>
              <span className="text-gray-800 font-medium">{profile?.name || "Не указано"}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Возраст</span>
              <span className="text-gray-800 font-medium">{profile?.age || "Не указан"}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Пол</span>
              <span className="text-gray-800 font-medium">{profile?.gender || "Не указан"}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Город</span>
              <span className="text-gray-800 font-medium">{profile?.city || "Не указан"}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Фотографии</span>
              <span className="text-gray-800 font-medium">{profile?.photos?.length || 0} из 3</span>
            </div>
          </div>
          
          {profile?.bio && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">О себе</h3>
              <p className="text-gray-600 text-sm">{profile.bio}</p>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="space-y-3">
          <button 
            onClick={handleEditProfile}
            className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold py-3 px-6 rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all duration-200 shadow-lg"
          >
            ✏️ Редактировать профиль
          </button>
        </div>

        {/* Footer */}
        <p className="text-xs text-gray-400 text-center mt-6">
          Dating App • Профиль пользователя
        </p>
      </div>
    </div>
  );
}

