import { useState } from 'react';
import { Files } from 'lucide-react';
import { ChatHeader } from './components/ChatHeader';
import { ChatSidebar } from './components/ChatSidebar';
import { ChatMessages } from './components/ChatMessages';
import { ChatInput, AttachedFile } from './components/ChatInput';
import { MediaViewerDemo } from './components/MediaViewerDemo';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  file?: AttachedFile;
  timestamp: string;
}

interface Chat {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: string;
  messages: Message[];
}

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [username, setUsername] = useState('Пользователь');
  const [activeChat, setActiveChat] = useState('1');
  const [showMediaViewer, setShowMediaViewer] = useState(false);
  const [chats, setChats] = useState<Chat[]>([
    {
      id: '1',
      title: 'Клеточная биология',
      lastMessage: 'Привет! Как я могу помочь?',
      timestamp: 'Сегодня, 14:30',
      messages: [
        {
          id: '1',
          role: 'assistant',
          content: 'Привет! Я AI ассистент. Чем могу помочь?',
          timestamp: '14:30'
        }
      ]
    },
    {
      id: '2',
      title: 'Нейронные сети',
      lastMessage: 'Давайте обсудим архитектуру',
      timestamp: 'Вчера, 18:45',
      messages: []
    },
    {
      id: '3',
      title: 'AutoCAD проекты',
      lastMessage: '3D моделирование деталей',
      timestamp: '12 мая',
      messages: []
    },
    {
      id: '4',
      title: 'Алгоритмы сортировки',
      lastMessage: 'Быстрая сортировка в Python',
      timestamp: '10 мая',
      messages: []
    }
  ]);

  const currentChat = chats.find(chat => chat.id === activeChat);

  // Get all files from current chat with message IDs
  const currentChatFiles = currentChat?.messages
    .filter(msg => msg.file)
    .map(msg => ({ ...msg.file!, messageId: msg.id })) || [];

  const handleDeleteFile = (messageId: string) => {
    setChats(prevChats =>
      prevChats.map(chat =>
        chat.id === activeChat
          ? {
              ...chat,
              messages: chat.messages.map(msg =>
                msg.id === messageId ? { ...msg, file: undefined } : msg
              )
            }
          : chat
      )
    );
  };

  const handleCopyFile = (messageId: string, targetChatId: string) => {
    const message = currentChat?.messages.find(msg => msg.id === messageId);
    if (!message?.file) return;

    const newMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: `Скопировано из чата "${currentChat?.title}"`,
      file: message.file,
      timestamp: new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
    };

    setChats(prevChats =>
      prevChats.map(chat =>
        chat.id === targetChatId
          ? {
              ...chat,
              messages: [...chat.messages, newMessage],
              lastMessage: `📎 ${message.file.name}`,
              timestamp: 'Только что'
            }
          : chat
      )
    );
  };

  const handleMoveFile = (messageId: string, targetChatId: string) => {
    const message = currentChat?.messages.find(msg => msg.id === messageId);
    if (!message?.file) return;

    const newMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: `Перемещено из чата "${currentChat?.title}"`,
      file: message.file,
      timestamp: new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
    };

    setChats(prevChats =>
      prevChats.map(chat => {
        if (chat.id === activeChat) {
          return {
            ...chat,
            messages: chat.messages.map(msg =>
              msg.id === messageId ? { ...msg, file: undefined } : msg
            )
          };
        }
        if (chat.id === targetChatId) {
          return {
            ...chat,
            messages: [...chat.messages, newMessage],
            lastMessage: `📎 ${message.file.name}`,
            timestamp: 'Только что'
          };
        }
        return chat;
      })
    );
  };

  const handleSendMessage = (content: string, file?: AttachedFile) => {
    const newMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      file,
      timestamp: new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
    };

    let lastMessagePreview = content;
    if (file && !content) {
      lastMessagePreview = file.type === 'image' ? '🖼 Изображение' :
                          file.type === 'text' ? '📄 ' + file.name :
                          file.type === 'audio' ? '🎵 ' + file.name :
                          '🎬 ' + file.name;
    }

    setChats(prevChats =>
      prevChats.map(chat =>
        chat.id === activeChat
          ? {
              ...chat,
              messages: [...chat.messages, newMessage],
              lastMessage: lastMessagePreview,
              timestamp: 'Только что'
            }
          : chat
      )
    );

    // Simulate AI response
    setTimeout(() => {
      let aiContent = 'Я получил ваше сообщение';

      if (file) {
        if (file.type === 'image') {
          aiContent = 'Я вижу изображение, которое вы отправили. В реальном приложении я мог бы его проанализировать.';
        } else if (file.type === 'text') {
          aiContent = `Я прочитал текстовый файл "${file.name}". В реальном приложении я мог бы проанализировать его содержимое.`;
        } else if (file.type === 'audio') {
          aiContent = `Я получил аудиофайл "${file.name}". В реальном приложении я мог бы его транскрибировать.`;
        } else if (file.type === 'video') {
          aiContent = `Я получил видеофайл "${file.name}". В реальном приложении я мог бы проанализировать его содержимое.`;
        }
      }

      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: aiContent,
        timestamp: new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
      };

      setChats(prevChats =>
        prevChats.map(chat =>
          chat.id === activeChat
            ? {
                ...chat,
                messages: [...chat.messages, aiResponse],
                lastMessage: aiResponse.content,
                timestamp: 'Только что'
              }
            : chat
        )
      );
    }, 1000);
  };

  const handleNewChat = () => {
    const newChat: Chat = {
      id: Date.now().toString(),
      title: 'Новый чат',
      lastMessage: '',
      timestamp: 'Только что',
      messages: []
    };
    setChats([newChat, ...chats]);
    setActiveChat(newChat.id);
  };

  const handleRenameChat = (chatId: string, newTitle: string) => {
    setChats(prevChats =>
      prevChats.map(chat =>
        chat.id === chatId
          ? { ...chat, title: newTitle }
          : chat
      )
    );
  };

  const handleLogin = () => {
    setIsAuthenticated(true);
    setUsername('Иван Петров');
  };

  const handleSignUp = () => {
    setIsAuthenticated(true);
    setUsername('Новый пользователь');
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setUsername('');
  };

  return (
    <div className="size-full flex flex-col bg-gray-950 text-white">
      <ChatHeader
        isAuthenticated={isAuthenticated}
        username={username}
        onLogin={handleLogin}
        onSignUp={handleSignUp}
        onLogout={handleLogout}
      />

      <div className="flex-1 flex overflow-hidden">
        <ChatSidebar
          chats={chats}
          activeChat={activeChat}
          onSelectChat={setActiveChat}
          onNewChat={handleNewChat}
          onRenameChat={handleRenameChat}
        />

        <div className="flex-1 flex flex-col">
          <div className="h-12 border-b border-gray-700 bg-gray-900 flex items-center justify-between px-4">
            <div className="text-gray-300 text-sm">
              {currentChat?.title || 'Выберите чат'}
            </div>
            <button
              onClick={() => setShowMediaViewer(true)}
              className="flex items-center gap-2 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded transition-colors"
            >
              <Files size={16} />
              <span className="text-sm">Медиа ({currentChatFiles.length})</span>
            </button>
          </div>
          <ChatMessages messages={currentChat?.messages || []} />
          <ChatInput onSendMessage={handleSendMessage} />
        </div>
      </div>

      {showMediaViewer && (
        <MediaViewerDemo
          files={currentChatFiles}
          currentChatId={activeChat}
          chats={chats}
          onClose={() => setShowMediaViewer(false)}
          onDelete={handleDeleteFile}
          onCopy={handleCopyFile}
          onMove={handleMoveFile}
        />
      )}
    </div>
  );
}