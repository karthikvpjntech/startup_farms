import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class PaymentWebhookResponse(BaseModel):
    status: str = Field(..., description="Processing status: PROCESSED, DUPLICATE, FAILED, or IGNORED")
    event_id: str
    event_type: str
    message: str
    error: Optional[str] = None


class WebhookLogItemResponse(BaseModel):
    id: uuid.UUID
    event_id: str
    event_type: str
    status: str
    signature: Optional[str] = None
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WebhookLogListResponse(BaseModel):
    items: List[WebhookLogItemResponse]
    total: int
    page: int
    page_size: int
