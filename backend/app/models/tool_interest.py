import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Numeric, Text, Uuid, ForeignKey, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.farmer_profile import FarmerProfile


class ToolInterest(Base):
    """
    Farmer Tool / Machinery Demand entity.
    Stores farmer's required equipment, desired location, specifications, and geofence parameters.
    Automatically triggers Google Places / local agro-discovery engine upon creation or refresh.
    """
    __tablename__ = "tool_interests"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    farmer_profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("farmer_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    tool_name: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False
    )
    tool_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="RENTAL"  # RENTAL, PURCHASE, SERVICE_REPAIR, OPERATOR_HIRE
    )
    required_location: Mapped[str] = mapped_column(
        String(200),
        index=True,
        nullable=False
    )
    latitude: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(9, 6),
        nullable=True
    )
    longitude: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(9, 6),
        nullable=True
    )
    search_radius_km: Mapped[float] = mapped_column(
        Float,
        default=25.0,
        nullable=False
    )
    geofence_radius_meters: Mapped[float] = mapped_column(
        Float,
        default=500.0,
        nullable=False
    )
    specifications: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    max_budget: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="ACTIVE",
        index=True
    )
    category: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        default="MACHINERY"
    )
    notify_in_app: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    notify_sms: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    notify_sound: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    auto_discovery_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    last_searched_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Status & Soft-delete fields
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        index=True,
        nullable=False
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
        nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    deleted_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Audit timestamps
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
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    farmer_profile: Mapped["FarmerProfile"] = relationship("FarmerProfile", lazy="joined")
    discovered_locations: Mapped[List["DiscoveredToolLocation"]] = relationship(
        "DiscoveredToolLocation",
        back_populates="tool_interest",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<ToolInterest(id={self.id}, tool='{self.tool_name}', type='{self.tool_type}', location='{self.required_location}')>"


class DiscoveredToolLocation(Base):
    """
    Vendor / Business location discovered via Google Places or Local Agro-Discovery.
    Persisted with coordinates for geofencing and proximity notifications.
    """
    __tablename__ = "discovered_tool_locations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    tool_interest_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tool_interests.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    place_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True
    )
    business_name: Mapped[str] = mapped_column(
        String(255),
        index=True,
        nullable=False
    )
    category: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        default="Agricultural Machinery & Equipment"
    )
    formatted_address: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    latitude: Mapped[Decimal] = mapped_column(
        Numeric(9, 6),
        nullable=False
    )
    longitude: Mapped[Decimal] = mapped_column(
        Numeric(9, 6),
        nullable=False
    )
    phone_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    rating: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(3, 2),
        nullable=True
    )
    user_ratings_total: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        default=0
    )
    opening_hours_text: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    google_maps_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    website: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    photo_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    products_available: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    distance_meters_cached: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    last_notified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    notification_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    # Status & Soft-delete fields
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        index=True,
        nullable=False
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
        nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    deleted_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Audit timestamps
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
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    tool_interest: Mapped["ToolInterest"] = relationship("ToolInterest", back_populates="discovered_locations")

    def __repr__(self) -> str:
        return f"<DiscoveredToolLocation(id={self.id}, name='{self.business_name}', lat={self.latitude}, lng={self.longitude})>"
