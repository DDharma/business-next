# Wipe all chats and messages from Supabase. Customers/transactions/products untouched.
# Usage:  python scripts/clear_chats.py        (prompts)
#         python scripts/clear_chats.py --yes  (no prompt)

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db import get_db  # noqa: E402

ALL_FILTER_UUID = "00000000-0000-0000-0000-000000000000"


def _count(db, table: str) -> int:
    return db.table(table).select("id", count="exact").limit(1).execute().count or 0


def main(skip_confirm: bool = False) -> None:
    db = get_db()

    chats = _count(db, "chats")
    messages = _count(db, "messages")
    print(f"Found {chats} chats, {messages} messages.")

    if chats == 0 and messages == 0:
        print("Nothing to delete.")
        return

    if not skip_confirm:
        ans = input("Delete all chats + messages? [y/N] ").strip().lower()
        if ans not in ("y", "yes"):
            print("Aborted.")
            return

    print("Deleting messages …")
    db.table("messages").delete().neq("id", ALL_FILTER_UUID).execute()
    print("Deleting chats …")
    db.table("chats").delete().neq("id", ALL_FILTER_UUID).execute()

    print(f"Done. Now {_count(db, 'chats')} chats, {_count(db, 'messages')} messages.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--yes", action="store_true", help="skip confirmation")
    args = p.parse_args()
    main(skip_confirm=args.yes)
