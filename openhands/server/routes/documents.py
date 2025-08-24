import asyncio
import os
import shutil
from pathlib import Path
from typing import List, Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel

from openhands.server.legal_case_workspace import LegalCaseWorkspace
from openhands.server.utils import get_conversation_metadata
from openhands.storage.data_models.conversation_metadata import ConversationMetadata

router = APIRouter(prefix="/api")

# In-memory cache for file structures
file_structure_cache = {}
CACHE_EXPIRATION = 300  # 5 minutes


class FileNode(BaseModel):
    name: str
    path: str
    type: Literal['file', 'directory']
    size: int | None = None
    # Epoch seconds for frontend display
    modified: int | None = None
    # Backward compatibility
    last_modified: str | None = None
    # Optional file extension
    extension: str | None = None
    children: List['FileNode'] | None = None


class FileListResponse(BaseModel):
    items: List[FileNode]
    path: str
    total: int


class UploadResult(BaseModel):
    filename: str
    path: str
    size: int
    content_type: str | None


class Document(BaseModel):
    filename: str
    path: str
    size: int
    last_modified: str


def is_safe_path(base_path: Path, relative_path: str) -> bool:
    """Check if the relative path is safe and within the base path."""
    try:
        full_path = (base_path / relative_path).resolve()
        return full_path.is_relative_to(base_path.resolve())
    except (ValueError, OSError):
        return False


async def get_case_workspace(conversation_id: str,
                             metadata: ConversationMetadata = Depends(get_conversation_metadata)) -> LegalCaseWorkspace:
    """Dependency to get the legal case workspace for the given conversation."""
    case_id = metadata.case_id
    if not case_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="No case associated with this conversation.")

    # Use the legal workspace manager to get the workspace path
    from openhands.server.legal_workspace_manager import get_legal_workspace_manager
    workspace_manager = get_legal_workspace_manager()

    if not workspace_manager or not workspace_manager.case_store:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Legal workspace manager not available.")

    # Get the cases directory (parent of case directories)
    # LegalCaseWorkspace expects the base_dir to be the parent that contains case-{id} directories
    cases_dir = str(workspace_manager.case_store.cases_dir)

    return LegalCaseWorkspace(case_id, cases_dir)


async def get_validated_path(workspace: LegalCaseWorkspace = Depends(get_case_workspace),
                           relative_path: str | None = None) -> Path:
    """Dependency to get a validated, safe path within the case workspace."""
    if not relative_path:
        return workspace.get_workspace_path()

    if not is_safe_path(workspace.get_workspace_path(), relative_path):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid or unsafe path provided.")

    return workspace.get_workspace_path(relative_path)


@router.get("/conversations/{conversation_id}/files/browse",
            response_model=FileListResponse,
            tags=["documents"],
            summary="Browse files and directories in the case workspace.")
async def browse_files(conversation_id: str, path: str | None = Query(None), workspace: LegalCaseWorkspace = Depends(get_case_workspace)):
    """Browses a specific directory, returning a list of its contents."""
    validated_path = await get_validated_path(workspace, path)
    if not validated_path.is_dir():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Path is not a directory.")

    items: List[FileNode] = []
    for item in sorted(validated_path.iterdir(), key=lambda x: (x.is_file(), x.name)):
        stat = item.stat()
        is_dir = item.is_dir()
        rel_path = str(item.relative_to(workspace.get_workspace_path()))
        node = FileNode(
            name=item.name,
            path=rel_path,
            type='directory' if is_dir else 'file',
            size=None if is_dir else stat.st_size,
            modified=int(stat.st_mtime),
            last_modified=str(stat.st_mtime),
            extension=None if is_dir else (item.suffix[1:] if item.suffix else None),
        )
        items.append(node)

    return FileListResponse(items=items, path=path or "", total=len(items))


@router.post("/conversations/{conversation_id}/documents/upload",
             response_model=List[UploadResult],
             tags=["documents"],
             summary="Upload one or more documents to the case intake folder.")
async def upload_document(conversation_id: str, files: List[UploadFile] = File(...),
                          workspace: LegalCaseWorkspace = Depends(get_case_workspace)):
    """Uploads files to the `intake` directory of the case workspace."""
    upload_dir = workspace.get_intake_path()
    if not upload_dir.exists():
        upload_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for file in files:
        if not file.filename:
            continue

        file_path = upload_dir / file.filename

        # Write file content
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        results.append(UploadResult(
            filename=file.filename,
            path=str(file_path.relative_to(workspace.get_workspace_path())),
            size=len(content),
            content_type=file.content_type
        ))

    return results

@router.delete("/conversations/{conversation_id}/files", tags=["documents"], summary="Delete a file within the case workspace")
async def delete_file(conversation_id: str, path: str = Query(..., description="Relative path to file"), workspace: LegalCaseWorkspace = Depends(get_case_workspace)):
    # Validate and resolve path
    if not path:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Path is required")
    full_path = await get_validated_path(workspace, path)

    # Ensure it's a file and within workspace
    if not full_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    if full_path.is_dir():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Refusing to delete a directory")

    try:
        full_path.unlink()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete file: {e}")

    return {"status": "ok"}


@router.get("/conversations/{conversation_id}/documents",
            response_model=List[Document],
            tags=["documents"],
            summary="List all documents in the case workspace.")
async def list_documents(conversation_id: str, workspace: LegalCaseWorkspace = Depends(get_case_workspace)):
    """Provides a flat list of all files in the case workspace."""
    all_files = []
    for dirpath, _, filenames in os.walk(workspace.get_workspace_path()):
        for filename in filenames:
            filepath = Path(dirpath) / filename
            all_files.append(
                Document(filename=filename, path=str(filepath.relative_to(workspace.get_workspace_path())),
                         size=filepath.stat().st_size, last_modified=str(filepath.stat().st_mtime)))
    return all_files
