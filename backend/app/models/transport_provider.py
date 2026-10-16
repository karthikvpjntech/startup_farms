import uuid
from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Uuid, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.shipment import Shipment


class TransportProvider(Base):
    """
    Logistics fleet partner and transport carrier entity.
    Tracks internal/external delivery providers (Pickups, Trucks, Reefer vans).
    """
    __tablename__ = "transport_providers"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    provider_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True
    )
    provider_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )
    contact_person: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True
    )
    phone_number: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    vehicle_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )  # e.g., Pickup Van, Mini Truck, Reefer Truck, 3-Wheeler, Tractor Trailer
    vehicle_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    service_areas: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )  # Comma-separated or JSON string of districts/pincodes
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    shipments: Mapped[List["Shipment"]] = relationship(
        "Shipment",
        back_populates="transport_provider"
    )

    def __repr__(self) -> str:
        return f"<TransportProvider(code='{self.provider_code}', name='{self.provider_name}', active={self.is_active})>"
