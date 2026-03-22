from contextlib import contextmanager
from contextvars import ContextVar


_current_user = ContextVar("audit_current_user", default=None)
_current_change_reason = ContextVar("audit_change_reason", default="")


def get_current_audit_user():
    return _current_user.get()


def get_current_change_reason() -> str:
    return _current_change_reason.get() or ""


@contextmanager
def audit_context(*, user=None, change_reason: str = ""):
    user_token = _current_user.set(user)
    reason_token = _current_change_reason.set(change_reason or "")
    try:
        yield
    finally:
        _current_user.reset(user_token)
        _current_change_reason.reset(reason_token)


def set_change_reason(instance, reason: str):
    instance._audit_change_reason = reason or ""
