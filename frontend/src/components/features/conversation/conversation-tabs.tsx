import { DiGit } from "react-icons/di";
import { FaServer, FaExternalLinkAlt } from "react-icons/fa";
import { useSelector } from "react-redux";
import { useTranslation } from "react-i18next";
import { VscCode } from "react-icons/vsc";
import { Container } from "#/components/layout/container";
import { I18nKey } from "#/i18n/declaration";
import { RootState } from "#/store";
import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";
import { ServedAppLabel } from "#/components/layout/served-app-label";
import { TabContent } from "#/components/layout/tab-content";
import { transformVSCodeUrl } from "#/utils/vscode-url-helper";
import { useConversationId } from "#/hooks/use-conversation-id";
import GlobeIcon from "#/icons/globe.svg?react";
import JupyterIcon from "#/icons/jupyter.svg?react";
import OpenHands from "#/api/open-hands";
import TerminalIcon from "#/icons/terminal.svg?react";

export function ConversationTabs() {
  const { curAgentState } = useSelector((state: RootState) => state.agent);

  const { conversationId } = useConversationId();

  const { t } = useTranslation();

  const basePath = `/conversations/${conversationId}`;

  return (
    <Container
      className="h-full w-full"
      labels={[
        {
          label: t(I18nKey.WORKSPACE$TERMINAL_TAB_LABEL),
          to: "terminal",
          icon: <TerminalIcon />,
        },
      ]}
    >
      {/* Only Terminal tab is available; make it the default */}
      <div className="h-full w-full">
        <TabContent conversationPath={basePath} />
      </div>
    </Container>
  );
}
