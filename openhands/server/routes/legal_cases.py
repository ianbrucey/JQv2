"""
Legal Case Management API Routes
"""
import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel

from openhands.server.dependencies import get_dependencies
from openhands.server.legal_workspace_manager import get_legal_workspace_manager, initialize_legal_workspace_manager
from openhands.server.shared import config, ConversationStoreImpl
from openhands.runtime import get_runtime_cls
from openhands.storage.legal_case_store import FileLegalCaseStore
from openhands.storage.data_models.legal_case import CaseStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/legal", tags=["legal_cases"], dependencies=get_dependencies())
from fastapi import UploadFile, File, Form, status
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import re
import hashlib
import uuid as uuidlib
import json as jsonlib
from pathlib import Path
from datetime import datetime, timezone



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
    request: Request,
    case_store: FileLegalCaseStore = Depends(get_case_store)
) -> Dict[str, str]:
    """Delete a legal case and all associated conversations and workspace data."""
    try:
        if not await case_store.case_exists(case_id):
            raise HTTPException(status_code=404, detail="Case not found")

        # 1) Delete any conversations linked to this case via metadata.case_id
        try:
            from openhands.server.utils import get_conversation_store
            conversation_store = await get_conversation_store(request)
            # Paginate through all conversations to find matches
            page_id = None
            to_delete: list[str] = []
            while True:
                result_set = await conversation_store.search(page_id=page_id, limit=100)
                for meta in result_set.results:
                    if getattr(meta, 'case_id', None) == case_id:
                        to_delete.append(meta.conversation_id)
                if not result_set.next_page_id:
                    break
                page_id = result_set.next_page_id

            # Delete each conversation safely via runtime cleanup + metadata removal
            runtime_cls = get_runtime_cls(config.runtime)
            for convo_id in to_delete:
                try:
                    is_running = False
                    from openhands.server.shared import conversation_manager
                    is_running = await conversation_manager.is_agent_loop_running(convo_id)
                    if is_running:
                        await conversation_manager.close_session(convo_id)
                    await runtime_cls.delete(convo_id)
                    await conversation_store.delete_metadata(convo_id)
                except Exception as de:
                    logger.warning(f"Failed to delete conversation {convo_id} for case {case_id}: {de}")
        except Exception as e:
            logger.warning(f"Conversation cleanup error for case {case_id}: {e}")

        # 2) If this request's session is currently in this case, exit it to avoid stale state
        try:
            session_id = request.headers.get('X-Session-ID')
            if session_id:
                manager = get_legal_workspace_manager(session_id)
                if manager and manager.get_current_case_id() == case_id:
                    await manager.exit_case_workspace()
        except Exception as e:
            logger.debug(f"Workspace exit after deletion failed (session scoped): {e}")

        # 3) Delete the case workspace directory and metadata
        await case_store.delete_case(case_id)

        logger.info(f"Deleted legal case: {case_id}")

        return {"message": "Case deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete case {case_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete case: {str(e)}")


