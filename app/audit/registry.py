from django.contrib.auth import get_user_model

from accounts.models import UserProfile
from core.models import SystemSettings
from assets.models import Asset
from maintenance.models import MaintenanceEvent, MaintenancePlan
from qualification.models import QualificationEvent, QualificationPlan
from tasks.models import Task

User = get_user_model()

TRACKED_MODELS = (
    User,
    UserProfile,
    SystemSettings,
    Asset,
    MaintenancePlan,
    MaintenanceEvent,
    QualificationPlan,
    QualificationEvent,
    Task,
)

TRACKED_MODEL_NAMES = {model.__name__ for model in TRACKED_MODELS}
STATUS_LIKE_FIELDS = {"status", "is_active"}
IGNORED_AUDIT_FIELDS = {
    "singleton_enforcer",
    "password",
    "last_login",
    "date_joined",
    "is_staff",
    "is_superuser",
}


def get_tracked_model_choices():
    return [(model.__name__, model._meta.verbose_name.title()) for model in TRACKED_MODELS]


def get_tracked_model_map():
    return {model.__name__: model for model in TRACKED_MODELS}
