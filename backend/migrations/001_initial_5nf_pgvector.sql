-- =============================================================================
-- Graphite Supabase Schema — Fifth Normal Form (5NF) with pgvector
-- =============================================================================
-- 5NF: Every non-trivial join dependency is implied by candidate keys.
-- All multi-valued facts are in separate tables joined by foreign keys.
-- =============================================================================

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- ────────────────────────────────────────────────────────────────────────────
-- 1. USERS — Auth source-of-truth (extends Supabase auth.users)
-- ────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.users (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email         TEXT UNIQUE,
  display_name  TEXT NOT NULL DEFAULT '',
  avatar_url    TEXT DEFAULT '',
  tier          TEXT NOT NULL DEFAULT 'free' CHECK (tier IN ('free', 'pro', 'admin')),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ────────────────────────────────────────────────────────────────────────────
-- 2. NOTES — Core note entity (no multi-valued columns)
-- ────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.notes (
  id              TEXT PRIMARY KEY,
  user_id         TEXT NOT NULL,  -- 'web-local' for guests, UUID for auth users
  title           TEXT NOT NULL DEFAULT '',
  content         TEXT NOT NULL DEFAULT '',
  excerpt         TEXT NOT NULL DEFAULT '',
  source_path     TEXT,
  is_ai_generated BOOLEAN NOT NULL DEFAULT FALSE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_notes_user_updated
  ON public.notes (user_id, updated_at DESC);

-- ────────────────────────────────────────────────────────────────────────────
-- 3. NOTE_EMBEDDINGS — Separate relation for vector data (5NF: embedding
--    is an independent fact about a note, not dependent on title/content)
-- ────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.note_embeddings (
  note_id     TEXT PRIMARY KEY REFERENCES public.notes(id) ON DELETE CASCADE,
  embedding   vector(768) NOT NULL,   -- pgvector column, 768-dim for Gemini
  model       TEXT NOT NULL DEFAULT 'text-embedding-004',
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- HNSW index for fast approximate nearest neighbor search
CREATE INDEX IF NOT EXISTS idx_note_embeddings_hnsw
  ON public.note_embeddings
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

-- ────────────────────────────────────────────────────────────────────────────
-- 4. NOTE_TAGS — Multi-valued fact: a note can have many tags (5NF split)
-- ────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.tags (
  id    SERIAL PRIMARY KEY,
  name  TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS public.note_tags (
  note_id TEXT NOT NULL REFERENCES public.notes(id) ON DELETE CASCADE,
  tag_id  INTEGER NOT NULL REFERENCES public.tags(id) ON DELETE CASCADE,
  PRIMARY KEY (note_id, tag_id)
);

-- ────────────────────────────────────────────────────────────────────────────
-- 5. PROJECTS — Projects that agents can analyze and generate notes from
-- ────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.projects (
  id          TEXT PRIMARY KEY,
  user_id     TEXT NOT NULL,
  name        TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  repo_url    TEXT DEFAULT '',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_projects_user
  ON public.projects (user_id, updated_at DESC);

-- ────────────────────────────────────────────────────────────────────────────
-- 6. PROJECT_NOTES — Join dependency between projects and notes (5NF)
-- ────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.project_notes (
  project_id TEXT NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  note_id    TEXT NOT NULL REFERENCES public.notes(id) ON DELETE CASCADE,
  PRIMARY KEY (project_id, note_id)
);

-- ────────────────────────────────────────────────────────────────────────────
-- 7. AGENTS — Agent definition registry
-- ────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.agents (
  id          TEXT PRIMARY KEY,
  name        TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  status      TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'disabled', 'error')),
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ────────────────────────────────────────────────────────────────────────────
-- 8. AGENT_CAPABILITIES — Multi-valued fact: an agent has many capabilities
-- ────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.capabilities (
  id    SERIAL PRIMARY KEY,
  name  TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS public.agent_capabilities (
  agent_id      TEXT NOT NULL REFERENCES public.agents(id) ON DELETE CASCADE,
  capability_id INTEGER NOT NULL REFERENCES public.capabilities(id) ON DELETE CASCADE,
  PRIMARY KEY (agent_id, capability_id)
);

-- ────────────────────────────────────────────────────────────────────────────
-- 9. AGENT_RUNS — Each invocation of an agent (immutable log)
-- ────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.agent_runs (
  id            TEXT PRIMARY KEY,
  agent_id      TEXT NOT NULL REFERENCES public.agents(id) ON DELETE CASCADE,
  user_id       TEXT NOT NULL,
  task          TEXT NOT NULL,
  status        TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
  result_json   JSONB,
  error_message TEXT,
  started_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at  TIMESTAMPTZ,
  duration_ms   INTEGER
);

CREATE INDEX IF NOT EXISTS idx_agent_runs_agent_started
  ON public.agent_runs (agent_id, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_agent_runs_user
  ON public.agent_runs (user_id, started_at DESC);

-- ────────────────────────────────────────────────────────────────────────────
-- 10. AGENT_ACTION_LOG — Individual actions within a run (trajectory steps)
-- ────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.agent_action_log (
  id          TEXT PRIMARY KEY,
  run_id      TEXT NOT NULL REFERENCES public.agent_runs(id) ON DELETE CASCADE,
  step_index  INTEGER NOT NULL,
  action_type TEXT NOT NULL,  -- 'tool_call', 'llm_call', 'reasoning', 'observation', 'error'
  tool_name   TEXT,
  tool_args   JSONB,
  tool_result JSONB,
  reasoning   TEXT,
  timestamp   TIMESTAMPTZ NOT NULL DEFAULT now(),
  duration_ms INTEGER
);

CREATE INDEX IF NOT EXISTS idx_action_log_run
  ON public.agent_action_log (run_id, step_index);

-- ────────────────────────────────────────────────────────────────────────────
-- 11. EVAL_SETS — Evaluation dataset containers (ADK-eval compatible)
-- ────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.eval_sets (
  id          TEXT PRIMARY KEY,
  name        TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ────────────────────────────────────────────────────────────────────────────
-- 12. EVAL_CASES — Individual evaluation cases within a set
-- ────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.eval_cases (
  id            TEXT PRIMARY KEY,
  eval_set_id   TEXT NOT NULL REFERENCES public.eval_sets(id) ON DELETE CASCADE,
  conversation  JSONB NOT NULL,    -- Array of invocations (ADK format)
  session_input JSONB NOT NULL DEFAULT '{}',
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_eval_cases_set
  ON public.eval_cases (eval_set_id);

-- ────────────────────────────────────────────────────────────────────────────
-- 13. EVAL_RESULTS — Results of running evaluations
-- ────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.eval_results (
  id                        TEXT PRIMARY KEY,
  eval_case_id              TEXT NOT NULL REFERENCES public.eval_cases(id) ON DELETE CASCADE,
  agent_id                  TEXT NOT NULL REFERENCES public.agents(id) ON DELETE CASCADE,
  tool_trajectory_score     REAL,
  response_match_score      REAL,
  overall_pass              BOOLEAN NOT NULL DEFAULT FALSE,
  actual_trajectory         JSONB,     -- list of actual tool call names
  expected_trajectory       JSONB,     -- list of expected tool call names
  actual_response           TEXT,
  expected_response         TEXT,
  metadata                  JSONB DEFAULT '{}',
  evaluated_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_eval_results_case
  ON public.eval_results (eval_case_id);

CREATE INDEX IF NOT EXISTS idx_eval_results_agent
  ON public.eval_results (agent_id, evaluated_at DESC);

-- ────────────────────────────────────────────────────────────────────────────
-- 14. WORKFLOWS — Workflow graph storage
-- ────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.workflows (
  id          TEXT PRIMARY KEY,
  user_id     TEXT NOT NULL,
  title       TEXT NOT NULL DEFAULT '',
  prompt      TEXT NOT NULL DEFAULT '',
  graph_json  JSONB,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_workflows_user
  ON public.workflows (user_id, updated_at DESC);

-- ────────────────────────────────────────────────────────────────────────────
-- 15. MEMORY_VECTORS — Vector memory store (alternative to PGVECTOR)
-- ────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.memory_vectors (
  id          TEXT PRIMARY KEY,
  user_id     TEXT NOT NULL,
  namespace   TEXT NOT NULL DEFAULT 'default',
  text        TEXT NOT NULL,
  embedding   vector(768) NOT NULL,
  metadata    JSONB DEFAULT '{}',
  stored_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_memory_vectors_ns
  ON public.memory_vectors (namespace, user_id);

CREATE INDEX IF NOT EXISTS idx_memory_vectors_hnsw
  ON public.memory_vectors
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

-- ────────────────────────────────────────────────────────────────────────────
-- RPC: Semantic search function for notes
-- ────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION match_notes(
  query_embedding vector(768),
  match_threshold FLOAT DEFAULT 0.5,
  match_count     INT DEFAULT 10,
  filter_user_id  TEXT DEFAULT NULL
)
RETURNS TABLE (
  note_id    TEXT,
  title      TEXT,
  excerpt    TEXT,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    n.id AS note_id,
    n.title,
    n.excerpt,
    1 - (ne.embedding <=> query_embedding) AS similarity
  FROM public.note_embeddings ne
  JOIN public.notes n ON n.id = ne.note_id
  WHERE (filter_user_id IS NULL OR n.user_id = filter_user_id)
    AND 1 - (ne.embedding <=> query_embedding) > match_threshold
  ORDER BY ne.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- ────────────────────────────────────────────────────────────────────────────
-- RPC: Semantic search function for memory
-- ────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION match_memory(
  query_embedding vector(768),
  match_threshold FLOAT DEFAULT 0.5,
  match_count     INT DEFAULT 5,
  filter_namespace TEXT DEFAULT 'default',
  filter_user_id  TEXT DEFAULT NULL
)
RETURNS TABLE (
  memory_id  TEXT,
  text       TEXT,
  metadata   JSONB,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    mv.id AS memory_id,
    mv.text,
    mv.metadata,
    1 - (mv.embedding <=> query_embedding) AS similarity
  FROM public.memory_vectors mv
  WHERE mv.namespace = filter_namespace
    AND (filter_user_id IS NULL OR mv.user_id = filter_user_id)
    AND 1 - (mv.embedding <=> query_embedding) > match_threshold
  ORDER BY mv.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- ────────────────────────────────────────────────────────────────────────────
-- Row Level Security policies
-- ────────────────────────────────────────────────────────────────────────────
ALTER TABLE public.notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.note_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.agent_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.agent_action_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workflows ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.memory_vectors ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to CRUD their own data
CREATE POLICY notes_user_policy ON public.notes
  FOR ALL USING (user_id = auth.uid()::TEXT OR user_id = 'web-local');

CREATE POLICY note_embeddings_policy ON public.note_embeddings
  FOR ALL USING (
    EXISTS (SELECT 1 FROM public.notes n WHERE n.id = note_id AND (n.user_id = auth.uid()::TEXT OR n.user_id = 'web-local'))
  );

CREATE POLICY projects_user_policy ON public.projects
  FOR ALL USING (user_id = auth.uid()::TEXT OR user_id = 'web-local');

CREATE POLICY agent_runs_user_policy ON public.agent_runs
  FOR ALL USING (user_id = auth.uid()::TEXT OR user_id = 'web-local');

CREATE POLICY agent_action_log_policy ON public.agent_action_log
  FOR ALL USING (
    EXISTS (SELECT 1 FROM public.agent_runs r WHERE r.id = run_id AND (r.user_id = auth.uid()::TEXT OR r.user_id = 'web-local'))
  );

CREATE POLICY workflows_user_policy ON public.workflows
  FOR ALL USING (user_id = auth.uid()::TEXT OR user_id = 'web-local');

CREATE POLICY memory_vectors_policy ON public.memory_vectors
  FOR ALL USING (user_id = auth.uid()::TEXT OR user_id = 'web-local');

-- Service role bypasses RLS, anon/public key gets RLS protection
