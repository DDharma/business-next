from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .db import count_customers, ping as db_ping


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # warm singletons
    get_settings()
    yield


app = FastAPI(title="Banking CRM Agent", version="0.1.0", lifespan=lifespan)

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

    supabase_ok = db_ping()
    customers = count_customers() if supabase_ok else 0

    lm_studio_ok = False
    lm_studio_models: list[str] = []
    try:
        async with httpx.AsyncClient(timeout=3.0) as c:
            r = await c.get(f"{s.lm_studio_url}/models")
            if r.status_code == 200:
                lm_studio_ok = True
                data = r.json().get("data", [])
                lm_studio_models = [m.get("id") for m in data if m.get("id")]
    except Exception:
        pass

    return {
        "supabase": "ok" if supabase_ok else "down",
        "customers": customers,
        "lm_studio": "ok" if lm_studio_ok else "down",
        "lm_studio_models": lm_studio_models,
        "configured_model": s.lm_studio_model,
    }
