from dataclasses import dataclass

from django.contrib.auth.models import Group, Permission
from django.utils.translation import gettext_lazy as _

from audit.models import AuditLog

from .roles import (
    ROLE_ADMIN,
    ROLE_NAMES,
    ROLE_USER,
    ROLE_VIEWER,
    get_primary_role_label,
    get_role_label,
    get_user_code,
    get_user_display_name,
)


@dataclass(frozen=True)
class PermissionRow:
    key: str
    label: str
    permission_codes: tuple[tuple[str, str], ...]


PERMISSION_SECTIONS = [
    (
        "geraete",
        "Geräte",
        [
            PermissionRow("assets_view", "Geräte anzeigen", (("assets", "view_asset"),)),
            PermissionRow("assets_add", "Geräte anlegen", (("assets", "add_asset"),)),
            PermissionRow("assets_change", "Geräte bearbeiten", (("assets", "change_asset"),)),
        ],
    ),
    (
        "vertraege",
        "Verträge",
        [
            PermissionRow("contracts_view", "Verträge anzeigen", (("contracts", "view_maintenancecontract"),)),
            PermissionRow("contracts_add", "Verträge anlegen", (("contracts", "add_maintenancecontract"),)),
            PermissionRow("contracts_change", "Verträge bearbeiten", (("contracts", "change_maintenancecontract"),)),
            PermissionRow("contracts_delete", "Verträge löschen", (("contracts", "delete_maintenancecontract"),)),
        ],
    ),
    (
        "wartung",
        "Wartung",
        [
            PermissionRow("maintenance_plan_view", "Wartungspläne anzeigen", (("maintenance", "view_maintenanceplan"),)),
            PermissionRow("maintenance_plan_add", "Wartungspläne anlegen", (("maintenance", "add_maintenanceplan"),)),
            PermissionRow("maintenance_plan_change", "Wartungspläne bearbeiten", (("maintenance", "change_maintenanceplan"),)),
            PermissionRow(
                "maintenance_event_manage",
                "Wartungsereignisse erfassen / bearbeiten",
                (
                    ("maintenance", "add_maintenanceevent"),
                    ("maintenance", "change_maintenanceevent"),
                ),
            ),
        ],
    ),
    (
        "qualifizierung",
        "Qualifizierung",
        [
            PermissionRow("qualification_plan_view", "Qualifizierungspläne anzeigen", (("qualification", "view_qualificationplan"),)),
            PermissionRow("qualification_plan_add", "Qualifizierungspläne anlegen", (("qualification", "add_qualificationplan"),)),
            PermissionRow("qualification_plan_change", "Qualifizierungspläne bearbeiten", (("qualification", "change_qualificationplan"),)),
            PermissionRow(
                "qualification_event_manage",
                "Qualifizierungsereignisse erfassen / bearbeiten",
                (
                    ("qualification", "add_qualificationevent"),
                    ("qualification", "change_qualificationevent"),
                ),
            ),
        ],
    ),
    (
        "massnahmen",
        "Maßnahmen",
        [
            PermissionRow("tasks_view", "Maßnahmen anzeigen", (("tasks", "view_task"),)),
            PermissionRow("tasks_add", "Maßnahmen anlegen", (("tasks", "add_task"),)),
            PermissionRow("tasks_change", "Maßnahmen bearbeiten", (("tasks", "change_task"),)),
        ],
    ),
    (
        "audit",
        "Audit",
        [
            PermissionRow("audit_view", "Audittrail anzeigen", (("audit", "view_auditlog"),)),
        ],
    ),
    (
        "administration",
        "Administration",
        [
            PermissionRow("settings_manage", "Einstellungen verwalten", (("core", "change_systemsettings"),)),
            PermissionRow(
                "users_manage",
                "Benutzer verwalten",
                (
                    ("auth", "view_user"),
                    ("auth", "add_user"),
                    ("auth", "change_user"),
                    ("accounts", "view_userprofile"),
                    ("accounts", "change_userprofile"),
                ),
            ),
            PermissionRow(
                "roles_manage",
                "Rollen und Rechte verwalten",
                (
                    ("auth", "view_group"),
                    ("auth", "change_group"),
                ),
            ),
        ],
    ),
]


