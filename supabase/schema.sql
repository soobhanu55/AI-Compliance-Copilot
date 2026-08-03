-- AI Compliance Copilot — Supabase schema
-- Run against a Supabase Postgres project. Requires the pgvector extension.

create extension if not exists vector;

-- users handled by Supabase Auth (auth.users)

create table if not exists documents (
  id uuid primary key default gen_random_uuid(),
  -- null for doc_type = 'regulation' — the shared corpus has no owning user
  user_id uuid references auth.users(id),
  filename text not null,
  doc_type text not null check (doc_type in ('company_policy', 'regulation')),
  uploaded_at timestamptz default now(),
  constraint company_policy_has_owner check (doc_type = 'regulation' or user_id is not null)
);

create table if not exists document_chunks (
  id uuid primary key default gen_random_uuid(),
  document_id uuid references documents(id) on delete cascade not null,
  content text not null,
  embedding vector(1024), -- match your embedding model dim (e5-large = 1024, text-embedding-3-large = 3072)
  metadata jsonb default '{}'::jsonb
);

create table if not exists compliance_reports (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) not null,
  company_profile jsonb not null,
  report_content jsonb not null,
  created_at timestamptz default now()
);

create table if not exists chat_history (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) not null,
  role text not null check (role in ('user', 'assistant')),
  content text not null,
  created_at timestamptz default now()
);

-- Vector similarity index (IVFFlat; tune `lists` to your corpus size)
create index if not exists document_chunks_embedding_idx
  on document_chunks using ivfflat (embedding vector_cosine_ops) with (lists = 100);

-- Row-level security
alter table documents enable row level security;
alter table document_chunks enable row level security;
alter table compliance_reports enable row level security;
alter table chat_history enable row level security;

create policy "documents_owner" on documents
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "document_chunks_owner" on document_chunks
  for all using (
    exists (
      select 1 from documents d
      where d.id = document_chunks.document_id and d.user_id = auth.uid()
    )
  );

create policy "compliance_reports_owner" on compliance_reports
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "chat_history_owner" on chat_history
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- Regulation corpus is shared/public (doc_type = 'regulation') — expose read-only to all authed users
create policy "regulation_documents_readable" on documents
  for select using (doc_type = 'regulation');

create policy "regulation_chunks_readable" on document_chunks
  for select using (
    exists (
      select 1 from documents d
      where d.id = document_chunks.document_id and d.doc_type = 'regulation'
    )
  );
