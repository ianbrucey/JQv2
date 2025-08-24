import React, { useState } from 'react';
import { useListCaseFiles, useDeleteCaseFile } from '#/hooks/mutation/use-legal-cases';
import { FileItem } from '#/api/legal-cases';
import { FaFolder, FaFolderOpen, FaFile, FaSpinner, FaTrash } from 'react-icons/fa';

interface CaseFileBrowserProps {
  conversationId: string;
}

interface FileTreeItemProps {
  item: FileItem;
  onNavigate: (path: string) => void;
  currentPath: string;
  onDelete: (path: string) => void;
}

function FileTreeItem({ item, onNavigate, currentPath, onDelete }: FileTreeItemProps) {
  const isDirectory = item.type === 'directory';
  const fullPath = currentPath ? `${currentPath}/${item.name}` : item.name;

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleDateString();
  };

  return (
    <div
      className={`flex items-center gap-2 p-2 rounded hover:bg-gray-800 ${
        isDirectory ? 'cursor-pointer' : 'cursor-default'
      }`}
      onClick={() => isDirectory && onNavigate(fullPath)}
    >
      <div className="flex-shrink-0">
        {isDirectory ? (
          <FaFolder className="text-blue-400 w-4 h-4" />
        ) : (
          <FaFile className="text-gray-400 w-4 h-4" />
        )}
      </div>
      
      <div className="flex-1 min-w-0">
        <div className="text-sm text-gray-200 truncate">{item.name}</div>
        {!isDirectory && (
          <div className="text-xs text-gray-500">
            {formatFileSize(item.size)} • {formatDate(item.modified)}
          </div>
        )}
      </div>
      <button
        onClick={(e) => {
          e.stopPropagation();
          if (window.confirm(`Are you sure you want to delete ${item.name}?`)) {
            onDelete(fullPath);
          }
        }}
        className="text-gray-500 hover:text-red-400 p-1 rounded-full"
      >
        <FaTrash />
      </button>
    </div>
  );
}

interface BreadcrumbProps {
  path: string;
  onNavigate: (path: string) => void;
}

function Breadcrumb({ path, onNavigate }: BreadcrumbProps) {
  const parts = path ? path.split('/').filter(Boolean) : [];
  
  return (
    <div className="flex items-center gap-1 text-sm text-gray-400 mb-4">
      <button
        onClick={() => onNavigate('')}
        className="hover:text-gray-200 px-2 py-1 rounded"
      >
        Root
      </button>
      {parts.map((part, index) => {
        const partPath = parts.slice(0, index + 1).join('/');
        return (
          <React.Fragment key={index}>
            <span>/</span>
            <button
              onClick={() => onNavigate(partPath)}
              className="hover:text-gray-200 px-2 py-1 rounded"
            >
              {part}
            </button>
          </React.Fragment>
        );
      })}
    </div>
  );
}

export function CaseFileBrowser({ conversationId }: CaseFileBrowserProps) {
  const [currentPath, setCurrentPath] = useState<string>('');
  const { data, isLoading, error, refetch } = useListCaseFiles(conversationId, currentPath);
  const deleteFileMutation = useDeleteCaseFile(conversationId, currentPath);

  const handleNavigate = (path: string) => {
    setCurrentPath(path);
  };

  const handleDelete = (path: string) => {
    deleteFileMutation.mutate(path);
  };

  const handleRefresh = () => {
    refetch();
  };

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-4">
        <div className="flex items-center gap-2 text-red-400">
          <span>Failed to load files</span>
          <button
            onClick={handleRefresh}
            className="text-xs bg-red-800 hover:bg-red-700 px-2 py-1 rounded"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-base-primary border border-gray-700 rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-sm text-gray-300 font-medium">File Browser</h4>
        <button
          onClick={handleRefresh}
          disabled={isLoading}
          className="text-xs text-gray-400 hover:text-gray-200 disabled:opacity-50"
        >
          {isLoading ? <FaSpinner className="animate-spin" /> : 'Refresh'}
        </button>
      </div>

      <Breadcrumb path={currentPath} onNavigate={handleNavigate} />

      <div className="bg-gray-900 rounded p-3 max-h-96 overflow-auto">
        {isLoading ? (
          <div className="flex items-center justify-center py-8 text-gray-400">
            <FaSpinner className="animate-spin mr-2" />
            Loading files...
          </div>
        ) : data?.items.length ? (
          <div className="space-y-1">
            {/* Show parent directory link if not at root */}
            {currentPath && (
              <div
                className="flex items-center gap-2 p-2 rounded hover:bg-gray-800 cursor-pointer border-b border-gray-700 mb-2"
                onClick={() => {
                  const parentPath = currentPath.split('/').slice(0, -1).join('/');
                  handleNavigate(parentPath);
                }}
              >
                <FaFolderOpen className="text-blue-400 w-4 h-4" />
                <span className="text-sm text-gray-300">.. (Parent Directory)</span>
              </div>
            )}
            
            {/* Sort directories first, then files */}
            {data.items
              .sort((a, b) => {
                if (a.type !== b.type) {
                  return a.type === 'directory' ? -1 : 1;
                }
                return a.name.localeCompare(b.name);
              })
              .map((item) => (
                <FileTreeItem
                  key={item.path}
                  item={item}
                  onNavigate={handleNavigate}
                  currentPath={currentPath}
                  onDelete={handleDelete}
                />
              ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <FaFolder className="mx-auto mb-2 w-8 h-8 opacity-50" />
            <p>No files found in this directory</p>
          </div>
        )}
      </div>

      {data && (
        <div className="mt-2 text-xs text-gray-500">
          {data.total} item{data.total !== 1 ? 's' : ''} in {currentPath || 'root'}
        </div>
      )}
    </div>
  );
}
