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
        "maintenance_plan_view",
        "qualification_plan_view",
        "tasks_view",
        "audit_view",
    },
}


def get_permission_rows():
    return PERMISSION_SECTIONS


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
