import { MessageSquare, Plus } from 'lucide-react';
import { ChatTitleEditor } from './ChatTitleEditor';

interface Chat {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: string;
}

interface ChatSidebarProps {
  chats: Chat[];
  activeChat: string;
  onSelectChat: (id: string) => void;
  onNewChat: () => void;
  onRenameChat: (chatId: string, newTitle: string) => void;
}

export function ChatSidebar({ chats, activeChat, onSelectChat, onNewChat, onRenameChat }: ChatSidebarProps) {
  return (
    <div className="w-64 bg-gray-900 border-r border-gray-700 flex flex-col h-full">
      <div className="p-4 border-b border-gray-700">
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
        >
          <Plus size={20} />
          Новый чат
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        {chats.map((chat) => (
          <div
            key={chat.id}
            className={`w-full p-4 border-b border-gray-800 transition-colors ${
              activeChat === chat.id ? 'bg-gray-800' : 'hover:bg-gray-800'
            }`}
          >
            <div className="flex items-start gap-3">
              <button
                onClick={() => onSelectChat(chat.id)}
                className="flex-shrink-0"
              >
                <MessageSquare size={20} className="text-gray-400 mt-1" />
              </button>
              <div className="flex-1 min-w-0">
                <div className="mb-1">
                  <div className="text-white text-sm font-medium">
                    <ChatTitleEditor
                      title={chat.title}
                      onSave={(newTitle) => onRenameChat(chat.id, newTitle)}
                    />
                  </div>
                </div>
                <button
                  onClick={() => onSelectChat(chat.id)}
                  className="w-full text-left"
                >
                  <div className="text-gray-400 text-xs truncate mt-1">
                    {chat.lastMessage}
                  </div>
                  <div className="text-gray-500 text-xs mt-1">
                    {chat.timestamp}
                  </div>
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
