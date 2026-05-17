import { LogIn, LogOut, UserPlus } from 'lucide-react';

interface ChatHeaderProps {
  isAuthenticated: boolean;
  username?: string;
  onLogin: () => void;
  onSignUp: () => void;
  onLogout: () => void;
}

export function ChatHeader({ isAuthenticated, username, onLogin, onSignUp, onLogout }: ChatHeaderProps) {
  return (
    <div className="h-16 bg-gray-900 border-b border-gray-700 flex items-center justify-between px-6">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg"></div>
        <span className="text-white font-semibold text-lg">AI Messenger</span>
      </div>

      <div className="flex items-center gap-3">
        {isAuthenticated ? (
          <>
            <span className="text-gray-300 text-sm">{username}</span>
            <button
              onClick={onLogout}
              className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
            >
              <LogOut size={18} />
              Выход
            </button>
          </>
        ) : (
          <>
            <button
              onClick={onLogin}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
            >
              <LogIn size={18} />
              Вход
            </button>
            <button
              onClick={onSignUp}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
            >
              <UserPlus size={18} />
              Регистрация
            </button>
          </>
        )}
      </div>
    </div>
  );
}
