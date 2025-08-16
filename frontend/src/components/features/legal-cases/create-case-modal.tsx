/**
 * Modal for creating new legal cases
 */
import React from 'react';
import { useTranslation } from 'react-i18next';
import { useCreateLegalCase } from '#/hooks/mutation/use-legal-cases';
import { CreateCaseRequest } from '#/api/legal-cases';

interface CreateCaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (caseId: string) => void;
}

export function CreateCaseModal({ isOpen, onClose, onSuccess }: CreateCaseModalProps) {
  const { t } = useTranslation();
  const [formData, setFormData] = React.useState<CreateCaseRequest>({
    title: '',
    case_number: '',
    description: '',
  });
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const {
    mutate: createCase,
    isPending,
    error,
  } = useCreateLegalCase();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate form
    const newErrors: Record<string, string> = {};
    if (!formData.title.trim()) {
      newErrors.title = t('LEGAL_CASES$TITLE_REQUIRED');
    }
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    // Create case
    createCase(
      {
        title: formData.title.trim(),
        case_number: formData.case_number?.trim() || undefined,
        description: formData.description?.trim() || undefined,
      },
      {
        onSuccess: (newCase) => {
          // Reset form
          setFormData({ title: '', case_number: '', description: '' });
          setErrors({});
          
          // Close modal
          onClose();
          
          // Notify parent
          onSuccess?.(newCase.case_id);
        },
        onError: () => {
          // Error is handled by the error state from the mutation
        },
      }
    );
  };

  const handleInputChange = (field: keyof CreateCaseRequest, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const handleClose = () => {
    if (!isPending) {
      setFormData({ title: '', case_number: '', description: '' });
      setErrors({});
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-base-secondary rounded-xl p-6 w-full max-w-md mx-4">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-white">
            {t('LEGAL_CASES$CREATE_NEW_CASE')}
          </h2>
          <button
            onClick={handleClose}
            disabled={isPending}
            className="text-gray-400 hover:text-white transition-colors"
            aria-label={t('COMMON$CLOSE')}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Case Title */}
          <div>
            <label htmlFor="case-title" className="block text-sm font-medium text-gray-300 mb-2">
              {t('LEGAL_CASES$CASE_TITLE')} *
            </label>
            <input
              id="case-title"
              type="text"
              value={formData.title}
              onChange={(e) => handleInputChange('title', e.target.value)}
              disabled={isPending}
              className={`w-full px-3 py-2 bg-base-primary border rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.title ? 'border-red-500' : 'border-gray-600'
              }`}
              placeholder={t('LEGAL_CASES$CASE_TITLE_PLACEHOLDER')}
              autoFocus
            />
            {errors.title && (
              <p className="mt-1 text-sm text-red-400">{errors.title}</p>
            )}
          </div>

          {/* Case Number */}
          <div>
            <label htmlFor="case-number" className="block text-sm font-medium text-gray-300 mb-2">
              {t('LEGAL_CASES$CASE_NUMBER')} ({t('COMMON$OPTIONAL')})
            </label>
            <input
              id="case-number"
              type="text"
              value={formData.case_number}
              onChange={(e) => handleInputChange('case_number', e.target.value)}
              disabled={isPending}
              className="w-full px-3 py-2 bg-base-primary border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder={t('LEGAL_CASES$CASE_NUMBER_PLACEHOLDER')}
            />
          </div>

          {/* Description */}
          <div>
            <label htmlFor="case-description" className="block text-sm font-medium text-gray-300 mb-2">
              {t('LEGAL_CASES$DESCRIPTION')} ({t('COMMON$OPTIONAL')})
            </label>
            <textarea
              id="case-description"
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              disabled={isPending}
              rows={3}
              className="w-full px-3 py-2 bg-base-primary border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              placeholder={t('LEGAL_CASES$DESCRIPTION_PLACEHOLDER')}
            />
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-3 bg-red-900/20 border border-red-500/50 rounded-lg">
              <p className="text-sm text-red-400">
                {error instanceof Error ? error.message : t('LEGAL_CASES$CREATE_ERROR')}
              </p>
            </div>
          )}

          {/* Buttons */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={handleClose}
              disabled={isPending}
              className="flex-1 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {t('COMMON$CANCEL')}
            </button>
            <button
              type="submit"
              disabled={isPending || !formData.title.trim()}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isPending ? t('LEGAL_CASES$CREATING') : t('LEGAL_CASES$CREATE_CASE')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
