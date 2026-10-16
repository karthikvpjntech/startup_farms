import os
import uuid
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import UploadFile, HTTPException, status
try:
    import cloudinary
    import cloudinary.uploader
    import cloudinary.utils
    HAS_CLOUDINARY = True
except ImportError:
    cloudinary = None
    HAS_CLOUDINARY = False

from app.core.config import settings

logger = logging.getLogger("agri_smart.cloudinary_service")


class CloudinaryService:
    """
    Production-ready Cloudinary media management service with local fallback.
    Handles image uploads, transformations, secure signatures, and cleanup.
    """

    _initialized: bool = False

    @classmethod
    def _ensure_init(cls) -> bool:
        """Initializes Cloudinary credentials if configured."""
        if not HAS_CLOUDINARY:
            return False

        if cls._initialized:
            return bool(settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY and settings.CLOUDINARY_API_SECRET)

        if settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY and settings.CLOUDINARY_API_SECRET:
            cloudinary.config(
                cloud_name=settings.CLOUDINARY_CLOUD_NAME,
                api_key=settings.CLOUDINARY_API_KEY,
                api_secret=settings.CLOUDINARY_API_SECRET,
                secure=settings.CLOUDINARY_SECURE,
            )
            cls._initialized = True
            logger.info("Cloudinary SDK initialized successfully for cloud: %s", settings.CLOUDINARY_CLOUD_NAME)
            return True
        else:
            logger.info("Cloudinary credentials not provided in environment. Media service operating in local fallback mode.")
            return False

    @classmethod
    def is_configured(cls) -> bool:
        return cls._ensure_init()

    @classmethod
    def upload_file(
        cls,
        file: UploadFile,
        folder: str = "general",
        transformation: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Uploads a FastAPI UploadFile to Cloudinary or saves locally if Cloudinary is not configured.
        """
        target_folder = f"{settings.CLOUDINARY_FOLDER}/{folder}".strip("/")
        unique_filename = f"{uuid.uuid4().hex}_{file.filename}"

        if cls.is_configured():
            try:
                # Read file contents
                file_bytes = file.file.read()
                file.file.seek(0)

                upload_params: Dict[str, Any] = {
                    "folder": target_folder,
                    "public_id": Path(unique_filename).stem,
                    "resource_type": "auto",
                    "overwrite": True,
                }
                if tags:
                    upload_params["tags"] = tags
                if transformation:
                    upload_params["transformation"] = transformation

                result = cloudinary.uploader.upload(file_bytes, **upload_params)
                logger.info("Uploaded media to Cloudinary: %s (public_id: %s)", result.get("secure_url"), result.get("public_id"))
                return {
                    "success": True,
                    "provider": "cloudinary",
                    "secure_url": result.get("secure_url"),
                    "public_id": result.get("public_id"),
                    "format": result.get("format"),
                    "width": result.get("width"),
                    "height": result.get("height"),
                    "bytes": result.get("bytes"),
                }
            except Exception as exc:
                logger.error("Cloudinary upload failed: %s. Falling back to local storage.", exc)

        # Local Fallback Storage
        local_dir = Path("uploads") / folder
        local_dir.mkdir(parents=True, exist_ok=True)
        local_path = local_dir / unique_filename

        with open(local_path, "wb") as buffer:
            buffer.write(file.file.read())
        file.file.seek(0)

        file_url = f"/uploads/{folder}/{unique_filename}"
        logger.info("Saved media locally: %s", file_url)
        return {
            "success": True,
            "provider": "local",
            "secure_url": file_url,
            "public_id": f"local_{unique_filename}",
            "format": Path(file.filename or "").suffix.lstrip("."),
            "bytes": os.path.getsize(local_path),
        }

    @classmethod
    def generate_presigned_signature(
        cls,
        folder: str = "general",
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generates signed parameters for direct frontend-to-Cloudinary widget upload.
        """
        if not cls.is_configured():
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Cloudinary is not configured on the server."
            )

        timestamp = int(time.time())
        target_folder = f"{settings.CLOUDINARY_FOLDER}/{folder}".strip("/")

        params_to_sign = {
            "timestamp": timestamp,
            "folder": target_folder,
        }
        if tags:
            params_to_sign["tags"] = ",".join(tags)

        signature = cloudinary.utils.api_sign_request(params_to_sign, settings.CLOUDINARY_API_SECRET or "")
        return {
            "signature": signature,
            "timestamp": timestamp,
            "cloud_name": settings.CLOUDINARY_CLOUD_NAME,
            "api_key": settings.CLOUDINARY_API_KEY,
            "folder": target_folder,
        }

    @classmethod
    def delete_media(cls, public_id: str) -> bool:
        """Deletes media by public_id from Cloudinary or local storage."""
        if public_id.startswith("local_"):
            filename = public_id.replace("local_", "")
            # Find and remove file in uploads
            for path in Path("uploads").rglob(filename):
                try:
                    path.unlink()
                    return True
                except Exception:
                    pass
            return False

        if cls.is_configured():
            try:
                res = cloudinary.uploader.destroy(public_id)
                return res.get("result") == "ok"
            except Exception as e:
                logger.error("Failed to delete Cloudinary media %s: %s", public_id, e)
                return False
        return False
