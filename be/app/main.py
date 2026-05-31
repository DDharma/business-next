from __future__ import annotations

import asyncio
import json
import time
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from . import db
from .config import get_settings
from .constants import CHAT_TITLE_MAX_LEN
from .events import EventBus
from .graph import build_graph


@asynccontextmanager
async def lifespan(_app: FastAPI):
    get_settings()
    _app.state.graph = build_graph()
    yield


app = FastAPI(title="Lakshya — Banking CRM Agent", version="0.1.0", lifespan=lifespan)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    s = get_settings()
    supabase_ok = db.ping()
    customers = db.count_customers() if supabase_ok else 0

    lm_studio_ok = False
    lm_studio_models: list[str] = []
    try:
        async with httpx.AsyncClient(timeout=3.0) as c:
            r = await c.get(f"{s.lm_studio_url}/models")
            if r.status_code == 200:
                lm_studio_ok = True
                lm_studio_models = [m.get("id") for m in r.json().get("data", []) if m.get("id")]
    except Exception:
        pass

    return {
        "supabase": "ok" if supabase_ok else "down",
        "customers": customers,
        "lm_studio": "ok" if lm_studio_ok else "down",
        "lm_studio_models": lm_studio_models,
        "configured_model": s.lm_studio_model,
    }


class ChatCreate(BaseModel):
    title: str | None = None


@app.post("/chats")
async def create_chat(body: ChatCreate) -> dict:
    title = (body.title or "New chat").strip()[:120] or "New chat"
    return db.create_chat(title)


@app.get("/chats")
async def list_chats() -> list[dict]:
    return db.list_chats()


@app.get("/chats/{chat_id}")
async def get_chat(chat_id: str) -> dict:
    chat = db.get_chat(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="chat not found")
    chat["messages"] = db.list_messages(chat_id)
    return chat


class ChatRequest(BaseModel):
    chat_id: str | None = None
    message: str = Field(..., min_length=1, max_length=2000)


def _history_for_graph(chat_id: str | None) -> list[dict]:
    if not chat_id:
        return []
    msgs = db.list_messages(chat_id)
    return [{"role": m["role"], "content": m["content"]} for m in msgs]


@app.post("/chat")
async def chat(req: ChatRequest):
    chat_id = req.chat_id or db.create_chat(req.message.strip()[:CHAT_TITLE_MAX_LEN])["id"]

    db.add_message(chat_id, role="user", content=req.message)
    history = _history_for_graph(chat_id)

    bus = EventBus()
    graph = app.state.graph

    async def run_graph() -> dict:
        state = {
            "chat_id": chat_id,
            "user_message": req.message,
            "history": history[:-1],
            "emit": bus.emit,
        }
        loop = asyncio.get_running_loop()
        try:
            return await loop.run_in_executor(None, lambda: graph.invoke(state))
        finally:
            bus.close()

    async def ndjson_generator():
        started = time.monotonic()
        yield json.dumps({"type": "chat_id", "chat_id": chat_id}) + "\n"

        task = asyncio.create_task(run_graph())
        cards: list[dict] = []
        collected_events: list[dict] = []
        last_error: str | None = None

        async for ev in bus.stream():
            ev_dict = ev.model_dump(exclude_none=True)
            collected_events.append(ev_dict)
            if ev.type == "card" and ev.card is not None:
                cards.append(ev.card.model_dump())
            if ev.type == "error":
                last_error = ev.message
            yield json.dumps(ev_dict, default=str) + "\n"

        try:
            await task
        except Exception as e:
            last_error = last_error or str(e)

        duration_ms = int((time.monotonic() - started) * 1000)
        summary = (
            f"{len(cards)} card(s) generated."
            if not last_error
            else f"Error: {last_error}"
        )
        db.add_message(
            chat_id,
            role="assistant",
            content=summary,
            metadata={
                "cards": cards,
                "events": collected_events,
                "duration_ms": duration_ms,
                "error": last_error,
            },
        )

        yield json.dumps({
            "type": "done",
            "chat_id": chat_id,
            "cards": len(cards),
            "duration_ms": duration_ms,
        }) + "\n"

    return StreamingResponse(
        ndjson_generator(),
        media_type="application/x-ndjson",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )
