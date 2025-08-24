import React from 'react';
import { DocumentsUploader } from './documents-uploader';

interface CaseDocumentsPanelProps {
  caseId: string;
}

export function CaseDocumentsPanel({ caseId }: CaseDocumentsPanelProps) {
  return (
    <section className="w-full flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg text-white font-medium">Documents</h3>
      </div>
      <DocumentsUploader caseId={caseId} />
    </section>
  );
}

