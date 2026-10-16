import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.orm import Session, selectinload
from app.models.farm_selling_product import FarmSellingProduct, FarmSellingProductImage
from app.models.farmer_profile import FarmerProfile
from app.models.marketplace_order import MarketplaceOrder, MarketplaceOrderItem
from app.models.farm import Farm
from app.models.user import User


class FarmSellingProductRepository:
    """
    Data Access Layer for Farmer Selling Products and Product Images.
    Includes atomic locking and concurrency protection.
    """

    @staticmethod
    def create(
        db: Session,
        farmer_profile_id: uuid.UUID,
        name: str,
        category: str,
        primary_image: str,
        price: Decimal,
        price_unit: str = "Kg",
        unit: str = "Kg",
        available_quantity: Decimal = Decimal("0.00"),
        minimum_order_quantity: Decimal = Decimal("1.00"),
        farm_id: Optional[uuid.UUID] = None,
        variety: Optional[str] = None,
        description: Optional[str] = None,
        harvest_date: Optional[Any] = None,
        delivery_available: bool = True,
        cod_available: bool = True,
        online_payment_available: bool = True,
        direct_pickup_available: bool = True,
        status: str = "ACTIVE",
        additional_images: Optional[List[str]] = None,
        user_id: Optional[uuid.UUID] = None,
    ) -> FarmSellingProduct:
        # Determine initial status
        initial_status = status
        if available_quantity <= 0:
            initial_status = "OUT_OF_STOCK"

        product = FarmSellingProduct(
            farmer_profile_id=farmer_profile_id,
            farm_id=farm_id,
            category=category.upper().strip(),
            name=name.strip(),
            variety=variety.strip() if variety else None,
            description=description,
            primary_image=primary_image.strip(),
            price=price,
            price_unit=price_unit.strip(),
            unit=unit.strip(),
            available_quantity=available_quantity,
            minimum_order_quantity=minimum_order_quantity,
            harvest_date=harvest_date,
            delivery_available=delivery_available,
            cod_available=cod_available,
            online_payment_available=online_payment_available,
            direct_pickup_available=direct_pickup_available,
            status=initial_status,
            created_by=user_id,
            updated_by=user_id,
        )
        db.add(product)
        db.flush()

        # Add primary image to gallery record
        primary_img = FarmSellingProductImage(
            product_id=product.id,
            image_url=primary_image.strip(),
            is_primary=True,
            display_order=0,
        )
        db.add(primary_img)

        # Add additional gallery images
        if additional_images:
            for idx, img_url in enumerate(additional_images, start=1):
                clean_url = img_url.strip()
                if clean_url and clean_url != primary_image.strip():
                    img = FarmSellingProductImage(
                        product_id=product.id,
                        image_url=clean_url,
                        is_primary=False,
                        display_order=idx,
                    )
                    db.add(img)

        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def get_by_id(db: Session, product_id: uuid.UUID) -> Optional[FarmSellingProduct]:
        query = (
            select(FarmSellingProduct)
            .where(
                FarmSellingProduct.id == product_id,
                FarmSellingProduct.is_deleted == False
            )
            .options(
                selectinload(FarmSellingProduct.images),
                selectinload(FarmSellingProduct.farmer_profile).selectinload(FarmerProfile.user),
                selectinload(FarmSellingProduct.farm),
            )
        )
        return db.execute(query).unique().scalar_one_or_none()

    @staticmethod
    def get_by_id_for_update(db: Session, product_id: uuid.UUID) -> Optional[FarmSellingProduct]:
        query = (
            select(FarmSellingProduct)
            .where(
                FarmSellingProduct.id == product_id,
                FarmSellingProduct.is_deleted == False
            )
            .with_for_update()
        )
        return db.execute(query).unique().scalar_one_or_none()


    @staticmethod
    def list_by_farmer(
        db: Session,
        farmer_profile_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[FarmSellingProduct], int]:
        filters = [
            FarmSellingProduct.farmer_profile_id == farmer_profile_id,
            FarmSellingProduct.is_deleted == False
        ]

        if category:
            filters.append(FarmSellingProduct.category == category.upper().strip())

        if status:
            filters.append(FarmSellingProduct.status == status.upper().strip())

        if search:
            s = f"%{search.strip().lower()}%"
            filters.append(
                or_(
                    func.lower(FarmSellingProduct.name).like(s),
                    func.lower(FarmSellingProduct.variety).like(s),
                    func.lower(FarmSellingProduct.category).like(s),
                )
            )

        count_query = select(func.count(FarmSellingProduct.id)).where(and_(*filters))
        total = db.execute(count_query).scalar() or 0

        offset = (page - 1) * page_size
        items_query = (
            select(FarmSellingProduct)
            .where(and_(*filters))
            .order_by(desc(FarmSellingProduct.created_at))
            .offset(offset)
            .limit(page_size)
            .options(
                selectinload(FarmSellingProduct.images),
                selectinload(FarmSellingProduct.farmer_profile).selectinload(FarmerProfile.user),
                selectinload(FarmSellingProduct.farm),
            )
        )
        items = list(db.execute(items_query).scalars().all())
        return items, total

    @staticmethod
    def search_public(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        search: Optional[str] = None,
        variety: Optional[str] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        in_stock_only: bool = False,
        delivery_type: Optional[str] = None,  # DELIVERY or PICKUP
        sort_by: str = "newest",  # newest, oldest, price_asc, price_desc, qty_desc
    ) -> Tuple[List[FarmSellingProduct], int]:
        filters = [
            FarmSellingProduct.is_deleted == False,
            FarmSellingProduct.status.in_(["ACTIVE", "OUT_OF_STOCK"])
        ]

        if in_stock_only:
            filters.append(
                and_(
                    FarmSellingProduct.status == "ACTIVE",
                    FarmSellingProduct.available_quantity > 0
                )
            )

        if category and category.upper() != "ALL":
            filters.append(FarmSellingProduct.category == category.upper().strip())

        if variety:
            filters.append(func.lower(FarmSellingProduct.variety).like(f"%{variety.strip().lower()}%"))

        if min_price is not None:
            filters.append(FarmSellingProduct.price >= min_price)

        if max_price is not None:
            filters.append(FarmSellingProduct.price <= max_price)

        if delivery_type == "DELIVERY":
            filters.append(FarmSellingProduct.delivery_available == True)
        elif delivery_type == "PICKUP":
            filters.append(FarmSellingProduct.direct_pickup_available == True)

        if search:
            s = f"%{search.strip().lower()}%"
            filters.append(
                or_(
                    func.lower(FarmSellingProduct.name).like(s),
                    func.lower(FarmSellingProduct.variety).like(s),
                    func.lower(FarmSellingProduct.category).like(s),
                    func.lower(FarmSellingProduct.description).like(s),
                    FarmSellingProduct.farmer_profile.has(
                        or_(
                            func.lower(FarmerProfile.village).like(s),
                            func.lower(FarmerProfile.district).like(s),
                            func.lower(FarmerProfile.state).like(s),
                            FarmerProfile.user.has(func.lower(User.full_name).like(s)),
                        )
                    )
                )
            )

        count_query = select(func.count(FarmSellingProduct.id)).where(and_(*filters))
        total = db.execute(count_query).scalar() or 0

        # Sort order
        if sort_by == "price_asc":
            order_clause = asc(FarmSellingProduct.price)
        elif sort_by == "price_desc":
            order_clause = desc(FarmSellingProduct.price)
        elif sort_by == "qty_desc":
            order_clause = desc(FarmSellingProduct.available_quantity)
        elif sort_by == "oldest":
            order_clause = asc(FarmSellingProduct.created_at)
        else:
            order_clause = desc(FarmSellingProduct.created_at)

        offset = (page - 1) * page_size
        items_query = (
            select(FarmSellingProduct)
            .where(and_(*filters))
            .order_by(order_clause)
            .offset(offset)
            .limit(page_size)
            .options(
                selectinload(FarmSellingProduct.images),
                selectinload(FarmSellingProduct.farmer_profile).selectinload(FarmerProfile.user),
                selectinload(FarmSellingProduct.farm),
            )
        )
        items = list(db.execute(items_query).scalars().all())
        return items, total

    @staticmethod
    def update(
        db: Session,
        product: FarmSellingProduct,
        update_data: Dict[str, Any],
        user_id: Optional[uuid.UUID] = None,
    ) -> FarmSellingProduct:
        additional_images = update_data.pop("additional_images", None)

        for key, value in update_data.items():
            if value is not None and hasattr(product, key):
                setattr(product, key, value)

        # Automatic status update based on available quantity
        if product.available_quantity <= 0:
            product.status = "OUT_OF_STOCK"
        elif product.status == "OUT_OF_STOCK" and product.available_quantity > 0:
            product.status = "ACTIVE"

        product.updated_at = datetime.now(timezone.utc)
        if user_id:
            product.updated_by = user_id

        # If additional images provided, update gallery
        if additional_images is not None:
            # Remove old gallery images
            db.query(FarmSellingProductImage).filter(
                FarmSellingProductImage.product_id == product.id
            ).delete()

            # Add primary
            db.add(
                FarmSellingProductImage(
                    product_id=product.id,
                    image_url=product.primary_image,
                    is_primary=True,
                    display_order=0,
                )
            )

            # Add additional
            for idx, img_url in enumerate(additional_images, start=1):
                clean_url = img_url.strip()
                if clean_url and clean_url != product.primary_image:
                    db.add(
                        FarmSellingProductImage(
                            product_id=product.id,
                            image_url=clean_url,
                            is_primary=False,
                            display_order=idx,
                        )
                    )

        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def update_stock(
        db: Session,
        product: FarmSellingProduct,
        new_quantity: Decimal,
        status: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
    ) -> FarmSellingProduct:
        product.available_quantity = new_quantity
        if status:
            product.status = status
        elif new_quantity <= 0:
            product.status = "OUT_OF_STOCK"
        elif product.status == "OUT_OF_STOCK" and new_quantity > 0:
            product.status = "ACTIVE"

        product.updated_at = datetime.now(timezone.utc)
        if user_id:
            product.updated_by = user_id

        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def soft_delete(
        db: Session,
        product: FarmSellingProduct,
        user_id: Optional[uuid.UUID] = None,
    ) -> FarmSellingProduct:
        product.is_deleted = True
        product.deleted_at = datetime.now(timezone.utc)
        product.deleted_by = user_id
        db.commit()
        return product

    @staticmethod
    def get_farmer_stats(db: Session, farmer_profile_id: uuid.UUID) -> Dict[str, Any]:
        # Count products
        total_p = db.scalar(
            select(func.count(FarmSellingProduct.id)).where(
                FarmSellingProduct.farmer_profile_id == farmer_profile_id,
                FarmSellingProduct.is_deleted == False
            )
        ) or 0

        active_p = db.scalar(
            select(func.count(FarmSellingProduct.id)).where(
                FarmSellingProduct.farmer_profile_id == farmer_profile_id,
                FarmSellingProduct.is_deleted == False,
                FarmSellingProduct.status == "ACTIVE",
                FarmSellingProduct.available_quantity > 0
            )
        ) or 0

        out_of_stock_p = db.scalar(
            select(func.count(FarmSellingProduct.id)).where(
                FarmSellingProduct.farmer_profile_id == farmer_profile_id,
                FarmSellingProduct.is_deleted == False,
                or_(
                    FarmSellingProduct.status == "OUT_OF_STOCK",
                    FarmSellingProduct.available_quantity <= 0
                )
            )
        ) or 0

        # Orders received count & revenue
        orders_q = (
            select(
                func.count(func.distinct(MarketplaceOrder.id)),
                func.coalesce(func.sum(MarketplaceOrder.total_amount), Decimal("0.00"))
            )
            .select_from(MarketplaceOrder)
            .join(MarketplaceOrderItem, MarketplaceOrder.id == MarketplaceOrderItem.order_id)
            .where(
                MarketplaceOrder.farmer_profile_id == farmer_profile_id,
                MarketplaceOrder.is_deleted == False,
                MarketplaceOrderItem.farm_product_id != None
            )
        )
        res = db.execute(orders_q).first()
        total_orders = res[0] if res else 0
        total_revenue = res[1] if res else Decimal("0.00")

        return {
            "total_products": total_p,
            "active_products": active_p,
            "out_of_stock_products": out_of_stock_p,
            "total_orders": total_orders,
            "total_revenue": total_revenue,
        }

    @staticmethod
    def list_farmer_orders(
        db: Session,
        farmer_profile_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
    ) -> Tuple[List[MarketplaceOrder], int]:
        filters = [
            MarketplaceOrder.farmer_profile_id == farmer_profile_id,
            MarketplaceOrder.is_deleted == False,
            MarketplaceOrder.items.any(MarketplaceOrderItem.farm_product_id != None)
        ]

        if status:
            filters.append(MarketplaceOrder.status == status.upper().strip())

        count_query = select(func.count(MarketplaceOrder.id)).where(and_(*filters))
        total = db.execute(count_query).scalar() or 0

        offset = (page - 1) * page_size
        items_query = (
            select(MarketplaceOrder)
            .where(and_(*filters))
            .order_by(desc(MarketplaceOrder.created_at))
            .offset(offset)
            .limit(page_size)
            .options(
                selectinload(MarketplaceOrder.customer),
                selectinload(MarketplaceOrder.farmer_profile).selectinload(FarmerProfile.user),
                selectinload(MarketplaceOrder.items),
                selectinload(MarketplaceOrder.payment),
                selectinload(MarketplaceOrder.delivery),
            )
        )
        items = list(db.execute(items_query).scalars().all())
        return items, total
