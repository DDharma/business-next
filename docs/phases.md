# Build Phases

Tracker for the build. Update checkboxes as each item lands. `[ ]` = todo, `[~]` = in progress, `[x]` = done.

---

## Phase 1 — Foundation

Goal: data + LLM connectivity + skeletons in place. Nothing user-facing yet.

- [ ] **P1.1** Apply schema to Supabase (`scripts/apply_schema.sql`) — *user runs in Supabase SQL Editor*
- [x] **P1.2** Rename `be/qpp` → `be/app`; create subfolders (`nodes/`, `tools/`, `prompts/`, `tests/`, `scripts/`)
- [x] **P1.3** Populate `be/requirements.txt`
- [x] **P1.4** `app/config.py` — env loading (SUPABASE_URL, SUPABASE_KEY, LM_STUDIO_URL, LM_STUDIO_MODEL)
- [x] **P1.5** `app/llm.py` — `ChatOpenAI(base_url, model)` factory *(smoke test pending — needs LM Studio running)*
- [x] **P1.6** `app/db.py` — Supabase client singleton + `count_customers`, `ping`
- [x] **P1.7** `app/seed.py` — Faker seeder (400 customers, 12mo transactions, 4 products, ~15% prospect cluster)
- [ ] **P1.8** Run seeder; eyeball counts and a sample customer with transactions — *user runs after P1.1*
- [x] **P1.9** `app/schemas.py` — Pydantic: `IntentSchema`, `CustomerCard`, `StepEvent`, `ScoreFactor`
- [x] **P1.10** FastAPI skeleton (`app/main.py`) with a `/health` endpoint that returns LM Studio + Supabase reachability

**Exit criteria:** `curl /health` returns `{ supabase: ok, lm_studio: ok }` and `select count(*) from customers` returns 400.

---

## Phase 2 — Agent core (no FE)

Goal: end-to-end agent via CLI. The graph runs, scores, drafts messages, prints results.

- [x] **P2.1** `app/tools/scoring.py` — weighted heuristic (7 factors) + per-factor breakdown
- [x] **P2.2** `tests/test_scoring.py` — unit tests for the scorer (6 tests passing)
- [x] **P2.3** `app/tools/customer_repo.py` — `get_candidates(filters)`, `get_recent_transactions`, `get_products`
- [x] **P2.4** `app/tools/product_match.py` — rule-based product fit (tier preference, eligibility checks)
- [x] **P2.5** `tests/test_product_match.py` (6 tests passing)
- [x] **P2.6** `app/state.py` — `GraphState` TypedDict
- [x] **P2.7** `app/nodes/parse_intent.py` — LLM JSON output via with_structured_output, multi-method fallback
- [x] **P2.8** `app/nodes/retrieve.py`
- [x] **P2.9** `app/nodes/score.py`
- [x] **P2.10** `app/nodes/recommend.py`
- [x] **P2.11** `app/nodes/draft_messages.py` — per-customer LLM call
- [x] **P2.12** `app/graph.py` — StateGraph + conditional edge (rewrite_message branch)
- [x] **P2.13** `scripts/run_cli.py` — invoke graph, print events + cards

**Smoke test result:** `python scripts/run_cli.py "find 3 high-value personal-loan prospects in Mumbai"` runs in ~27s and produces 3 cards with score breakdowns and personalized WhatsApp drafts.

**Exit criteria:** `python scripts/run_cli.py "find 5 high-value personal-loan prospects in Mumbai"` prints 5 ranked customers with score breakdown + a draft WhatsApp message each.

---

## Phase 3 — Streaming + FE

Goal: clickable UI that streams reasoning live.

