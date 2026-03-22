from .roles import (
    ROLE_ADMIN,
    ROLE_EDITOR,
    ROLE_VIEWER,
    can_access_editor_area,
    can_manage_users,
    get_primary_role,
    get_user_role_names,
)


def role_context(request):
    user = request.user
    return {
        "ROLE_ADMIN": ROLE_ADMIN,
        "ROLE_EDITOR": ROLE_EDITOR,
        "ROLE_VIEWER": ROLE_VIEWER,
        "current_user_role": get_primary_role(user),
        "current_user_roles": get_user_role_names(user),
        "can_access_editor_area": can_access_editor_area(user),
        "can_manage_users": can_manage_users(user),
    }
