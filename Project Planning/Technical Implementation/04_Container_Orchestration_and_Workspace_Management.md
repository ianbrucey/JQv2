# Container Orchestration and Workspace Management

## Technology Stack
- **Container Runtime**: Docker Engine 24.0+
- **Container Management**: docker-py (Python Docker SDK)
- **Process Management**: asyncio with concurrent.futures
- **File System**: Local SSD with bind mounts
- **Monitoring**: Custom health checks and metrics

## Container Architecture

### Container Configuration
```python
from docker import DockerClient
from docker.models.containers import Container
from typing import Dict, Optional, List
import asyncio
import logging
from pathlib import Path

class ContainerConfig:
    """Container configuration settings."""
    
    def __init__(self):
        self.image_name = "legal-workspace:latest"
        self.memory_limit = "4g"
        self.cpu_quota = 200000  # 2 CPU cores (100000 = 1 core)
        self.cpu_period = 100000
        self.port_range = range(8001, 9000)
        self.network_mode = "bridge"
        self.restart_policy = {"Name": "no"}
        self.security_opts = [
            "no-new-privileges:true",
            "seccomp:unconfined"  # May need adjustment for OpenHands
        ]
        self.cap_drop = ["ALL"]
        self.cap_add = ["CHOWN", "DAC_OVERRIDE", "FOWNER", "SETGID", "SETUID"]

class ContainerManager:
    """Manages Docker containers for user sessions."""
    
    def __init__(self):
        self.docker_client = DockerClient.from_env()
        self.config = ContainerConfig()
        self.allocated_ports = set()
        self.active_containers: Dict[str, ContainerInfo] = {}
        self.logger = logging.getLogger(__name__)
    
    async def provision_container(
        self,
        user_id: str,
        case_id: str,
        workspace_path: str
    ) -> ContainerInfo:
        """Provision new container for user session."""
        try:
            # Allocate port
            port = self._allocate_port()
            
            # Generate container name
            container_name = f"legal-session-{user_id}-{int(time.time())}"
            
            # Prepare environment variables
            environment = {
                "USER_ID": user_id,
                "CASE_ID": case_id,
                "WORKSPACE_BASE": "/opt/workspace",
                "OPENHANDS_USER_ID": user_id,
                "PYTHONPATH": "/opt/openhands",
            }
            
            # Configure volumes
            volumes = {
                workspace_path: {
                    "bind": "/opt/workspace",
                    "mode": "rw"
                },
                "/var/run/docker.sock": {
                    "bind": "/var/run/docker.sock",
                    "mode": "rw"
                }
            }
            
            # Create container
            container = await self._create_container(
                name=container_name,
                port=port,
                environment=environment,
                volumes=volumes
            )
            
            # Wait for container to be ready
            await self._wait_for_container_ready(container, port)
            
            # Create container info
            container_info = ContainerInfo(
                container_id=container.id,
                container_name=container_name,
                user_id=user_id,
                case_id=case_id,
                port=port,
                workspace_path=workspace_path,
                status="running",
                created_at=datetime.utcnow()
            )
            
            self.active_containers[user_id] = container_info
            
            self.logger.info(f"Container provisioned for user {user_id}: {container_name}")
            return container_info
            
        except Exception as e:
            self.logger.error(f"Failed to provision container for user {user_id}: {e}")
            if port:
                self._release_port(port)
            raise ContainerProvisionError(f"Container provisioning failed: {e}")
    
    async def _create_container(
        self,
        name: str,
        port: int,
        environment: Dict[str, str],
        volumes: Dict[str, Dict[str, str]]
    ) -> Container:
        """Create Docker container with specified configuration."""
        
        container_config = {
            "image": self.config.image_name,
            "name": name,
            "detach": True,
            "environment": environment,
            "volumes": volumes,
            "ports": {"3000/tcp": port},  # OpenHands internal port
            "mem_limit": self.config.memory_limit,
            "cpu_quota": self.config.cpu_quota,
            "cpu_period": self.config.cpu_period,
            "network_mode": self.config.network_mode,
            "restart_policy": self.config.restart_policy,
            "security_opt": self.config.security_opts,
            "cap_drop": self.config.cap_drop,
            "cap_add": self.config.cap_add,
            "read_only": False,  # OpenHands needs write access
            "tmpfs": {
                "/tmp": "rw,noexec,nosuid,size=1g"
            }
        }
        
        # Run container creation in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        container = await loop.run_in_executor(
            None,
            lambda: self.docker_client.containers.run(**container_config)
        )
        
        return container
    
    async def _wait_for_container_ready(
        self,
        container: Container,
        port: int,
        timeout: int = 60
    ) -> bool:
        """Wait for container to be ready and responsive."""
        import aiohttp
        
        url = f"http://localhost:{port}/health"
        
        for attempt in range(timeout):
            try:
                # Check container status
                container.reload()
                if container.status != "running":
                    await asyncio.sleep(1)
                    continue
                
                # Check HTTP endpoint
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=2) as response:
                        if response.status == 200:
                            return True
                            
            except Exception:
                pass
            
            await asyncio.sleep(1)
        
        raise ContainerReadyTimeout(f"Container not ready after {timeout} seconds")
    
    def _allocate_port(self) -> int:
        """Allocate next available port."""
        for port in self.config.port_range:
            if port not in self.allocated_ports:
                self.allocated_ports.add(port)
                return port
        
        raise NoAvailablePortsError("No available ports in range")
    
    def _release_port(self, port: int):
        """Release allocated port."""
        self.allocated_ports.discard(port)
    
    async def get_container_info(self, user_id: str) -> Optional[ContainerInfo]:
        """Get container info for user."""
        return self.active_containers.get(user_id)
    
    async def cleanup_container(self, user_id: str) -> bool:
        """Clean up user's container."""
        container_info = self.active_containers.get(user_id)
        if not container_info:
            return False
        
        try:
            # Get container
            container = self.docker_client.containers.get(container_info.container_id)
            
            # Stop and remove container
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, container.stop, 10)  # 10 second timeout
            await loop.run_in_executor(None, container.remove)
            
            # Release port
            self._release_port(container_info.port)
            
            # Remove from active containers
            del self.active_containers[user_id]
            
            self.logger.info(f"Container cleaned up for user {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup container for user {user_id}: {e}")
            return False
    
    async def cleanup_all_containers(self) -> int:
        """Clean up all active containers."""
        cleanup_count = 0
        
        for user_id in list(self.active_containers.keys()):
            if await self.cleanup_container(user_id):
                cleanup_count += 1
        
        return cleanup_count
    
    async def get_container_stats(self, user_id: str) -> Optional[Dict]:
        """Get container resource usage statistics."""
        container_info = self.active_containers.get(user_id)
        if not container_info:
            return None
        
        try:
            container = self.docker_client.containers.get(container_info.container_id)
            
            # Get stats (non-streaming)
            loop = asyncio.get_event_loop()
            stats = await loop.run_in_executor(
                None,
                lambda: container.stats(stream=False)
            )
            
            return self._parse_container_stats(stats)
            
        except Exception as e:
            self.logger.error(f"Failed to get stats for user {user_id}: {e}")
            return None
    
    def _parse_container_stats(self, stats: Dict) -> Dict:
        """Parse Docker container stats into useful metrics."""
        try:
            # CPU usage
            cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - \
                       stats["precpu_stats"]["cpu_usage"]["total_usage"]
            system_delta = stats["cpu_stats"]["system_cpu_usage"] - \
                          stats["precpu_stats"]["system_cpu_usage"]
            cpu_percent = (cpu_delta / system_delta) * 100.0 if system_delta > 0 else 0.0
            
            # Memory usage
            memory_usage = stats["memory_stats"]["usage"]
            memory_limit = stats["memory_stats"]["limit"]
            memory_percent = (memory_usage / memory_limit) * 100.0
            
            # Network I/O
            network_rx = 0
            network_tx = 0
            if "networks" in stats:
                for interface in stats["networks"].values():
                    network_rx += interface["rx_bytes"]
                    network_tx += interface["tx_bytes"]
            
            return {
                "cpu_percent": round(cpu_percent, 2),
                "memory_usage_mb": round(memory_usage / 1024 / 1024, 2),
                "memory_limit_mb": round(memory_limit / 1024 / 1024, 2),
                "memory_percent": round(memory_percent, 2),
                "network_rx_mb": round(network_rx / 1024 / 1024, 2),
                "network_tx_mb": round(network_tx / 1024 / 1024, 2),
            }
            
        except Exception as e:
            self.logger.error(f"Failed to parse container stats: {e}")
            return {}

@dataclass
class ContainerInfo:
    """Container information data class."""
    container_id: str
    container_name: str
    user_id: str
    case_id: str
    port: int
    workspace_path: str
    status: str
    created_at: datetime
```