- [x] **P3.1** `app/events.py` — `EventBus` with thread-safe `queue.Queue` + async `stream()`
- [x] **P3.2** Emitter wired through all 5 nodes (already in place from P2)
- [x] **P3.3** `app/main.py` — `POST /chat` SSE endpoint via `sse-starlette`
- [x] **P3.4** `POST /chats`, `GET /chats`, `GET /chats/{id}` REST endpoints
- [x] **P3.5** Persist user message + assistant cards (in `metadata.cards`) to `messages` table
- [x] **P3.6** FE already scaffolded (Next 16.2.6, React 19, Tailwind v4, shadcn radix-sera style)
- [x] **P3.7** Added shadcn components: input, card, scroll-area, separator, badge, skeleton
- [x] **P3.8** `lib/types.ts` mirrors backend `StepEvent` + `CustomerCard`
- [x] **P3.9** `lib/sse.ts` — `fetch` + ReadableStream parser (POST-able SSE)
- [x] **P3.10** `hooks/use-chat-stream.ts` — owns stream lifecycle, exposes `events`, `cards`, `send()`, `reset()`
- [x] **P3.11** `components/chat-input.tsx`
- [x] **P3.12** `components/reasoning-log.tsx` — monospace terminal, autoscroll, color-coded events
- [x] **P3.13** `components/customer-card.tsx` — score pill, top 3 factors, message + copy button
- [x] **P3.14** `app/chat/[id]/page.tsx` + `app/page.tsx` + `components/chat-workspace.tsx` (two-pane)
- [x] **P3.15** Browser smoke test passed: SSE streams `chat_id → node_started/tool_call/tool_result/card... → done`, cards render live, persisted to Supabase

**Stack notes:**
- BE CORS allows `localhost:3000` and `localhost:3001`
- FE env: `NEXT_PUBLIC_API_URL` defaults to `http://localhost:8000`
- Dev: `cd be && uvicorn app.main:app --reload --port 8000` + `cd fe && pnpm dev`

**Exit criteria:** A user can type "find 5 high-value personal-loan prospects in Mumbai" in the browser and see the reasoning log fill in real-time, followed by 5 customer cards with copy-able WhatsApp drafts.

---

## Phase 4 — Polish & deliverables

Goal: ready to submit.

- [x] **P4.1** `components/chat-sidebar.tsx` — list chats, click to navigate, "New chat" button
- [x] **P4.2** `app/chat/[id]/page.tsx` — rehydrates cards + `metadata.events` + `duration_ms` via `getChat`
- [x] **P4.3** Auto-title chats from the first user message (first 80 chars)
- [x] **P4.4** Empty state (sample prompt cards) + loading skeletons + error banner + LM-Studio-down → fallback intent
- [x] **P4.5** Dark mode default, IDE excludes for `node_modules`/`.next` for clean DX
- [x] **P4.6** README.md — architecture diagram, execution flow, tool design, decisions, trade-offs, setup
- [x] **P4.7** Setup script in README: schema apply → seed → start LM Studio → start backend → start FE
- [x] **P4.8** Demo script — 3 flows scripted in README §"Demo scripts": (a) canonical PDF query, (b) refinement, (c) different product/city
- [ ] **P4.9** Record 5–10 min demo video — *user records*
- [x] **P4.10** Final code pass — comments only where non-obvious, no dead code

**Exit criteria met:** Repo is shippable. README runs end-to-end on a fresh machine. Three demo flows scripted. Demo video remains for the user to record.

## Bonus refactor (post-Phase 3) — SSE → NDJSON

After Phase 3 the user requested removing SSE in favor of a "normal chat" with NDJSON streaming. Implemented:

- BE: `/chat` switched from `EventSourceResponse` to `StreamingResponse(media_type="application/x-ndjson")`. One JSON-per-line. `sse-starlette` removed from `requirements.txt`.
- BE: `metadata.events` + `metadata.duration_ms` now persisted on the assistant message — enables collapsible "Thought for Xs · N cards" header to render from history without re-running the agent.
- FE: `lib/sse.ts` → `lib/stream.ts` (NDJSON parser). Layout refactored from two-pane workspace to ChatGPT-style sidebar + scrolling thread. Each assistant turn collapses reasoning into a one-liner (click to expand).

---

## Out of scope (parking lot)

- Cross-chat memory / user profiles
- Auth / multi-user
- WhatsApp Business API integration (we draft messages, not send them)
- Vector search over customer notes
- Model fine-tuning
- Caching / rate limiting
- Production deploy
