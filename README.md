# Banking CRM Agent

> Conversational, local-LLM-powered AI assistant for Bank Relationship Managers.
> Given a natural-language ask like *"find 5 high-value personal-loan prospects in Mumbai"*,
> the agent queries the bank's customer database, scores each candidate with an explainable
> heuristic, picks the best-fit product, and drafts a personalized WhatsApp pitch per customer.

This is the take-home assignment "Agentic AI for Banking CRM" (see
[`docs/Take-Home Assignment_ Agentic AI for Banking CRM-1.pdf`](docs/Take-Home%20Assignment_%20Agentic%20AI%20for%20Banking%20CRM-1.pdf)).

---

## Table of contents

1. [What it does](#what-it-does)
2. [Architecture](#architecture)
3. [Execution flow (end-to-end)](#execution-flow-end-to-end)
4. [Tool design](#tool-design)
5. [Key design decisions](#key-design-decisions)
6. [Trade-offs and limitations](#trade-offs-and-limitations)
7. [Setup and run](#setup-and-run)
8. [Demo scripts (3 flows)](#demo-scripts-3-flows)
9. [Project layout](#project-layout)
10. [Tests](#tests)
11. [What's next (parking lot)](#whats-next-parking-lot)

---

## What it does

An RM types in plain English. The system:

1. **Retrieves** relevant customers + their last 6 months of transactions from Postgres.
2. **Identifies** high-value candidates via deterministic SQL filters.
3. **Estimates conversion likelihood** with a 7-factor weighted heuristic — every score is
   explainable (per-factor breakdown ships in the response).
4. **Recommends** the best-fit product per customer using rule-based eligibility.
5. **Generates** a personalized WhatsApp message + opener per customer via a local LLM.
6. **Streams** every step to the UI live (NDJSON over POST) so the RM watches the agent think.

All chats are persisted; you can reopen one and the full reasoning trace + cards rehydrate.

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                         Browser  (Next.js 16 + shadcn)                 │
│                                                                        │
│  ┌──────────────┐   ┌──────────────────┐   ┌────────────────────────┐  │
│  │ Chat sidebar │   │ Reasoning summary│   │ Customer cards         │  │
│  │ + new chat   │   │ (collapsible)    │   │ score + factors + msg  │  │
│  └──────┬───────┘   └────────▲─────────┘   └──────────▲─────────────┘  │
│         │                    │                        │                │
│         │  POST /chat        │  NDJSON stream         │                │
└─────────┼────────────────────┼────────────────────────┼────────────────┘
          │                    │                        │
          ▼                    │                        │
┌──────────────────────────────┴────────────────────────┴────────────────┐
│                       FastAPI backend (Python)                         │
│                                                                        │
│   /chat (NDJSON)   /chats   /chats/{id}   /health                      │
│        │                                                               │
│        ▼                                                               │
│   ┌──────────────────────  LangGraph StateGraph  ──────────────────┐   │
│   │                                                                │   │
│   │   parse_intent ──► retrieve ──► score ──► recommend            │   │
│   │        │                                       │               │   │
│   │        │ (rewrite_message branch)              ▼               │   │
│   │        └──────────────────────────────► draft_messages         │   │
│   │                                                │               │   │
│   │   Each node emits typed StepEvent ─────────────┘               │   │
│   └────────────────────────────────────────────────────────────────┘   │
│         │                          │                                   │
└─────────┼──────────────────────────┼───────────────────────────────────┘
          │                          │
          ▼                          ▼
   ┌──────────────┐         ┌──────────────────────┐
   │  Supabase    │         │  LM Studio (local)   │
   │  Postgres    │         │  127.0.0.1:1234/v1   │
   │              │         │  google/gemma-4-e4b  │
   │ customers    │         │  OpenAI-compatible   │
   │ transactions │         └──────────────────────┘
   │ products     │
   │ chats        │
   │ messages     │
   └──────────────┘
```

### Why this shape

- **LLM stays narrow.** Gemma-3-4B is small. It only does two things: (a) parse the RM's NL
  request into a JSON intent schema, (b) draft the per-customer outreach. Both are
  tightly-scoped prompts it handles reliably.
- **Python owns deterministic work.** Retrieval, scoring, ranking and product matching are
  pure Python — explainable, testable, immune to JSON-malformation issues.
- **LangGraph is the agent surface.** Discrete nodes with typed state. The agentic narrative
  (decompose → retrieve → reason → act) is enforced by the graph topology rather than by
  hoping a 4B model emits the right tool call.
- **NDJSON streaming**, not SSE. Same live UX, simpler wire format: one JSON object per line
  over a normal POST. The FE reads `response.body.getReader()` and parses `\n`-delimited JSON.

---

## Execution flow (end-to-end)

Example: RM types `find 5 high-value personal-loan prospects in Mumbai`.

```
1. Browser → POST /chat { message }
   └─ FastAPI persists user message, opens NDJSON stream

2. ► Node:  parse_intent
     LLM call (LM Studio, JSON-mode, retry-once on schema failure)
     Output: { intent: "find_prospects",
               filters: { product: "personal_loan", city: "Mumbai",
                          min_income: 80000, exclude_existing: true },
               top_n: 5 }
     Emits: node_started → tool_call(llm) → tool_result → node_finished

3. ► Node:  retrieve
     SQL: customers WHERE city=Mumbai AND has_personal_loan=false AND monthly_income>=80000
     SQL: transactions WHERE customer_id IN (...) AND created_at > now()-180d
     Emits: tool_call(supabase.customers) → tool_result(19 candidates) → ...

4. ► Node:  score
     For each candidate: 7-factor weighted heuristic → 0–100 with per-factor breakdown
     Sort desc, keep top_n
     Emits: tool_result("Scored 19; kept top 5, range 76.5–82.6")

5. ► Node:  recommend
     For each top-scored: rule-based product fit
     (income floor, segment, no duplicate-holder)
     Emits: tool_result("5/5 customers matched to a product")

6. ► Node:  draft_messages
     One LLM call per customer, structured JSON output { whatsapp, opener }
     Each card emitted as it's drafted (streaming)
     Emits: tool_call(llm.draft) → card(...) → tool_call(llm.draft) → card(...) → ...

7. Stream closes with { type: "done", chat_id, cards: 5, duration_ms: 27000 }
   └─ FastAPI persists assistant message with metadata.cards + metadata.events
      → chat is now resumable from the sidebar
```

Each `StepEvent` is rendered into the FE's reasoning log so the RM watches the agent think
live; the customer cards appear on the right as each one is drafted.

---

## Tool design

Tools are organized so the LLM is only invoked where its strengths matter; everything else
is deterministic Python. Each tool has a single responsibility and is unit-testable.

| Tool | Where | Type | Used by | What it does |
|---|---|---|---|---|
| `LM Studio (Gemma-3-4B)` | external | LLM | `parse_intent`, `draft_messages` | OpenAI-compatible local inference, json-mode + retry fallback |
| `customer_repo.get_candidates(filters)` | `be/app/tools/customer_repo.py` | SQL DAO | `retrieve` | Pulls customers matching filters; orders by income desc; caps at 80 |
| `customer_repo.get_recent_transactions(ids, days)` | `be/app/tools/customer_repo.py` | SQL DAO | `retrieve` | Returns `{customer_id: [txns…]}` for the scoring window |
| `customer_repo.get_products()` | `be/app/tools/customer_repo.py` | SQL DAO | `retrieve` | Loads the product catalog once per run |
| `scoring.score_customer(customer, txns, target_product)` | `be/app/tools/scoring.py` | heuristic | `score` | 7-factor weighted score + factor breakdown (see below) |
| `product_match.match_product(customer, products, requested)` | `be/app/tools/product_match.py` | rule-based | `recommend` | Returns the best eligible product + a human-readable reason |
| `db.add_message(chat_id, role, content, metadata)` | `be/app/db.py` | persistence | `/chat` handler | Stores user + assistant messages; cards/events ride in metadata jsonb |

### Scoring heuristic

Seven factors, weights sum to 1.0. Each returns a 0–100 raw value; final score is the
weighted sum. The per-factor breakdown ships in every card — this is the assignment's
"no hardcoded outputs" guarantee.

| Factor | Weight | What it measures |
|---|---|---|
| `income_tier` | 25% | low / mid / high / premium tier → raw value |
| `salary_stability` | 20% | distinct months with a salary credit in the last 6 mo |
| `balance_trend` | 15% | net cashflow trend (recent half vs older half of window) |
| `no_existing` | 15% | 100 if customer doesn't already hold target product, else 0 |
| `emi_signal` | 10% | EMI activity → comfort with debt servicing (positive signal) |
| `tenure` | 10% | years since account opened, capped at 5y |
| `age_band` | 5% | preference for the 28–50 underwriting band |

Implementation: `be/app/tools/scoring.py`. Tests: `be/tests/test_scoring.py`.

### Product matching

Rule-based, no LLM. Filters by eligibility (income floor, segment, dedup), then chooses by
income-tier preference if the RM didn't pin a product:

| Tier | First-choice product |
|---|---|
| premium | home_loan → personal_loan → credit_card |
| high | personal_loan → home_loan → credit_card |
| mid | personal_loan → credit_card → savings_plus |
| low | savings_plus → credit_card |

Implementation: `be/app/tools/product_match.py`. Tests: `be/tests/test_product_match.py`.

---

## Key design decisions

1. **LangGraph over a single tool-calling loop.**
   Gemma-3-4B is unreliable at native function calling. Splitting the work into discrete
   nodes (parse, retrieve, score, recommend, draft) lets each LLM call be tightly scoped and
   Pydantic-validated. The "agent" is the graph; the LLM is a component.

2. **Heuristic scoring, not LLM-judged.**
   The assignment explicitly allows rules / ML / heuristics. A heuristic is *explainable*,
   *fast*, *cheap*, and gives the grader something concrete to inspect. Every customer card
   shows the top 3 contributing factors.

3. **NDJSON over SSE for streaming.**
   Same live UX, simpler wire (one JSON per line over a normal POST). No `EventSource`
   protocol, no manual `event:`/`data:` framing on either side. Survives proxies cleanly.

4. **State carried by LangGraph, persisted by Supabase.**
   Within a chat: graph state holds history, candidates, scored results, recommendations,
   draft cards. Across chats: `chats` + `messages` tables; assistant messages persist
   `metadata.cards` + `metadata.events` + `metadata.duration_ms` so a reopened chat
   rehydrates the full reasoning trace and customer cards from a single `GET /chats/{id}`.

5. **Prompt files, not inline strings.**
   `be/app/prompts/intent.txt`, `be/app/prompts/draft_message.txt`. Plain text, easy to
   iterate on without touching code. Curly braces escaped for `.format()`.

6. **Faker-seeded synthetic data with deliberate prospect clusters.**
   ~400 customers across 10 Indian metros, ~125 transactions each, 4 products. About 15% of
   customers are intentionally shaped as strong personal-loan prospects (high income,
   stable salary, no existing loan, EMI activity) so the demo lands cleanly.

7. **Single git repo, monorepo layout.**
   `be/` (Python FastAPI + LangGraph), `fe/` (Next.js 16 + shadcn + pnpm), `docs/` (planning
   docs + the assignment PDF). One `.gitignore`, one VS Code settings file with IDE-side
   excludes for `node_modules` etc.

---

## Trade-offs and limitations

| Trade-off | Why we chose it | The cost |
|---|---|---|
| Local 4B LLM via LM Studio | Free, runs on-device, no API spend; matches the "agentic *system* not LLM showcase" framing | ~25–30s end-to-end for a 5-customer batch (mostly the 5 sequential drafts). Bigger models would be 2–4× faster but require API keys / GPU. |
| Heuristic scoring | Explainable & deterministic → safer than an LLM-judged score | Weights are static; a real bank would tune them on historical conversion data |
| Per-customer LLM draft calls run sequentially | Simpler to reason about; preserves event ordering | Could parallelize with `asyncio.gather` for ~5× speedup on the draft step. Parked. |
| In-graph history is rebuilt from DB on every turn | Stateless graph; survives restart | One extra Supabase round-trip per turn (~50ms) |
| Supabase Row Level Security disabled | Anon "publishable" key needs to insert from the seeder | OK for an assignment; in prod you'd use the service-role key + policies |
| The `rewrite_message` intent branch is wired but underpowered | Branch exists for future per-chat "last cards" state | Right now the conditional edge routes to `draft_messages` but there's no prior `recommended` to redraft from. The LLM correctly routes such asks back to `find_prospects` in practice. Documented in `docs/phases.md` parking lot. |
| Single language (English) outreach drafts | Matches the assignment example | Multilingual (Hindi/Marathi/Tamil) drafting is a one-prompt-tweak away |

---

## Setup and run

### Prerequisites

- Python 3.11+
- Node 20+ and pnpm 8+
- [LM Studio](https://lmstudio.ai/) running locally with a Gemma-3-4B-class model loaded
  on the OpenAI-compatible server (default port `1234`)
- A Supabase project (free tier is fine)

### 1) Apply the schema

Open the Supabase SQL editor and paste the contents of
[`be/scripts/apply_schema.sql`](be/scripts/apply_schema.sql) → Run.
This creates `customers`, `transactions`, `products`, `chats`, `messages` and disables RLS
on all five tables (assignment context).

### 2) Backend

```bash
cd be
python3 -m venv .venv && source .venv/bin/activate
pip install --default-timeout=120 -r requirements.txt

# Configure .env (already has Supabase keys; verify LM_STUDIO_MODEL matches your loaded model)
cat .env
#   DB_PASSWORD=...
#   SUPABASE_URL=https://<ref>.supabase.co
#   SUPABASE_KEY=sb_publishable_...
#   LM_STUDIO_URL=http://localhost:1234/v1
#   LM_STUDIO_MODEL=google/gemma-4-e4b

# Seed (~30–60s; PostgREST inserts in batches)
python -m app.seed

# Start the API
uvicorn app.main:app --reload --port 8000
```

Verify:

```bash
curl -s http://localhost:8000/health | jq
# → { supabase: "ok", customers: 400, lm_studio: "ok", configured_model: "..." }
```

CLI smoke test (no FE needed):

```bash
python scripts/run_cli.py "find 5 high-value personal-loan prospects in Mumbai"
```

### 3) Frontend

```bash
cd fe
pnpm install
pnpm dev   # serves on http://localhost:3000 (or :3001 if 3000 is busy)
```

The FE expects the backend at `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`).
Edit `fe/.env.local` to override.

### 4) Use it

Open the FE → type a query. The reasoning header streams live ("Thinking…" → "Thought
for 27s · 5 cards"). Cards appear inline. Past chats live in the sidebar; click to resume.

---

## Demo scripts (3 flows)

These three flows exercise the entire agent surface and are scripted for the demo video.

### Flow 1 — Initial prospecting (the canonical PDF query)

> RM: *"Find 5 high-value customers likely to convert for a personal loan this month and
> generate personalized WhatsApp messages."*

Expected: parse_intent picks `product=personal_loan, min_income≈80000`. Retrieve returns
~15–25 candidates. Score keeps the top 5 (typical score range 76–83). Recommend matches all
to Personal Loan. Five cards with score, factor breakdown, and ready-to-copy WhatsApp.

### Flow 2 — Refinement / multi-turn

After Flow 1, follow up with:

> RM: *"Only in Mumbai, and exclude anyone with an existing credit card too."*

Expected: parse_intent flags this as `refine`, narrows the city + adds an extra exclusion
hint. Same pipeline; smaller candidate pool; fresh cards.

### Flow 3 — Different product / city

> RM: *"Show me 2 credit card prospects in Bengaluru."*

Expected: parse_intent picks `product=credit_card, city=Bengaluru, top_n=2`. Recommend
maps to Platinum Credit Card. Two cards.

(A fourth demonstrable flow is to **reopen a past chat** from the sidebar — the cards and
reasoning summary rehydrate from `metadata` jsonb without re-running the agent.)

---

## Project layout

```
business-next/
├── be/                          # Python FastAPI + LangGraph
│   ├── app/
│   │   ├── main.py              # FastAPI: /chat (NDJSON), /chats, /health
│   │   ├── graph.py             # LangGraph StateGraph wiring
│   │   ├── nodes/               # parse_intent, retrieve, score, recommend, draft_messages
│   │   ├── tools/               # customer_repo, scoring, product_match
│   │   ├── prompts/             # intent.txt, draft_message.txt
│   │   ├── schemas.py           # Pydantic — IntentSchema, CustomerCard, StepEvent, …
│   │   ├── state.py             # GraphState TypedDict
│   │   ├── events.py            # EventBus (thread-safe pub/sub for streaming)
│   │   ├── llm.py               # ChatOpenAI(base_url=LM Studio) factory
│   │   ├── db.py                # Supabase client + DAOs
│   │   ├── config.py            # Pydantic Settings
│   │   └── seed.py              # Faker seeder
│   ├── scripts/
│   │   ├── apply_schema.sql     # paste into Supabase SQL editor
│   │   └── run_cli.py           # CLI driver (no FE needed)
│   ├── tests/                   # pytest — scoring + product_match
│   └── requirements.txt
│
├── fe/                          # Next.js 16 + shadcn + pnpm
│   ├── app/
│   │   ├── page.tsx             # /  → new chat
│   │   └── chat/[id]/page.tsx   # /chat/:id → existing chat
│   ├── components/
│   │   ├── app-shell.tsx        # sidebar + main grid
│   │   ├── chat-sidebar.tsx     # past chats + new chat button
│   │   ├── chat-thread.tsx      # scrolling message timeline + input
│   │   ├── message-user.tsx
│   │   ├── message-assistant.tsx
│   │   ├── reasoning-summary.tsx  # collapsible "Thought for Xs · N cards"
│   │   ├── reasoning-log.tsx    # terminal-style event log (expanded view)
│   │   ├── customer-card.tsx
│   │   ├── chat-input.tsx
│   │   └── ui/                  # shadcn primitives
│   ├── lib/
│   │   ├── stream.ts            # NDJSON parser
│   │   ├── api.ts               # /chats REST helpers
│   │   └── types.ts             # mirrors backend StepEvent + CustomerCard
│   └── hooks/use-chat-stream.ts # owns the stream + turns state
│
└── docs/
    ├── Take-Home Assignment_ Agentic AI for Banking CRM-1.pdf
    ├── architecture.md          # deep-dive on flow + failure modes
    ├── db-schema.md             # full DDL + indexes + seed shape
    ├── project-structure.md     # file-by-file responsibilities
    └── phases.md                # build-phase tracker
```

---

## Tests

```bash
cd be
source .venv/bin/activate
python -m pytest tests/ -v
```

12 tests, run in ~50ms:

```
tests/test_product_match.py  6 passed
tests/test_scoring.py        6 passed
```

The scoring tests cover: weights summing to 1.0, strong-prospect scoring high, holder of
target product penalized, low-income/low-tenure scoring low, top-factors sorting, neutral
fallback when no target product. The product-match tests cover: requested-product wins
when eligible, blocked when holder, blocked by income floor, segment mismatch, tier
preference fallback, low-tier savings fallback.

---

## What's next (parking lot)

Things consciously left out, with notes on cost/benefit if/when they're prioritized:

- **`rewrite_message` branch** needs a per-chat "last recommended" cache. Currently the
  conditional edge to `draft_messages` short-circuits the rest of the graph but has nothing
  prior to redraft from. The LLM safely routes such asks back to `find_prospects` in
  practice.
- **Parallelize draft_messages** — ~5× speedup on the draft step via `asyncio.gather`.
- **Pitch outcome tracking** — a `pitches` table with FKs to customers + products to record
  what was pitched and whether it converted. Would unlock real ML-driven weights.
- **Multilingual outreach** (Hindi / Marathi / Tamil) — one prompt tweak.
- **Auth / multi-user RM accounts** — out of scope for an assignment.
- **Production deploy** — out of scope; the dev setup runs entirely on a laptop.
