import logging
import sys
from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.config import settings
from app.models.user import User
from app.models.user_role import UserRole
from app.models.role import Role
from app.models.enums import RoleEnum
from app.models.farmer_profile import FarmerProfile
from app.models.trader_profile import TraderProfile
from app.models.driver_profile import DriverProfile
from app.models.worker_profile import WorkerProfile
from app.models.farm import Farm
from app.models.cultivation import CultivationRun, CultivationStage, StageExpense, StageWorkerLog
from app.models.farm_crop_plan import FarmCropPlan
from app.models.cultivation_schedule import CultivationSchedule
from app.models.worker import Worker
from app.models.worker_attendance import WorkerAttendance
from app.models.machine import Machine
from app.models.machine_usage import MachineUsage
from app.models.material_purchase import MaterialPurchase
from app.models.bill import Bill, BillItem
from app.models.payment import Payment
from app.models.logistics import Logistics
from app.models.procurement_request import ProcurementRequest
from app.models.cart import Cart, CartItem
from app.models.marketplace_order import MarketplaceOrder, MarketplaceOrderItem, MarketplacePayment, MarketplaceDelivery
from app.models.livestock import Livestock, LivestockImage, LivestockReview
from app.models.refresh_token import RefreshToken
from app.models.sms_log import SMSLog

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("agri_smart.clean_mock_data")


from app.core.database import Base

def purge_mock_data(db: Session) -> dict:
    """
    Purges all demo, mock, and test data across the system,
    preserving ONLY the Super Admin account and Master Taxonomy (Roles, Crops, Stages, Inputs, Suppliers, Livestock taxonomy).
    """
    logger.info("=== Starting Mock Data Purge ===")
    
    # Ensure all tables exist in database schema
    Base.metadata.create_all(bind=db.get_bind())

    # 1. Identify Super Admin user
    super_admin_email = settings.SUPER_ADMIN_EMAIL or "admin@agrismart.local"
    super_admin_mobile = settings.SUPER_ADMIN_MOBILE or "9999999999"

    stmt = select(User).where(
        (User.email == super_admin_email) | (User.mobile_number == super_admin_mobile)
    )
    admin_user = db.execute(stmt).scalar_one_or_none()

    admin_user_id = admin_user.id if admin_user else None
    logger.info("Identified Super Admin ID: %s (Email: %s)", admin_user_id, super_admin_email)

    # 2. Delete transactional order & marketplace records
    db.execute(delete(LivestockReview))
    db.execute(delete(MarketplaceDelivery))
    db.execute(delete(MarketplacePayment))
    db.execute(delete(MarketplaceOrderItem))
    db.execute(delete(MarketplaceOrder))
    db.execute(delete(CartItem))
    db.execute(delete(Cart))
    logger.info("Cleared all marketplace orders, items, cart items, deliveries, and reviews.")

    # 3. Delete farm-specific livestock listings (keep master categories & breeds)
    db.execute(delete(LivestockImage))
    db.execute(delete(Livestock))
    logger.info("Cleared farmer livestock inventory.")

    # 4. Delete farm operations: bills, payments, logistics, attendance, machinery, materials
    db.execute(delete(Payment))
    db.execute(delete(BillItem))
    db.execute(delete(Bill))
    db.execute(delete(Logistics))
    db.execute(delete(WorkerAttendance))
    db.execute(delete(Worker))
    db.execute(delete(MachineUsage))
    db.execute(delete(Machine))
    db.execute(delete(MaterialPurchase))
    db.execute(delete(CultivationSchedule))
    db.execute(delete(ProcurementRequest))
    db.execute(delete(SMSLog))
    logger.info("Cleared all farm operational bills, payments, logistics, workers, machines, and material records.")

    # 5. Delete cultivations and farm crop plans
    db.execute(delete(StageWorkerLog))
    db.execute(delete(StageExpense))
    db.execute(delete(CultivationStage))
    db.execute(delete(CultivationRun))
    db.execute(delete(FarmCropPlan))
    db.execute(delete(Farm))
    logger.info("Cleared all farms, crop plans, and cultivation runs.")

    # 6. Delete role-specific profiles for non-superadmin users
    db.execute(delete(FarmerProfile))
    db.execute(delete(TraderProfile))
    db.execute(delete(DriverProfile))
    db.execute(delete(WorkerProfile))
    logger.info("Cleared role profiles.")

    # 7. Delete refresh tokens and user roles for non-superadmin users
    if admin_user_id:
        db.execute(delete(RefreshToken).where(RefreshToken.user_id != admin_user_id))
        db.execute(delete(UserRole).where(UserRole.user_id != admin_user_id))
        db.execute(delete(User).where(User.id != admin_user_id))
    else:
        db.execute(delete(RefreshToken))
        db.execute(delete(UserRole))
        db.execute(delete(User))
    logger.info("Cleared all non-Super-Admin user accounts and authentication sessions.")

    db.commit()
    logger.info("=== Mock Data Purge Completed Successfully ===")

    # Verify counts
    remaining_users = db.execute(select(User)).scalars().all()
    return {
        "status": "success",
        "remaining_users_count": len(remaining_users),
        "super_admin_email": super_admin_email,
    }


def run_clean() -> None:
    db = SessionLocal()
    try:
        result = purge_mock_data(db)
        logger.info("Purge result: %s", result)
    except Exception as e:
        logger.error("Error during mock data purge: %s", e, exc_info=True)
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    run_clean()
