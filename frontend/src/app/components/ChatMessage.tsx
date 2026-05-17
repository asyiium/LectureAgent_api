import { Bot, User, FileText, Music, Video } from 'lucide-react';
import { QuickFileActions } from './QuickFileActions';

export interface AttachedFile {
  type: 'image' | 'text' | 'audio' | 'video';
  data: string;
  name: string;
  size?: number;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  file?: AttachedFile;
  timestamp: string;
}

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex gap-4 p-6 ${isUser ? 'bg-transparent' : 'bg-gray-800/50'}`}>
      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
        isUser ? 'bg-blue-600' : 'bg-purple-600'
      }`}>
        {isUser ? <User size={18} /> : <Bot size={18} />}
      </div>

      <div className="flex-1 min-w-0">
        <div className="text-gray-300 text-sm mb-1">
          {isUser ? 'Вы' : 'AI Ассистент'}
        </div>

        {message.content && (
          <div className="text-white whitespace-pre-wrap break-words">
            {message.content}
          </div>
        )}

        {message.file && (
          <div className="mt-3 group/file">
            {message.file.type === 'image' && (
              <div className="relative inline-block">
                <img
                  src={message.file.data}
                  alt={message.file.name}
                  className="max-w-sm rounded-lg border border-gray-700"
                />
                <div className="absolute top-2 right-2 opacity-0 group-hover/file:opacity-100 transition-opacity">
                  <QuickFileActions
                    fileName={message.file.name}
                    fileData={message.file.data}
                    fileType={message.file.type}
                  />
                </div>
              </div>
            )}

            {message.file.type === 'text' && (
              <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 max-w-2xl">
                <div className="flex items-center gap-2 text-blue-400 mb-3 pb-3 border-b border-gray-700">
                  <FileText size={20} />
                  <span className="font-medium flex-1">{message.file.name}</span>
                  <QuickFileActions
                    fileName={message.file.name}
                    fileData={message.file.data}
                    fileType={message.file.type}
                  />
                </div>
                <div className="text-gray-300 text-sm whitespace-pre-wrap break-words max-h-96 overflow-y-auto">
                  {message.file.data}
                </div>
              </div>
            )}

            {message.file.type === 'audio' && (
              <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 max-w-md">
                <div className="flex items-center gap-3 mb-3">
                  <Music size={24} className="text-green-400" />
                  <div className="flex-1 min-w-0">
                    <div className="text-white text-sm truncate">{message.file.name}</div>
                  </div>
                  <QuickFileActions
                    fileName={message.file.name}
                    fileData={message.file.data}
                    fileType={message.file.type}
                  />
                </div>
                <audio
                  src={message.file.data}
                  controls
                  className="w-full"
                />
              </div>
            )}

            {message.file.type === 'video' && (
              <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden max-w-2xl">
                <video
                  src={message.file.data}
                  controls
                  className="w-full max-h-96"
                />
                <div className="p-3 flex items-center gap-2 text-gray-400 text-sm">
                  <Video size={18} />
                  <span className="flex-1">{message.file.name}</span>
                  <QuickFileActions
                    fileName={message.file.name}
                    fileData={message.file.data}
                    fileType={message.file.type}
                  />
                </div>
              </div>
            )}
          </div>
        )}

        <div className="text-gray-500 text-xs mt-2">
          {message.timestamp}
        </div>
      </div>
    </div>
  );
}