ROLE_PERMISSION_DEFAULTS = {
    ROLE_ADMIN: {row.key for _, _, rows in PERMISSION_SECTIONS for row in rows},
    ROLE_USER: {
        "assets_view",
        "assets_add",
        "assets_change",
        "contracts_view",
        "contracts_add",
        "contracts_change",
        "maintenance_plan_view",
        "maintenance_plan_add",
        "maintenance_plan_change",
        "maintenance_event_manage",
        "qualification_plan_view",
        "qualification_plan_add",
        "qualification_plan_change",
        "qualification_event_manage",
        "tasks_view",
        "tasks_add",
        "tasks_change",
        "audit_view",
    },
    ROLE_VIEWER: {
        "assets_view",
        "contracts_view",
        "maintenance_plan_view",
        "qualification_plan_view",
        "tasks_view",
        "audit_view",
    },
}


def get_permission_rows():
    return PERMISSION_SECTIONS


def permission_codes_to_names(permission_codes: tuple[tuple[str, str], ...]) -> tuple[str, ...]:
    return tuple(f"{app_label}.{codename}" for app_label, codename in permission_codes)


PERMISSION_ROW_MAP = {
    row.key: row
    for _, _, rows in PERMISSION_SECTIONS
    for row in rows
}

PERMISSION_NAME_MAP = {
    row_key: permission_codes_to_names(row.permission_codes)
    for row_key, row in PERMISSION_ROW_MAP.items()
}

ASSETS_VIEW = PERMISSION_NAME_MAP["assets_view"]
ASSETS_ADD = PERMISSION_NAME_MAP["assets_add"]
ASSETS_CHANGE = PERMISSION_NAME_MAP["assets_change"]

CONTRACTS_VIEW = PERMISSION_NAME_MAP["contracts_view"]
CONTRACTS_ADD = PERMISSION_NAME_MAP["contracts_add"]
CONTRACTS_CHANGE = PERMISSION_NAME_MAP["contracts_change"]
CONTRACTS_DELETE = PERMISSION_NAME_MAP["contracts_delete"]

MAINTENANCE_PLAN_VIEW = PERMISSION_NAME_MAP["maintenance_plan_view"]
MAINTENANCE_PLAN_ADD = PERMISSION_NAME_MAP["maintenance_plan_add"]
MAINTENANCE_PLAN_CHANGE = PERMISSION_NAME_MAP["maintenance_plan_change"]
MAINTENANCE_EVENT_MANAGE = PERMISSION_NAME_MAP["maintenance_event_manage"]
MAINTENANCE_EVENT_ADD = ("maintenance.add_maintenanceevent",)
MAINTENANCE_EVENT_CHANGE = ("maintenance.change_maintenanceevent",)

QUALIFICATION_PLAN_VIEW = PERMISSION_NAME_MAP["qualification_plan_view"]
QUALIFICATION_PLAN_ADD = PERMISSION_NAME_MAP["qualification_plan_add"]
QUALIFICATION_PLAN_CHANGE = PERMISSION_NAME_MAP["qualification_plan_change"]
QUALIFICATION_EVENT_MANAGE = PERMISSION_NAME_MAP["qualification_event_manage"]
QUALIFICATION_EVENT_ADD = ("qualification.add_qualificationevent",)
QUALIFICATION_EVENT_CHANGE = ("qualification.change_qualificationevent",)

TASKS_VIEW = PERMISSION_NAME_MAP["tasks_view"]
TASKS_ADD = PERMISSION_NAME_MAP["tasks_add"]
TASKS_CHANGE = PERMISSION_NAME_MAP["tasks_change"]

AUDIT_VIEW = PERMISSION_NAME_MAP["audit_view"]
SETTINGS_MANAGE = PERMISSION_NAME_MAP["settings_manage"]
USERS_MANAGE = PERMISSION_NAME_MAP["users_manage"]
ROLES_MANAGE = PERMISSION_NAME_MAP["roles_manage"]

DASHBOARD_VIEW_PERMISSIONS = tuple(
    sorted(
        {
            *ASSETS_VIEW,
            *CONTRACTS_VIEW,
            *MAINTENANCE_PLAN_VIEW,
            *QUALIFICATION_PLAN_VIEW,
            *TASKS_VIEW,
            *AUDIT_VIEW,
            *USERS_MANAGE,
            *SETTINGS_MANAGE,
        }
    )
)

