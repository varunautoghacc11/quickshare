import uuid
import os
import shutil
import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models import ShareTextRequest, ShareResponse
from app.storage import store_share
from app.utils import generate_secure_code, sanitize_filename, validate_extension
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

MAX_FILE_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024


@router.post("/text", response_model=ShareResponse)
@limiter.limit("20/minute")
async def share_text(request: Request, payload: ShareTextRequest) -> ShareResponse:
    """Accept text and return a 6-digit access code."""
    code = generate_secure_code()
    now = datetime.now(timezone.utc).isoformat()

    data = {
        "type": "text",
        "content": payload.text,
        "filename": None,
        "filepath": None,
        "created_at": now,
    }

    await store_share(code, data, settings.CODE_TTL_SECONDS)
    logger.info(f"Text share created: code={code}")

    return ShareResponse(
        code=code,
        expires_in=settings.CODE_TTL_SECONDS,
        type="text",
    )


@router.post("/file", response_model=ShareResponse)
@limiter.limit("10/minute")
async def share_file(request: Request, file: UploadFile = File(...)) -> ShareResponse:
    """Accept a file upload and return a 6-digit access code."""
    original_filename = file.filename or "upload"

    # Validate extension
    if not validate_extension(original_filename, settings.ALLOWED_EXTENSIONS):
        ext = Path(original_filename).suffix
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' is not allowed. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}",
        )

    # Sanitize filename
    safe_filename = sanitize_filename(original_filename)

    # Read file in chunks to enforce size limit
    ext = Path(safe_filename).suffix
    uuid_filename = f"{uuid.uuid4()}{ext}"
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    filepath = upload_dir / uuid_filename

    bytes_read = 0
    try:
        with open(filepath, "wb") as out:
            while chunk := await file.read(65536):  # 64KB chunks
                bytes_read += len(chunk)
                if bytes_read > MAX_FILE_BYTES:
                    out.close()
                    filepath.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File exceeds maximum size of {settings.MAX_FILE_SIZE_MB}MB",
                    )
                out.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        filepath.unlink(missing_ok=True)
        logger.error(f"File write error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")

    code = generate_secure_code()
    now = datetime.now(timezone.utc).isoformat()

    data = {
        "type": "file",
        "content": None,
        "filename": safe_filename,
        "filepath": str(filepath),
        "created_at": now,
        "size_bytes": bytes_read,
    }

    await store_share(code, data, settings.CODE_TTL_SECONDS)
    logger.info(f"File share created: code={code}, file={safe_filename}, size={bytes_read}B")

    return ShareResponse(
        code=code,
        expires_in=settings.CODE_TTL_SECONDS,
        type="file",
    )
