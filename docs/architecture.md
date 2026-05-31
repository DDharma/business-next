# Architecture & Data Flow

## High-level architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                          Browser (Next.js 15)                          │
│                                                                        │
│  ┌──────────────┐   ┌──────────────────┐   ┌────────────────────────┐  │
│  │ Chat input   │   │ Reasoning log    │   │ Customer cards         │  │
│  │ (shadcn)     │   │ (streaming)      │   │ (score + WhatsApp msg) │  │
│  └──────┬───────┘   └────────▲─────────┘   └──────────▲─────────────┘  │
│         │                    │                        │                │
│         │  POST /chat        │  SSE events stream     │                │
└─────────┼────────────────────┼────────────────────────┼────────────────┘
          │                    │                        │
          ▼                    │                        │
┌──────────────────────────────┴────────────────────────┴────────────────┐
│                       FastAPI backend (Python)                         │
│                                                                        │
│   /chat (SSE)   /chats   /chats/{id}   /seed                           │
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
   │              │         │  gemma-3-4b-it       │
   │ customers    │         │  OpenAI-compatible   │
   │ transactions │         └──────────────────────┘
   │ products     │
   │ chats        │
   │ messages     │
   └──────────────┘
```

## Why this shape

- **LLM stays narrow.** Gemma-3-4B is small. It only does (a) intent parsing into a JSON schema and (b) per-customer WhatsApp drafting. Both are tightly-scoped prompts it handles reliably.
- **Python owns deterministic work.** Retrieval, scoring, ranking and product matching are pure Python — explainable, testable, fast, immune to JSON malformation.
- **LangGraph is the agent surface.** Discrete nodes with typed state. The agentic narrative (decompose → retrieve → reason → act) is enforced by the graph topology, not by hoping a 4B model emits the right tool call.
- **SSE for live reasoning.** Each node emits typed `StepEvent`s. FE renders them in a terminal-style log so the RM can watch the agent think.

## End-to-end data flow (single turn)

```
1. RM types: "find 5 high-value personal-loan prospects in Mumbai"
   └─► POST /chat { chat_id, message }
        └─► FastAPI persists user message ──► messages table

2. SSE stream opens. Backend invokes LangGraph with initial state:
   { chat_id, user_message, history, cards: [], events: [] }

3. Node: parse_intent
   ├─ LLM call (LM Studio, JSON mode)
   ├─ Output: { intent: "find_prospects",
   │           filters: { product: "personal_loan", city: "Mumbai" },
   │           top_n: 5 }
   └─ Emit: node_started → tool_call(llm) → tool_result → node_finished

4. Node: retrieve
   ├─ SQL: customers WHERE city=Mumbai AND has_personal_loan=false
   ├─ SQL: transactions WHERE customer_id IN (...) AND created_at > now()-90d
   └─ Emit: tool_call(sql) → tool_result(N candidates)

5. Node: score
   ├─ For each candidate: weighted heuristic on 7 factors
   ├─ Output: [(customer, score, factor_breakdown)]
   └─ Emit: tool_result(top-5 with scores)

6. Node: recommend
   ├─ Rule-based product fit (income vs min_income, segment, no dup product)
   ├─ Output: [(customer, product, reason)]
   └─ Emit: tool_result

7. Node: draft_messages  (one LLM call per customer, can parallelize)
   ├─ Prompt: customer profile + product + reason → JSON { whatsapp, opener }
   ├─ For each result, emit a `card` event as soon as its draft is ready
   └─ Emit: node_finished

8. Stream closes with `done` event.
   └─► FastAPI persists assistant message with metadata.cards = [...]
       to messages table — enables resume.
```

## Conversation context & persistence

- **Within a chat:** LangGraph state carries `history` (last N turns of user/assistant text). The RM can say "only Mumbai" or "rewrite message #3" and the next turn re-uses the prior state.
- **Across chats:** No cross-chat memory. Each chat is isolated.
- **Resume:** Chats and messages are persisted to Supabase. Opening an old chat rehydrates messages + cards from `messages.metadata` jsonb.

## SSE event taxonomy

```ts
type StepEvent =
  | { type: 'node_started';  node: string; label: string }
  | { type: 'tool_call';     node: string; tool: string; args: object }
  | { type: 'tool_result';   node: string; tool: string; preview: string }
  | { type: 'node_finished'; node: string; ms: number }
  | { type: 'card';          card: CustomerCard }
  | { type: 'done' }
  | { type: 'error';         message: string }
```

## Failure modes & fallbacks

| Failure | Handling |
|---|---|
| LM Studio unreachable | `/chat` returns 503 + emits `error` event; FE shows banner |
| `parse_intent` returns invalid JSON | One retry with reinforced schema; on second fail, fall back to default filters and surface a warning event |
| `retrieve` returns 0 candidates | Skip score/recommend; emit `card`-less `done` with a `no_results` notice |
| LLM message draft malformed | Per-customer retry once; if still bad, ship card with `opener=null` rather than blocking the batch |
