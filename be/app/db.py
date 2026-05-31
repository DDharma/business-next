from functools import lru_cache

from supabase import Client, create_client

from .config import get_settings


@lru_cache
def get_db() -> Client:
    s = get_settings()
    return create_client(s.supabase_url, s.supabase_key)


def count_customers() -> int:
    res = (
        get_db()
        .table("customers")
        .select("id", count="exact")
        .limit(1)
        .execute()
    )
    return res.count or 0


def ping() -> bool:
    try:
        get_db().table("customers").select("id").limit(1).execute()
        return True
    except Exception:
        return False
