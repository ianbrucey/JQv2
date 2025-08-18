import asyncio
import os
import time
from copy import deepcopy
from logging import LoggerAdapter

import socketio

from openhands.controller.agent import Agent
from openhands.core.config import OpenHandsConfig
from openhands.core.config.condenser_config import (
    BrowserOutputCondenserConfig,
    CondenserPipelineConfig,
    ConversationWindowCondenserConfig,
    LLMSummarizingCondenserConfig,
)
from openhands.core.config.mcp_config import OpenHandsMCPConfigImpl
from openhands.core.exceptions import MicroagentValidationError
from openhands.core.logger import OpenHandsLoggerAdapter
from openhands.core.schema import AgentState
from openhands.events.action import MessageAction, NullAction
from openhands.events.event import Event, EventSource
from openhands.events.observation import (
    AgentStateChangedObservation,
    CmdOutputObservation,
    NullObservation,
)
from openhands.events.observation.agent import RecallObservation
from openhands.events.observation.error import ErrorObservation
from openhands.events.serialization import event_from_dict, event_to_dict
from openhands.events.stream import EventStreamSubscriber
from openhands.llm.llm import LLM
from openhands.runtime.runtime_status import RuntimeStatus
from openhands.server.constants import ROOM_KEY
from openhands.server.legal_workspace_manager import (
    get_legal_workspace_manager,
    initialize_legal_workspace_manager,
    cleanup_legal_workspace_manager
)
from openhands.server.session.agent_session import AgentSession
from openhands.server.session.conversation_init_data import ConversationInitData
from openhands.storage.data_models.settings import Settings
from openhands.storage.files import FileStore


