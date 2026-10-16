from typing import List, Set
from app.models.enums import RoleEnum

# Centralized Role-to-Scope Mapping
ROLE_SCOPES_MAP = {
    RoleEnum.SUPER_ADMIN.value: ["admin:manage", "farmer:manage", "trader:access", "driver:trip", "worker:profile"],
    RoleEnum.FARMER.value: ["farmer:manage"],
    RoleEnum.TRADER.value: ["trader:access"],
    RoleEnum.DRIVER.value: ["driver:trip"],
    RoleEnum.WORKER.value: ["worker:profile"],
}


def get_scopes_for_roles(roles: List[str]) -> List[str]:
    """
    Returns a deduplicated, sorted list of permission scopes for the given roles.
    """
    scopes: Set[str] = set()
    for role in roles:
        role_key = role.upper() if isinstance(role, str) else str(role)
        if role_key in ROLE_SCOPES_MAP:
            scopes.update(ROLE_SCOPES_MAP[role_key])
    return sorted(list(scopes))
