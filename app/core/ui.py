def count_active_filters(params, *, ignored_keys: set[str] | None = None) -> int:
    ignored = {"page"}
    if ignored_keys:
        ignored |= set(ignored_keys)
    return sum(1 for key, value in params.items() if key not in ignored and str(value).strip())
