import React from "react";
import { useConversationId } from "#/hooks/use-conversation-id";

function TerminalTab() {
  const Terminal = React.useMemo(
    () => React.lazy(() => import("#/components/features/terminal/terminal")),
    [],
  );

  const { conversationId } = useConversationId();

  return (
    <div className="h-full flex flex-col">
      <div className="flex-grow overflow-auto">
        {/* Terminal uses some API that is not compatible in a server-environment. For this reason, we lazy load it to ensure
         * that it loads only in the client-side. */}
        <React.Suspense fallback={<div className="h-full" />}>
          {/* Force remount on conversation switch to reattach terminal session */}
          <Terminal key={conversationId} />
        </React.Suspense>
      </div>
    </div>
  );
}

export default TerminalTab;
