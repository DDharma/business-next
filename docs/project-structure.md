# Project Structure

```
business-next/
├── be/                          # Python FastAPI + LangGraph backend
│   ├── app/                     # (renamed from qpp)
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app, routes, SSE handler
│   │   ├── config.py            # env loading, settings
│   │   ├── llm.py               # ChatOpenAI bound to LM Studio
│   │   ├── db.py                # Supabase client + DAOs
│   │   ├── schemas.py           # Pydantic models (events, cards, intents)
│   │   ├── events.py            # SSE event queue + emitter helpers
│   │   ├── state.py             # LangGraph State TypedDict
│   │   ├── graph.py             # StateGraph wiring + conditional edges
│   │   ├── nodes/
│   │   │   ├── __init__.py
│   │   │   ├── parse_intent.py
│   │   │   ├── retrieve.py
│   │   │   ├── score.py
│   │   │   ├── recommend.py
│   │   │   └── draft_messages.py
│   │   ├── tools/               # pure functions used by nodes
│   │   │   ├── __init__.py
│   │   │   ├── customer_repo.py # SQL queries
│   │   │   ├── scoring.py       # weighted heuristic + per-factor breakdown
│   │   │   └── product_match.py # rule-based product fit
│   │   ├── prompts/
│   │   │   ├── intent.txt
│   │   │   └── draft_message.txt
│   │   └── seed.py              # Faker seeder (run once)
│   ├── tests/
│   │   ├── test_scoring.py
│   │   ├── test_product_match.py
│   │   └── test_graph_smoke.py  # end-to-end CLI smoke
│   ├── scripts/
│   │   ├── apply_schema.sql     # the DDL from db-schema.md
│   │   └── run_cli.py           # CLI driver to test agent without FE
│   ├── requirements.txt
│   ├── pyproject.toml           # optional, for tooling
│   ├── .env                     # SUPABASE_URL, SUPABASE_KEY, LM_STUDIO_URL, MODEL
│   └── .venv/                   # local virtualenv (gitignored)
│
├── fe/                          # Next.js 15 + shadcn + pnpm frontend
│   ├── app/
│   │   ├── layout.tsx           # root layout, font, providers
│   │   ├── page.tsx             # landing → redirects to new chat
│   │   ├── globals.css
│   │   └── chat/
│   │       └── [id]/
│   │           └── page.tsx     # active chat view
│   ├── components/
│   │   ├── ui/                  # shadcn primitives (button, input, card, scroll-area, etc.)
│   │   ├── chat-input.tsx
│   │   ├── chat-sidebar.tsx     # list of past chats
│   │   ├── reasoning-log.tsx    # streaming terminal panel
│   │   ├── customer-card.tsx    # name, score, factors, product, msg
│   │   └── score-breakdown.tsx  # per-factor pill list
│   ├── lib/
│   │   ├── sse.ts               # typed SSE consumer (POST + parse stream)
│   │   ├── api.ts               # REST helpers for /chats endpoints
│   │   └── types.ts             # StepEvent, CustomerCard, ChatSummary
│   ├── hooks/
│   │   └── use-chat-stream.ts   # React hook that owns the SSE lifecycle
│   ├── public/
│   ├── package.json
│   ├── pnpm-lock.yaml
│   ├── tsconfig.json
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── components.json          # shadcn config
│   └── .env.local               # NEXT_PUBLIC_API_URL
│
├── docs/
│   ├── Take-Home Assignment_ Agentic AI for Banking CRM-1.pdf
│   ├── myplan.md                # original blueprint
│   ├── architecture.md          # arch diagram + data flow
│   ├── db-schema.md             # tables + DDL
│   ├── project-structure.md     # this file
│   └── phases.md                # build tracker
│
└── README.md                    # final deliverable: arch, flow, decisions, setup
```

## File responsibilities (key files)

### Backend

| File | Responsibility |
|---|---|
| `app/main.py` | FastAPI app, CORS, route definitions, SSE response wiring |
| `app/llm.py` | Single source of truth for LLM client — `ChatOpenAI(base_url=LM Studio, model=...)` |
| `app/db.py` | Supabase client singleton + thin DAO functions (`get_customers_filtered`, `save_message`, `list_chats`) |
| `app/schemas.py` | All Pydantic models — `IntentSchema`, `CustomerCard`, `StepEvent`, `ChatMessage` |
| `app/state.py` | `GraphState` TypedDict — what flows between nodes |
| `app/graph.py` | `build_graph()` — composes nodes, conditional edge from `parse_intent` |
| `app/events.py` | `EventEmitter` — per-request asyncio.Queue + helpers for each event type |
| `app/nodes/*` | One file per node; each node takes & returns `GraphState`, emits events as it works |
| `app/tools/scoring.py` | `score_customer(customer, txns) -> (score, factors)` — pure, testable |
| `app/tools/product_match.py` | `match_product(customer, products) -> (product, reason)` |

### Frontend

| File | Responsibility |
|---|---|
| `app/chat/[id]/page.tsx` | Two-pane layout: reasoning log + cards. Owns chat state, calls `use-chat-stream` |
| `hooks/use-chat-stream.ts` | Opens SSE, parses events, appends to log, materializes cards |
| `lib/sse.ts` | Low-level SSE parser using `fetch` + `ReadableStream` (App Router compatible) |
| `components/reasoning-log.tsx` | Renders `StepEvent[]` in monospace terminal style with collapsible tool calls |
| `components/customer-card.tsx` | Score + factor breakdown + WhatsApp message + copy button |
| `components/chat-sidebar.tsx` | Lists chats from `GET /chats`, click to navigate |

## Conventions

- **No business logic in routes.** `main.py` only orchestrates; logic lives in nodes/tools.
- **No SQL in nodes.** Nodes call into `tools/customer_repo.py` or `db.py`.
- **Events are emitted by nodes, not by tools.** Tools stay pure and unit-testable.
- **Prompts in `prompts/` as text files**, not string literals — easier to iterate.
- **One shadcn component per file** under `components/ui/` (default shadcn convention).
