-- Banking CRM Agent — Supabase schema
-- Apply via Supabase SQL Editor (paste & run) or psql.
-- Safe to re-run: drops tables first.

drop table if exists messages cascade;
drop table if exists chats cascade;
drop table if exists transactions cascade;
drop table if exists products cascade;
drop table if exists customers cascade;

create extension if not exists "pgcrypto";

-- ── customers ───────────────────────────────────────────────────────────
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

-- ── transactions ────────────────────────────────────────────────────────
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

-- ── products ────────────────────────────────────────────────────────────
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

-- ── chats / messages ────────────────────────────────────────────────────
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

-- ── RLS off (assignment context; anon key needs full r/w) ───────────────
alter table customers    disable row level security;
alter table transactions disable row level security;
alter table products     disable row level security;
alter table chats        disable row level security;
alter table messages     disable row level security;