@router.post("/cases/{case_id}/enter")
async def enter_case(case_id: str) -> Dict[str, Any]:
    """Enter a legal case workspace."""
    try:
        # Get the singleton workspace manager
        workspace_manager = get_legal_workspace_manager()
        if not workspace_manager:
            workspace_manager = initialize_legal_workspace_manager(config)

        # Enter the case workspace
        result = await workspace_manager.enter_case_workspace(case_id)

        logger.info(f"Entered legal case workspace: {case_id}")

        result['workspace_transition'] = True
        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to enter case {case_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to enter case: {str(e)}")


@router.post("/workspace/exit")
async def exit_case_workspace() -> Dict[str, Any]:
    """Exit the current case workspace."""
    try:
        # Get the singleton workspace manager
        workspace_manager = get_legal_workspace_manager()
        if not workspace_manager:
            raise HTTPException(status_code=500, detail="Workspace manager not initialized")

        result = await workspace_manager.exit_case_workspace()

        logger.info("Exited case workspace")

        result['workspace_transition'] = True
        return result

    except Exception as e:
        logger.error(f"Failed to exit case workspace: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to exit workspace: {str(e)}")


@router.get("/workspace/current")
async def get_current_workspace() -> Dict[str, Any]:
    """Get current workspace information."""
    try:
        # Get the singleton workspace manager
        workspace_manager = get_legal_workspace_manager()
        if not workspace_manager:
            return {
                "is_in_case_workspace": False,
                "message": "Workspace manager not initialized"
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


# --------------------------
# Document Uploads & Listing
# --------------------------

ALLOWED_EXTENSIONS = {
    '.pdf', '.png', '.jpg', '.jpeg', '.tif', '.tiff', '.docx', '.txt', '.md'
}
ALLOWED_MIME_PREFIXES = (
    'application/pdf',
    'image/png', 'image/jpeg', 'image/tiff',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain', 'text/markdown'
)

FOLDER_MAP = {
    'inbox': ['Intake', 'inbox'],
    'exhibits': ['exhibits'],
    'research': ['research'],
    'active_drafts': ['active_drafts']
}


def _sanitize_filename(name: str) -> str:
    # Remove path separators and control characters
    name = name.replace('\\', '_').replace('/', '_')
    name = re.sub(r'[^A-Za-z0-9._\- ]+', '', name)
    name = name.strip()
    if not name:
        name = f'file-{uuidlib.uuid4().hex[:8]}'
    # Limit length
    if len(name) > 120:
        base, ext = os.path.splitext(name)
        name = base[:100] + '_' + uuidlib.uuid4().hex[:8] + ext
    return name


def _unique_path(dir_path: Path, filename: str) -> Path:
    base, ext = os.path.splitext(filename)
    candidate = dir_path / filename
    idx = 1
    while candidate.exists():
        candidate = dir_path / f"{base}-{idx}{ext}"
        idx += 1
    return candidate


def _compute_checksum_and_write(upload: UploadFile, dest_path: Path) -> tuple[str, int]:
    sha256 = hashlib.sha256()
    total = 0
    tmp_path = dest_path.with_suffix(dest_path.suffix + '.part')
    with open(tmp_path, 'wb') as out:
        while True:
            chunk = upload.file.read(1024 * 1024)
            if not chunk:
                break
            sha256.update(chunk)
            out.write(chunk)
            total += len(chunk)
    tmp_path.rename(dest_path)
    return sha256.hexdigest(), total


def _load_manifest(case_root: Path) -> dict:
    manifest_path = case_root / 'documents_manifest.json'
    if manifest_path.exists():
        try:
            return jsonlib.loads(manifest_path.read_text())
        except Exception:
            return {'documents': []}
    return {'documents': []}


def _save_manifest(case_root: Path, manifest: dict) -> None:
    manifest_path = case_root / 'documents_manifest.json'
    manifest_path.write_text(jsonlib.dumps(manifest, indent=2))


def _find_duplicate(manifest: dict, checksum: str) -> Optional[dict]:
    for doc in manifest.get('documents', []):
        if doc.get('checksum_sha256') == checksum:
            return doc
    return None


@router.post("/cases/{case_id}/documents")
async def upload_case_documents(
    case_id: str,
    files: List[UploadFile] = File(...),
    target_folder: str = Form('inbox'),
    tags: Optional[str] = Form(None),
    note: Optional[str] = Form(None),
):
    try:
        # Get the singleton workspace manager
        workspace_manager = get_legal_workspace_manager()
        if not workspace_manager:
            workspace_manager = initialize_legal_workspace_manager(config)

        if not workspace_manager.case_store:
            await workspace_manager.initialize()

        # Simple case existence check
        case = await workspace_manager.case_store.get_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        # Resolve paths
        case_store = workspace_manager.case_store
        case_workspace = Path(case_store.get_case_workspace_path(case_id))  # draft_system
        case_root = Path(case_store.get_case_root_path(case_id))

        # Determine destination dir
        if target_folder not in FOLDER_MAP:
            raise HTTPException(status_code=400, detail="Invalid target_folder")
        dest_dir = case_workspace.joinpath(*FOLDER_MAP[target_folder])
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Load manifest
        manifest = _load_manifest(case_root)

        uploaded, skipped, errors = [], [], []
        tag_list = []
        if tags:
            try:
                # try JSON first
                tag_list = jsonlib.loads(tags) if tags.strip().startswith('[') else [t.strip() for t in tags.split(',') if t.strip()]
            except Exception:
                tag_list = [t.strip() for t in tags.split(',') if t.strip()]

        # Validation limits
        MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB per file
        ALLOWED = ALLOWED_EXTENSIONS

        for up in files:
            try:
                # Quick type/extension checks
                orig_name = up.filename or 'unnamed'
                ext = os.path.splitext(orig_name)[1].lower()
                if ext not in ALLOWED:
                    raise HTTPException(status_code=400, detail=f"File type not allowed: {orig_name}")
                if up.content_type and not any(up.content_type.startswith(p) for p in ALLOWED_MIME_PREFIXES):
                    # Be permissive if content_type missing/misreported; only block obvious mismatches
                    pass

                safe_name = _sanitize_filename(orig_name)
                dest_path = _unique_path(dest_dir, safe_name)

                # Compute checksum while writing; also enforce size limit during stream
                sha256 = hashlib.sha256()
                total = 0
                tmp_path = dest_path.with_suffix(dest_path.suffix + '.part')
                with open(tmp_path, 'wb') as out:
                    while True:
                        chunk = up.file.read(1024 * 1024)
                        if not chunk:
                            break
                        total += len(chunk)
                        if total > MAX_FILE_SIZE:
                            raise HTTPException(status_code=413, detail=f"File too large: {orig_name}")
                        sha256.update(chunk)
                        out.write(chunk)
                checksum = sha256.hexdigest()

                # Duplicate detection
                dup = _find_duplicate(manifest, checksum)
                if dup is not None:
                    # Remove temp and skip
                    tmp_path.unlink(missing_ok=True)
                    skipped.append({
                        'original_name': orig_name,
                        'reason': 'duplicate',
                        'duplicate_of': dup.get('id'),
                    })
                    continue

                # Finalize write
                tmp_path.rename(dest_path)

                doc_id = uuidlib.uuid4().hex
                rel_path = str(dest_path.relative_to(case_workspace))
                now = datetime.now(timezone.utc).isoformat()
                meta = {
                    'id': doc_id,
                    'case_id': case_id,
                    'original_name': orig_name,
                    'stored_name': dest_path.name,
                    'rel_path': rel_path,
                    'size': total,
                    'mime': up.content_type or None,
                    'checksum_sha256': checksum,
                    'target_folder': target_folder,
                    'tags': tag_list,
                    'note': note,
                    'uploaded_at': now,
                    'source': 'ui',
                }
                manifest.setdefault('documents', []).append(meta)
                uploaded.append(meta)

            except HTTPException as he:
                errors.append({'file': up.filename, 'error': he.detail, 'status': he.status_code})
            except Exception as e:
                errors.append({'file': getattr(up, 'filename', 'unnamed'), 'error': str(e)})

        # Persist manifest
        _save_manifest(case_root, manifest)

        return JSONResponse(status_code=status.HTTP_201_CREATED, content={
            'uploaded': uploaded,
            'skipped': skipped,
            'errors': errors
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload documents for case {case_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload documents: {str(e)}")


@router.get("/cases/{case_id}/documents")
async def list_case_documents(
    case_id: str,
    folder: Optional[str] = None,
):
    try:
        # Get the singleton workspace manager
        workspace_manager = get_legal_workspace_manager()
        if not workspace_manager:
            workspace_manager = initialize_legal_workspace_manager(config)

        if not workspace_manager.case_store:
            await workspace_manager.initialize()

        # Simple case existence check
        case = await workspace_manager.case_store.get_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        case_store = workspace_manager.case_store
        case_root = Path(case_store.get_case_root_path(case_id))
        manifest = _load_manifest(case_root)
        docs = manifest.get('documents', [])

        if folder:
            if folder not in FOLDER_MAP:
                raise HTTPException(status_code=400, detail="Invalid folder filter")
            docs = [d for d in docs if d.get('target_folder') == folder]

        return {'items': docs, 'total': len(docs)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list documents for case {case_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@router.get("/cases/{case_id}/files")
async def list_case_files(
    case_id: str,
    path: Optional[str] = None,
):
    """List files and directories in the case workspace."""
    try:
        # Get the singleton workspace manager
        workspace_manager = get_legal_workspace_manager()
        if not workspace_manager:
            workspace_manager = initialize_legal_workspace_manager(config)

        if not workspace_manager.case_store:
            await workspace_manager.initialize()

        # Simple case existence check
        case = await workspace_manager.case_store.get_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        case_store = workspace_manager.case_store
        case_root = Path(case_store.get_case_root_path(case_id))

        # Determine the target path
        if path:
            # Sanitize path to prevent directory traversal
            clean_path = path.strip('/').replace('..', '')
            target_path = case_root / clean_path
        else:
            target_path = case_root

        # Ensure the target path is within the case root
        try:
            target_path = target_path.resolve()
            case_root = case_root.resolve()
            if not str(target_path).startswith(str(case_root)):
                raise HTTPException(status_code=403, detail="Access denied")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid path")

        if not target_path.exists():
            return {'items': [], 'path': path or '', 'total': 0}

        items = []
        if target_path.is_dir():
            try:
                for item in sorted(target_path.iterdir()):
                    # Skip hidden files and system files
                    if item.name.startswith('.'):
                        continue

                    relative_path = item.relative_to(case_root)
                    item_info = {
                        'name': item.name,
                        'path': str(relative_path),
                        'type': 'directory' if item.is_dir() else 'file',
                        'size': item.stat().st_size if item.is_file() else None,
                        'modified': item.stat().st_mtime,
                    }

                    # Add file extension for files
                    if item.is_file():
                        item_info['extension'] = item.suffix.lower()

                    items.append(item_info)
            except PermissionError:
                raise HTTPException(status_code=403, detail="Permission denied")
        else:
            # Single file info
            relative_path = target_path.relative_to(case_root)
            items.append({
                'name': target_path.name,
                'path': str(relative_path),
                'type': 'file',
                'size': target_path.stat().st_size,
                'modified': target_path.stat().st_mtime,
                'extension': target_path.suffix.lower(),
            })

        return {
            'items': items,
            'path': path or '',
            'total': len(items)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list files for case {case_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")
