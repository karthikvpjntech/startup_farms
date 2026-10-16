from fastapi import APIRouter
from app.schemas.common import APIResponse, HealthData
from app.api.v1.auth import router as auth_router
from app.api.v1.admin import router as admin_router
from app.api.v1.admin_users import router as admin_users_router
from app.api.v1.rbac import router as rbac_router
from app.api.v1.trash_bin import router as trash_bin_router
from app.api.v1.farmer_profile import router as farmer_profile_router
from app.api.v1.trader_profile import router as trader_profile_router
from app.api.v1.driver_profile import router as driver_profile_router
from app.api.v1.worker_profile import router as worker_profile_router
from app.api.v1.farms import router as farms_router
from app.api.v1.admin_crops import router as admin_crops_router
from app.api.v1.crops import router as crops_router
from app.api.v1.admin_crop_stages import router as admin_crop_stages_router
from app.api.v1.crop_stages import router as crop_stages_router
from app.api.v1.farm_crop_plans import router as farm_crop_plans_router
from app.api.v1.cultivations import router as cultivations_router
from app.api.v1.pre_activities import router as pre_activities_router
from app.api.v1.media import router as media_router
from app.api.v1.inputs import router as inputs_router
from app.api.v1.suppliers import router as suppliers_router
from app.api.v1.admin_suppliers import router as admin_suppliers_router
from app.api.v1.procurement_requests import router as procurement_requests_router
from app.api.v1.farmer_crm import router as farmer_crm_router
from app.api.v1.livestock_master import router as livestock_master_router
from app.api.v1.farmer_livestock import router as farmer_livestock_router
from app.api.v1.marketplace import router as marketplace_router
from app.api.v1.cart import router as cart_router
from app.api.v1.marketplace_orders import router as marketplace_orders_router
from app.api.v1.admin_marketplace import router as admin_marketplace_router
from app.api.v1.produce_procurement import router as produce_procurement_router
from app.api.v1.subscriptions import router as subscriptions_router

api_router = APIRouter()

# System endpoints
@api_router.get("/health", response_model=APIResponse[HealthData], summary="Health Check")
def health_check():
    """
    System health check endpoint verifying API service availability.
    """
    return APIResponse[HealthData](
        success=True,
        message="Agri-Smart API is running",
        data=HealthData(status="UP")
    )


# Mount Authentication endpoints
api_router.include_router(auth_router)

# Mount RBAC validation & Admin endpoints
api_router.include_router(admin_router)
api_router.include_router(admin_users_router)
api_router.include_router(trash_bin_router)
api_router.include_router(rbac_router)
api_router.include_router(admin_suppliers_router)
api_router.include_router(admin_marketplace_router)

# Mount Role Profile endpoints
api_router.include_router(farmer_profile_router)
api_router.include_router(trader_profile_router)
api_router.include_router(driver_profile_router)
api_router.include_router(worker_profile_router)

# Mount Farm Management endpoints
api_router.include_router(farms_router)

# Mount Crop Master & Process Stage Planning endpoints
api_router.include_router(admin_crops_router)
api_router.include_router(admin_crop_stages_router)
api_router.include_router(crops_router)
api_router.include_router(crop_stages_router)
api_router.include_router(farm_crop_plans_router)

# Mount Input Catalog & Suppliers endpoints
api_router.include_router(inputs_router)
api_router.include_router(suppliers_router)

# Mount Procurement Requisitions endpoints
api_router.include_router(procurement_requests_router)

# Mount Cultivation Lifecycle, Pre-Activities & Media endpoints
api_router.include_router(cultivations_router)
api_router.include_router(pre_activities_router)
api_router.include_router(media_router)

# Mount Farmer CRM / Farm Operations Management endpoints
api_router.include_router(farmer_crm_router)

from app.api.v1.farmer_products import router as farmer_products_router
from app.api.v1.farm_products import router as farm_products_router
from app.api.v1.tool_interests import router as tool_interests_router

from app.api.v1.payment_webhooks import router as payment_webhooks_router
from app.api.v1.shipments import router as shipments_router
from app.api.v1.admin_transport import router as admin_transport_router

# Mount Livestock Master, Farmer Livestock, Public Marketplace, Cart & Order endpoints
api_router.include_router(livestock_master_router)
api_router.include_router(farmer_livestock_router)
api_router.include_router(farmer_products_router)
api_router.include_router(farm_products_router)
api_router.include_router(tool_interests_router)
api_router.include_router(marketplace_router)
api_router.include_router(cart_router)
api_router.include_router(marketplace_orders_router)
api_router.include_router(produce_procurement_router)
api_router.include_router(subscriptions_router)
api_router.include_router(payment_webhooks_router)
api_router.include_router(shipments_router)
api_router.include_router(admin_transport_router)






