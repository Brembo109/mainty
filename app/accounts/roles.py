from django.utils.translation import gettext_lazy as _


ROLE_ADMIN = "Admin"
ROLE_USER = "User"
ROLE_EDITOR = ROLE_USER
ROLE_VIEWER = "Viewer"
LEGACY_ROLE_EDITOR = "Editor"

ROLE_NAMES = (
    ROLE_ADMIN,
    ROLE_USER,
    ROLE_VIEWER,
)

ROLE_LABELS = {
    ROLE_ADMIN: _("Admin"),
    ROLE_USER: _("User"),
    ROLE_VIEWER: _("Viewer"),
}


def normalize_role_name(role_name: str) -> str:
    normalized = role_name.strip().lower()
    if normalized == LEGACY_ROLE_EDITOR.lower():
        return ROLE_USER
    for candidate in ROLE_NAMES:
        if candidate.lower() == normalized:
            return candidate
    raise ValueError(f"Unknown role: {role_name}")


def get_user_role_names(user) -> list[str]:
    if not getattr(user, "is_authenticated", False):
        return []
    if getattr(user, "is_superuser", False):
        return [ROLE_ADMIN]

    assigned_roles = {
        normalize_role_name(name)
        for name in user.groups.values_list("name", flat=True)
        if name in ROLE_NAMES or name == LEGACY_ROLE_EDITOR
    }
    return [role_name for role_name in ROLE_NAMES if role_name in assigned_roles]


def get_primary_role(user) -> str | None:
    roles = get_user_role_names(user)
    if roles:
        return roles[0]

    profile = getattr(user, "profile", None)
    if profile and profile.role:
        return normalize_role_name(profile.role)
    return None


def get_role_label(role_name: str | None):
    if role_name is None:
        return None
    return ROLE_LABELS.get(role_name, role_name)


def get_user_role_labels(user) -> list:
    return [get_role_label(role_name) for role_name in get_user_role_names(user)]


def get_primary_role_label(user):
    return get_role_label(get_primary_role(user))


def get_user_code(user) -> str:
    profile = getattr(user, "profile", None)
    return getattr(profile, "user_code", "") or ""


def get_user_display_name(user) -> str:
    full_name = user.get_full_name().strip()
    return full_name or user.username


def get_user_display_with_role(user) -> str:
    if not getattr(user, "is_authenticated", False):
        return str(_("System"))

    display_name = get_user_display_name(user)
    user_code = get_user_code(user)
    role_label = get_primary_role_label(user)

    if user_code:
        display_name = f"{display_name} [{user_code}]"
    if role_label:
        display_name = f"{display_name} - {role_label}"
    return display_name


def has_role(user, *role_names: str) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False

    normalized = {normalize_role_name(role_name) for role_name in role_names}
    return any(role_name in normalized for role_name in get_user_role_names(user))


def can_manage_users(user) -> bool:
    return has_role(user, ROLE_ADMIN)


def can_access_editor_area(user) -> bool:
    return has_role(user, ROLE_ADMIN, ROLE_USER)


def can_access_internal_area(user) -> bool:
    return has_role(user, ROLE_ADMIN, ROLE_USER, ROLE_VIEWER)
