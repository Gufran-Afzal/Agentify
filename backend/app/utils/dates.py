from datetime import datetime, timezone

def utc_now_iso() -> str:
    """Return the current UTC timestamp formatted as ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()