class Session:
    sid: str
    sio: socketio.AsyncServer | None
    last_active_ts: int = 0
    is_alive: bool = True
    agent_session: AgentSession
    loop: asyncio.AbstractEventLoop
    config: OpenHandsConfig
    file_store: FileStore
    user_id: str | None
    logger: LoggerAdapter

    def __init__(
        self,
        sid: str,
        config: OpenHandsConfig,
        file_store: FileStore,
        sio: socketio.AsyncServer | None,
        user_id: str | None = None,
    ):
        self.sid = sid
        self.sio = sio
        self.last_active_ts = int(time.time())
        self.file_store = file_store
        self.logger = OpenHandsLoggerAdapter(extra={'session_id': sid})
        self.agent_session = AgentSession(
            sid,
            file_store,
            status_callback=self.queue_status_message,
            user_id=user_id,
        )
        self.agent_session.event_stream.subscribe(
            EventStreamSubscriber.SERVER, self.on_event, self.sid
        )
        # Copying this means that when we update variables they are not applied to the shared global configuration!
        self.config = deepcopy(config)
        # Lazy import to avoid circular dependency
        from openhands.experiments.experiment_manager import ExperimentManagerImpl

        self.config = ExperimentManagerImpl.run_config_variant_test(
            user_id, sid, self.config
        )
        self.loop = asyncio.get_event_loop()
        self.user_id = user_id

        # Initialize session-specific legal workspace manager
        self.legal_workspace_manager = initialize_legal_workspace_manager(
            self.config, self.sid, user_id
        )

    async def close(self) -> None:
        if self.sio:
            await self.sio.emit(
                'oh_event',
                event_to_dict(
                    AgentStateChangedObservation('', AgentState.STOPPED.value)
                ),
                to=ROOM_KEY.format(sid=self.sid),
            )
        self.is_alive = False

        # Clean up session-specific legal workspace manager
        cleanup_legal_workspace_manager(self.sid)

        await self.agent_session.close()

    async def initialize_agent(
        self,
        settings: Settings,
        initial_message: MessageAction | None,
        replay_json: str | None,
    ) -> None:
        self.agent_session.event_stream.add_event(
            AgentStateChangedObservation('', AgentState.LOADING),
            EventSource.ENVIRONMENT,
        )
        agent_cls = settings.agent or self.config.default_agent
        self.config.security.confirmation_mode = (
            self.config.security.confirmation_mode
            if settings.confirmation_mode is None
            else settings.confirmation_mode
        )
        self.config.security.security_analyzer = (
            settings.security_analyzer or self.config.security.security_analyzer
        )
        self.config.sandbox.base_container_image = (
            settings.sandbox_base_container_image
            or self.config.sandbox.base_container_image
        )
        self.config.sandbox.runtime_container_image = (
            settings.sandbox_runtime_container_image
            if settings.sandbox_base_container_image
            or settings.sandbox_runtime_container_image
            else self.config.sandbox.runtime_container_image
        )

        # Set Git user configuration if provided in settings
        git_user_name = getattr(settings, 'git_user_name', None)
        if git_user_name is not None:
            self.config.git_user_name = git_user_name
        git_user_email = getattr(settings, 'git_user_email', None)
        if git_user_email is not None:
            self.config.git_user_email = git_user_email
        max_iterations = settings.max_iterations or self.config.max_iterations

        # Prioritize settings over config for max_budget_per_task
        max_budget_per_task = (
            settings.max_budget_per_task
            if settings.max_budget_per_task is not None
            else self.config.max_budget_per_task
        )

        # This is a shallow copy of the default LLM config, so changes here will
        # persist if we retrieve the default LLM config again when constructing
        # the agent
        default_llm_config = self.config.get_llm_config()
        default_llm_config.model = settings.llm_model or ''
        default_llm_config.api_key = settings.llm_api_key
        default_llm_config.base_url = settings.llm_base_url
        self.config.search_api_key = settings.search_api_key
        if settings.sandbox_api_key:
            self.config.sandbox.api_key = settings.sandbox_api_key.get_secret_value()

        # NOTE: this need to happen AFTER the config is updated with the search_api_key
        self.logger.debug(
            f'MCP configuration before setup - self.config.mcp_config: {self.config.mcp}'
        )

        # Check if settings has custom mcp_config
        mcp_config = getattr(settings, 'mcp_config', None)
        if mcp_config is not None:
            # Use the provided MCP SHTTP servers instead of default setup
            self.config.mcp = self.config.mcp.merge(mcp_config)
            self.logger.debug(f'Merged custom MCP Config: {mcp_config}')

        # Add OpenHands' MCP server by default
        openhands_mcp_server, openhands_mcp_stdio_servers = (
            OpenHandsMCPConfigImpl.create_default_mcp_server_config(
                self.config.mcp_host, self.config, self.user_id
            )
        )

        if openhands_mcp_server:
            self.config.mcp.shttp_servers.append(openhands_mcp_server)
            self.logger.debug('Added default MCP HTTP server to config')

            self.config.mcp.stdio_servers.extend(openhands_mcp_stdio_servers)

        self.logger.debug(
            f'MCP configuration after setup - self.config.mcp: {self.config.mcp}'
        )

        # TODO: override other LLM config & agent config groups (#2075)

        llm = self._create_llm(agent_cls)
        agent_config = self.config.get_agent_config(agent_cls)

        if settings.enable_default_condenser:
            # Default condenser chains three condensers together:
            # 1. a conversation window condenser that handles explicit
            # condensation requests,
            # 2. a condenser that limits the total size of browser observations,
            # and
            # 3. a condenser that limits the size of the view given to the LLM.
            # The order matters: with the browser output first, the summarizer
            # will only see the most recent browser output, which should keep
            # the summarization cost down.
            default_condenser_config = CondenserPipelineConfig(
                condensers=[
                    ConversationWindowCondenserConfig(),
                    BrowserOutputCondenserConfig(attention_window=2),
                    LLMSummarizingCondenserConfig(
                        llm_config=llm.config, keep_first=4, max_size=120
                    ),
                ]
            )

            self.logger.info(
                f'Enabling pipeline condenser with:'
                f' browser_output_masking(attention_window=2), '
                f' llm(model="{llm.config.model}", '
                f' base_url="{llm.config.base_url}", '
                f' keep_first=4, max_size=80)'
            )
            agent_config.condenser = default_condenser_config
        agent = Agent.get_cls(agent_cls)(llm, agent_config)

        git_provider_tokens = None
        selected_repository = None
        selected_branch = None
        custom_secrets = None
        conversation_instructions = None
        if isinstance(settings, ConversationInitData):
            git_provider_tokens = settings.git_provider_tokens
            selected_repository = settings.selected_repository
            selected_branch = settings.selected_branch
            custom_secrets = settings.custom_secrets
            conversation_instructions = settings.conversation_instructions

        # Detect and configure legal case workspace BEFORE runtime creation
        runtime_config = await self._configure_legal_runtime_with_case_detection(
            self.config, conversation_instructions
        )

        try:
            await self.agent_session.start(
                runtime_name=runtime_config.runtime,
                config=runtime_config,
                agent=agent,
                max_iterations=max_iterations,
                max_budget_per_task=max_budget_per_task,
                agent_to_llm_config=runtime_config.get_agent_to_llm_config_map(),
                agent_configs=runtime_config.get_agent_configs(),
                git_provider_tokens=git_provider_tokens,
                custom_secrets=custom_secrets,
                selected_repository=selected_repository,
                selected_branch=selected_branch,
                initial_message=initial_message,
                conversation_instructions=conversation_instructions,
                replay_json=replay_json,
            )
        except MicroagentValidationError as e:
            self.logger.exception(f'Error creating agent_session: {e}')
            # For microagent validation errors, provide more helpful information
            await self.send_error(f'Failed to create agent session: {str(e)}')
            return
        except ValueError as e:
            self.logger.exception(f'Error creating agent_session: {e}')
            error_message = str(e)
            # For ValueError related to microagents, provide more helpful information
            if 'microagent' in error_message.lower():
                await self.send_error(
                    f'Failed to create agent session: {error_message}'
                )
            else:
                # For other ValueErrors, just show the error class
                await self.send_error('Failed to create agent session: ValueError')
            return
        except Exception as e:
            self.logger.exception(f'Error creating agent_session: {e}')
            # For other errors, just show the error class to avoid exposing sensitive information
            await self.send_error(
                f'Failed to create agent session: {e.__class__.__name__}'
            )
            return

    def _create_llm(self, agent_cls: str | None) -> LLM:
        """Initialize LLM, extracted for testing."""
        agent_name = agent_cls if agent_cls is not None else 'agent'
        return LLM(
            config=self.config.get_llm_config_from_agent(agent_name),
            retry_listener=self._notify_on_llm_retry,
        )

    def _notify_on_llm_retry(self, retries: int, max: int) -> None:
        self.queue_status_message(
            'info', RuntimeStatus.LLM_RETRY, f'Retrying LLM request, {retries} / {max}'
        )

    def on_event(self, event: Event) -> None:
        asyncio.get_event_loop().run_until_complete(self._on_event(event))

    async def _on_event(self, event: Event) -> None:
        """Callback function for events that mainly come from the agent.

        Event is the base class for any agent action and observation.

        Args:
            event: The agent event (Observation or Action).
        """
        if isinstance(event, NullAction):
            return
        if isinstance(event, NullObservation):
            return
        if event.source == EventSource.AGENT:
            await self.send(event_to_dict(event))
        elif event.source == EventSource.USER:
            await self.send(event_to_dict(event))
        # NOTE: ipython observations are not sent here currently
        elif event.source == EventSource.ENVIRONMENT and isinstance(
            event,
            (CmdOutputObservation, AgentStateChangedObservation, RecallObservation),
        ):
            # feedback from the environment to agent actions is understood as agent events by the UI
            event_dict = event_to_dict(event)
            event_dict['source'] = EventSource.AGENT
            await self.send(event_dict)
            if (
                isinstance(event, AgentStateChangedObservation)
                and event.agent_state == AgentState.ERROR
            ):
                self.logger.error(
                    f'Agent status error: {event.reason}',
                    extra={'signal': 'agent_status_error'},
                )
        elif isinstance(event, ErrorObservation):
            # send error events as agent events to the UI
            event_dict = event_to_dict(event)
            event_dict['source'] = EventSource.AGENT
            await self.send(event_dict)

    async def dispatch(self, data: dict) -> None:
        event = event_from_dict(data.copy())
        # This checks if the model supports images
        if isinstance(event, MessageAction) and event.image_urls:
            controller = self.agent_session.controller
            if controller:
                if controller.agent.llm.config.disable_vision:
                    await self.send_error(
                        'Support for images is disabled for this model, try without an image.'
                    )
                    return
                if not controller.agent.llm.vision_is_active():
                    await self.send_error(
                        'Model does not support image upload, change to a different model or try without an image.'
                    )
                    return
        self.agent_session.event_stream.add_event(event, EventSource.USER)

    async def send(self, data: dict[str, object]) -> None:
        if asyncio.get_running_loop() != self.loop:
            self.loop.create_task(self._send(data))
            return
        await self._send(data)

    async def _send(self, data: dict[str, object]) -> bool:
        try:
            if not self.is_alive:
                return False
            if self.sio:
                await self.sio.emit('oh_event', data, to=ROOM_KEY.format(sid=self.sid))
            await asyncio.sleep(0.001)  # This flushes the data to the client
            self.last_active_ts = int(time.time())
            return True
        except RuntimeError as e:
            self.logger.error(f'Error sending data to websocket: {str(e)}')
            self.is_alive = False
            return False

    async def send_error(self, message: str) -> None:
        """Sends an error message to the client."""
        await self.send({'error': True, 'message': message})

    async def _send_status_message(
        self, msg_type: str, runtime_status: RuntimeStatus, message: str
    ) -> None:
        """Sends a status message to the client."""
        if msg_type == 'error':
            agent_session = self.agent_session
            controller = self.agent_session.controller
            if controller is not None and not agent_session.is_closed():
                await controller.set_agent_state_to(AgentState.ERROR)
            self.logger.error(
                f'Agent status error: {message}',
                extra={'signal': 'agent_status_error'},
            )
        await self.send(
            {
                'status_update': True,
                'type': msg_type,
                'id': runtime_status.value,
                'message': message,
            }
        )

    def queue_status_message(
        self, msg_type: str, runtime_status: RuntimeStatus, message: str
    ) -> None:
        """Queues a status message to be sent asynchronously."""
        asyncio.run_coroutine_threadsafe(
            self._send_status_message(msg_type, runtime_status, message), self.loop
        )

    async def _configure_legal_runtime_if_needed(self, config: OpenHandsConfig) -> OpenHandsConfig:
        """Configure runtime for legal case workspace if we're in legal mode.

        This method checks if we're currently in a legal case workspace and if so,
        configures the runtime to use LocalRuntime for instant startup instead of Docker.

        Args:
            config: The original OpenHands configuration

        Returns:
            Modified configuration with legal runtime settings if applicable
        """
        # Use session-specific legal workspace manager
        legal_workspace_manager = get_legal_workspace_manager(self.sid)

        # Check multiple indicators for legal case context
        is_legal_case = False
        case_id = None
        case_workspace_path = None

        # Method 1: Check if legal workspace manager indicates we're in a case
        if legal_workspace_manager and legal_workspace_manager.is_in_case_workspace():
            is_legal_case = True
            case_id = legal_workspace_manager.current_case_id
            case_workspace_path = config.workspace_base
            self.logger.debug(f"Legal case detected via workspace manager: {case_id}")

        # Method 2: Check if workspace path indicates legal case
        elif config.workspace_base and "legal_workspace/cases/" in str(config.workspace_base):
            is_legal_case = True
            # Extract case ID from path
            try:
                path_parts = str(config.workspace_base).split("/")
                if "cases" in path_parts:
                    case_idx = path_parts.index("cases")
                    if case_idx + 1 < len(path_parts):
                        case_id = path_parts[case_idx + 1]
                case_workspace_path = config.workspace_base
                self.logger.debug(f"Legal case detected via workspace path: {case_id}")
            except Exception as e:
                self.logger.debug(f"Could not extract case ID from path: {e}")

        # Method 3: Check session ID for legal case pattern
        elif self.sid and ("legal_" in self.sid or "case_" in self.sid):
            is_legal_case = True
            case_id = self.sid
            case_workspace_path = config.workspace_base
            self.logger.debug(f"Legal case detected via session ID: {case_id}")

        # If not a legal case, use original config
        if not is_legal_case:
            return config

        # Create a copy of the config for legal case modifications
        legal_config = config.model_copy(deep=True)

        # Configure for LocalRuntime to avoid Docker startup delay
        legal_config.runtime = "local"

        if case_workspace_path:
            # Configure workspace for LocalRuntime
            legal_config.workspace_base = case_workspace_path
            legal_config.workspace_mount_path = case_workspace_path
            legal_config.workspace_mount_path_in_sandbox = "/workspace"

            # Configure sandbox volumes for local runtime
            legal_config.sandbox.volumes = f"{case_workspace_path}:/workspace:rw"

            # Set up environment variables for the runtime
            if not legal_config.sandbox.runtime_startup_env_vars:
                legal_config.sandbox.runtime_startup_env_vars = {}

            # Add legal case environment variables that will be available to the agent
            legal_config.sandbox.runtime_startup_env_vars.update({
                'OH_CASE_WORKSPACE': case_workspace_path,
                'LEGAL_CASE_ID': case_id or '',
                'WORKSPACE_BASE': case_workspace_path,
                'LEGAL_WORKSPACE_ROOT': os.environ.get('LEGAL_WORKSPACE_ROOT', '/tmp/legal_workspace'),
                'DRAFT_SYSTEM_PATH': os.environ.get('DRAFT_SYSTEM_PATH', '/tmp/draft_system'),
            })

            # Create the sentinel file in the workspace
            try:
                from pathlib import Path
                import json
                sentinel_path = Path(case_workspace_path) / '.case_workspace.json'
                sentinel_data = {
                    'case_id': case_id,
                    'workspace_path': case_workspace_path,
                    'session_id': self.sid
                }
                sentinel_path.write_text(json.dumps(sentinel_data, indent=2))
                self.logger.debug(f"Created sentinel file: {sentinel_path}")
            except Exception as e:
                self.logger.warning(f"Failed to create sentinel file: {e}")

            self.logger.info(
                f"🏛️ Legal Runtime Configuration Applied:\n"
                f"  • Runtime: {legal_config.runtime} (bypassing Docker for instant startup)\n"
                f"  • Case ID: {case_id}\n"
                f"  • Workspace: {case_workspace_path}\n"
                f"  • Environment Variables: OH_CASE_WORKSPACE, LEGAL_CASE_ID\n"
                f"  • Expected startup time: < 5 seconds"
            )

        return legal_config

    async def _configure_legal_runtime_with_case_detection(
        self, config: OpenHandsConfig, conversation_instructions: str | None = None
    ) -> OpenHandsConfig:
        """Simple direct approach: Extract case_id from conversation_instructions and set workspace."""

        # Step 1: Extract case_id from conversation_instructions
        case_id = None
        if conversation_instructions:
            import re
            case_id_match = re.search(r'Case ID:\s*([a-f0-9-]+)', conversation_instructions)
            if case_id_match:
                case_id = case_id_match.group(1)
                self.logger.info(f"🏛️ Extracted case_id from conversation instructions: {case_id}")

        if case_id:
            try:
                # Step 2: Construct workspace path directly
                case_workspace_path = f"/tmp/legal_workspace/cases/case-{case_id}/draft_system"

                # Step 3: Set workspace_base directly in config
                legal_config = config.model_copy(deep=True)
                legal_config.runtime = "local"  # Use LocalRuntime for instant startup
                legal_config.workspace_base = case_workspace_path
                legal_config.workspace_mount_path = case_workspace_path
                legal_config.workspace_mount_path_in_sandbox = "/workspace"
                legal_config.sandbox.volumes = f"{case_workspace_path}:/workspace:rw"

                # Set environment variables
                if not legal_config.sandbox.runtime_startup_env_vars:
                    legal_config.sandbox.runtime_startup_env_vars = {}

                legal_config.sandbox.runtime_startup_env_vars.update({
                    'OH_CASE_WORKSPACE': case_workspace_path,
                    'LEGAL_CASE_ID': case_id,
                    'WORKSPACE_BASE': case_workspace_path,
                    'LEGAL_WORKSPACE_ROOT': '/tmp/legal_workspace',
                    'DRAFT_SYSTEM_PATH': '/tmp/draft_system',
                })

                # Create workspace directory and sentinel file
                from pathlib import Path
                import json
                Path(case_workspace_path).mkdir(parents=True, exist_ok=True)
                sentinel_path = Path(case_workspace_path) / '.case_workspace.json'
                sentinel_data = {
                    'case_id': case_id,
                    'workspace_path': case_workspace_path,
                    'session_id': self.sid
                }
                sentinel_path.write_text(json.dumps(sentinel_data, indent=2))

                self.logger.info(
                    f"🏛️ Legal Workspace Configured Successfully:\n"
                    f"  • Case ID: {case_id}\n"
                    f"  • Workspace: {case_workspace_path}\n"
                    f"  • Runtime: LocalRuntime\n"
                    f"  • Environment: OH_CASE_WORKSPACE={case_workspace_path}"
                )

                return legal_config

            except Exception as e:
                self.logger.warning(f"Failed to configure legal workspace for case {case_id}: {e}")

        # Fallback to regular configuration
        self.logger.debug("No legal case detected, using regular configuration")
        return config
