/**
 * Component for displaying list of legal cases
 */
import React from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router';
import { useLegalCases, useEnterLegalCase, useCurrentWorkspace } from '#/hooks/mutation/use-legal-cases';
import { useCreateConversation } from '#/hooks/mutation/use-create-conversation';
import { LegalCase } from '#/api/legal-cases';
import { formatDistanceToNow } from 'date-fns';

interface CaseListProps {
  onCreateCase: () => void;
}

export function CaseList({ onCreateCase }: CaseListProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { data: cases, isLoading, error } = useLegalCases();
  const { data: currentWorkspace } = useCurrentWorkspace();
  const { mutate: enterCase, isPending: isEnteringCase } = useEnterLegalCase();
  const { mutate: createConversation } = useCreateConversation();

  const handleEnterCase = (caseItem: LegalCase) => {
    enterCase(caseItem.case_id, {
      onSuccess: () => {
        // Create a new conversation for this case with legal context
        createConversation(
          {
            // Pass case context to conversation
            conversationInstructions: `Legal Case Context:
- Case ID: ${caseItem.case_id}
- Case Title: ${caseItem.title}
- Case Number: ${caseItem.case_number || 'N/A'}
- Case Status: ${caseItem.status}

This conversation is for legal document management and case work. The system is configured for instant startup using LocalRuntime for optimal legal workflow performance.`,
            query: `I'm working on legal case "${caseItem.title}". Please help me with legal document management, research, and case preparation tasks.`,
          },
          {
            onSuccess: (data) => {
              window.location.href = `/conversations/${data.conversation_id}`;
            },
          }
        );
      },
    });
  };

  const formatLastAccessed = (dateString?: string) => {
    if (!dateString) return t('LEGAL_CASES$NEVER_ACCESSED');
    
    try {
      return formatDistanceToNow(new Date(dateString), { addSuffix: true });
    } catch {
      return t('LEGAL_CASES$UNKNOWN_DATE');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active':
        return 'text-green-400';
      case 'closed':
        return 'text-gray-400';
      case 'on_hold':
        return 'text-yellow-400';
      case 'archived':
        return 'text-gray-500';
      default:
        return 'text-gray-400';
    }
  };

  if (isLoading) {
    return (
      <section className="w-full flex flex-col gap-6">
        <div className="flex items-center justify-between">
          <h2 className="heading">{t('LEGAL_CASES$YOUR_CASES')}</h2>
        </div>
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="p-4 bg-base-primary rounded-lg animate-pulse">
              <div className="h-4 bg-gray-600 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-gray-700 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="w-full flex flex-col gap-6">
        <div className="flex items-center justify-between">
          <h2 className="heading">{t('LEGAL_CASES$YOUR_CASES')}</h2>
        </div>
        <div className="p-4 bg-red-900/20 border border-red-500/50 rounded-lg">
          <p className="text-red-400">
            {t('LEGAL_CASES$LOAD_ERROR')}: {error instanceof Error ? error.message : 'Unknown error'}
          </p>
        </div>
      </section>
    );
  }

  if (!cases || cases.length === 0) {
    return (
      <section className="w-full flex flex-col gap-6">
        <div className="flex items-center justify-between">
          <h2 className="heading">{t('LEGAL_CASES$YOUR_CASES')}</h2>
        </div>
        <div className="text-center py-12">
          <div className="mb-4">
            <svg className="w-16 h-16 text-gray-500 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-300 mb-2">
            {t('LEGAL_CASES$NO_CASES_TITLE')}
          </h3>
          <p className="text-gray-400 mb-6 max-w-md mx-auto">
            {t('LEGAL_CASES$NO_CASES_DESCRIPTION')}
          </p>
          <button
            onClick={onCreateCase}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            {t('LEGAL_CASES$CREATE_YOUR_FIRST_CASE')}
          </button>
        </div>
      </section>
    );
  }

  return (
    <section className="w-full flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h2 className="heading">{t('LEGAL_CASES$YOUR_CASES')}</h2>
        <button
          onClick={onCreateCase}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
        >
          {t('LEGAL_CASES$CREATE_NEW_CASE')}
        </button>
      </div>

      <div className="space-y-3">
        {cases.map((caseItem) => {
          const isCurrentCase = currentWorkspace?.current_case_id === caseItem.case_id;
          
          return (
            <div
              key={caseItem.case_id}
              className={`p-4 rounded-lg border transition-all cursor-pointer hover:border-blue-500/50 ${
                isCurrentCase
                  ? 'bg-blue-900/20 border-blue-500/50'
                  : 'bg-base-primary border-gray-600 hover:bg-base-primary/80'
              }`}
              onClick={() => handleEnterCase(caseItem)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-medium text-white truncate">
                      {caseItem.title}
                    </h3>
                    {caseItem.case_number && (
                      <span className="text-xs bg-gray-700 text-gray-300 px-2 py-1 rounded">
                        {caseItem.case_number}
                      </span>
                    )}
                    {isCurrentCase && (
                      <span className="text-xs bg-blue-600 text-white px-2 py-1 rounded">
                        {t('LEGAL_CASES$CURRENT')}
                      </span>
                    )}
                  </div>
                  
                  {caseItem.description && (
                    <p className="text-sm text-gray-400 mb-2 line-clamp-2">
                      {caseItem.description}
                    </p>
                  )}
                  
                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    <span className={getStatusColor(caseItem.status)}>
                      {t(`LEGAL_CASES$STATUS_${caseItem.status.toUpperCase()}`)}
                    </span>
                    <span>
                      {t('LEGAL_CASES$LAST_ACCESSED')}: {formatLastAccessed(caseItem.last_accessed_at)}
                    </span>
                    {caseItem.draft_system_initialized && (
                      <span className="text-green-400">
                        {t('LEGAL_CASES$DRAFT_SYSTEM_READY')}
                      </span>
                    )}
                  </div>
                </div>
                
                <div className="flex items-center gap-2 ml-4">
                  {isEnteringCase && (
                    <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                  )}
                  <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
