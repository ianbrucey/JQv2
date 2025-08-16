/**
 * Header component for legal case management
 */
import React from 'react';
import { useTranslation } from 'react-i18next';
import { BrandButton } from '../settings/brand-button';
import AllHandsLogo from '#/assets/branding/all-hands-logo-spark.svg?react';

interface LegalCaseHeaderProps {
  onCreateCase: () => void;
  isCreatingCase?: boolean;
}

export function LegalCaseHeader({ onCreateCase, isCreatingCase = false }: LegalCaseHeaderProps) {
  const { t } = useTranslation();

  return (
    <header className="flex flex-col gap-5">
      <AllHandsLogo />

      <div className="flex items-center justify-between">
        <h1 className="heading">{t('LEGAL_CASES$LETS_START_BUILDING')}</h1>
        <BrandButton
          testId="header-create-case-button"
          variant="primary"
          type="button"
          onClick={onCreateCase}
          isDisabled={isCreatingCase}
        >
          {!isCreatingCase && t('LEGAL_CASES$CREATE_NEW_CASE')}
          {isCreatingCase && t('LEGAL_CASES$CREATING')}
        </BrandButton>
      </div>

      <div className="flex items-center justify-between">
        <p className="text-sm max-w-[424px]">
          {t('LEGAL_CASES$OPENHANDS_LEGAL_DESCRIPTION')}
        </p>
        <p className="text-sm">
          {t('LEGAL_CASES$NOT_SURE_HOW_TO_START')}{" "}
          <a
            href="https://docs.all-hands.dev/usage/getting-started"
            target="_blank"
            rel="noopener noreferrer"
            className="underline underline-offset-2"
          >
            {t('LEGAL_CASES$READ_THIS')}
          </a>
        </p>
      </div>
    </header>
  );
}