EDITOR_AREA_PERMISSIONS = tuple(
    sorted(
        {
            *ASSETS_ADD,
            *ASSETS_CHANGE,
            *CONTRACTS_ADD,
            *CONTRACTS_CHANGE,
            *CONTRACTS_DELETE,
            *MAINTENANCE_PLAN_ADD,
            *MAINTENANCE_PLAN_CHANGE,
            *MAINTENANCE_EVENT_MANAGE,
            *QUALIFICATION_PLAN_ADD,
            *QUALIFICATION_PLAN_CHANGE,
            *QUALIFICATION_EVENT_MANAGE,
            *TASKS_ADD,
            *TASKS_CHANGE,
            *SETTINGS_MANAGE,
            *USERS_MANAGE,
            *ROLES_MANAGE,
        }
    )
)


def get_permission_names_for_row(row_key: str) -> tuple[str, ...]:
    return PERMISSION_NAME_MAP[row_key]


def get_role_groups():
    groups = {}
    for role_name in ROLE_NAMES:
        groups[role_name], _ = Group.objects.get_or_create(name=role_name)
    return groups


def get_permission_objects_for_row(row: PermissionRow):
    permissions = []
    for app_label, codename in row.permission_codes:
        permissions.append(Permission.objects.get(content_type__app_label=app_label, codename=codename))
    return permissions


def get_user_permission_names(user) -> set[str]:
    if not getattr(user, "is_authenticated", False):
        return set()

    cached = getattr(user, "_mainty_permission_names_cache", None)
    if cached is not None:
        return cached

    direct_permissions = user.user_permissions.values_list("content_type__app_label", "codename")
    group_permissions = Permission.objects.filter(group__user=user).values_list("content_type__app_label", "codename")
    permissions = {
        f"{app_label}.{codename}"
        for app_label, codename in [*direct_permissions, *group_permissions]
    }
    setattr(user, "_mainty_permission_names_cache", permissions)
    return permissions


def invalidate_user_permission_cache(user):
    if hasattr(user, "_mainty_permission_names_cache"):
        delattr(user, "_mainty_permission_names_cache")


def user_has_permissions(user, permissions: tuple[str, ...] | list[str] | set[str], *, require_all: bool = True) -> bool:
    if getattr(user, "is_superuser", False):
        return True

    if not getattr(user, "is_authenticated", False):
        return False

    required_permissions = tuple(permissions)
    if not required_permissions:
        return True

    assigned_permissions = get_user_permission_names(user)
    if require_all:
        return all(permission_name in assigned_permissions for permission_name in required_permissions)
    return any(permission_name in assigned_permissions for permission_name in required_permissions)


def user_has_row_permission(user, row_key: str) -> bool:
    return user_has_permissions(user, get_permission_names_for_row(row_key))


def get_template_permission_context(user) -> dict:
    return {
        "can_view_dashboard": user_has_permissions(user, DASHBOARD_VIEW_PERMISSIONS, require_all=False),
        "can_access_internal_area": user_has_permissions(user, DASHBOARD_VIEW_PERMISSIONS, require_all=False),
        "can_access_editor_area": user_has_permissions(user, EDITOR_AREA_PERMISSIONS, require_all=False),
        "can_view_assets": user_has_permissions(user, ASSETS_VIEW),
        "can_add_assets": user_has_permissions(user, ASSETS_ADD),
        "can_change_assets": user_has_permissions(user, ASSETS_CHANGE),
        "can_view_contracts": user_has_permissions(user, CONTRACTS_VIEW),
        "can_add_contracts": user_has_permissions(user, CONTRACTS_ADD),
        "can_change_contracts": user_has_permissions(user, CONTRACTS_CHANGE),
        "can_delete_contracts": user_has_permissions(user, CONTRACTS_DELETE),
        "can_view_maintenance_plans": user_has_permissions(user, MAINTENANCE_PLAN_VIEW),
        "can_add_maintenance_plans": user_has_permissions(user, MAINTENANCE_PLAN_ADD),
        "can_change_maintenance_plans": user_has_permissions(user, MAINTENANCE_PLAN_CHANGE),
        "can_add_maintenance_events": user_has_permissions(user, MAINTENANCE_EVENT_ADD),
        "can_change_maintenance_events": user_has_permissions(user, MAINTENANCE_EVENT_CHANGE),
        "can_view_qualification_plans": user_has_permissions(user, QUALIFICATION_PLAN_VIEW),
        "can_add_qualification_plans": user_has_permissions(user, QUALIFICATION_PLAN_ADD),
        "can_change_qualification_plans": user_has_permissions(user, QUALIFICATION_PLAN_CHANGE),
        "can_add_qualification_events": user_has_permissions(user, QUALIFICATION_EVENT_ADD),
        "can_change_qualification_events": user_has_permissions(user, QUALIFICATION_EVENT_CHANGE),
        "can_view_tasks": user_has_permissions(user, TASKS_VIEW),
        "can_add_tasks": user_has_permissions(user, TASKS_ADD),
        "can_change_tasks": user_has_permissions(user, TASKS_CHANGE),
        "can_view_audit": user_has_permissions(user, AUDIT_VIEW),
        "can_manage_settings": user_has_permissions(user, SETTINGS_MANAGE),
        "can_manage_users": user_has_permissions(user, USERS_MANAGE),
        "can_manage_roles": user_has_permissions(user, ROLES_MANAGE),
    }


