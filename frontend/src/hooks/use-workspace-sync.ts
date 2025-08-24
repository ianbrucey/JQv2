/**
 * Workspace Synchronization Hook - handles workspace state sync for legal cases
 */
import { useEffect, useCallback } from "react";
import { useLocation } from "react-router";

interface WorkspaceState {
  sessionId: string;
  currentCaseId: string | null;
  isInCaseWorkspace: boolean;
  workspaceBase: string | null;
}

interface WorkspaceSyncOptions {
  onWorkspaceChange?: (newWorkspace: WorkspaceState) => void;
  onTerminalReset?: () => void;
  enableAutoSync?: boolean;
}

/**
 * Hook to synchronize workspace state when switching between legal case conversations
 */
export function useWorkspaceSync(options: WorkspaceSyncOptions = {}) {
  const location = useLocation();
  const { onWorkspaceChange, onTerminalReset, enableAutoSync = true } = options;

  // Extract session/case information from current route
  const getCurrentSessionInfo = useCallback(() => {
    const path = location.pathname;

    // Check if we're in a legal case route
    const legalCaseMatch = path.match(/\/legal\/cases\/([^\/]+)/);
    if (legalCaseMatch) {
      return {
        type: "legal_case",
        caseId: legalCaseMatch[1],
        sessionId: `legal_case_${legalCaseMatch[1]}`,
      };
    }

    // Check if we're in legal home
    if (path.includes("/legal")) {
      return {
        type: "legal_home",
        caseId: null,
        sessionId: "legal_home",
      };
    }

    // Regular repository mode
    return {
      type: "repository",
      caseId: null,
      sessionId: "repository",
    };
  }, [location.pathname]);

  // Reset terminal state when switching contexts
  const resetTerminalState = useCallback(() => {
    if (onTerminalReset) {
      onTerminalReset();
    }

    // Clear terminal content by sending a clear command
    // This ensures the terminal shows the correct workspace context
    const terminalElement = document.querySelector(".xterm-screen");
    if (terminalElement) {
      // Trigger a terminal refresh event
      const event = new CustomEvent("terminal-workspace-change", {
        detail: { action: "reset" },
      });
      window.dispatchEvent(event);
    }
  }, [onTerminalReset]);

  // Sync workspace state with backend
  const syncWorkspaceState = useCallback(
    async (sessionInfo: ReturnType<typeof getCurrentSessionInfo>) => {
      try {
        if (sessionInfo.type === "legal_case" && sessionInfo.caseId) {
          // Enter legal case workspace
          const response = await fetch(
            `/api/legal/cases/${sessionInfo.caseId}/enter`,
            {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                "X-Session-ID": sessionInfo.sessionId,
              },
            },
          );

          if (response.ok) {
            const workspaceData = await response.json();

            if (onWorkspaceChange) {
              onWorkspaceChange({
                sessionId: sessionInfo.sessionId,
                currentCaseId: sessionInfo.caseId,
                isInCaseWorkspace: true,
                workspaceBase: workspaceData.workspace_path,
              });
            }

            // Reset terminal to show new workspace
            resetTerminalState();

            console.log(
              `🏛️ Entered legal case workspace: ${sessionInfo.caseId}`,
            );
          }
        } else if (sessionInfo.type === "repository") {
          // Exit legal workspace if we were in one
          try {
            const response = await fetch("/api/legal/workspace/exit", {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                "X-Session-ID": sessionInfo.sessionId,
              },
            });

            if (response.ok) {
              if (onWorkspaceChange) {
                onWorkspaceChange({
                  sessionId: sessionInfo.sessionId,
                  currentCaseId: null,
                  isInCaseWorkspace: false,
                  workspaceBase: null,
                });
              }

              // Reset terminal to show repository workspace
              resetTerminalState();

              console.log(
                "📁 Exited legal workspace, returned to repository mode",
              );
            }
          } catch (error) {
            // Ignore errors when exiting - might not have been in legal workspace
            console.debug("No legal workspace to exit from");
          }
        }
      } catch (error) {
        console.error("Workspace sync error:", error);
      }
    },
    [onWorkspaceChange, resetTerminalState],
  );

  // Effect to handle route changes
  useEffect(() => {
    if (!enableAutoSync) return;

    const sessionInfo = getCurrentSessionInfo();

    // Add a small delay to ensure the route has fully changed
    const timeoutId = setTimeout(() => {
      syncWorkspaceState(sessionInfo);
    }, 100);

    return () => clearTimeout(timeoutId);
  }, [
    location.pathname,
    enableAutoSync,
    getCurrentSessionInfo,
    syncWorkspaceState,
  ]);

  // Manual sync function for explicit workspace changes
  const manualSync = useCallback(() => {
    const sessionInfo = getCurrentSessionInfo();
    return syncWorkspaceState(sessionInfo);
  }, [getCurrentSessionInfo, syncWorkspaceState]);

  // Get current workspace status
  const getCurrentWorkspaceStatus = useCallback(async () => {
    const sessionInfo = getCurrentSessionInfo();

    try {
      const response = await fetch("/api/legal/workspace/current", {
        headers: {
          "X-Session-ID": sessionInfo.sessionId,
        },
      });

      if (response.ok) {
        return await response.json();
      }
    } catch (error) {
      console.error("Failed to get workspace status:", error);
    }

    return null;
  }, [getCurrentSessionInfo]);

  return {
    manualSync,
    getCurrentWorkspaceStatus,
    resetTerminalState,
    currentSessionInfo: getCurrentSessionInfo(),
  };
}

/**
 * Terminal event listener for workspace changes
 */
export function setupTerminalWorkspaceListener() {
  const handleWorkspaceChange = (event: CustomEvent) => {
    const { action } = event.detail;

    if (action === "reset") {
      // Send clear command to terminal
      const terminalInput = document.querySelector(
        ".xterm-helper-textarea",
      ) as HTMLTextAreaElement;
      if (terminalInput) {
        // Simulate typing 'clear' command
        const clearEvent = new KeyboardEvent("keydown", {
          key: "Enter",
          code: "Enter",
          keyCode: 13,
        });

        // First send 'clear' text
        terminalInput.value = "clear";
        terminalInput.dispatchEvent(new Event("input", { bubbles: true }));

        // Then send Enter
        setTimeout(() => {
          terminalInput.dispatchEvent(clearEvent);
        }, 50);
      }
    }
  };

  window.addEventListener(
    "terminal-workspace-change",
    handleWorkspaceChange as EventListener,
  );

  return () => {
    window.removeEventListener(
      "terminal-workspace-change",
      handleWorkspaceChange as EventListener,
    );
  };
}
