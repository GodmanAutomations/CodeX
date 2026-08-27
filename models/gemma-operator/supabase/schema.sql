create table if not exists public.gemma_operator_memories (
  id uuid primary key default gen_random_uuid(),
  device_id text not null,
  local_id integer,
  kind text not null,
  text text not null,
  tags text,
  confidence double precision not null default 1.0,
  source text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists gemma_operator_memories_kind_idx
  on public.gemma_operator_memories (kind);

create index if not exists gemma_operator_memories_updated_at_idx
  on public.gemma_operator_memories (updated_at desc);

create unique index if not exists gemma_operator_memories_device_local_uidx
  on public.gemma_operator_memories (device_id, local_id);

create index if not exists gemma_operator_memories_text_fts_idx
  on public.gemma_operator_memories
  using gin (to_tsvector('english', text));

alter table public.gemma_operator_memories enable row level security;

-- Local private sync should use a service-role key from the local machine.
-- Do not expose private companion memory through browser anon policies.