## Workspace Management

### Workspace Manager
```python
import shutil
import aiofiles
from pathlib import Path

class WorkspaceManager:
    """Manages user workspaces and case materialization."""
    
    def __init__(self, storage_service, container_manager: ContainerManager):
        self.storage_service = storage_service
        self.container_manager = container_manager
        self.workspace_root = Path("/var/legal-workspaces")
        self.logger = logging.getLogger(__name__)
    
    async def create_user_workspace(
        self,
        user_id: str,
        case_id: str
    ) -> str:
        """Create workspace directory for user and case."""
        workspace_path = self.workspace_root / user_id
        case_workspace = workspace_path / "active" / case_id
        
        # Create directory structure
        case_workspace.mkdir(parents=True, exist_ok=True)
        
        # Create standard legal folders
        await self._create_case_structure(case_workspace)
        
        return str(workspace_path)
    
    async def _create_case_structure(self, case_path: Path):
        """Create standard legal case folder structure."""
        folders = [
            "pleadings",
            "motions", 
            "discovery",
            "exhibits",
            "correspondence",
            "research",
            "drafts",
            "final"
        ]
        
        for folder in folders:
            folder_path = case_path / folder
            folder_path.mkdir(exist_ok=True)
            
            # Create .gitkeep to preserve empty directories
            gitkeep_file = folder_path / ".gitkeep"
            gitkeep_file.touch()
    
    async def materialize_case_files(
        self,
        user_id: str,
        case_id: str,
        case_data: Dict
    ) -> bool:
        """Download and materialize case files from object storage."""
        try:
            workspace_path = self.workspace_root / user_id / "active" / case_id
            
            # Get case file manifest from storage
            file_manifest = await self.storage_service.get_case_manifest(
                user_id, case_id
            )
            
            # Download files based on priority
            await self._download_priority_files(workspace_path, file_manifest)
            
            self.logger.info(f"Case files materialized for {user_id}/{case_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to materialize case files: {e}")
            return False
    
    async def _download_priority_files(
        self,
        workspace_path: Path,
        file_manifest: List[Dict]
    ):
        """Download files based on priority (small files first)."""
        # Sort files by size (small files first for faster startup)
        sorted_files = sorted(file_manifest, key=lambda f: f.get("size", 0))
        
        # Download small files immediately (< 1MB)
        small_files = [f for f in sorted_files if f.get("size", 0) < 1024 * 1024]
        
        for file_info in small_files:
            await self._download_file(workspace_path, file_info)
        
        # Create stubs for large files (download on demand)
        large_files = [f for f in sorted_files if f.get("size", 0) >= 1024 * 1024]
        
        for file_info in large_files:
            await self._create_file_stub(workspace_path, file_info)
    
    async def _download_file(self, workspace_path: Path, file_info: Dict):
        """Download individual file from object storage."""
        try:
            file_path = workspace_path / file_info["logical_path"]
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Download file content
            content = await self.storage_service.download_file(
                file_info["storage_key"]
            )
            
            # Write to local file
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)
                
        except Exception as e:
            self.logger.error(f"Failed to download file {file_info['logical_path']}: {e}")
    
    async def _create_file_stub(self, workspace_path: Path, file_info: Dict):
        """Create stub file for lazy loading."""
        file_path = workspace_path / file_info["logical_path"]
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create stub file with metadata
        stub_content = f"""# File Stub: {file_info['file_name']}
# Size: {file_info.get('size', 0)} bytes
# Storage Key: {file_info['storage_key']}
# This file will be downloaded when accessed.
"""
        
        async with aiofiles.open(file_path.with_suffix(".stub"), "w") as f:
            await f.write(stub_content)
    
    async def sync_workspace_changes(
        self,
        user_id: str,
        case_id: str
    ) -> bool:
        """Sync workspace changes back to object storage."""
        try:
            workspace_path = self.workspace_root / user_id / "active" / case_id
            
            if not workspace_path.exists():
                return False
            
            # Find changed files
            changed_files = await self._find_changed_files(workspace_path)
            
            # Upload changed files
            for file_path in changed_files:
                await self._upload_file(user_id, case_id, file_path)
            
            self.logger.info(f"Workspace synced for {user_id}/{case_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to sync workspace: {e}")
            return False
    
    async def _find_changed_files(self, workspace_path: Path) -> List[Path]:
        """Find files that have been modified since last sync."""
        changed_files = []
        
        # Simple implementation: check all files
        # In production, use file system events or checksums
        for file_path in workspace_path.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith("."):
                changed_files.append(file_path)
        
        return changed_files
    
    async def _upload_file(self, user_id: str, case_id: str, file_path: Path):
        """Upload file to object storage."""
        try:
            # Read file content
            async with aiofiles.open(file_path, "rb") as f:
                content = await f.read()
            
            # Calculate relative path
            workspace_path = self.workspace_root / user_id / "active" / case_id
            relative_path = file_path.relative_to(workspace_path)
            
            # Upload to storage
            await self.storage_service.upload_file(
                user_id=user_id,
                case_id=case_id,
                logical_path=str(relative_path),
                content=content,
                file_name=file_path.name
            )
            
        except Exception as e:
            self.logger.error(f"Failed to upload file {file_path}: {e}")
    
    async def cleanup_workspace(self, user_id: str) -> bool:
        """Clean up user workspace."""
        try:
            workspace_path = self.workspace_root / user_id
            
            if workspace_path.exists():
                # Sync any pending changes first
                for case_dir in (workspace_path / "active").iterdir():
                    if case_dir.is_dir():
                        await self.sync_workspace_changes(user_id, case_dir.name)
                
                # Remove workspace directory
                shutil.rmtree(workspace_path)
            
            self.logger.info(f"Workspace cleaned up for user {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup workspace for {user_id}: {e}")
            return False
```

