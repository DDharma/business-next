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

- [ ] **P2.1** `app/tools/scoring.py` — weighted heuristic (7 factors) + per-factor breakdown
- [ ] **P2.2** `tests/test_scoring.py` — unit tests for the scorer
- [ ] **P2.3** `app/tools/customer_repo.py` — `get_candidates(filters)` + `get_recent_transactions(customer_ids)`
- [ ] **P2.4** `app/tools/product_match.py` — rule-based product fit
- [ ] **P2.5** `tests/test_product_match.py`
- [ ] **P2.6** `app/state.py` — `GraphState` TypedDict
- [ ] **P2.7** `app/nodes/parse_intent.py` — LLM call with JSON output; retry-once on schema failure
- [ ] **P2.8** `app/nodes/retrieve.py`
- [ ] **P2.9** `app/nodes/score.py`
- [ ] **P2.10** `app/nodes/recommend.py`
- [ ] **P2.11** `app/nodes/draft_messages.py` — per-customer LLM call, parallel where safe
- [ ] **P2.12** `app/graph.py` — build StateGraph + conditional edge (rewrite_message branch)
- [ ] **P2.13** `scripts/run_cli.py` — invoke graph with a hardcoded prompt, print events + cards

**Exit criteria:** `python scripts/run_cli.py "find 5 high-value personal-loan prospects in Mumbai"` prints 5 ranked customers with score breakdown + a draft WhatsApp message each.

---

## Phase 3 — Streaming + FE

Goal: clickable UI that streams reasoning live.

- [ ] **P3.1** `app/events.py` — `EventEmitter` with per-request asyncio.Queue
- [ ] **P3.2** Wire emitter into all nodes (replace prints from Phase 2)
- [ ] **P3.3** `app/main.py` — `POST /chat` SSE endpoint using `sse-starlette`
- [ ] **P3.4** `app/main.py` — `POST /chats`, `GET /chats`, `GET /chats/{id}` REST endpoints
- [ ] **P3.5** Persist user message + assistant card payload to `messages` table
- [ ] **P3.6** Scaffold FE: `pnpm create next-app fe` (App Router, TS, Tailwind)
- [ ] **P3.7** `pnpm dlx shadcn@latest init` + add: button, input, card, scroll-area, separator, badge, skeleton, sonner
- [ ] **P3.8** `lib/types.ts` — mirror backend `StepEvent` + `CustomerCard`
- [ ] **P3.9** `lib/sse.ts` — `fetch` + ReadableStream parser
- [ ] **P3.10** `hooks/use-chat-stream.ts` — owns the stream lifecycle, exposes `events`, `cards`, `send()`
- [ ] **P3.11** `components/chat-input.tsx`
- [ ] **P3.12** `components/reasoning-log.tsx` — monospace, autoscroll, collapsible tool calls
- [ ] **P3.13** `components/customer-card.tsx` — score, top 3 factors, message + copy button
- [ ] **P3.14** `app/chat/[id]/page.tsx` — two-pane layout
- [ ] **P3.15** First end-to-end demo: type a prompt → reasoning streams → cards appear

**Exit criteria:** A user can type "find 5 high-value personal-loan prospects in Mumbai" in the browser and see the reasoning log fill in real-time, followed by 5 customer cards with copy-able WhatsApp drafts.

---

## Phase 4 — Polish & deliverables

Goal: ready to submit.

- [ ] **P4.1** `components/chat-sidebar.tsx` — list chats, click to navigate
- [ ] **P4.2** `app/chat/[id]/page.tsx` — rehydrate cards + reasoning from saved `metadata` on load
- [ ] **P4.3** Auto-title chats from the first user message
- [ ] **P4.4** Empty / loading / error states (no candidates, LM Studio down, etc.)
- [ ] **P4.5** Light visual polish (spacing, typography, dark mode default)
- [ ] **P4.6** README.md — architecture diagram, execution flow, tool design, decisions, trade-offs, setup
- [ ] **P4.7** Setup script in README: schema apply → seed → start LM Studio → start backend → start FE
- [ ] **P4.8** Demo script — 3 flows scripted: (a) initial prospecting, (b) refine ("only Mumbai, exclude existing loan holders"), (c) "rewrite message #3 friendlier"
- [ ] **P4.9** Record 5–10 min demo video
- [ ] **P4.10** Final code pass — comments only where non-obvious, no dead code

**Exit criteria:** Repo is shippable. README runs end-to-end on a fresh machine. Demo video covers 3 use cases.

---

## Out of scope (parking lot)

- Cross-chat memory / user profiles
- Auth / multi-user
- WhatsApp Business API integration (we draft messages, not send them)
- Vector search over customer notes
- Model fine-tuning
- Caching / rate limiting
- Production deploy
