import React, { lazy, Suspense } from "react";
import { useLocation } from "react-router";
import { LoadingSpinner } from "../shared/loading-spinner";

// Lazy load tabs
const TerminalTab = lazy(() => import("#/routes/terminal-tab"));
const DocumentsTab = lazy(() => import("#/routes/documents-tab"));
const DraftsTab = lazy(() => import("#/routes/drafts-tab"));

interface TabContentProps {
  conversationPath: string;
}

export function TabContent({ conversationPath }: TabContentProps) {
  const location = useLocation();
  const currentPath = location.pathname;

  // Determine which tab is active
  const isTerminalActive =
    currentPath === `${conversationPath}/terminal` ||
    currentPath === conversationPath;
  const isDocumentsActive = currentPath === `${conversationPath}/documents`;
  const isDraftsActive = currentPath === `${conversationPath}/drafts`;

  return (
    <div className="h-full w-full relative">
      {/* Each tab content is always loaded but only visible when active */}
      <Suspense
        fallback={
          <div className="flex items-center justify-center h-full">
            <LoadingSpinner size="large" />
          </div>
        }
      >
        <div
          className={`absolute inset-0 ${isTerminalActive ? "block" : "hidden"}`}
        >
          <TerminalTab />
        </div>
        <div
          className={`absolute inset-0 ${isDocumentsActive ? "block" : "hidden"}`}
        >
          <DocumentsTab />
        </div>
        <div
          className={`absolute inset-0 ${isDraftsActive ? "block" : "hidden"}`}
        >
          <DraftsTab />
        </div>
      </Suspense>
    </div>
  );
}
