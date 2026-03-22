ROLE_ADMIN = "Admin"
ROLE_EDITOR = "Editor"
ROLE_VIEWER = "Viewer"

ROLE_NAMES = (
    ROLE_ADMIN,
    ROLE_EDITOR,
    ROLE_VIEWER,
)


def normalize_role_name(role_name: str) -> str:
    normalized = role_name.strip().lower()
    for candidate in ROLE_NAMES:
        if candidate.lower() == normalized:
            return candidate
    raise ValueError(f"Unknown role: {role_name}")


def get_user_role_names(user) -> list[str]:
    if not getattr(user, "is_authenticated", False):
        return []
    if getattr(user, "is_superuser", False):
        return [ROLE_ADMIN]

    assigned_roles = {name for name in user.groups.values_list("name", flat=True) if name in ROLE_NAMES}
    return [role_name for role_name in ROLE_NAMES if role_name in assigned_roles]


def get_primary_role(user) -> str | None:
    roles = get_user_role_names(user)
    return roles[0] if roles else None


def has_role(user, *role_names: str) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False

    normalized = {normalize_role_name(role_name) for role_name in role_names}
    return any(role_name in normalized for role_name in get_user_role_names(user))


def can_manage_users(user) -> bool:
    return has_role(user, ROLE_ADMIN)


def can_access_editor_area(user) -> bool:
    return has_role(user, ROLE_ADMIN, ROLE_EDITOR)


def can_access_internal_area(user) -> bool:
    return has_role(user, ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER)
