import logging
from sqlalchemy.orm import Session
from app.models.enums import RoleEnum, ROLE_DESCRIPTIONS
from app.repositories.role_repository import RoleRepository

logger = logging.getLogger("agri_smart.seeds.roles")


def seed_roles(db: Session) -> dict:
    """
    Idempotently seeds default system roles if they do not exist.
    Returns a summary dictionary of created and existing roles.
    """
    logger.info("Starting role seeding process...")
    created_roles = []
    existing_roles = []

    for role_enum in RoleEnum:
        role_name = role_enum.value
        description = ROLE_DESCRIPTIONS.get(role_enum, "")
        
        role = RoleRepository.get_by_name(db, role_name)
        if not role:
            role = RoleRepository.create(
                db,
                name=role_name,
                description=description,
                is_active=True
            )
            created_roles.append(role_name)
            logger.info("Created role: %s", role_name)
        else:
            existing_roles.append(role_name)
            logger.info("Role already exists: %s", role_name)

    logger.info(
        "Role seeding completed. Created: %d, Existing: %d",
        len(created_roles),
        len(existing_roles)
    )
    return {
        "created": created_roles,
        "existing": existing_roles
    }
