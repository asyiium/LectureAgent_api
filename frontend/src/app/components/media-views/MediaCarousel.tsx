import { FileText, Music, Video, ChevronLeft, ChevronRight, Download } from 'lucide-react';
import { AttachedFile } from '../ChatMessage';
import { FileActionsMenu } from '../FileActionsMenu';
import { useState } from 'react';

interface Chat {
  id: string;
  title: string;
}

interface MediaCarouselProps {
  files: Array<AttachedFile & { messageId?: string }>;
  currentChatId?: string;
  chats?: Chat[];
  onFileClick?: (file: AttachedFile) => void;
  onDelete?: (fileId: string) => void;
  onCopy?: (fileId: string, targetChatId: string) => void;
  onMove?: (fileId: string, targetChatId: string) => void;
}

// Вариант 5: Карусель/галерея с большими превью
export function MediaCarousel({
  files,
  currentChatId,
  chats = [],
  onFileClick,
  onDelete,
  onCopy,
  onMove
}: MediaCarouselProps) {
  const [currentIndex, setCurrentIndex] = useState(0);

  if (files.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500 text-sm">
        Нет прикрепленных файлов
      </div>
    );
  }

  const currentFile = files[currentIndex];

  const goToPrevious = () => {
    setCurrentIndex((prev) => (prev === 0 ? files.length - 1 : prev - 1));
  };

  const goToNext = () => {
    setCurrentIndex((prev) => (prev === files.length - 1 ? 0 : prev + 1));
  };

  const handleDownload = () => {
    const link = document.createElement('a');
    link.href = currentFile.data;
    link.download = currentFile.name;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="p-3">
      <div className="text-gray-400 text-xs font-semibold mb-3 flex items-center justify-between">
        <span>МЕДИА</span>
        <div className="flex items-center gap-2">
          <span>{currentIndex + 1} / {files.length}</span>
          <button
            onClick={handleDownload}
            className="p-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded transition-colors"
            title="Скачать"
          >
            <Download size={16} />
          </button>
          {currentChatId && onDelete && onCopy && onMove && (
            <FileActionsMenu
              fileId={currentFile.messageId || `${currentIndex}`}
              fileName={currentFile.name}
              fileData={currentFile.data}
              fileType={currentFile.type}
              currentChatId={currentChatId}
              chats={chats}
              onDelete={(fileId) => {
                onDelete(fileId);
                if (currentIndex >= files.length - 1 && currentIndex > 0) {
                  setCurrentIndex(currentIndex - 1);
                }
              }}
              onCopy={onCopy}
              onMove={onMove}
            />
          )}
        </div>
      </div>

      <div className="relative">
        {/* Main preview */}
        <button
          onClick={() => onFileClick?.(currentFile)}
          className="w-full aspect-video bg-gray-800 rounded-lg overflow-hidden border border-gray-700 flex items-center justify-center mb-3"
        >
          {currentFile.type === 'image' && (
            <img
              src={currentFile.data}
              alt={currentFile.name}
              className="w-full h-full object-contain"
            />
          )}
          {currentFile.type === 'video' && (
            <video
              src={currentFile.data}
              className="w-full h-full object-contain"
            />
          )}
          {currentFile.type === 'audio' && (
            <Music size={48} className="text-purple-400" />
          )}
          {currentFile.type === 'text' && (
            <FileText size={48} className="text-green-400" />
          )}
        </button>

        {/* Navigation */}
        {files.length > 1 && (
          <>
            <button
              onClick={goToPrevious}
              className="absolute left-2 top-1/2 -translate-y-1/2 w-8 h-8 bg-black/50 hover:bg-black/75 rounded-full flex items-center justify-center text-white transition-colors"
            >
              <ChevronLeft size={20} />
            </button>
            <button
              onClick={goToNext}
              className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 bg-black/50 hover:bg-black/75 rounded-full flex items-center justify-center text-white transition-colors"
            >
              <ChevronRight size={20} />
            </button>
          </>
        )}
      </div>

      {/* File info */}
      <div className="text-sm text-gray-300 truncate mb-2">
        {currentFile.name}
      </div>

      {/* Thumbnails */}
      {files.length > 1 && (
        <div className="flex gap-2 overflow-x-auto pb-2">
          {files.map((file, index) => (
            <button
              key={index}
              onClick={() => setCurrentIndex(index)}
              className={`flex-shrink-0 w-16 h-16 rounded border-2 overflow-hidden transition-all ${
                index === currentIndex
                  ? 'border-blue-500 scale-105'
                  : 'border-gray-700 opacity-50 hover:opacity-100'
              }`}
            >
              {file.type === 'image' ? (
                <img
                  src={file.data}
                  alt={file.name}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full bg-gray-800 flex items-center justify-center">
                  {file.type === 'video' && <Video size={20} className="text-red-400" />}
                  {file.type === 'audio' && <Music size={20} className="text-purple-400" />}
                  {file.type === 'text' && <FileText size={20} className="text-green-400" />}
                </div>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
