from core.models import SystemSettings
from assets.models import Asset
from maintenance.models import MaintenanceEvent, MaintenancePlan
from qualification.models import QualificationEvent, QualificationPlan
from tasks.models import Task


TRACKED_MODELS = (
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
IGNORED_AUDIT_FIELDS = {"singleton_enforcer"}


def get_tracked_model_choices():
    return [(model.__name__, model._meta.verbose_name.title()) for model in TRACKED_MODELS]


def get_tracked_model_map():
    return {model.__name__: model for model in TRACKED_MODELS}
