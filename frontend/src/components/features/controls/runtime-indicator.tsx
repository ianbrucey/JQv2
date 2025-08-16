import React from "react";
import { useTranslation } from "react-i18next";
import { useSelector } from "react-redux";
import { RootState } from "#/store";
import { useActiveConversation } from "#/hooks/query/use-active-conversation";

interface RuntimeIndicatorProps {
  className?: string;
}

export function RuntimeIndicator({ className = "" }: RuntimeIndicatorProps) {
  const { t } = useTranslation();
  const { data: conversation } = useActiveConversation();
  const { curAgentState } = useSelector((state: RootState) => state.agent);
  
  // Check if we're in legal mode by looking for legal-specific indicators
  // This is a simple heuristic - in a real implementation, you'd want to
  // get this information from the backend
  const isLegalMode = conversation?.selected_repository?.includes("legal") || 
                     window.location.pathname.includes("legal");
  
  // Determine runtime type based on context
  const runtimeType = isLegalMode ? "local" : "docker";
  const isStarting = conversation?.runtime_status?.includes("STARTING") || 
                    conversation?.status === "STARTING";
  
  // Don't show indicator if conversation is stopped
  if (conversation?.status === "STOPPED" || !conversation) {
    return null;
  }
  
  const getRuntimeIcon = () => {
    if (runtimeType === "local") {
      return "⚡"; // Lightning bolt for fast local runtime
    }
    return "🐳"; // Docker whale for container runtime
  };
  
  const getRuntimeLabel = () => {
    if (runtimeType === "local") {
      return t("RUNTIME$LOCAL_RUNTIME", "Local Runtime");
    }
    return t("RUNTIME$DOCKER_RUNTIME", "Docker Runtime");
  };
  
  const getRuntimeDescription = () => {
    if (runtimeType === "local") {
      return t("RUNTIME$LOCAL_DESCRIPTION", "Instant startup, direct file access");
    }
    return t("RUNTIME$DOCKER_DESCRIPTION", "Sandboxed environment");
  };
  
  const getStatusColor = () => {
    if (isStarting) {
      return "text-yellow-500";
    }
    if (runtimeType === "local") {
      return "text-green-500";
    }
    return "text-blue-500";
  };
  
  return (
    <div className={`flex items-center gap-2 text-xs ${className}`}>
      <div className="flex items-center gap-1">
        <span className="text-base" title={getRuntimeDescription()}>
          {getRuntimeIcon()}
        </span>
        <span className={`font-medium ${getStatusColor()}`}>
          {getRuntimeLabel()}
        </span>
      </div>
      {isLegalMode && (
        <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded-full text-xs font-medium">
          🏛️ Legal
        </span>
      )}
    </div>
  );
}
