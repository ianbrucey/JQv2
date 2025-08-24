import { useTranslation } from "react-i18next";
import { Container } from "#/components/layout/container";
import { TabContent } from "#/components/layout/tab-content";
import { I18nKey } from "#/i18n/declaration";
import { useConversationId } from "#/hooks/use-conversation-id";
import TerminalIcon from "#/icons/terminal.svg?react";

export function ConversationTabs() {
  const { conversationId } = useConversationId();

  const { t } = useTranslation();

  const basePath = `/conversations/${conversationId}`;

  const tabs = [
    {
      label: t(I18nKey.WORKSPACE$TERMINAL_TAB_LABEL),
      to: basePath, // Use full path for terminal
      icon: <TerminalIcon />,
    },
    {
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
    },
    {
      label: "Drafts",
      to: `${basePath}/drafts`, // Use full path for drafts
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
            d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
          />
        </svg>
      ),
    },
  ];

  return (
    <Container className="h-full w-full" labels={tabs}>
      <div className="h-full w-full">
        <TabContent conversationPath={basePath} />
      </div>
    </Container>
  );
}
