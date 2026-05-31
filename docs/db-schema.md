# Database Schema (Supabase Postgres)

## ER overview

```
┌────────────┐         ┌───────────────┐
│ customers  │ 1─────* │ transactions  │
└────┬───────┘         └───────────────┘
     │
     │ (referenced by recommend/score; no FK)
     ▼
┌────────────┐
│ products   │
└────────────┘

┌────────────┐         ┌───────────────┐
│ chats      │ 1─────* │ messages      │
└────────────┘         └───────────────┘
```

`customers` ⨯ `products` is computed at runtime by the recommend node — no join table needed because product fit is rules-driven, not pre-assigned.

## Tables

### customers

| column                 | type         | notes                                              |
| ---------------------- | ------------ | -------------------------------------------------- |
| id                     | uuid PK      | `gen_random_uuid()`                                |
| name                   | text         |                                                    |
| age                    | int          | 22–65                                              |
| city                   | text         | one of ~10 Indian metros                           |
| occupation             | text         | salaried / self_employed / business_owner          |
| employer_type          | text         | mnc / startup / govt / sme / self                  |
| income_tier            | text         | low / mid / high / premium                         |
| monthly_income         | numeric(12,2)| INR                                                |
| account_open_date      | date         | drives tenure score                                |
| has_personal_loan      | boolean      |                                                    |
| has_credit_card        | boolean      |                                                    |
| has_home_loan          | boolean      |                                                    |
| phone                  | text         | E.164, +91XXXXXXXXXX                               |
| email                  | text         |                                                    |
| created_at             | timestamptz  | default `now()`                                    |

Indexes: `(city)`, `(income_tier)`, `(has_personal_loan)`.

### transactions

| column        | type          | notes                                          |
| ------------- | ------------- | ---------------------------------------------- |
| id            | uuid PK       |                                                |
| customer_id   | uuid FK → customers(id) ON DELETE CASCADE |              |
| amount        | numeric(12,2) | always positive; direction tells sign           |
| direction     | text          | credit / debit                                  |
| category      | text          | salary / rent / emi / shopping / utility / transfer / other |
| description   | text          |                                                |
| created_at    | timestamptz   | 12-month spread                                |

Indexes: `(customer_id, created_at desc)`, `(category)`.

### products

| column         | type          | notes                                              |
| -------------- | ------------- | -------------------------------------------------- |
| id             | uuid PK       |                                                    |
| code           | text UNIQUE   | `personal_loan` / `credit_card` / `savings_plus` / `home_loan` |
| name           | text          | display name                                       |
| type           | text          | loan / card / deposit                              |
| min_income     | numeric(12,2) | eligibility floor                                  |
| target_segment | text          | salaried / self_employed / any                     |
| interest_rate  | numeric(5,2)  | annual %                                           |
| tenure_months  | int           | nullable for cards                                 |
| max_amount     | numeric(14,2) | sanction cap                                       |

Seed with 4 products covering the assignment's demo surface.

### chats

| column      | type        | notes                          |
| ----------- | ----------- | ------------------------------ |
| id          | uuid PK     |                                |
| title       | text        | auto from first user message   |
| created_at  | timestamptz | default `now()`                |
| updated_at  | timestamptz | bumped on every new message    |

Index: `(updated_at desc)` for sidebar listing.

### messages

| column     | type        | notes                                                              |
| ---------- | ----------- | ------------------------------------------------------------------ |
| id         | uuid PK     |                                                                    |
| chat_id    | uuid FK → chats(id) ON DELETE CASCADE |                                        |
| role       | text        | user / assistant                                                   |
| content    | text        | user's text or assistant's summary sentence                        |
| metadata   | jsonb       | assistant only: `{ cards: [...], events: [...], filters: {...} }`  |
| created_at | timestamptz | default `now()`                                                    |

Index: `(chat_id, created_at)`.

## Why `metadata` jsonb instead of normalized tables

Cards are read-only artifacts of a turn. Storing them as `messages.metadata` means:
- Resume rehydrates with one query: `SELECT * FROM messages WHERE chat_id = ?`.
- No schema migration if we add a new card field later.
- Reasoning trace (events) ride along for "show me what the agent did last time".

If we ever needed to query *across* cards (e.g. "show all customers we pitched personal loans to"), we'd add a normalized `card_history` table — not needed for the assignment.

## Seed shape (Faker)

- **~400 customers** across 10 Indian cities, tiered:
  - 20% premium (₹2L+/mo), 30% high (₹80k–2L), 35% mid (₹30k–80k), 15% low (<₹30k)
  - Salaried 60% / self-employed 25% / business 15%
- **~50 transactions per customer** over 12 months:
  - Monthly salary credit for salaried customers (creates "stable income" signal)
  - Rent, utilities, shopping, occasional EMIs
  - Realistic spending ratios per income tier
- **4 products** seeded once.
- **Deliberate prospect clusters** — ~15% of customers configured to be obvious "high-value personal loan prospects" (high income, no existing loan, stable salary, EMI spending pattern) so the demo lands cleanly.

## DDL (canonical)

```sql
create extension if not exists "pgcrypto";

create table customers (
  id                uuid primary key default gen_random_uuid(),
  name              text not null,
  age               int  not null check (age between 18 and 80),
  city              text not null,
  occupation        text not null,
  employer_type     text not null,
  income_tier       text not null check (income_tier in ('low','mid','high','premium')),
  monthly_income    numeric(12,2) not null,
  account_open_date date not null,
  has_personal_loan boolean not null default false,
  has_credit_card   boolean not null default false,
  has_home_loan     boolean not null default false,
  phone             text,
  email             text,
  created_at        timestamptz not null default now()
);
create index on customers(city);
create index on customers(income_tier);
create index on customers(has_personal_loan);

create table transactions (
  id          uuid primary key default gen_random_uuid(),
  customer_id uuid not null references customers(id) on delete cascade,
  amount      numeric(12,2) not null check (amount > 0),
  direction   text not null check (direction in ('credit','debit')),
  category    text not null,
  description text,
  created_at  timestamptz not null default now()
);
create index on transactions(customer_id, created_at desc);
create index on transactions(category);

create table products (
  id             uuid primary key default gen_random_uuid(),
  code           text unique not null,
  name           text not null,
  type           text not null,
  min_income     numeric(12,2) not null,
  target_segment text not null,
  interest_rate  numeric(5,2),
  tenure_months  int,
  max_amount     numeric(14,2)
);

create table chats (
  id         uuid primary key default gen_random_uuid(),
  title      text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index on chats(updated_at desc);

create table messages (
  id         uuid primary key default gen_random_uuid(),
  chat_id    uuid not null references chats(id) on delete cascade,
  role       text not null check (role in ('user','assistant')),
  content    text not null,
  metadata   jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index on messages(chat_id, created_at);
```
