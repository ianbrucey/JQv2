import React from "react";
import { PrefetchPageLinks } from "react-router";
import {
  useWorkspaceSync,
  setupTerminalWorkspaceListener,
} from "#/hooks/use-workspace-sync";

// Legal case components (conditional imports)
const LegalCaseHeader = React.lazy(() =>
  import("#/components/features/legal-cases/legal-case-header").then(
    (module) => ({ default: module.LegalCaseHeader }),
  ),
);
const CaseList = React.lazy(() =>
  import("#/components/features/legal-cases/case-list").then((module) => ({
    default: module.CaseList,
  })),
);
const CreateCaseModal = React.lazy(() =>
  import("#/components/features/legal-cases/create-case-modal").then(
    (module) => ({ default: module.CreateCaseModal }),
  ),
);
const CaseDocumentsPanel = React.lazy(() =>
  import("#/components/features/legal-cases/case-documents-panel").then(
    (module) => ({ default: module.CaseDocumentsPanel }),
  ),
);

<PrefetchPageLinks page="/conversations/:conversationId" />;

function CurrentCaseDocuments() {
  const [currentCaseId, setCurrentCaseId] = React.useState<string | null>(null);

  React.useEffect(() => {
    fetch("/api/legal/workspace/current", {
      headers: { "X-Session-ID": "legal_home" },
    })
      .then((res) => res.json())
      .then((data) => setCurrentCaseId(data?.current_case_id || null))
      .catch(() => setCurrentCaseId(null));
  }, []);

  if (!currentCaseId) return null;

  return (
    <React.Suspense
      fallback={<div className="text-sm text-gray-500">Loading documents…</div>}
    >
      <CaseDocumentsPanel caseId={currentCaseId} />
    </React.Suspense>
  );
}

function HomeScreen() {
  const [isCreateModalOpen, setIsCreateModalOpen] = React.useState(false);
  const [workspaceState, setWorkspaceState] = React.useState<any>(null);

  // Initialize workspace synchronization
  const { manualSync, resetTerminalState, currentSessionInfo } =
    useWorkspaceSync({
      onWorkspaceChange: (newWorkspace) => {
        setWorkspaceState(newWorkspace);
        console.log("Workspace changed:", newWorkspace);
      },
      onTerminalReset: () => {
        console.log("Terminal reset for workspace change");
      },
      enableAutoSync: true,
    });

  // Setup terminal workspace listener on mount
  React.useEffect(() => {
    const cleanup = setupTerminalWorkspaceListener();
    return cleanup;
  }, []);

  // Legal system is always available - no need to check
  const [legalSystemAvailable, setLegalSystemAvailable] = React.useState(true);

  const handleCreateCase = () => {
    setIsCreateModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsCreateModalOpen(false);
  };

  const handleCaseCreated = (caseId: string) => {
    console.log("Case created:", caseId);
  };

  return (
    <div
      data-testid="home-screen"
      className="bg-base-secondary h-full flex flex-col rounded-xl px-[42px] pt-[42px] gap-8 overflow-y-auto"
    >
      {/* Legal Cases Dashboard - Always Visible */}
      {legalSystemAvailable && (
        <React.Suspense
          fallback={
            <div className="text-center py-8">Loading legal system...</div>
          }
        >
          <LegalCaseHeader
            onCreateCase={handleCreateCase}
            isCreatingCase={false}
          />
          {/* If currently in a case workspace, show documents panel */}
          <CurrentCaseDocuments />
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
      {!legalSystemAvailable && (
        <div className="flex items-center justify-center h-full">
          <div className="text-center max-w-md">
            <div className="mb-4">
              <svg
                className="w-16 h-16 text-yellow-400 mx-auto"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
                />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-white mb-2">
              Legal System Not Available
            </h2>
            <p className="text-gray-400 mb-4">
              The legal document management system is not initialized. Please
              check the server configuration.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default HomeScreen;
