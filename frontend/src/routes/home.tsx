import React from "react";
import { PrefetchPageLinks } from "react-router";
import { HomeHeader } from "#/components/features/home/home-header";
import { RepoConnector } from "#/components/features/home/repo-connector";
import { TaskSuggestions } from "#/components/features/home/tasks/task-suggestions";
import { useUserProviders } from "#/hooks/use-user-providers";
import { GitRepository } from "#/types/git";

// Legal case components (conditional imports)
const LegalCaseHeader = React.lazy(() =>
  import("#/components/features/legal-cases/legal-case-header").then(module => ({ default: module.LegalCaseHeader }))
);
const CaseList = React.lazy(() =>
  import("#/components/features/legal-cases/case-list").then(module => ({ default: module.CaseList }))
);
const CreateCaseModal = React.lazy(() =>
  import("#/components/features/legal-cases/create-case-modal").then(module => ({ default: module.CreateCaseModal }))
);

<PrefetchPageLinks page="/conversations/:conversationId" />;

function HomeScreen() {
  const { providers } = useUserProviders();
  const [selectedRepo, setSelectedRepo] = React.useState<GitRepository | null>(
    null,
  );
  const [mode, setMode] = React.useState<'repository' | 'legal'>('repository');
  const [isCreateModalOpen, setIsCreateModalOpen] = React.useState(false);

  const providersAreSet = providers.length > 0;

  // Check if legal system is available
  const [legalSystemAvailable, setLegalSystemAvailable] = React.useState(false);

  React.useEffect(() => {
    // Check if legal system is available
    fetch('/api/legal/system/status')
      .then(res => res.json())
      .then(data => {
        setLegalSystemAvailable(data.system_initialized);
      })
      .catch(() => {
        setLegalSystemAvailable(false);
      });
  }, []);

  const handleCreateCase = () => {
    setIsCreateModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsCreateModalOpen(false);
  };

  const handleCaseCreated = (caseId: string) => {
    console.log('Case created:', caseId);
  };

  return (
    <div
      data-testid="home-screen"
      className="bg-base-secondary h-full flex flex-col rounded-xl px-[42px] pt-[42px] gap-8 overflow-y-auto"
    >
      {/* Mode Toggle */}
      {legalSystemAvailable && (
        <div className="flex justify-center mb-4">
          <div className="bg-base-primary rounded-lg p-1 flex">
            <button
              onClick={() => setMode('repository')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                mode === 'repository'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              Repository Mode
            </button>
            <button
              onClick={() => setMode('legal')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                mode === 'legal'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              Legal Cases
            </button>
          </div>
        </div>
      )}

      {/* Repository Mode (Original) */}
      {mode === 'repository' && (
        <>
          <HomeHeader />
          <hr className="border-[#717888]" />
          <main className="flex flex-col lg:flex-row justify-between gap-8">
            <RepoConnector onRepoSelection={(repo) => setSelectedRepo(repo)} />
            <hr className="md:hidden border-[#717888]" />
            {providersAreSet && <TaskSuggestions filterFor={selectedRepo} />}
          </main>
        </>
      )}

      {/* Legal Mode */}
      {mode === 'legal' && legalSystemAvailable && (
        <React.Suspense fallback={<div className="text-center py-8">Loading legal system...</div>}>
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
        </React.Suspense>
      )}

      {/* Legal System Not Available */}
      {mode === 'legal' && !legalSystemAvailable && (
        <div className="flex items-center justify-center h-full">
          <div className="text-center max-w-md">
            <div className="mb-4">
              <svg className="w-16 h-16 text-yellow-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-white mb-2">
              Legal System Not Available
            </h2>
            <p className="text-gray-400 mb-4">
              The legal document management system is not initialized. Please check the server configuration.
            </p>
            <button
              onClick={() => setMode('repository')}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Switch to Repository Mode
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default HomeScreen;
