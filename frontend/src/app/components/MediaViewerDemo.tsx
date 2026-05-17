import { X } from 'lucide-react';
import { AttachedFile } from './ChatMessage';
import { MediaCarousel } from './media-views/MediaCarousel';

interface Chat {
  id: string;
  title: string;
}

interface MediaViewerDemoProps {
  files: Array<AttachedFile & { messageId?: string }>;
  currentChatId: string;
  chats: Chat[];
  onClose: () => void;
  onDelete: (fileId: string) => void;
  onCopy: (fileId: string, targetChatId: string) => void;
  onMove: (fileId: string, targetChatId: string) => void;
}

export function MediaViewerDemo({
  files,
  currentChatId,
  chats,
  onClose,
  onDelete,
  onCopy,
  onMove
}: MediaViewerDemoProps) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 rounded-lg border border-gray-700 w-full max-w-2xl max-h-[90vh] flex flex-col">
        <div className="p-4 border-b border-gray-700 flex items-center justify-between">
          <h2 className="text-white font-semibold">
            Медиа-файлы
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto bg-gray-950">
          <MediaCarousel
            files={files}
            currentChatId={currentChatId}
            chats={chats}
            onDelete={onDelete}
            onCopy={onCopy}
            onMove={onMove}
          />
        </div>
      </div>
    </div>
  );
}
