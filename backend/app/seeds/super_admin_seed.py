import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.enums import RoleEnum
from app.models.user import User
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository

logger = logging.getLogger("agri_smart.seeds.super_admin")


def seed_super_admin(db: Session, password_override: Optional[str] = None) -> dict:
    """
    Idempotently seeds the root SUPER_ADMIN user.

    Reads configuration from application settings (environment variables).
    Uses Argon2id for password hashing.
    Skips creation if an administrator already exists.
    Never logs or exposes plaintext passwords.
    """
    logger.info("Checking Super Admin existence...")

    # Validate Super Admin password configuration
    password = password_override or settings.SUPER_ADMIN_PASSWORD
    if not password:
        raise ValueError(
            "SUPER_ADMIN_PASSWORD is not set in the environment or configuration. "
            "Please configure SUPER_ADMIN_PASSWORD before running the seed."
        )

    # 1. Fetch SUPER_ADMIN role
    super_admin_role = RoleRepository.get_by_name(db, RoleEnum.SUPER_ADMIN.value)
    if not super_admin_role:
        # Create role if missing
        super_admin_role = RoleRepository.create(
            db,
            name=RoleEnum.SUPER_ADMIN.value,
            description="Complete system administration",
            is_active=True
        )
        logger.info("Created missing SUPER_ADMIN role.")

    # 2. Check if a user with SUPER_ADMIN role already exists
    existing_admins = UserRepository.get_users_by_role_name(db, RoleEnum.SUPER_ADMIN.value)
    if existing_admins:
        admin_user = existing_admins[0]
        logger.info(
            "SUPER_ADMIN user already exists (User ID: %s, Mobile: %s). Skipping creation.",
            admin_user.id,
            admin_user.mobile_number
        )
        return {
            "created": False,
            "user_id": str(admin_user.id),
            "mobile_number": admin_user.mobile_number,
            "message": "SUPER_ADMIN already exists. Skipped creation."
        }

    # 3. Check if user with configured mobile already exists
    mobile = settings.SUPER_ADMIN_MOBILE
    existing_by_mobile = UserRepository.get_by_mobile(db, mobile)
    if existing_by_mobile:
        # Assign SUPER_ADMIN role if missing
        UserRepository.assign_role(db, existing_by_mobile.id, super_admin_role.id)
        logger.info(
            "User with mobile %s exists. Assigned SUPER_ADMIN role (User ID: %s).",
            mobile,
            existing_by_mobile.id
        )
        return {
            "created": False,
            "user_id": str(existing_by_mobile.id),
            "mobile_number": existing_by_mobile.mobile_number,
            "message": "Assigned SUPER_ADMIN role to existing user."
        }

    # 4. Create new Super Admin user
    password_hash = get_password_hash(password)
    user = UserRepository.create(
        db,
        full_name=settings.SUPER_ADMIN_NAME,
        mobile_number=mobile,
        email=settings.SUPER_ADMIN_EMAIL,
        password_hash=password_hash,
        is_active=True
    )

    # 5. Assign SUPER_ADMIN role
    UserRepository.assign_role(db, user.id, super_admin_role.id)

    logger.info(
        "Successfully created root SUPER_ADMIN user (User ID: %s, Mobile: %s).",
        user.id,
        user.mobile_number
    )
    return {
        "created": True,
        "user_id": str(user.id),
        "mobile_number": user.mobile_number,
        "message": "SUPER_ADMIN user created successfully."
    }
