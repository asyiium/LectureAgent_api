import { MoreVertical, Trash2, Copy, MoveRight, X, Download, ExternalLink } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';

interface Chat {
  id: string;
  title: string;
}

interface FileActionsMenuProps {
  fileId: string;
  fileName: string;
  fileData: string;
  fileType: string;
  currentChatId: string;
  chats: Chat[];
  onDelete: (fileId: string) => void;
  onCopy: (fileId: string, targetChatId: string) => void;
  onMove: (fileId: string, targetChatId: string) => void;
}

export function FileActionsMenu({
  fileId,
  fileName,
  fileData,
  fileType,
  currentChatId,
  chats,
  onDelete,
  onCopy,
  onMove
}: FileActionsMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [showChatSelector, setShowChatSelector] = useState<'copy' | 'move' | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setShowChatSelector(null);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const handleDelete = () => {
    if (confirm(`Удалить файл "${fileName}"?`)) {
      onDelete(fileId);
      setIsOpen(false);
    }
  };

  const handleCopyToChat = (targetChatId: string) => {
    onCopy(fileId, targetChatId);
    setIsOpen(false);
    setShowChatSelector(null);
  };

  const handleMoveToChat = (targetChatId: string) => {
    onMove(fileId, targetChatId);
    setIsOpen(false);
    setShowChatSelector(null);
  };

  const handleDownload = () => {
    const link = document.createElement('a');
    link.href = fileData;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    setIsOpen(false);
  };

  const handleOpen = () => {
    window.open(fileData, '_blank');
    setIsOpen(false);
  };

  const otherChats = chats.filter(chat => chat.id !== currentChatId);

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={(e) => {
          e.stopPropagation();
          setIsOpen(!isOpen);
        }}
        className="p-1 hover:bg-gray-700 rounded transition-colors"
      >
        <MoreVertical size={16} className="text-gray-400" />
      </button>

      {isOpen && (
        <div className="absolute right-0 top-full mt-1 bg-gray-800 border border-gray-700 rounded-lg shadow-lg z-50 min-w-48">
          {!showChatSelector ? (
            <>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleDownload();
                }}
                className="w-full flex items-center gap-3 px-4 py-2 hover:bg-gray-700 text-gray-300 text-sm transition-colors rounded-t-lg"
              >
                <Download size={16} />
                Скачать
              </button>
              {(fileType === 'image' || fileType === 'video' || fileType === 'audio') && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleOpen();
                  }}
                  className="w-full flex items-center gap-3 px-4 py-2 hover:bg-gray-700 text-gray-300 text-sm transition-colors"
                >
                  <ExternalLink size={16} />
                  Открыть в новой вкладке
                </button>
              )}
              <div className="border-t border-gray-700"></div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setShowChatSelector('copy');
                }}
                className="w-full flex items-center gap-3 px-4 py-2 hover:bg-gray-700 text-gray-300 text-sm transition-colors"
              >
                <Copy size={16} />
                Копировать в чат
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setShowChatSelector('move');
                }}
                className="w-full flex items-center gap-3 px-4 py-2 hover:bg-gray-700 text-gray-300 text-sm transition-colors"
              >
                <MoveRight size={16} />
                Переместить в чат
              </button>
              <div className="border-t border-gray-700"></div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleDelete();
                }}
                className="w-full flex items-center gap-3 px-4 py-2 hover:bg-red-600 text-red-400 hover:text-white text-sm transition-colors rounded-b-lg"
              >
                <Trash2 size={16} />
                Удалить
              </button>
            </>
          ) : (
            <>
              <div className="px-4 py-2 border-b border-gray-700 flex items-center justify-between">
                <span className="text-gray-400 text-xs font-semibold">
                  {showChatSelector === 'copy' ? 'КОПИРОВАТЬ В:' : 'ПЕРЕМЕСТИТЬ В:'}
                </span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setShowChatSelector(null);
                  }}
                  className="text-gray-400 hover:text-white"
                >
                  <X size={14} />
                </button>
              </div>
              <div className="max-h-48 overflow-y-auto">
                {otherChats.length === 0 ? (
                  <div className="px-4 py-3 text-gray-500 text-sm">
                    Нет других чатов
                  </div>
                ) : (
                  otherChats.map((chat) => (
                    <button
                      key={chat.id}
                      onClick={(e) => {
                        e.stopPropagation();
                        if (showChatSelector === 'copy') {
                          handleCopyToChat(chat.id);
                        } else {
                          handleMoveToChat(chat.id);
                        }
                      }}
                      className="w-full px-4 py-2 hover:bg-gray-700 text-gray-300 text-sm text-left transition-colors"
                    >
                      <div className="truncate">{chat.title}</div>
                    </button>
                  ))
                )}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
