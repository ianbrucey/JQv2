/**
 * Legal Document Management Home Screen
 */
import React from "react";
import { PrefetchPageLinks } from "react-router";
import { LegalCaseHeader } from "#/components/features/legal-cases/legal-case-header";
import { CaseList } from "#/components/features/legal-cases/case-list";
import { CreateCaseModal } from "#/components/features/legal-cases/create-case-modal";
import { useLegalSystemStatus } from "#/hooks/mutation/use-legal-cases";

<PrefetchPageLinks page="/conversations/:conversationId" />;

function LegalHomeScreen() {
  const [isCreateModalOpen, setIsCreateModalOpen] = React.useState(false);
  const { data: systemStatus, isLoading: isLoadingStatus } = useLegalSystemStatus();

  const handleCreateCase = () => {
    setIsCreateModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsCreateModalOpen(false);
  };

  const handleCaseCreated = (caseId: string) => {
    console.log('Case created:', caseId);
    // Modal will close automatically via handleCloseModal
  };

  // Show loading state while checking system status
  if (isLoadingStatus) {
    return (
      <div
        data-testid="legal-home-screen"
        className="bg-base-secondary h-full flex flex-col rounded-xl px-[42px] pt-[42px] gap-8 overflow-y-auto"
      >
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-gray-400">Initializing legal document system...</p>
          </div>
        </div>
      </div>
    );
  }

  // Show error state if system is not ready
  if (!systemStatus?.system_initialized) {
    return (
      <div
        data-testid="legal-home-screen"
        className="bg-base-secondary h-full flex flex-col rounded-xl px-[42px] pt-[42px] gap-8 overflow-y-auto"
      >
        <div className="flex items-center justify-center h-full">
          <div className="text-center max-w-md">
            <div className="mb-4">
              <svg className="w-16 h-16 text-red-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-white mb-2">
              Legal Document System Not Available
            </h2>
            <p className="text-gray-400 mb-4">
              The legal document management system is not properly initialized. 
              Please check the server configuration and ensure all required services are running.
            </p>
            <div className="text-sm text-gray-500 space-y-1">
              <p>System Status:</p>
              <ul className="text-left space-y-1">
                <li>• System Initialized: {systemStatus?.system_initialized ? '✅' : '❌'}</li>
                <li>• Workspace Manager: {systemStatus?.workspace_manager_ready ? '✅' : '❌'}</li>
                <li>• Database: {systemStatus?.database_ready ? '✅' : '❌'}</li>
                <li>• Draft System: {systemStatus?.draft_system_available ? '✅' : '❌'}</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      data-testid="legal-home-screen"
      className="bg-base-secondary h-full flex flex-col rounded-xl px-[42px] pt-[42px] gap-8 overflow-y-auto"
    >
      <LegalCaseHeader 
        onCreateCase={handleCreateCase}
        isCreatingCase={false}
      />

      <hr className="border-[#717888]" />

      <main className="flex flex-col gap-8">
        <CaseList onCreateCase={handleCreateCase} />
      </main>

      <CreateCaseModal
        isOpen={isCreateModalOpen}
        onClose={handleCloseModal}
        onSuccess={handleCaseCreated}
      />
    </div>
  );
}

export default LegalHomeScreen;
