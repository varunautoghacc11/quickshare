import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models import RetrieveResponse
from app.storage import retrieve_share, get_ttl
from app.utils import validate_code_format
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/{code}", response_model=RetrieveResponse)
@limiter.limit("10/minute")
async def retrieve(request: Request, code: str) -> RetrieveResponse:
    """Retrieve share metadata by 6-digit code."""
    try:
        validate_code_format(code)
    except ValueError:
        raise HTTPException(status_code=422, detail="Code must be exactly 6 digits")

    data = await retrieve_share(code)
    if data is None:
        raise HTTPException(
            status_code=404,
            detail="Code not found or has expired. Shares are deleted after 10 minutes.",
        )

    remaining = await get_ttl(code)
    if remaining <= 0:
        raise HTTPException(status_code=404, detail="Share has expired.")

    response = RetrieveResponse(
        type=data["type"],
        content=data.get("content"),
        filename=data.get("filename"),
        expires_in=remaining,
        created_at=data.get("created_at"),
    )

    if data["type"] == "file":
        response.download_url = f"/api/receive/{code}/download"

    return response


@router.get("/{code}/download")
@limiter.limit("10/minute")
async def download_file(request: Request, code: str):
    """Stream the file associated with a share code."""
    try:
        validate_code_format(code)
    except ValueError:
        raise HTTPException(status_code=422, detail="Code must be exactly 6 digits")

    data = await retrieve_share(code)
    if data is None:
        raise HTTPException(status_code=404, detail="Code not found or has expired.")

    if data["type"] != "file":
        raise HTTPException(status_code=404, detail="This code points to a text share, not a file.")

    filepath = Path(data["filepath"])
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="File no longer exists on server.")

    # Security: ensure file is within upload dir (prevent path traversal)
    try:
        resolved = filepath.resolve()
        upload_dir_resolved = Path(settings.UPLOAD_DIR).resolve()
        resolved.relative_to(upload_dir_resolved)
    except ValueError:
        logger.warning(f"Path traversal attempt detected for code {code}: {filepath}")
        raise HTTPException(status_code=403, detail="Access denied.")

    filename = data.get("filename", "download")
    return FileResponse(
        path=str(filepath),
        filename=filename,
        media_type="application/octet-stream",
    )
