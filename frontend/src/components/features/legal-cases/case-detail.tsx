import React from 'react';
import { CaseDocumentsPanel } from './case-documents-panel';

interface CaseDetailProps {
  caseId: string;
  title: string;
}

export function CaseDetail({ caseId, title }: CaseDetailProps) {
  return (
    <section className="w-full flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl text-white font-semibold">{title}</h2>
      </div>
      <CaseDocumentsPanel caseId={caseId} />
    </section>
  );
}

