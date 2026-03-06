import secrets
import re
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

ALLOWED_CODE_RE = re.compile(r"^\d{6}$")
SAFE_FILENAME_RE = re.compile(r"[^\w\.\-]")


def generate_secure_code() -> str:
    """Generate a cryptographically secure 6-digit code (000000-999999)."""
    return str(secrets.randbelow(1_000_000)).zfill(6)


def sanitize_filename(filename: str) -> str:
    """
    Strip path components, restrict to safe characters, limit length.
    Prevents directory traversal and shell injection.
    """
    if not filename:
        return "upload"

    # Strip path separators — prevent directory traversal
    filename = os.path.basename(filename)
    filename = filename.replace("..", "").replace("/", "").replace("\\", "")

    # Keep only alphanumeric, dots, dashes, underscores
    name, _, ext = filename.rpartition(".")
    if not name:
        name = "file"
        ext = filename

    name = SAFE_FILENAME_RE.sub("_", name)
    ext = SAFE_FILENAME_RE.sub("", ext)

    # Limit length
    if len(name) > 100:
        name = name[:100]
    if len(ext) > 10:
        ext = ext[:10]

    sanitized = f"{name}.{ext}" if ext else name
    return sanitized[:255]


def validate_extension(filename: str, allowed: list[str]) -> bool:
    """Return True if file extension is in allowed list."""
    ext = Path(filename).suffix.lstrip(".").lower()
    return ext in [e.lower() for e in allowed]


def get_redis_key(code: str) -> str:
    """
    Build Redis key with prefix. Validates code format first
    to prevent Redis key injection.
    """
    validate_code_format(code)
    return f"share:{code}"


def validate_code_format(code: str) -> None:
    """Raise ValueError if code is not exactly 6 digits."""
    if not ALLOWED_CODE_RE.match(str(code)):
        raise ValueError(f"Invalid code format: must be exactly 6 digits, got '{code}'")
