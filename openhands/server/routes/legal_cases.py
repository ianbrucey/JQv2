"""
Legal Case Management API Routes
"""
import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel

from openhands.server.dependencies import get_dependencies
from openhands.server.legal_workspace_manager import get_legal_workspace_manager
from openhands.server.shared import config
from openhands.storage.legal_case_store import FileLegalCaseStore
from openhands.storage.data_models.legal_case import CaseStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/legal", tags=["legal_cases"], dependencies=get_dependencies())


class CreateCaseRequest(BaseModel):
    title: str
    case_number: str | None = None
    description: str | None = None


class UpdateCaseRequest(BaseModel):
    title: str | None = None
    case_number: str | None = None
    description: str | None = None
    status: str | None = None


class CaseResponse(BaseModel):
    case_id: str
    title: str
    case_number: str | None
    description: str | None
    status: str
    created_at: str
    updated_at: str
    last_accessed_at: str | None
    workspace_path: str | None
    draft_system_initialized: bool
    conversation_id: str | None


async def get_case_store() -> FileLegalCaseStore:
    """Dependency to get legal case store."""
    # TODO: Add user authentication and pass user_id
    return await FileLegalCaseStore.get_instance(config, user_id=None)


@router.post("/cases", response_model=CaseResponse)
async def create_case(
    request: CreateCaseRequest,
    case_store: FileLegalCaseStore = Depends(get_case_store)
) -> CaseResponse:
    """Create a new legal case."""
    try:
        case = await case_store.create_case(
            title=request.title,
            case_number=request.case_number,
            description=request.description
        )
        
        logger.info(f"Created legal case: {case.case_id} - {case.title}")
        
        return CaseResponse(
            case_id=case.case_id,
            title=case.title,
            case_number=case.case_number,
            description=case.description,
            status=case.status.value,
            created_at=case.created_at.isoformat(),
            updated_at=case.updated_at.isoformat(),
            last_accessed_at=case.last_accessed_at.isoformat() if case.last_accessed_at else None,
            workspace_path=case.workspace_path,
            draft_system_initialized=case.draft_system_initialized,
            conversation_id=case.conversation_id
        )
        
    except Exception as e:
        logger.error(f"Failed to create case: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create case: {str(e)}")


@router.get("/cases", response_model=list[CaseResponse])
async def list_cases(
    case_store: FileLegalCaseStore = Depends(get_case_store)
) -> list[CaseResponse]:
    """List all legal cases for the current user."""
    try:
        cases = await case_store.list_cases()
        
        return [
            CaseResponse(
                case_id=case.case_id,
                title=case.title,
                case_number=case.case_number,
                description=case.description,
                status=case.status.value,
                created_at=case.created_at.isoformat(),
                updated_at=case.updated_at.isoformat(),
                last_accessed_at=case.last_accessed_at.isoformat() if case.last_accessed_at else None,
                workspace_path=case.workspace_path,
                draft_system_initialized=case.draft_system_initialized,
                conversation_id=case.conversation_id
            )
            for case in cases
        ]
        
    except Exception as e:
        logger.error(f"Failed to list cases: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list cases: {str(e)}")


