import json
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Literal, Optional

from fastapi import APIRouter, Body, HTTPException, status
from fastapi.responses import JSONResponse

from openhands.server.dependencies import get_dependencies

app = APIRouter(prefix="/api/cases", dependencies=get_dependencies())


# ---- Helpers ----

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slugify(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9-_]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or uuid.uuid4().hex[:8]


def _cases_base_path() -> str:
    # Prefer explicit env; fallback to persisted OpenHands volume
    base = os.environ.get("CASES_BASE_PATH") or "/.openhands/cases"
    os.makedirs(base, exist_ok=True)
    return base


def _case_dir(case_id: str) -> str:
    return os.path.join(_cases_base_path(), case_id)


# ---- Models ----

StorageLocal = dict


class Case(dict):  # simple dict-based model to avoid pydantic import bloat
    pass


# ---- IO ----

CASE_JSON = "case.json"


def _read_case_json(path: str) -> Optional[dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except Exception:
        return None


def _write_case_json(path: str, data: dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _fs_case_to_model(case_id: str) -> Optional[Case]:
    cdir = _case_dir(case_id)
    if not os.path.isdir(cdir):
        return None

    meta = _read_case_json(os.path.join(cdir, CASE_JSON)) or {}

    # Defaults if metadata missing
    name = meta.get("name") or case_id
    description = meta.get("description") or ""

    # Timestamps
    try:
        stat = os.stat(cdir)
        created_at = meta.get("created_at") or _now_iso()
        updated_at = meta.get("updated_at") or datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
    except Exception:
        created_at = meta.get("created_at") or _now_iso()
        updated_at = meta.get("updated_at") or _now_iso()

    storage: StorageLocal = {"type": "local", "path": cdir}

    return Case(
        id=case_id,
        name=name,
        description=description,
        storage=storage,
        created_at=created_at,
        updated_at=updated_at,
    )


# ---- Routes ----

@app.get("")
async def list_cases(q: Optional[str] = None) -> dict:
    base = _cases_base_path()
    items: list[Case] = []
    for entry in sorted(os.listdir(base)):
        if not entry or entry.startswith("."):
            continue
        c = _fs_case_to_model(entry)
        if not c:
            continue
        if q and q.lower() not in (c.get("name", "").lower() + " " + c.get("description", "").lower()):
            continue
        items.append(c)
    return {"items": items, "total": len(items)}


@app.post("")
async def create_case(payload: dict = Body(...)) -> JSONResponse:
    name = (payload.get("name") or "").strip()
    description = (payload.get("description") or "").strip()
    storage = payload.get("storage") or {"type": "local"}

    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="name is required")

    # Only local supported in MVP
    if storage.get("type") != "local":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only local storage is supported at this time")

    # Create directory
    case_id = f"{_slugify(name)}-{uuid.uuid4().hex[:8]}"
    cdir = _case_dir(case_id)
    os.makedirs(cdir, exist_ok=True)

    created_at = _now_iso()
    model = Case(
        id=case_id,
        name=name,
        description=description,
        storage={"type": "local", "path": cdir},
        created_at=created_at,
        updated_at=created_at,
    )

    # Persist metadata
    _write_case_json(os.path.join(cdir, CASE_JSON), model)

    return JSONResponse(status_code=status.HTTP_201_CREATED, content=model)