## Session Orchestration Service

### Session Orchestrator
```python
class SessionOrchestrator:
    """Orchestrates container and workspace lifecycle."""
    
    def __init__(
        self,
        container_manager: ContainerManager,
        workspace_manager: WorkspaceManager,
        db: AsyncSession
    ):
        self.container_manager = container_manager
        self.workspace_manager = workspace_manager
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    async def start_user_session(
        self,
        user_id: str,
        case_id: str,
        case_data: Dict
    ) -> ContainerInfo:
        """Start complete user session with container and workspace."""
        try:
            # Create workspace
            workspace_path = await self.workspace_manager.create_user_workspace(
                user_id, case_id
            )
            
            # Materialize case files
            await self.workspace_manager.materialize_case_files(
                user_id, case_id, case_data
            )
            
            # Provision container
            container_info = await self.container_manager.provision_container(
                user_id, case_id, workspace_path
            )
            
            # Update session in database
            await self._update_session_record(user_id, container_info)
            
            self.logger.info(f"Session started for user {user_id}")
            return container_info
            
        except Exception as e:
            self.logger.error(f"Failed to start session for user {user_id}: {e}")
            # Cleanup on failure
            await self._cleanup_failed_session(user_id)
            raise
    
    async def end_user_session(self, user_id: str) -> bool:
        """End user session and cleanup resources."""
        try:
            # Sync workspace changes
            container_info = await self.container_manager.get_container_info(user_id)
            if container_info:
                await self.workspace_manager.sync_workspace_changes(
                    user_id, container_info.case_id
                )
            
            # Cleanup container
            await self.container_manager.cleanup_container(user_id)
            
            # Cleanup workspace
            await self.workspace_manager.cleanup_workspace(user_id)
            
            # Update session in database
            await self._invalidate_session_record(user_id)
            
            self.logger.info(f"Session ended for user {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to end session for user {user_id}: {e}")
            return False
    
    async def _update_session_record(
        self,
        user_id: str,
        container_info: ContainerInfo
    ):
        """Update session record in database."""
        session_service = SessionService(self.db)
        
        # Find active session
        query = select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.is_active == True
        )
        result = await self.db.execute(query)
        session = result.scalar_one_or_none()
        
        if session:
            session.container_id = container_info.container_id
            session.container_port = container_info.port
            session.active_case_id = container_info.case_id
            session.workspace_path = container_info.workspace_path
            await self.db.commit()
    
    async def _invalidate_session_record(self, user_id: str):
        """Invalidate session record in database."""
        query = update(UserSession).where(
            UserSession.user_id == user_id
        ).values(
            is_active=False,
            container_id=None,
            container_port=None
        )
        
        await self.db.execute(query)
        await self.db.commit()
    
    async def _cleanup_failed_session(self, user_id: str):
        """Cleanup resources after failed session start."""
        try:
            await self.container_manager.cleanup_container(user_id)
            await self.workspace_manager.cleanup_workspace(user_id)
        except Exception as e:
            self.logger.error(f"Failed to cleanup after session failure: {e}")
```

## Custom Exceptions

```python
class ContainerError(Exception):
    """Base container error."""
    pass

class ContainerProvisionError(ContainerError):
    """Container provisioning failed."""
    pass

class ContainerReadyTimeout(ContainerError):
    """Container failed to become ready in time."""
    pass

class NoAvailablePortsError(ContainerError):
    """No available ports for container."""
    pass

class WorkspaceError(Exception):
    """Base workspace error."""
    pass

class WorkspaceMaterializationError(WorkspaceError):
    """Workspace materialization failed."""
    pass
```

This container orchestration system provides robust container lifecycle management with proper resource allocation, monitoring, and cleanup for the multi-tenant legal workspace environment.
