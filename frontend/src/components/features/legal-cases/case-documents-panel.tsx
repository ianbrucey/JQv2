import React from 'react';
import { DocumentsUploader } from './documents-uploader';
import { useCurrentWorkspace } from '#/hooks/mutation/use-legal-cases';

interface CaseDocumentsPanelProps {
  caseId: string;
}

export function CaseDocumentsPanel({ caseId }: CaseDocumentsPanelProps) {
  const { data: workspace } = useCurrentWorkspace();
  const isInCase = workspace?.current_case_id === caseId;

  return (
    <section className="w-full flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg text-white font-medium">Documents</h3>
        {!isInCase && (
          <span className="text-xs text-yellow-400">Enter this case to upload and view documents</span>
        )}
      </div>
      <DocumentsUploader caseId={caseId} />
    </section>
  );
}

