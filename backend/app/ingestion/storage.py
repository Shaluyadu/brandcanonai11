import os
import uuid
from typing import Optional
from pathlib import Path
from app.core.config import settings
from app.core.exceptions import NotFoundError, PermissionDeniedError, ValidationError

STORAGE_BASE_DIR = os.getenv("STORAGE_LOCAL_DIR", os.path.join(os.getcwd(), "private_storage"))


class PrivateStorageService:
    """
    Tenant-isolated private object storage abstraction.
    Stores files using UUID-based opaque keys in tenant-specific subdirectories.
    Never exposes raw filesystem paths to public clients.
    """
    def __init__(self, base_dir: str = STORAGE_BASE_DIR):
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_tenant_dir(self, organisation_id: str) -> Path:
        tenant_dir = (self.base_dir / organisation_id).resolve()
        # Security: Prevent path traversal
        if not str(tenant_dir).startswith(str(self.base_dir)):
            raise PermissionDeniedError("Invalid organization storage path")
        tenant_dir.mkdir(parents=True, exist_ok=True)
        return tenant_dir

    def save_file(self, organisation_id: str, content: bytes, file_ext: str) -> str:
        """
        Save file bytes into tenant private storage. Returns opaque storage_key.
        """
        ext = file_ext if file_ext.startswith(".") else f".{file_ext}"
        storage_key = f"{uuid.uuid4()}{ext}"
        tenant_dir = self._get_tenant_dir(organisation_id)
        file_path = (tenant_dir / storage_key).resolve()

        if not str(file_path).startswith(str(tenant_dir)):
            raise PermissionDeniedError("Storage key path traversal attempt detected")

        with open(file_path, "wb") as f:
            f.write(content)

        return storage_key

    def get_file(self, organisation_id: str, storage_key: str) -> bytes:
        """
        Retrieve file bytes from tenant private storage.
        """
        tenant_dir = self._get_tenant_dir(organisation_id)
        file_path = (tenant_dir / storage_key).resolve()

        if not str(file_path).startswith(str(tenant_dir)):
            raise PermissionDeniedError("Path traversal attempt detected")

        if not file_path.exists() or not file_path.is_file():
            raise NotFoundError(f"Storage object '{storage_key}' not found in workspace storage")

        with open(file_path, "rb") as f:
            return f.read()

    def delete_file(self, organisation_id: str, storage_key: str) -> bool:
        """
        Delete file from tenant private storage.
        """
        tenant_dir = self._get_tenant_dir(organisation_id)
        file_path = (tenant_dir / storage_key).resolve()

        if not str(file_path).startswith(str(tenant_dir)):
            raise PermissionDeniedError("Path traversal attempt detected")

        if file_path.exists() and file_path.is_file():
            file_path.unlink()
            return True
        return False


storage_service = PrivateStorageService()

