import { useState, useEffect, useRef } from 'react';
import { Edit2, Check, X } from 'lucide-react';

interface ChatTitleEditorProps {
  title: string;
  onSave: (newTitle: string) => void;
  className?: string;
}

export function ChatTitleEditor({ title, onSave, className = '' }: ChatTitleEditorProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedTitle, setEditedTitle] = useState(title);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  const handleSave = () => {
    const trimmedTitle = editedTitle.trim();
    if (trimmedTitle && trimmedTitle !== title) {
      onSave(trimmedTitle);
    } else {
      setEditedTitle(title);
    }
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditedTitle(title);
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSave();
    } else if (e.key === 'Escape') {
      handleCancel();
    }
  };

  if (isEditing) {
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        <input
          ref={inputRef}
          type="text"
          value={editedTitle}
          onChange={(e) => setEditedTitle(e.target.value)}
          onKeyDown={handleKeyDown}
          className="flex-1 bg-gray-800 text-white px-3 py-1.5 rounded border border-gray-600 focus:outline-none focus:border-blue-500"
          maxLength={50}
        />
        <button
          onClick={handleSave}
          className="p-1.5 bg-green-600 hover:bg-green-700 text-white rounded transition-colors"
          title="Сохранить"
        >
          <Check size={16} />
        </button>
        <button
          onClick={handleCancel}
          className="p-1.5 bg-gray-600 hover:bg-gray-700 text-white rounded transition-colors"
          title="Отмена"
        >
          <X size={16} />
        </button>
      </div>
    );
  }

  return (
    <div className={`flex items-center gap-2 group ${className}`}>
      <span className="flex-1 truncate">{title}</span>
      <button
        onClick={() => setIsEditing(true)}
        className="opacity-0 group-hover:opacity-100 p-1 hover:bg-gray-700 rounded transition-all"
        title="Редактировать название"
      >
        <Edit2 size={14} className="text-gray-400" />
      </button>
    </div>
  );
}
