import React, { lazy, Suspense } from "react";
import { useLocation } from "react-router";
import { LoadingSpinner } from "../shared/loading-spinner";

// Lazy load only the Terminal tab (others temporarily removed)
const TerminalTab = lazy(() => import("#/routes/terminal-tab"));

interface TabContentProps {
  conversationPath: string;
}

export function TabContent({ conversationPath }: TabContentProps) {
  const location = useLocation();
  const currentPath = location.pathname;

  // Only Terminal tab remains; default to it when at base path
  const isTerminalActive =
    currentPath === `${conversationPath}/terminal` ||
    currentPath === conversationPath;
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
      </Suspense>
    </div>
  );
}
