import React, { useCallback, useMemo, useRef, useState } from 'react';
import { useCurrentWorkspace, useListCaseDocuments, useUploadCaseDocuments } from '#/hooks/mutation/use-legal-cases';

const FOLDERS = [
  { value: 'inbox', label: 'Inbox' },
  { value: 'exhibits', label: 'Exhibits' },
  { value: 'research', label: 'Research' },
  { value: 'active_drafts', label: 'Active Drafts' },
] as const;

type FolderValue = typeof FOLDERS[number]['value'];

interface DocumentsUploaderProps {
  caseId: string;
}

export function DocumentsUploader({ caseId }: DocumentsUploaderProps) {
  const { data: workspace } = useCurrentWorkspace();
  const [folder, setFolder] = useState<FolderValue>('inbox');
  const [files, setFiles] = useState<File[]>([]);
  const [errors, setErrors] = useState<string[]>([]);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const { mutateAsync: uploadDocs, isPending } = useUploadCaseDocuments(caseId);
  const { data: listData, refetch } = useListCaseDocuments(caseId, folder);

  const onFilesSelected = useCallback((selected: FileList | null) => {
    if (!selected) return;
    const allowedExt = ['.pdf', '.png', '.jpg', '.jpeg', '.tif', '.tiff', '.docx', '.txt', '.md'];
    const maxSize = 100 * 1024 * 1024;
    const newErrors: string[] = [];
    const accepted: File[] = [];

    Array.from(selected).forEach((f) => {
      const ext = (f.name.match(/\.[^\.]+$/)?.[0] || '').toLowerCase();
      if (!allowedExt.includes(ext)) {
        newErrors.push(`Blocked type: ${f.name}`);
        return;
      }
      if (f.size > maxSize) {
        newErrors.push(`Too large (>100MB): ${f.name}`);
        return;
      }
      accepted.push(f);
    });

    setErrors((prev) => [...prev, ...newErrors]);
    setFiles((prev) => [...prev, ...accepted]);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    onFilesSelected(e.dataTransfer.files);
  }, [onFilesSelected]);

  const handleUpload = useCallback(async () => {
    if (!files.length) return;
    try {
      await uploadDocs({ files, targetFolder: folder });
      setFiles([]);
      await refetch();
    } catch (e) {
      setErrors((prev) => [...prev, (e as Error).message]);
    }
  }, [files, folder, uploadDocs, refetch]);

  const removeFile = (idx: number) => setFiles((prev) => prev.filter((_, i) => i !== idx));

  const isInCase = workspace?.current_case_id === caseId;

  return (
    <section className="bg-base-primary border border-gray-700 rounded-lg p-4">
      <div className="flex items-center gap-3 mb-3">
        <label className="text-sm text-gray-300">Target Folder</label>
        <select
          value={folder}
          onChange={(e) => setFolder(e.target.value as FolderValue)}
          className="bg-gray-800 text-gray-100 px-2 py-1 rounded border border-gray-600 text-sm"
        >
          {FOLDERS.map((f) => (
            <option key={f.value} value={f.value}>{f.label}</option>
          ))}
        </select>
        {!isInCase && (
          <span className="text-xs text-yellow-400">Enter this case to enable uploads</span>
        )}
      </div>

      <div
        onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); }}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-6 text-center ${isInCase ? 'border-gray-600' : 'border-gray-700 opacity-60'}`}
      >
        <p className="text-gray-300 mb-2">Drag and drop files here</p>
        <p className="text-gray-500 text-sm mb-3">PDF, Images (PNG/JPG/TIFF), DOCX, TXT, MD • Max 100MB each</p>
        <button
          className="px-3 py-1 bg-gray-700 text-gray-100 rounded text-sm"
          onClick={() => inputRef.current?.click()}
          disabled={!isInCase}
        >
          Select files
        </button>
        <input
          ref={inputRef}
          type="file"
          multiple
          className="hidden"
          onChange={(e) => onFilesSelected(e.target.files)}
          disabled={!isInCase}
        />
      </div>

      {files.length > 0 && (
        <div className="mt-4">
          <h4 className="text-sm text-gray-300 mb-2">Files to upload</h4>
          <ul className="space-y-2">
            {files.map((f, i) => (
              <li key={`${f.name}-${i}`} className="flex items-center justify-between text-sm text-gray-200 bg-gray-800 px-3 py-2 rounded">
                <span className="truncate mr-3">{f.name}</span>
                <button className="text-xs text-red-300" onClick={() => removeFile(i)}>Remove</button>
              </li>
            ))}
          </ul>
          <div className="mt-3 flex gap-2">
            <button
              className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-60"
              onClick={handleUpload}
              disabled={!isInCase || isPending}
            >
              {isPending ? 'Uploading…' : 'Upload'}
            </button>
            <button
              className="px-3 py-2 bg-gray-700 text-gray-100 rounded"
              onClick={() => setFiles([])}
            >
              Clear
            </button>
          </div>
        </div>
      )}

      {errors.length > 0 && (
        <div className="mt-4 p-3 bg-red-900/20 border border-red-500/50 rounded">
          <h4 className="text-sm text-red-300 mb-1">Errors</h4>
          <ul className="text-sm text-red-200 list-disc pl-5 space-y-1">
            {errors.map((e, i) => <li key={i}>{e}</li>)}
          </ul>
        </div>
      )}

      <div className="mt-6">
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-sm text-gray-300">Uploaded Documents</h4>
          <button className="text-xs text-gray-400" onClick={() => refetch()}>Refresh</button>
        </div>
        <div className="bg-gray-900 rounded p-3 max-h-64 overflow-auto">
          {listData?.length ? (
            <ul className="space-y-2">
              {listData.map((doc: any) => (
                <li key={doc.id} className="flex items-center justify-between text-sm text-gray-200">
                  <div className="truncate">
                    <span className="text-gray-400 mr-2">[{doc.target_folder}]</span>
                    <span title={doc.original_name}>{doc.original_name}</span>
                  </div>
                  <span className="text-xs text-gray-500">{(doc.size / 1024).toFixed(1)} KB</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-500 text-sm">No documents yet.</p>
          )}
        </div>
      </div>
    </section>
  );
}

