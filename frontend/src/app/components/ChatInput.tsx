import { useState, useRef } from 'react';
import { Send, Paperclip, X, FileText, Music, Video, Image as ImageIcon } from 'lucide-react';

export interface AttachedFile {
  type: 'image' | 'text' | 'audio' | 'video';
  data: string;
  name: string;
  size?: number;
}

interface ChatInputProps {
  onSendMessage: (message: string, file?: AttachedFile) => void;
}

export function ChatInput({ onSendMessage }: ChatInputProps) {
  const [message, setMessage] = useState('');
  const [attachedFile, setAttachedFile] = useState<AttachedFile | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() || attachedFile) {
      onSendMessage(message, attachedFile || undefined);
      setMessage('');
      setAttachedFile(null);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const fileName = file.name;
    const fileSize = file.size;

    // Determine file type
    let fileType: 'image' | 'text' | 'audio' | 'video';
    if (file.type.startsWith('image/')) {
      fileType = 'image';
    } else if (file.type.startsWith('audio/')) {
      fileType = 'audio';
    } else if (file.type.startsWith('video/')) {
      fileType = 'video';
    } else if (file.type === 'text/plain' || file.type === 'text/markdown' || fileName.endsWith('.md') || fileName.endsWith('.txt')) {
      fileType = 'text';
    } else {
      alert('Неподдерживаемый тип файла');
      return;
    }

    const reader = new FileReader();
    reader.onloadend = () => {
      setAttachedFile({
        type: fileType,
        data: reader.result as string,
        name: fileName,
        size: fileSize
      });
    };

    if (fileType === 'text') {
      reader.readAsText(file);
    } else {
      reader.readAsDataURL(file);
    }
  };

  const handleRemoveFile = () => {
    setAttachedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const getFileIcon = (type: string) => {
    switch (type) {
      case 'image':
        return <ImageIcon size={20} />;
      case 'text':
        return <FileText size={20} />;
      case 'audio':
        return <Music size={20} />;
      case 'video':
        return <Video size={20} />;
      default:
        return <Paperclip size={20} />;
    }
  };

  return (
    <div className="border-t border-gray-700 bg-gray-900 p-4">
      {attachedFile && (
        <div className="mb-3 relative inline-block">
          {attachedFile.type === 'image' && (
            <img
              src={attachedFile.data}
              alt="Preview"
              className="max-h-32 rounded-lg border border-gray-700"
            />
          )}

          {attachedFile.type === 'text' && (
            <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 max-w-md">
              <div className="flex items-center gap-2 text-blue-400 mb-2">
                <FileText size={20} />
                <span className="font-medium">{attachedFile.name}</span>
              </div>
              <div className="text-gray-400 text-sm max-h-20 overflow-y-auto">
                {attachedFile.data.substring(0, 200)}
                {attachedFile.data.length > 200 && '...'}
              </div>
            </div>
          )}

          {attachedFile.type === 'audio' && (
            <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 flex items-center gap-3">
              <Music size={24} className="text-green-400" />
              <div>
                <div className="text-white text-sm">{attachedFile.name}</div>
                <div className="text-gray-400 text-xs">{formatFileSize(attachedFile.size)}</div>
              </div>
            </div>
          )}

          {attachedFile.type === 'video' && (
            <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden max-w-md">
              <video
                src={attachedFile.data}
                className="max-h-32 w-full"
                controls
              />
              <div className="p-2 text-gray-400 text-xs">
                {attachedFile.name} · {formatFileSize(attachedFile.size)}
              </div>
            </div>
          )}

          <button
            onClick={handleRemoveFile}
            className="absolute -top-2 -right-2 w-6 h-6 bg-red-600 hover:bg-red-700 rounded-full flex items-center justify-center text-white"
          >
            <X size={14} />
          </button>
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex items-end gap-3">
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileSelect}
          accept="image/*,audio/mp3,audio/mpeg,video/mp4,.txt,.md"
          className="hidden"
        />

        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="flex-shrink-0 w-10 h-10 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg flex items-center justify-center transition-colors"
          title="Прикрепить файл"
        >
          <Paperclip size={20} />
        </button>

        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
          placeholder="Введите сообщение..."
          className="flex-1 bg-gray-800 text-white placeholder-gray-400 rounded-lg px-4 py-3 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
          rows={1}
          style={{
            minHeight: '44px',
            maxHeight: '120px',
          }}
        />

        <button
          type="submit"
          disabled={!message.trim() && !attachedFile}
          className="flex-shrink-0 w-10 h-10 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded-lg flex items-center justify-center transition-colors"
        >
          <Send size={20} />
        </button>
      </form>
    </div>
  );
}
