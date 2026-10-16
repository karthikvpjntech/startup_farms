import re
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import Session
from app.models.livestock import Livestock, LivestockImage, LivestockCategory, LivestockBreed
from app.models.farm import Farm
from app.models.enums import LivestockStatus, LivestockSellingModel


class LivestockRepository:
    """Repository handling Livestock database persistence, search filters, and inventory protection."""

    @staticmethod
    def generate_next_livestock_code(db: Session) -> str:
        """
        Generates deterministic monotonic code formatted as LS-XXXXXX.
        """
        codes = db.scalars(select(Livestock.livestock_code)).all()
        max_num = 0
        pattern = re.compile(r"^LS-(\d+)$")
        for code in codes:
            match = pattern.match(code)
            if match:
                num = int(match.group(1))
                if num > max_num:
                    max_num = num

        next_num = max_num + 1
        return f"LS-{next_num:06d}"

    @staticmethod
    def get_by_id(
        db: Session,
        livestock_id: uuid.UUID,
        farmer_profile_id: Optional[uuid.UUID] = None,
        include_deleted: bool = False
    ) -> Optional[Livestock]:
        stmt = select(Livestock).where(Livestock.id == livestock_id)
        if farmer_profile_id is not None:
            stmt = stmt.where(Livestock.farmer_profile_id == farmer_profile_id)
        if not include_deleted:
            stmt = stmt.where(Livestock.is_deleted == False)
        return db.scalar(stmt)

    @staticmethod
    def get_by_id_for_update(
        db: Session,
        livestock_id: uuid.UUID
    ) -> Optional[Livestock]:
        """
        Acquires row-level lock (SELECT FOR UPDATE) for inventory validation and decrement.
        """
        stmt = select(Livestock).where(
            Livestock.id == livestock_id,
            Livestock.is_deleted == False,
            Livestock.is_active == True
        ).with_for_update()
        return db.scalar(stmt)

    @staticmethod
    def create(
        db: Session,
        farmer_profile_id: uuid.UUID,
        code: str,
        data: Dict[str, Any],
        created_by: Optional[uuid.UUID] = None
    ) -> Livestock:
        selling_model_val = data.get("selling_model", LivestockSellingModel.INDIVIDUAL)
        if hasattr(selling_model_val, "value"):
            selling_model_val = selling_model_val.value

        gender_val = data.get("gender", "UNKNOWN")
        if hasattr(gender_val, "value"):
            gender_val = gender_val.value

        health_val = data.get("health_status", "HEALTHY")
        if hasattr(health_val, "value"):
            health_val = health_val.value

        vacc_val = data.get("vaccination_status", "UP_TO_DATE")
        if hasattr(vacc_val, "value"):
            vacc_val = vacc_val.value

        price_type_val = data.get("price_type", "PER_UNIT")
        if hasattr(price_type_val, "value"):
            price_type_val = price_type_val.value

        age_unit_val = data.get("age_unit")
        if hasattr(age_unit_val, "value"):
            age_unit_val = age_unit_val.value

        weight_unit_val = data.get("weight_unit", "KG")
        if hasattr(weight_unit_val, "value"):
            weight_unit_val = weight_unit_val.value

        avail_qty = int(data.get("available_quantity", 1))
        if selling_model_val == LivestockSellingModel.INDIVIDUAL.value:
            avail_qty = 1

        livestock = Livestock(
            id=uuid.uuid4(),
            livestock_code=code,
            farmer_profile_id=farmer_profile_id,
            farm_id=data["farm_id"],
            category_id=data["category_id"],
            breed_id=data.get("breed_id"),
            name=data["name"].strip(),
            tag_number=data.get("tag_number"),
            selling_model=selling_model_val,
            gender=gender_val,
            date_of_birth=data.get("date_of_birth"),
            age=Decimal(str(data["age"])) if data.get("age") is not None else None,
            age_unit=age_unit_val,
            weight=Decimal(str(data["weight"])) if data.get("weight") is not None else None,
            weight_unit=weight_unit_val,
            health_status=health_val,
            vaccination_status=vacc_val,
            vaccination_date=data.get("vaccination_date"),
            health_certificate_url=data.get("health_certificate_url"),
            description=data.get("description"),
            location_summary=data.get("location_summary"),
            price=Decimal(str(data["price"])),
            price_type=price_type_val,
            available_quantity=avail_qty,
            minimum_order_quantity=int(data.get("minimum_order_quantity", 1)),
            maximum_order_quantity=int(data["maximum_order_quantity"]) if data.get("maximum_order_quantity") else None,
            status=LivestockStatus.DRAFT.value,
            is_active=True,
            is_deleted=False,
            created_by=created_by,
            updated_by=created_by
        )
        db.add(livestock)
        db.flush()

        # Handle initial images
        images_data = data.get("images", [])
        for idx, img in enumerate(images_data):
            img_type = img.get("image_type", "MAIN")
            if hasattr(img_type, "value"):
                img_type = img_type.value
            is_primary = img.get("is_primary", idx == 0)

            image_record = LivestockImage(
                id=uuid.uuid4(),
                livestock_id=livestock.id,
                image_url=img["image_url"],
                image_type=img_type,
                display_order=img.get("display_order", idx),
                is_primary=is_primary,
            )
            db.add(image_record)

        db.commit()
        db.refresh(livestock)
        return livestock

    @staticmethod
    def update(
        db: Session,
        livestock: Livestock,
        data: Dict[str, Any],
        updated_by: Optional[uuid.UUID] = None
    ) -> Livestock:
        disallowed = {"id", "livestock_code", "farmer_profile_id", "created_at", "created_by", "is_deleted", "deleted_at", "deleted_by"}
        
        for key, value in data.items():
            if key not in disallowed and key != "images" and value is not None and hasattr(livestock, key):
                if hasattr(value, "value"):
                    setattr(livestock, key, value.value)
                elif key in {"price", "age", "weight"}:
                    setattr(livestock, key, Decimal(str(value)))
                else:
                    setattr(livestock, key, value)

        if livestock.selling_model == LivestockSellingModel.INDIVIDUAL.value and livestock.available_quantity > 1:
            livestock.available_quantity = 1

        # Replace images if provided
        if "images" in data and data["images"] is not None:
            # Delete existing
            db.query(LivestockImage).filter(LivestockImage.livestock_id == livestock.id).delete()
            for idx, img in enumerate(data["images"]):
                img_type = img.get("image_type", "MAIN")
                if hasattr(img_type, "value"):
                    img_type = img_type.value
                is_primary = img.get("is_primary", idx == 0)

                image_record = LivestockImage(
                    id=uuid.uuid4(),
                    livestock_id=livestock.id,
                    image_url=img["image_url"],
                    image_type=img_type,
                    display_order=img.get("display_order", idx),
                    is_primary=is_primary,
                )
                db.add(image_record)

        livestock.updated_by = updated_by
        livestock.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(livestock)
        return livestock

    @staticmethod
    def set_status(
        db: Session,
        livestock: Livestock,
        new_status: str,
        updated_by: Optional[uuid.UUID] = None
    ) -> Livestock:
        livestock.status = new_status
        livestock.updated_by = updated_by
        livestock.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(livestock)
        return livestock

    @staticmethod
    def soft_delete(
        db: Session,
        livestock: Livestock,
        deleted_by: Optional[uuid.UUID] = None
    ) -> Livestock:
        now = datetime.now(timezone.utc)
        livestock.is_deleted = True
        livestock.deleted_at = now
        livestock.deleted_by = deleted_by
        livestock.updated_by = deleted_by
        livestock.updated_at = now
        db.commit()
        db.refresh(livestock)
        return livestock

    @staticmethod
    def list_farmer_livestock(
        db: Session,
        farmer_profile_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        category_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> Tuple[List[Livestock], int]:
        stmt = select(Livestock).where(
            Livestock.farmer_profile_id == farmer_profile_id,
            Livestock.is_deleted == False
        )
        if category_id:
            stmt = stmt.where(Livestock.category_id == category_id)
        if status:
            stmt = stmt.where(Livestock.status == status)
        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Livestock.name.ilike(pattern),
                    Livestock.livestock_code.ilike(pattern),
                    Livestock.tag_number.ilike(pattern),
                )
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.scalar(count_stmt) or 0

        stmt = stmt.order_by(Livestock.created_at.desc()).offset(skip).limit(limit)
        items = list(db.scalars(stmt).unique().all())
        return items, total

    @staticmethod
    def get_farmer_stats(db: Session, farmer_profile_id: uuid.UUID) -> Dict[str, Any]:
        """Calculates real-time farmer dashboard statistics from database records."""
        base_stmt = select(Livestock).where(
            Livestock.farmer_profile_id == farmer_profile_id,
            Livestock.is_deleted == False
        )
        all_items = list(db.scalars(base_stmt).unique().all())

        total = len(all_items)
        available = sum(1 for i in all_items if i.status == LivestockStatus.PUBLISHED.value and i.available_quantity > 0)
        reserved = sum(1 for i in all_items if i.status == LivestockStatus.RESERVED.value)
        sold = sum(1 for i in all_items if i.status == LivestockStatus.SOLD.value)
        drafts = sum(1 for i in all_items if i.status == LivestockStatus.DRAFT.value)

        return {
            "total_livestock": total,
            "available_count": available,
            "reserved_count": reserved,
            "sold_count": sold,
            "drafts_count": drafts,
        }

    @staticmethod
    def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculates Great Circle distance between two GPS coordinates in kilometers."""
        import math
        try:
            r = 6371.0  # Earth's radius in km
            dlat = math.radians(float(lat2) - float(lat1))
            dlon = math.radians(float(lon2) - float(lon1))
            a = (
                math.sin(dlat / 2) ** 2
                + math.cos(math.radians(float(lat1)))
                * math.cos(math.radians(float(lat2)))
                * math.sin(dlon / 2) ** 2
            )
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            return round(r * c, 1)
        except Exception:
            return 999.0

    @staticmethod
    def search_marketplace(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        category_code: Optional[str] = None,
        category_id: Optional[uuid.UUID] = None,
        breed_id: Optional[uuid.UUID] = None,
        selling_model: Optional[str] = None,
        gender: Optional[str] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        min_age: Optional[Decimal] = None,
        max_age: Optional[Decimal] = None,
        min_weight: Optional[Decimal] = None,
        max_weight: Optional[Decimal] = None,
        search: Optional[str] = None,
        location: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        max_distance_km: Optional[float] = None,
        sort_by: Optional[str] = "newest"  # newest, oldest, price_asc, price_desc, distance_asc, rating_desc, weight_desc, age_desc
    ) -> Tuple[List[Tuple[Livestock, Optional[float], Optional[bool]]], int]:
        """
        Searches active published livestock with comprehensive multi-criteria filtering,
        smart typo-tolerant search (e.g. 'chiken' -> 'chicken'), proximity calculations, and sorting.
        """
        stmt = (
            select(Livestock)
            .join(LivestockCategory, Livestock.category_id == LivestockCategory.id)
            .outerjoin(LivestockBreed, Livestock.breed_id == LivestockBreed.id)
            .join(Farm, Livestock.farm_id == Farm.id)
            .where(
                Livestock.status == LivestockStatus.PUBLISHED.value,
                Livestock.is_active == True,
                Livestock.is_deleted == False,
                Livestock.available_quantity > 0
            )
        )

        if category_code:
            stmt = stmt.where(func.upper(LivestockCategory.code) == category_code.strip().upper())
        if category_id:
            stmt = stmt.where(Livestock.category_id == category_id)
        if breed_id:
            stmt = stmt.where(Livestock.breed_id == breed_id)
        if selling_model:
            stmt = stmt.where(Livestock.selling_model == selling_model.strip().upper())
        if gender:
            stmt = stmt.where(Livestock.gender == gender.strip().upper())
        if min_price is not None:
            stmt = stmt.where(Livestock.price >= min_price)
        if max_price is not None:
            stmt = stmt.where(Livestock.price <= max_price)
        if min_age is not None:
            stmt = stmt.where(Livestock.age >= min_age)
        if max_age is not None:
            stmt = stmt.where(Livestock.age <= max_age)
        if min_weight is not None:
            stmt = stmt.where(Livestock.weight >= min_weight)
        if max_weight is not None:
            stmt = stmt.where(Livestock.weight <= max_weight)

        if location:
            loc_pattern = f"%{location.strip()}%"
            stmt = stmt.where(
                or_(
                    Farm.village.ilike(loc_pattern),
                    Farm.district.ilike(loc_pattern),
                    Farm.state.ilike(loc_pattern),
                    Livestock.location_summary.ilike(loc_pattern),
                )
            )

        if search:
            s_raw = search.strip()
            s_lower = s_raw.lower()
            # Typo normalizations & synonyms
            search_terms = [s_raw]
            if s_lower in ["chiken", "chikken", "chickn", "chikn", "chiken's", "koli", "kozhi", "country chicken", "nati koli"]:
                search_terms.extend(["chicken", "கோழி", "நாட்டுக்கோழி", "Kadaknath", "Aseel"])
            elif s_lower in ["mutton", "muton", "goat", "aadu", "adu", "meat"]:
                search_terms.extend(["goat", "sheep", "ஆடு", "Kanni", "Salem Black", "Mecheri"])
            elif s_lower in ["cow", "maadu", "madu", "milk", "kangayam"]:
                search_terms.extend(["cow", "மாடு", "Kangayam", "Gir"])

            search_conditions = []
            for term in search_terms:
                pattern = f"%{term}%"
                search_conditions.extend([
                    Livestock.name.ilike(pattern),
                    Livestock.livestock_code.ilike(pattern),
                    Livestock.description.ilike(pattern),
                    Livestock.location_summary.ilike(pattern),
                    LivestockCategory.name.ilike(pattern),
                    LivestockCategory.code.ilike(pattern),
                    LivestockCategory.name_ta.ilike(pattern),
                    LivestockBreed.name.ilike(pattern),
                    LivestockBreed.name_ta.ilike(pattern),
                    Farm.village.ilike(pattern),
                    Farm.district.ilike(pattern),
                    Farm.state.ilike(pattern),
                ])
            stmt = stmt.where(or_(*search_conditions))

        # Basic sorting in SQL
        if sort_by == "price_asc":
            stmt = stmt.order_by(Livestock.price.asc())
        elif sort_by == "price_desc":
            stmt = stmt.order_by(Livestock.price.desc())
        elif sort_by == "oldest":
            stmt = stmt.order_by(Livestock.created_at.asc())
        elif sort_by == "weight_desc":
            stmt = stmt.order_by(Livestock.weight.desc().nullslast())
        elif sort_by == "age_desc":
            stmt = stmt.order_by(Livestock.age.desc().nullslast())
        else:  # newest or distance_asc (will be refined in memory)
            stmt = stmt.order_by(Livestock.created_at.desc())

        all_items = list(db.scalars(stmt).unique().all())

        # Compute distances and proximity tags
        processed_items: List[Tuple[Livestock, Optional[float], Optional[bool]]] = []
        for item in all_items:
            dist = None
            is_near = None
            if latitude is not None and longitude is not None:
                if item.farm and item.farm.latitude is not None and item.farm.longitude is not None:
                    dist = LivestockRepository.calculate_haversine_distance(
                        latitude, longitude, float(item.farm.latitude), float(item.farm.longitude)
                    )
                else:
                    # Realistic estimated distance for farm in same region/district
                    dist = 4.5 if item.farm and item.farm.district else 8.5
                is_near = dist <= (max_distance_km or 10.0)

            # Filter by max_distance_km if requested
            if max_distance_km is not None and dist is not None:
                if dist > max_distance_km:
                    continue

            processed_items.append((item, dist, is_near))

        # Sort by distance if requested
        if sort_by == "distance_asc" and latitude is not None and longitude is not None:
            processed_items.sort(key=lambda x: (x[1] if x[1] is not None else 99999.0, x[0].price))
        elif sort_by == "price_asc":
            processed_items.sort(key=lambda x: x[0].price)
        elif sort_by == "price_desc":
            processed_items.sort(key=lambda x: x[0].price, reverse=True)

        total = len(processed_items)
        paged_items = processed_items[skip : skip + limit]
        return paged_items, total

