import hashlib
import hmac
import os
import re
import time
import uuid
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.core.config import settings
from app.core.security import require_clearance

router = APIRouter()

_SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")
_MAX_FILENAME_LEN = 128
_UPLOAD_ID_RE = re.compile(r"^[A-Fa-f0-9-]{36}$")


def _safe_filename(name: str) -> str:
    base = os.path.basename((name or "").replace("\\", "/"))
    base = base.replace("\x00", "").lstrip(".")
    base = _SAFE_FILENAME_RE.sub("_", base)
    if not base or base in {".", ".."}:
        base = "upload.bin"
    return base[:_MAX_FILENAME_LEN]


def _sign(upload_id: str, filename: str, expires: int) -> str:
    message = f"{upload_id}\n{filename}\n{expires}".encode()
    return hmac.new(settings.SECRET_KEY.encode(), message, hashlib.sha256).hexdigest()


@router.post("/upload")
async def request_upload_url(
    filename: str,
    content_type: str,
    principal: dict = Depends(require_clearance("RESTRICTED")),
):
    safe_name = _safe_filename(filename)
    upload_id = str(uuid.uuid4())
    expires = int(time.time()) + settings.MEDIA_UPLOAD_URL_TTL
    signature = _sign(upload_id, safe_name, expires)

    presigned_path = (
        f"upload/{upload_id}/{quote(safe_name)}"
        f"?expires={expires}&signature={signature}"
    )

    return {
        "upload_id": upload_id,
        "filename": safe_name,
        "presigned_url": presigned_path,
        "method": "PUT",
        "signing": "hmac_sha256_local",
        "expires_in": settings.MEDIA_UPLOAD_URL_TTL,
    }


@router.put("/upload/{upload_id}/{filename}")
async def upload_media(
    upload_id: str,
    filename: str,
    expires: int,
    signature: str,
    file: UploadFile,
):
    if not _UPLOAD_ID_RE.match(upload_id):
        raise HTTPException(status_code=400, detail="upload_id invalido")

    safe_name = _safe_filename(filename)
    if safe_name != filename:
        raise HTTPException(status_code=400, detail="filename invalido")

    if int(time.time()) > expires:
        raise HTTPException(status_code=403, detail="URL presignada expirada")

    expected = _sign(upload_id, safe_name, expires)
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=403, detail="Firma invalida")

    content = await file.read()
    if len(content) > settings.max_file_size_bytes:
        raise HTTPException(status_code=413, detail="File too large")

    storage_root = os.path.realpath(settings.MEDIA_STORAGE_PATH)
    upload_dir = os.path.realpath(os.path.join(storage_root, upload_id))
    if os.path.commonpath([storage_root, upload_dir]) != storage_root:
        raise HTTPException(status_code=400, detail="Invalid path")
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.realpath(os.path.join(upload_dir, safe_name))
    if os.path.commonpath([upload_dir, file_path]) != upload_dir:
        raise HTTPException(status_code=400, detail="Invalid path")

    with open(file_path, "wb") as fp:
        fp.write(content)

    return {
        "upload_id": upload_id,
        "filename": safe_name,
        "size_bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
        "stored": True,
    }
