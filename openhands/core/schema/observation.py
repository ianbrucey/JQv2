from enum import Enum


class ObservationType(str, Enum):
    READ = 'read'
    """The content of a file
    """

    WRITE = 'write'

    EDIT = 'edit'

    BROWSE = 'browse'
    """The HTML content of a URL
    """

    RUN = 'run'
    """The output of a command
    """

    RUN_IPYTHON = 'run_ipython'
    """Runs a IPython cell.
    """

    CHAT = 'chat'
    """A message from the user
    """

    DELEGATE = 'delegate'
    """The result of a task delegated to another agent
    """

    MESSAGE = 'message'

    ERROR = 'error'

    SUCCESS = 'success'

    NULL = 'null'

    THINK = 'think'

    AGENT_STATE_CHANGED = 'agent_state_changed'

    USER_REJECTED = 'user_rejected'

    CONDENSE = 'condense'
    """Result of a condensation operation."""

    RECALL = 'recall'
    """Result of a recall operation. This can be the workspace context, a microagent, or other types of information."""

    MCP = 'mcp'
    """Result of a MCP Server operation"""

    DOWNLOAD = 'download'
    """Result of downloading/opening a file via the browser"""

    DRAFT_SECTIONS_CHANGED = 'draft_sections_changed'
    """Draft sections were added, removed, or reordered"""

    DRAFT_CONTENT_CHANGED = 'draft_content_changed'
    """Draft section content was modified"""

    DRAFT_METADATA_CHANGED = 'draft_metadata_changed'
    """Draft metadata (name, type, etc.) was modified"""

    DRAFT_SYNC_STATUS = 'draft_sync_status'
    """Draft synchronization status update"""
