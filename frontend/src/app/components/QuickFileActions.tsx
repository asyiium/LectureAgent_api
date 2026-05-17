import { Download, ExternalLink } from 'lucide-react';

interface QuickFileActionsProps {
  fileName: string;
  fileData: string;
  fileType: string;
  className?: string;
}

export function QuickFileActions({ fileName, fileData, fileType, className = '' }: QuickFileActionsProps) {
  const handleDownload = (e: React.MouseEvent) => {
    e.stopPropagation();
    const link = document.createElement('a');
    link.href = fileData;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleOpen = (e: React.MouseEvent) => {
    e.stopPropagation();
    window.open(fileData, '_blank');
  };

  return (
    <div className={`flex gap-1 ${className}`}>
      <button
        onClick={handleDownload}
        className="p-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded transition-colors"
        title="Скачать"
      >
        <Download size={16} />
      </button>
      {(fileType === 'image' || fileType === 'video' || fileType === 'audio') && (
        <button
          onClick={handleOpen}
          className="p-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded transition-colors"
          title="Открыть в новой вкладке"
        >
          <ExternalLink size={16} />
        </button>
      )}
    </div>
  );
}
