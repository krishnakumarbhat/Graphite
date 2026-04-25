create table if not exists public.notes (
  id text primary key,
  user_id text not null,
  title text not null default '',
  content text not null default '',
  excerpt text not null default '',
  source_path text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  is_ai_generated boolean not null default false
);

create index if not exists notes_user_updated_idx
  on public.notes (user_id, updated_at desc);

create table if not exists public.note_embeddings (
  note_id text primary key references public.notes (id) on delete cascade,
  user_id text not null,
  embedding_json jsonb not null,
  updated_at timestamptz not null default timezone('utc', now())
);

create index if not exists note_embeddings_user_idx
  on public.note_embeddings (user_id, updated_at desc);

create or replace function public.touch_note_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$;

drop trigger if exists notes_touch_updated_at on public.notes;

create trigger notes_touch_updated_at
before update on public.notes
for each row execute function public.touch_note_updated_at();