@router.get("/cases/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: str,
    case_store: FileLegalCaseStore = Depends(get_case_store)
) -> CaseResponse:
    """Get a specific legal case."""
    try:
        case = await case_store.get_case(case_id)
        
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        
        return CaseResponse(
            case_id=case.case_id,
            title=case.title,
            case_number=case.case_number,
            description=case.description,
            status=case.status.value,
            created_at=case.created_at.isoformat(),
            updated_at=case.updated_at.isoformat(),
            last_accessed_at=case.last_accessed_at.isoformat() if case.last_accessed_at else None,
            workspace_path=case.workspace_path,
            draft_system_initialized=case.draft_system_initialized,
            conversation_id=case.conversation_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get case {case_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get case: {str(e)}")


@router.put("/cases/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: str,
    request: UpdateCaseRequest,
    case_store: FileLegalCaseStore = Depends(get_case_store)
) -> CaseResponse:
    """Update a legal case."""
    try:
        case = await case_store.get_case(case_id)
        
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        
        # Update fields if provided
        if request.title is not None:
            case.title = request.title
        if request.case_number is not None:
            case.case_number = request.case_number
        if request.description is not None:
            case.description = request.description
        if request.status is not None:
            case.status = CaseStatus(request.status)
        
        await case_store.update_case(case)
        
        logger.info(f"Updated legal case: {case.case_id}")
        
        return CaseResponse(
            case_id=case.case_id,
            title=case.title,
            case_number=case.case_number,
            description=case.description,
            status=case.status.value,
            created_at=case.created_at.isoformat(),
            updated_at=case.updated_at.isoformat(),
            last_accessed_at=case.last_accessed_at.isoformat() if case.last_accessed_at else None,
            workspace_path=case.workspace_path,
            draft_system_initialized=case.draft_system_initialized,
            conversation_id=case.conversation_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update case {case_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update case: {str(e)}")


@router.delete("/cases/{case_id}")
async def delete_case(
    case_id: str,
    case_store: FileLegalCaseStore = Depends(get_case_store)
) -> Dict[str, str]:
    """Delete a legal case."""
    try:
        if not await case_store.case_exists(case_id):
            raise HTTPException(status_code=404, detail="Case not found")
        
        await case_store.delete_case(case_id)
        
        logger.info(f"Deleted legal case: {case_id}")
        
        return {"message": "Case deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete case {case_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete case: {str(e)}")


@router.post("/cases/{case_id}/enter")
async def enter_case(
    case_id: str,
    request: Request
) -> Dict[str, Any]:
    """Enter a legal case workspace with proper session isolation."""
    try:
        # Extract session ID from request headers or generate one
        session_id = request.headers.get('X-Session-ID', 'default')

        # Get the session-specific workspace manager
        workspace_manager = get_legal_workspace_manager(session_id)
        if not workspace_manager:
            raise HTTPException(status_code=500, detail="Workspace manager not initialized for this session")

        # Initialize workspace manager if needed
        if not workspace_manager.case_store:
            await workspace_manager.initialize()

        # Enter the case workspace
        result = await workspace_manager.enter_case_workspace(case_id)

        logger.info(f"Entered legal case workspace: {case_id} for session: {session_id}")

        # Add session information to the result
        result['session_id'] = session_id
        result['workspace_transition'] = True

        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to enter case {case_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to enter case: {str(e)}")


@router.post("/workspace/exit")
async def exit_case_workspace(request: Request) -> Dict[str, Any]:
    """Exit the current case workspace with proper session isolation."""
    try:
        # Extract session ID from request headers
        session_id = request.headers.get('X-Session-ID', 'default')

        # Get the session-specific workspace manager
        workspace_manager = get_legal_workspace_manager(session_id)
        if not workspace_manager:
            raise HTTPException(status_code=500, detail="Workspace manager not initialized for this session")

        result = await workspace_manager.exit_case_workspace()

        logger.info(f"Exited case workspace for session: {session_id}")

        # Add session information to the result
        result['session_id'] = session_id
        result['workspace_transition'] = True

        return result

    except Exception as e:
        logger.error(f"Failed to exit case workspace: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to exit workspace: {str(e)}")


@router.get("/workspace/current")
async def get_current_workspace(request: Request) -> Dict[str, Any]:
    """Get current workspace information with session isolation."""
    try:
        # Extract session ID from request headers
        session_id = request.headers.get('X-Session-ID', 'default')

        # Get the session-specific workspace manager
        workspace_manager = get_legal_workspace_manager(session_id)
        if not workspace_manager:
            return {
                "session_id": session_id,
                "is_in_case_workspace": False,
                "message": f"Workspace manager not initialized for session: {session_id}"
            }

        workspace_info = workspace_manager.get_workspace_info()
        current_case = await workspace_manager.get_current_case()

        if current_case:
            workspace_info.update({
                "current_case": {
                    "case_id": current_case.case_id,
                    "title": current_case.title,
                    "case_number": current_case.case_number,
                    "status": current_case.status.value
                }
            })

        workspace_info['session_id'] = session_id
        return workspace_info

    except Exception as e:
        logger.error(f"Failed to get workspace info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get workspace info: {str(e)}")


@router.get("/workspace/available-cases")
async def get_available_cases() -> Dict[str, Any]:
    """Get list of available cases for workspace switching."""
    try:
        workspace_manager = get_legal_workspace_manager()
        if not workspace_manager:
            raise HTTPException(status_code=500, detail="Workspace manager not initialized")

        if not workspace_manager.case_store:
            await workspace_manager.initialize()

        cases = await workspace_manager.list_available_cases()

        return {
            "available_cases": cases,
            "current_case_id": workspace_manager.get_current_case_id()
        }

    except Exception as e:
        logger.error(f"Failed to get available cases: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get available cases: {str(e)}")


@router.get("/system/status")
async def get_system_status() -> Dict[str, Any]:
    """Get legal document system status."""
    try:
        workspace_manager = get_legal_workspace_manager()

        status = {
            "system_initialized": workspace_manager is not None,
            "workspace_manager_ready": False,
            "database_ready": False,
            "draft_system_available": False,
            "current_case_id": None
        }

        if workspace_manager:
            status["workspace_manager_ready"] = workspace_manager.case_store is not None
            status["current_case_id"] = workspace_manager.get_current_case_id()

            if workspace_manager.case_store:
                # Check if database is working
                try:
                    await workspace_manager.case_store.list_cases()
                    status["database_ready"] = True
                except Exception:
                    status["database_ready"] = False

                # Check if draft system is available
                import os
                from pathlib import Path
                draft_system_path = Path(os.environ.get('DRAFT_SYSTEM_PATH', '/app/draft_system'))
                status["draft_system_available"] = draft_system_path.exists()

        return status

    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        return {
            "system_initialized": False,
            "error": str(e)
        }
