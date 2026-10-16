from typing import Optional, List
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query, status
from app.dependencies.auth import get_current_user
from app.dependencies.authorization import require_roles
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.cultivation import MediaUploadProofRequest, MediaUploadProofResponse
from app.services.cultivation_service import CultivationService
from app.services.cloudinary_service import CloudinaryService

router = APIRouter(prefix="/media", tags=["Media & Uploads"])


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    summary="Upload Media to Cloudinary / Storage",
    description="Uploads an image, certificate, or video file to Cloudinary with automatic local storage fallback."
)
async def upload_media(
    file: UploadFile = File(...),
    folder: str = Form(default="general"),
    tags: Optional[str] = Form(default=None),
    current_user: User = Depends(get_current_user),
):
    """
    Direct multipart media upload. Supports folders: 'crops', 'stages', 'livestock', 'bills', 'profiles'.
    """
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    result = CloudinaryService.upload_file(
        file=file,
        folder=folder,
        tags=tag_list,
    )
    return result


@router.get(
    "/cloudinary-signature",
    summary="Get Cloudinary Signed Upload Parameters",
    description="Generates a pre-signed signature allowing the frontend to upload directly to Cloudinary."
)
def get_cloudinary_signature(
    folder: str = Query(default="general"),
    current_user: User = Depends(get_current_user),
):
    return CloudinaryService.generate_presigned_signature(folder=folder)


@router.post(
    "/upload-proof",
    response_model=MediaUploadProofResponse,
    summary="Request Pre-signed Proof Upload URL",
    description="Issues a pre-signed URL to upload optional bill photos or inspection clips directly to cloud storage.",
)
def request_upload_proof(
    request: MediaUploadProofRequest,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
):
    return CultivationService.generate_media_upload_url(request)
