from .permissions import get_template_permission_context
from .roles import (
    ROLE_ADMIN,
    ROLE_USER,
    ROLE_VIEWER,
    get_primary_role_label,
    get_user_code,
    get_user_role_labels,
)


def role_context(request):
    user = request.user
    context = {
        "ROLE_ADMIN": ROLE_ADMIN,
        "ROLE_USER": ROLE_USER,
        "ROLE_VIEWER": ROLE_VIEWER,
        "current_user_role": get_primary_role_label(user),
        "current_user_roles": get_user_role_labels(user),
        "current_user_code": get_user_code(user),
    }
    context.update(get_template_permission_context(user))
    return context