def build_permissions_matrix():
    groups = get_role_groups()
    matrix = []
    for section_key, section_label, rows in PERMISSION_SECTIONS:
        matrix_rows = []
        for row in rows:
            permission_objects = get_permission_objects_for_row(row)
            permission_ids = {permission.id for permission in permission_objects}
            group_states = {
                role_name: groups[role_name].permissions.filter(id__in=permission_ids).count() == len(permission_ids)
                for role_name in ROLE_NAMES
            }
            matrix_rows.append(
                {
                    "key": row.key,
                    "label": row.label,
                    "permissions": permission_objects,
                    "group_states": group_states,
                    "role_states": [{"name": role_name, "enabled": group_states[role_name]} for role_name in ROLE_NAMES],
                }
            )
        matrix.append({"key": section_key, "label": section_label, "rows": matrix_rows})
    return matrix


def get_role_columns():
    return [{"name": role_name, "label": get_role_label(role_name)} for role_name in ROLE_NAMES]


def assign_default_role_permissions():
    groups = get_role_groups()
    row_map = {row.key: row for _, _, rows in PERMISSION_SECTIONS for row in rows}
    for role_name, row_keys in ROLE_PERMISSION_DEFAULTS.items():
        permission_ids = []
        for row_key in row_keys:
            permission_ids.extend(permission.id for permission in get_permission_objects_for_row(row_map[row_key]))
        groups[role_name].permissions.set(sorted(set(permission_ids)))


def update_group_permissions_from_matrix(post_data):
    groups = get_role_groups()
    row_map = {row.key: row for _, _, rows in PERMISSION_SECTIONS for row in rows}
    changes = []

    for role_name in ROLE_NAMES:
        group = groups[role_name]
        for row_key, row in row_map.items():
            permission_objects = get_permission_objects_for_row(row)
            permission_ids = {permission.id for permission in permission_objects}
            should_have = post_data.get(f"perm__{row_key}__{role_name}") == "on"
            currently_has = group.permissions.filter(id__in=permission_ids).count() == len(permission_ids)
            if should_have == currently_has:
                continue

            if should_have:
                group.permissions.add(*permission_objects)
                changes.append((group, row.label, "added"))
            else:
                group.permissions.remove(*permission_objects)
                changes.append((group, row.label, "removed"))

    return changes


def log_permission_matrix_changes(user, changes):
    if not changes:
        return

    user_display = ""
    user_role = ""
    if user and getattr(user, "is_authenticated", False):
        user_display = get_user_display_name(user)
        user_code = get_user_code(user)
        if user_code:
            user_display = f"{user_display} [{user_code}]"
        user_role = get_primary_role_label(user) or ""

    entries = []
    for group, row_label, change_type in changes:
        entries.append(
            AuditLog(
                user=user if getattr(user, "is_authenticated", False) else None,
                user_display_snapshot=user_display,
                user_role_snapshot=user_role,
                action=AuditLog.ACTION_UPDATE,
                model_name=str(_("Rolle")),
                object_id=str(group.pk),
                object_repr=str(get_role_label(group.name) or group.name),
                field_name=row_label,
                old_value=str(_("Ja")) if change_type == "removed" else str(_("Nein")),
                new_value=str(_("Ja")) if change_type == "added" else str(_("Nein")),
                change_reason="",
            )
        )
    AuditLog.objects.bulk_create(entries)
