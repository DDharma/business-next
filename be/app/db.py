from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

from supabase import Client, create_client

from .config import get_settings
from .constants import SIDEBAR_CHAT_LIMIT


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


def create_chat(title: str) -> dict:
    return get_db().table("chats").insert({"title": title}).execute().data[0]


def get_chat(chat_id: str) -> dict | None:
    res = get_db().table("chats").select("*").eq("id", chat_id).limit(1).execute()
    return (res.data or [None])[0]


def list_chats(limit: int = SIDEBAR_CHAT_LIMIT) -> list[dict]:
    res = (
        get_db()
        .table("chats")
        .select("*")
        .order("updated_at", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data or []


def touch_chat(chat_id: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    get_db().table("chats").update({"updated_at": now}).eq("id", chat_id).execute()


def add_message(
    chat_id: str,
    role: str,
    content: str,
    metadata: dict[str, Any] | None = None,
) -> dict:
    payload = {
        "chat_id": chat_id,
        "role": role,
        "content": content,
        "metadata": metadata or {},
    }
    res = get_db().table("messages").insert(payload).execute()
    touch_chat(chat_id)
    return res.data[0]


def list_messages(chat_id: str) -> list[dict]:
    res = (
        get_db()
        .table("messages")
        .select("*")
        .eq("chat_id", chat_id)
        .order("created_at")
        .execute()
    )
    return res.data or []
