export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 text-center">
        {/* Logo/Icon */}
        <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full mx-auto mb-6 flex items-center justify-center">
          <span className="text-white text-2xl font-bold">💕</span>
        </div>
        
        {/* Title */}
        <h1 className="text-3xl font-bold text-gray-800 mb-4">
          Добро пожаловать в Dating!
        </h1>
        
        {/* Description */}
        <p className="text-gray-600 mb-8 leading-relaxed">
          Найди свою половинку, общайся с интересными людьми и встречайся рядом с тобой
        </p>
        
        {/* Status */}
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
          <div className="flex items-center justify-center text-green-700">
            <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
            <span className="text-sm font-medium">Приложение готово к работе!</span>
          </div>
        </div>
        
        {/* Features */}
        <div className="space-y-3 text-left mb-8">
          <div className="flex items-center text-gray-600">
            <span className="text-green-500 mr-3">✓</span>
            <span>Безопасная авторизация через Telegram</span>
          </div>
          <div className="flex items-center text-gray-600">
            <span className="text-green-500 mr-3">✓</span>
            <span>Поиск людей рядом с тобой</span>
          </div>
          <div className="flex items-center text-gray-600">
            <span className="text-green-500 mr-3">✓</span>
            <span>Приватность и безопасность</span>
          </div>
        </div>
        
        {/* Button */}
        <button className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold py-3 px-6 rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all duration-200 shadow-lg">
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
