import { useTranslation } from "react-i18next";
import { Container } from "#/components/layout/container";
import { TabContent } from "#/components/layout/tab-content";
import { I18nKey } from "#/i18n/declaration";
import { useConversationId } from "#/hooks/use-conversation-id";
import TerminalIcon from "#/icons/terminal.svg?react";
import { useCurrentWorkspace } from "#/hooks/mutation/use-legal-cases";

export function ConversationTabs() {
  const { data: currentWorkspace } = useCurrentWorkspace();

  const { conversationId } = useConversationId();

  const { t } = useTranslation();

  const basePath = `/conversations/${conversationId}`;

  // Check if we're in a legal case workspace - try multiple detection methods
  const isInLegalCase =
    currentWorkspace?.current_case_id || currentWorkspace?.is_in_case_workspace;

  // Debug logging
  console.log("ConversationTabs Debug:", {
    conversationId,
    basePath,
    currentWorkspace,
    isInLegalCase,
  });

  const tabs = [
    {
      label: t(I18nKey.WORKSPACE$TERMINAL_TAB_LABEL),
      to: basePath, // Use full path for terminal
      icon: <TerminalIcon />,
    },
  ];

  // Always add document upload tab for testing - remove this later
  tabs.push({
    label: "Documents",
    to: `${basePath}/documents`, // Use full path for documents
    icon: (
      <svg
        className="w-4 h-4"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
        />
      </svg>
    ),
  });

  return (
    <Container className="h-full w-full" labels={tabs}>
      <div className="h-full w-full">
        <TabContent conversationPath={basePath} />
      </div>
    </Container>
  );
}
