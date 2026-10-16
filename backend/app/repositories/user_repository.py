import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session, selectinload
from app.models.user import User
from app.models.role import Role
from app.models.user_role import UserRole
from app.models.enums import RoleEnum
from app.core.phone_utils import extract_search_variants


class UserRepository:
    """Repository for User database operations."""

    @staticmethod
    def get_by_id(db: Session, user_id: uuid.UUID, include_deleted: bool = False) -> Optional[User]:
        stmt = (
            select(User)
            .options(
                selectinload(User.user_roles).selectinload(UserRole.role)
            )
            .where(User.id == user_id)
        )
        if not include_deleted:
            stmt = stmt.where(User.is_deleted == False)
        return db.scalar(stmt)

    @staticmethod
    def get_by_mobile(db: Session, mobile_number: str) -> Optional[User]:
        variants = extract_search_variants(mobile_number)
        return db.scalar(
            select(User).where(User.mobile_number.in_(variants), User.is_deleted == False)
        )

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        return db.scalar(
            select(User).where(User.email == email.strip(), User.is_deleted == False)
        )

    @staticmethod
    def get_by_mobile_any(db: Session, mobile_number: str) -> Optional[User]:
        """Find user by mobile number regardless of deleted status (for uniqueness validation)."""
        variants = extract_search_variants(mobile_number)
        return db.scalar(
            select(User).where(User.mobile_number.in_(variants))
        )

    @staticmethod
    def get_by_email_any(db: Session, email: str) -> Optional[User]:
        """Find user by email regardless of deleted status (for uniqueness validation)."""
        return db.scalar(
            select(User).where(User.email == email.strip())
        )

    @staticmethod
    def get_by_identifier(db: Session, identifier: str) -> Optional[User]:
        """Lookup non-deleted user by email or mobile number."""
        clean = identifier.strip()
        variants = extract_search_variants(clean)
        stmt = (
            select(User)
            .options(
                selectinload(User.user_roles).selectinload(UserRole.role)
            )
            .where(
                (User.email == clean) | (User.mobile_number.in_(variants)),
                User.is_deleted == False
            )
        )
        return db.scalar(stmt)

    @staticmethod
    def create(
        db: Session,
        full_name: str,
        mobile_number: str,
        password_hash: str,
        email: Optional[str] = None,
        is_active: bool = True
    ) -> User:
        user = User(
            full_name=full_name,
            mobile_number=mobile_number,
            password_hash=password_hash,
            email=email,
            is_active=is_active
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def create_with_roles(
        db: Session,
        full_name: str,
        mobile_number: str,
        password_hash: str,
        email: Optional[str] = None,
        roles: Optional[List[Role]] = None,
        created_by: Optional[uuid.UUID] = None,
        is_active: bool = True
    ) -> User:
        """Transactionally create a user and assign roles."""
        user = User(
            full_name=full_name,
            mobile_number=mobile_number,
            password_hash=password_hash,
            email=email,
            is_active=is_active,
            created_by=created_by
        )
        db.add(user)
        db.flush()  # Generates user.id without committing

        if roles:
            for role in roles:
                user_role = UserRole(user_id=user.id, role_id=role.id)
                db.add(user_role)

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def assign_role(db: Session, user_id: uuid.UUID, role_id: uuid.UUID) -> UserRole:
        # Check if already assigned
        existing = db.scalar(
            select(UserRole).where(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id
            )
        )
        if existing:
            return existing

        user_role = UserRole(user_id=user_id, role_id=role_id)
        db.add(user_role)
        db.commit()
        db.refresh(user_role)
        db.expire_all()
        return user_role

    @staticmethod
    def get_users_by_role_name(db: Session, role_name: str) -> List[User]:
        stmt = (
            select(User)
            .join(UserRole, User.id == UserRole.user_id)
            .join(Role, UserRole.role_id == Role.id)
            .where(Role.name == role_name, User.is_deleted == False)
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def remove_role(db: Session, user_id: uuid.UUID, role_id: uuid.UUID) -> bool:
        """Removes a role assignment for a user."""
        user_role = db.scalar(
            select(UserRole).where(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id
            )
        )
        if user_role:
            db.delete(user_role)
            db.commit()
            db.expire_all()
            return True
        return False

    @staticmethod
    def list_users(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        role_name: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_deleted: Optional[bool] = None
    ) -> List[User]:
        stmt = (
            select(User)
            .options(
                selectinload(User.user_roles).selectinload(UserRole.role)
            )
        )

        if search:
            search_pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    User.full_name.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                    User.mobile_number.ilike(search_pattern)
                )
            )

        if role_name:
            stmt = stmt.join(UserRole, User.id == UserRole.user_id).join(Role, UserRole.role_id == Role.id).where(Role.name == role_name.upper())

        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)

        if is_deleted is not None:
            stmt = stmt.where(User.is_deleted == is_deleted)

        stmt = stmt.order_by(User.created_at.desc()).offset(skip).limit(limit)
        return list(db.scalars(stmt).unique().all())

    @staticmethod
    def count_users(
        db: Session,
        search: Optional[str] = None,
        role_name: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_deleted: Optional[bool] = None
    ) -> int:
        stmt = select(func.count(func.distinct(User.id)))

        if role_name:
            stmt = stmt.join(UserRole, User.id == UserRole.user_id).join(Role, UserRole.role_id == Role.id).where(Role.name == role_name.upper())

        if search:
            search_pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    User.full_name.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                    User.mobile_number.ilike(search_pattern)
                )
            )

        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)

        if is_deleted is not None:
            stmt = stmt.where(User.is_deleted == is_deleted)

        return db.scalar(stmt) or 0

    @staticmethod
    def count_active_super_admins(db: Session) -> int:
        """Counts total active, non-deleted users assigned the SUPER_ADMIN role."""
        stmt = (
            select(func.count(func.distinct(User.id)))
            .join(UserRole, User.id == UserRole.user_id)
            .join(Role, UserRole.role_id == Role.id)
            .where(
                Role.name == RoleEnum.SUPER_ADMIN.value,
                Role.is_active == True,
                User.is_active == True,
                User.is_deleted == False
            )
        )
        return db.scalar(stmt) or 0

    @staticmethod
    def update_profile(
        db: Session,
        user: User,
        full_name: Optional[str] = None,
        mobile_number: Optional[str] = None,
        email: Optional[str] = None,
        updated_by: Optional[uuid.UUID] = None
    ) -> User:
        now = datetime.now(timezone.utc)
        if full_name is not None:
            user.full_name = full_name
        if mobile_number is not None:
            user.mobile_number = mobile_number
        if email is not None:
            user.email = email
        user.updated_by = updated_by
        user.updated_at = now
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def set_active_status(
        db: Session,
        user: User,
        is_active: bool,
        updated_by: Optional[uuid.UUID] = None
    ) -> User:
        now = datetime.now(timezone.utc)
        user.is_active = is_active
        user.updated_by = updated_by
        user.updated_at = now
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def soft_delete(
        db: Session,
        user: User,
        deleted_by: Optional[uuid.UUID] = None
    ) -> User:
        now = datetime.now(timezone.utc)
        user.is_deleted = True
        user.is_active = False
        user.deleted_at = now
        user.deleted_by = deleted_by
        user.updated_at = now
        user.updated_by = deleted_by
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def restore(
        db: Session,
        user: User,
        restored_by: Optional[uuid.UUID] = None
    ) -> User:
        now = datetime.now(timezone.utc)
        user.is_deleted = False
        user.deleted_at = None
        user.deleted_by = None
        user.updated_at = now
        user.updated_by = restored_by
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def count(db: Session) -> int:
        return db.scalar(select(func.count(User.id)).where(User.is_deleted == False)) or 0
