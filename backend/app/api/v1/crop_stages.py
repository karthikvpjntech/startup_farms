import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.crop_stage import CropStageListResponse
from app.services.crop_stage_service import CropStageService

router = APIRouter(prefix="/crops/{crop_id}/process-stages", tags=["Crops (Cultivation Process)"])


@router.get(
    "",
    response_model=CropStageListResponse,
    summary="Get Cultivation Process Stages for Dynamic Visualization",
    description="Retrieves active, ordered cultivation stages for a crop to drive dynamic 3D/interactive visualizations for farmers and customers."
)
def get_crop_process_stages(
    crop_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    return CropStageService.list_stages_public(db=db, crop_id=crop_id)
