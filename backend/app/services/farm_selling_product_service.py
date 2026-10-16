import logging
import uuid
from decimal import Decimal
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.farm_selling_product import FarmSellingProduct, FarmSellingProductImage
from app.models.marketplace_order import MarketplaceOrder, MarketplaceOrderItem, MarketplacePayment, MarketplaceDelivery
from app.schemas.farm_selling_product import (
    FarmSellingProductCreateRequest,
    FarmSellingProductUpdateRequest,
    FarmSellingProductStockUpdateRequest,
    FarmSellingProductResponse,
    FarmSellingProductListResponse,
    FarmerSellingProductStatsResponse,
    FarmSellingProductImageResponse,
    FarmProductBuyNowRequest,
)
from app.schemas.marketplace_order import MarketplaceOrderResponse
from app.repositories.farm_selling_product_repository import FarmSellingProductRepository
from app.repositories.farmer_profile_repository import FarmerProfileRepository
from app.services.marketplace_order_service import MarketplaceOrderService

logger = logging.getLogger("agri_smart.farm_selling_product_service")


class FarmSellingProductService:
    """
    Business service for Farmer Selling Products and Public Farm Marketplace.
    """

    @staticmethod
    def _map_to_response(product: FarmSellingProduct) -> FarmSellingProductResponse:
        f_name = None
        f_mobile = None
        f_img = None
        village = None
        district = None
        state = None
        lat = None
        lng = None

        if product.farmer_profile:
            village = product.farmer_profile.village
            district = product.farmer_profile.district
            state = product.farmer_profile.state
            f_img = product.farmer_profile.profile_image_url
            if product.farmer_profile.latitude:
                lat = float(product.farmer_profile.latitude)
            if product.farmer_profile.longitude:
                lng = float(product.farmer_profile.longitude)
            if product.farmer_profile.user:
                f_name = product.farmer_profile.user.full_name
                f_mobile = product.farmer_profile.user.mobile_number

        loc_parts = [p for p in [village, district, state] if p]
        location_summary = ", ".join(loc_parts) if loc_parts else None

        img_responses = [
            FarmSellingProductImageResponse(
                id=img.id,
                product_id=img.product_id,
                image_url=img.image_url,
                is_primary=img.is_primary,
                display_order=img.display_order,
                created_at=img.created_at,
            )
            for img in product.images
        ]

        is_out = product.status == "OUT_OF_STOCK" or product.available_quantity <= Decimal("0.00")

        return FarmSellingProductResponse(
            id=product.id,
            farmer_profile_id=product.farmer_profile_id,
            farmer_name=f_name,
            farmer_mobile=f_mobile,
            farmer_profile_image=f_img,
            farm_id=product.farm_id,
            farm_name=product.farm.farm_name if product.farm else None,
            village=village,
            district=district,
            state=state,
            location_summary=location_summary,
            latitude=lat,
            longitude=lng,
            category=product.category,
            name=product.name,
            variety=product.variety,
            description=product.description,
            primary_image=product.primary_image,
            price=product.price,
            price_unit=product.price_unit,
            unit=product.unit,
            available_quantity=product.available_quantity,
            minimum_order_quantity=product.minimum_order_quantity,
            harvest_date=product.harvest_date,
            delivery_available=product.delivery_available,
            cod_available=product.cod_available,
            online_payment_available=product.online_payment_available,
            direct_pickup_available=product.direct_pickup_available,
            status=product.status,
            is_out_of_stock=is_out,
            images=img_responses,
            created_at=product.created_at,
            updated_at=product.updated_at,
        )

    # ========================================================================
    # Farmer Operations
    # ========================================================================

    @staticmethod
    def create_product(
        db: Session,
        current_user: User,
        request: FarmSellingProductCreateRequest
    ) -> FarmSellingProductResponse:
        farmer_profile = FarmerProfileRepository.get_by_user_id(db, current_user.id)
        if not farmer_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Farmer profile required to create selling products. Please set up your profile first."
            )

        product = FarmSellingProductRepository.create(
            db=db,
            farmer_profile_id=farmer_profile.id,
            farm_id=request.farm_id,
            category=request.category,
            name=request.name,
            variety=request.variety,
            description=request.description,
            primary_image=request.primary_image,
            price=request.price,
            price_unit=request.price_unit,
            unit=request.unit,
            available_quantity=request.available_quantity,
            minimum_order_quantity=request.minimum_order_quantity,
            harvest_date=request.harvest_date,
            delivery_available=request.delivery_available,
            cod_available=request.cod_available,
            online_payment_available=request.online_payment_available,
            direct_pickup_available=request.direct_pickup_available,
            status=request.status,
            additional_images=request.additional_images,
            user_id=current_user.id,
        )
        logger.info("Farmer %s created product %s (%s)", current_user.id, product.name, product.id)
        return FarmSellingProductService._map_to_response(product)

    @staticmethod
    def list_farmer_products(
        db: Session,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        status_filter: Optional[str] = None,
        search: Optional[str] = None,
    ) -> FarmSellingProductListResponse:
        farmer_profile = FarmerProfileRepository.get_by_user_id(db, current_user.id)
        if not farmer_profile:
            return FarmSellingProductListResponse(
                items=[], total=0, page=page, page_size=page_size, total_pages=0
            )

        items, total = FarmSellingProductRepository.list_by_farmer(
            db=db,
            farmer_profile_id=farmer_profile.id,
            page=page,
            page_size=page_size,
            category=category,
            status=status_filter,
            search=search,
        )

        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        return FarmSellingProductListResponse(
            items=[FarmSellingProductService._map_to_response(p) for p in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    @staticmethod
    def get_farmer_stats(db: Session, current_user: User) -> FarmerSellingProductStatsResponse:
        farmer_profile = FarmerProfileRepository.get_by_user_id(db, current_user.id)
        if not farmer_profile:
            return FarmerSellingProductStatsResponse()

        stats_dict = FarmSellingProductRepository.get_farmer_stats(db, farmer_profile.id)
        return FarmerSellingProductStatsResponse(**stats_dict)

    @staticmethod
    def get_product_detail(
        db: Session,
        current_user: User,
        product_id: uuid.UUID
    ) -> FarmSellingProductResponse:
        product = FarmSellingProductRepository.get_by_id(db, product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

        farmer_profile = FarmerProfileRepository.get_by_user_id(db, current_user.id)
        if not farmer_profile or product.farmer_profile_id != farmer_profile.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this product listing.")

        return FarmSellingProductService._map_to_response(product)

    @staticmethod
    def update_product(
        db: Session,
        current_user: User,
        product_id: uuid.UUID,
        request: FarmSellingProductUpdateRequest
    ) -> FarmSellingProductResponse:
        product = FarmSellingProductRepository.get_by_id(db, product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

        farmer_profile = FarmerProfileRepository.get_by_user_id(db, current_user.id)
        if not farmer_profile or product.farmer_profile_id != farmer_profile.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this product listing.")

        update_dict = request.model_dump(exclude_unset=True)
        updated_product = FarmSellingProductRepository.update(
            db=db,
            product=product,
            update_data=update_dict,
            user_id=current_user.id
        )
        return FarmSellingProductService._map_to_response(updated_product)

    @staticmethod
    def update_stock(
        db: Session,
        current_user: User,
        product_id: uuid.UUID,
        request: FarmSellingProductStockUpdateRequest
    ) -> FarmSellingProductResponse:
        product = FarmSellingProductRepository.get_by_id(db, product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

        farmer_profile = FarmerProfileRepository.get_by_user_id(db, current_user.id)
        if not farmer_profile or product.farmer_profile_id != farmer_profile.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this product listing.")

        updated = FarmSellingProductRepository.update_stock(
            db=db,
            product=product,
            new_quantity=request.available_quantity,
            status=request.status,
            user_id=current_user.id
        )
        return FarmSellingProductService._map_to_response(updated)

    @staticmethod
    def delete_product(
        db: Session,
        current_user: User,
        product_id: uuid.UUID
    ) -> FarmSellingProductResponse:
        product = FarmSellingProductRepository.get_by_id(db, product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

        farmer_profile = FarmerProfileRepository.get_by_user_id(db, current_user.id)
        if not farmer_profile or product.farmer_profile_id != farmer_profile.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this product listing.")

        deleted = FarmSellingProductRepository.soft_delete(db=db, product=product, user_id=current_user.id)
        return FarmSellingProductService._map_to_response(deleted)

    # ========================================================================
    # Public Marketplace Operations
    # ========================================================================

    @staticmethod
    def search_public_products(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        search: Optional[str] = None,
        variety: Optional[str] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        in_stock_only: bool = False,
        delivery_type: Optional[str] = None,
        sort_by: str = "newest",
    ) -> FarmSellingProductListResponse:
        items, total = FarmSellingProductRepository.search_public(
            db=db,
            page=page,
            page_size=page_size,
            category=category,
            search=search,
            variety=variety,
            min_price=min_price,
            max_price=max_price,
            in_stock_only=in_stock_only,
            delivery_type=delivery_type,
            sort_by=sort_by,
        )

        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        return FarmSellingProductListResponse(
            items=[FarmSellingProductService._map_to_response(p) for p in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    @staticmethod
    def get_public_product_detail(
        db: Session,
        product_id: uuid.UUID
    ) -> FarmSellingProductResponse:
        product = FarmSellingProductRepository.get_by_id(db, product_id)
        if not product or product.status not in ["ACTIVE", "OUT_OF_STOCK"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm product listing not found.")
        return FarmSellingProductService._map_to_response(product)

    # ========================================================================
    # Order & Buy Now Checkout
    # ========================================================================

    @staticmethod
    def buy_now(
        db: Session,
        current_user: User,
        request: FarmProductBuyNowRequest
    ) -> MarketplaceOrderResponse:
        # 1. Acquire row-level lock on product for atomic stock check
        product = FarmSellingProductRepository.get_by_id_for_update(db, request.product_id)
        if not product or product.is_deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm product not found.")

        if product.status != "ACTIVE" or product.available_quantity <= Decimal("0.00"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product is currently out of stock.")

        if product.available_quantity < request.quantity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Requested quantity {request.quantity} exceeds available stock of {product.available_quantity} {product.unit}."
            )

        if request.quantity < product.minimum_order_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Minimum order quantity is {product.minimum_order_quantity} {product.unit}."
            )

        # 2. Validate enabled purchase methods
        is_pickup = request.fulfillment_type == "FARM_PICKUP"
        if is_pickup and not product.direct_pickup_available:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Direct farm pickup is not available for this product.")
        if not is_pickup and not product.delivery_available:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Home delivery is not available for this product.")

        if request.payment_method == "CASH_ON_DELIVERY" and not product.cod_available:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cash on Delivery is not available for this product.")
        if request.payment_method in ["UPI", "NET_BANKING", "CARD"] and not product.online_payment_available:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Online payment is not available for this product.")

        # 3. Calculate Financials
        unit_price = product.price
        subtotal = unit_price * request.quantity
        delivery_charge = Decimal("0.00") if is_pickup else Decimal("0.00")
        tax_amount = Decimal("0.00")
        total_amount = subtotal + delivery_charge + tax_amount

        # 4. Atomically Deduct Inventory
        product.available_quantity -= request.quantity
        if product.available_quantity <= Decimal("0.00"):
            product.status = "OUT_OF_STOCK"

        # 5. Create Order
        order_number = f"AGRI-FP-{uuid.uuid4().hex[:8].upper()}"
        initial_order_status = "CONFIRMED" if request.payment_method == "CASH_ON_DELIVERY" or is_pickup else "PENDING"
        initial_payment_status = "PENDING"

        order = MarketplaceOrder(
            id=uuid.uuid4(),
            order_number=order_number,
            customer_id=current_user.id,
            farmer_profile_id=product.farmer_profile_id,
            total_items_count=int(request.quantity),
            subtotal_amount=subtotal,
            delivery_charge=delivery_charge,
            tax_amount=tax_amount,
            discount_amount=Decimal("0.00"),
            total_amount=total_amount,
            status=initial_order_status,
            payment_status=initial_payment_status,
            delivery_type="FARM_PICKUP" if is_pickup else "FARMER_DELIVERY",
            delivery_contact_name=request.delivery_contact_name,
            delivery_contact_phone=request.delivery_contact_phone,
            delivery_address=request.delivery_address or ("Farm Direct Pickup" if is_pickup else "N/A"),
            delivery_city=request.delivery_city,
            delivery_pincode=request.delivery_pincode,
            notes=request.notes,
            created_by=current_user.id,
        )
        db.add(order)
        db.flush()

        # 6. Create Order Item Snapshot
        item = MarketplaceOrderItem(
            id=uuid.uuid4(),
            order_id=order.id,
            product_type="FARM_PRODUCT",
            farm_product_id=product.id,
            farm_id=product.farm_id,
            livestock_name=product.name,
            category_name=product.category,
            variety_name=product.variety,
            unit=product.unit,
            image_url=product.primary_image,
            unit_price=unit_price,
            quantity=int(request.quantity) if request.quantity == int(request.quantity) else 1,
            subtotal=subtotal,
        )
        db.add(item)


        # 7. Create Payment record
        payment = MarketplacePayment(
            id=uuid.uuid4(),
            payment_number=f"PAY-{uuid.uuid4().hex[:8].upper()}",
            order_id=order.id,
            customer_id=current_user.id,
            amount=total_amount,
            payment_method=request.payment_method,
            status=initial_payment_status,
        )
        db.add(payment)

        # 8. Create Delivery / Pickup Tracking record
        pickup_loc = f"{product.farmer_profile.village or 'Farm'}, {product.farmer_profile.district or ''}".strip(", ") if product.farmer_profile else "Farm"
        delivery = MarketplaceDelivery(
            id=uuid.uuid4(),
            delivery_code=f"DEL-{uuid.uuid4().hex[:8].upper()}",
            order_id=order.id,
            pickup_location=pickup_loc,
            drop_location=request.delivery_address or pickup_loc,
            status="PENDING",
            tracking_notes=f"Fulfillment Type: {'Farm Pickup' if is_pickup else 'Farmer Delivery'}",
        )
        db.add(delivery)

        db.commit()
        db.refresh(order)
        logger.info("Order %s created for farm product %s by user %s", order.order_number, product.name, current_user.id)
        return MarketplaceOrderService._map_order_to_response(order)
