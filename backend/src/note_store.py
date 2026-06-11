import json
import logging
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any


def _format_pgvector_literal(values: list[float]) -> str:
  return '[' + ','.join(f'{float(value):.10f}' for value in values) + ']'


def _parse_pgvector_payload(payload: Any) -> list[float]:
  if isinstance(payload, list):
    return [float(value) for value in payload]
  if isinstance(payload, str):
    cleaned = payload.strip()
    if not cleaned:
      return []
    try:
      parsed = json.loads(cleaned)
    except json.JSONDecodeError:
      parsed = [value.strip() for value in cleaned.strip('[]').split(',') if value.strip()]
    return [float(value) for value in parsed]
  return []


class LocalNoteStore:
  is_remote = False

  def __init__(self, database_path: Path) -> None:
    self.database_path = Path(database_path)
    self.database_path.parent.mkdir(parents=True, exist_ok=True)
    self.connection = sqlite3.connect(self.database_path, check_same_thread=False)
    self.connection.row_factory = sqlite3.Row
    self.connection.execute('PRAGMA foreign_keys = ON')
    self._ensure_schema()

  def _ensure_schema(self) -> None:
    self.connection.executescript(
      '''
      CREATE TABLE IF NOT EXISTS notes (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        title TEXT NOT NULL DEFAULT '',
        content TEXT NOT NULL DEFAULT '',
        excerpt TEXT NOT NULL DEFAULT '',
        source_path TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        is_ai_generated INTEGER NOT NULL DEFAULT 0
      );

      CREATE TABLE IF NOT EXISTS note_embeddings (
        note_id TEXT PRIMARY KEY,
        embedding_json TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(note_id) REFERENCES notes(id) ON DELETE CASCADE
      );

      CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
      );

      CREATE TABLE IF NOT EXISTS note_tags (
        note_id TEXT NOT NULL,
        tag_id INTEGER NOT NULL,
        PRIMARY KEY (note_id, tag_id),
        FOREIGN KEY(note_id) REFERENCES notes(id) ON DELETE CASCADE,
        FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE CASCADE
      );

      CREATE INDEX IF NOT EXISTS idx_notes_user_updated_at
      ON notes(user_id, updated_at DESC);

      CREATE INDEX IF NOT EXISTS idx_note_tags_note
      ON note_tags(note_id);

      CREATE INDEX IF NOT EXISTS idx_note_tags_tag
      ON note_tags(tag_id);

      CREATE TABLE IF NOT EXISTS agent_runs (
        id TEXT PRIMARY KEY,
        agent_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        task TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        result_json TEXT,
        error_message TEXT,
        started_at TEXT NOT NULL,
        completed_at TEXT,
        duration_ms INTEGER
      );

      CREATE INDEX IF NOT EXISTS idx_agent_runs_started
      ON agent_runs(agent_id, started_at DESC);

      CREATE TABLE IF NOT EXISTS agent_action_log (
        id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        step_index INTEGER NOT NULL,
        action_type TEXT NOT NULL,
        tool_name TEXT,
        tool_args TEXT,
        tool_result TEXT,
        reasoning TEXT,
        timestamp TEXT NOT NULL,
        duration_ms INTEGER,
        FOREIGN KEY(run_id) REFERENCES agent_runs(id) ON DELETE CASCADE
      );

      CREATE INDEX IF NOT EXISTS idx_action_log_run
      ON agent_action_log(run_id, step_index);

      CREATE TABLE IF NOT EXISTS eval_results (
        id TEXT PRIMARY KEY,
        eval_case_id TEXT NOT NULL,
        agent_id TEXT NOT NULL,
        tool_trajectory_score REAL,
        response_match_score REAL,
        overall_pass INTEGER NOT NULL DEFAULT 0,
        actual_trajectory TEXT,
        expected_trajectory TEXT,
        actual_response TEXT,
        expected_response TEXT,
        metadata TEXT DEFAULT '{}',
        evaluated_at TEXT NOT NULL
      );

      CREATE INDEX IF NOT EXISTS idx_eval_results_agent
      ON eval_results(agent_id, evaluated_at DESC);

      CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        name TEXT NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        repo_url TEXT DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
      );

      CREATE TABLE IF NOT EXISTS project_notes (
        project_id TEXT NOT NULL,
        note_id TEXT NOT NULL,
        PRIMARY KEY (project_id, note_id),
        FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY(note_id) REFERENCES notes(id) ON DELETE CASCADE
      );
      '''
    )
    self.connection.commit()

  def list_notes(self, user_id: str, limit: int = 100) -> list[dict[str, Any]]:
    rows = self.connection.execute(
      '''
      SELECT id, user_id, title, content, excerpt, source_path, created_at, updated_at,
             is_ai_generated
      FROM notes
      WHERE user_id = ?
      ORDER BY updated_at DESC
      LIMIT ?
      ''',
      (user_id, limit),
    ).fetchall()
    notes = [self._row_to_note(row) for row in rows]
    return self._attach_tags(notes)

  def get_note(self, note_id: str) -> dict[str, Any] | None:
    row = self.connection.execute(
      '''
      SELECT id, user_id, title, content, excerpt, source_path, created_at, updated_at,
             is_ai_generated
      FROM notes
      WHERE id = ?
      ''',
      (note_id,),
    ).fetchone()
    if not row:
      return None

    note = self._row_to_note(row)
    self._attach_tags([note])
    return note

  def upsert_note(
    self,
    payload: dict[str, Any],
    embedding: list[float],
    *,
    tags: list[str] | None = None,
  ) -> dict[str, Any]:
    normalized_tags = self._normalize_tags(tags) if tags is not None else None
    with self.connection:
      self.connection.execute(
        '''
        INSERT INTO notes (
          id,
          user_id,
          title,
          content,
          excerpt,
          source_path,
          created_at,
          updated_at,
          is_ai_generated
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          user_id = excluded.user_id,
          title = excluded.title,
          content = excluded.content,
          excerpt = excluded.excerpt,
          source_path = excluded.source_path,
          updated_at = excluded.updated_at,
          is_ai_generated = excluded.is_ai_generated
        ''',
        (
          payload['id'],
          payload['user_id'],
          payload['title'],
          payload['content'],
          payload['excerpt'],
          payload.get('source_path'),
          payload['created_at'],
          payload['updated_at'],
          int(payload.get('is_ai_generated', False)),
        ),
      )
      self.connection.execute(
        '''
        INSERT INTO note_embeddings (note_id, embedding_json, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(note_id) DO UPDATE SET
          embedding_json = excluded.embedding_json,
          updated_at = excluded.updated_at
        ''',
        (
          payload['id'],
          json.dumps(embedding),
          payload['updated_at'],
        ),
      )
      if normalized_tags is not None:
        self._sync_note_tags(payload['id'], normalized_tags)

    stored_note = self.get_note(payload['id'])
    if stored_note is None:
      raise RuntimeError('Saved note could not be reloaded from SQLite.')
    return stored_note

  def list_notes_by_tag(self, user_id: str, tag: str, limit: int = 50) -> list[dict[str, Any]]:
    normalized_tag = tag.strip().lower()
    if not normalized_tag:
      return []

    rows = self.connection.execute(
      '''
      SELECT DISTINCT n.id, n.user_id, n.title, n.content, n.excerpt, n.source_path,
             n.created_at, n.updated_at, n.is_ai_generated
      FROM notes n
      JOIN note_tags nt ON nt.note_id = n.id
      JOIN tags t ON t.id = nt.tag_id
      WHERE n.user_id = ? AND t.name = ?
      ORDER BY n.updated_at DESC
      LIMIT ?
      ''',
      (user_id, normalized_tag, limit),
    ).fetchall()
    notes = [self._row_to_note(row) for row in rows]
    return self._attach_tags(notes)

  def list_tag_counts(self, user_id: str) -> dict[str, int]:
    rows = self.connection.execute(
      '''
      SELECT t.name, COUNT(*) AS note_count
      FROM notes n
      JOIN note_tags nt ON nt.note_id = n.id
      JOIN tags t ON t.id = nt.tag_id
      WHERE n.user_id = ?
      GROUP BY t.name
      ORDER BY note_count DESC, t.name ASC
      ''',
      (user_id,),
    ).fetchall()
    return {str(row['name']): int(row['note_count']) for row in rows}

  def get_rankable_notes(self, user_id: str, limit: int = 250) -> list[dict[str, Any]]:
    rows = self.connection.execute(
      '''
      SELECT n.id, n.user_id, n.title, n.content, n.excerpt, n.source_path,
             n.created_at, n.updated_at, n.is_ai_generated, e.embedding_json
      FROM notes n
      JOIN note_embeddings e ON e.note_id = n.id
      WHERE n.user_id = ?
      ORDER BY n.updated_at DESC
      LIMIT ?
      ''',
      (user_id, limit),
    ).fetchall()
    notes: list[dict[str, Any]] = []
    for row in rows:
      note = self._row_to_note(row)
      try:
        note['embedding'] = [float(value) for value in json.loads(row['embedding_json'])]
      except (TypeError, ValueError, json.JSONDecodeError):
        note['embedding'] = []
      notes.append(note)
    return self._attach_tags(notes)

  def close(self) -> None:
    self.connection.close()

  # ── Agent run & action log ──────────────────────────────────────────────

  def insert_agent_run(self, run: dict[str, Any]) -> None:
    with self.connection:
      self.connection.execute(
        '''
        INSERT INTO agent_runs (id, agent_id, user_id, task, status, result_json,
                                error_message, started_at, completed_at, duration_ms)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
          run['id'], run['agent_id'], run['user_id'], run['task'],
          run.get('status', 'pending'), run.get('result_json'),
          run.get('error_message'), run['started_at'],
          run.get('completed_at'), run.get('duration_ms'),
        ),
      )

  def update_agent_run(self, run_id: str, updates: dict[str, Any]) -> None:
    set_clauses = ', '.join(f'{k} = ?' for k in updates)
    values = list(updates.values()) + [run_id]
    with self.connection:
      self.connection.execute(
        f'UPDATE agent_runs SET {set_clauses} WHERE id = ?',
        values,
      )

  def insert_action_log(self, entry: dict[str, Any]) -> None:
    with self.connection:
      self.connection.execute(
        '''
        INSERT INTO agent_action_log (id, run_id, step_index, action_type, tool_name,
                                      tool_args, tool_result, reasoning, timestamp, duration_ms)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
          entry['id'], entry['run_id'], entry['step_index'], entry['action_type'],
          entry.get('tool_name'), entry.get('tool_args'), entry.get('tool_result'),
          entry.get('reasoning'), entry['timestamp'], entry.get('duration_ms'),
        ),
      )

  def get_agent_run(self, run_id: str) -> dict[str, Any] | None:
    row = self.connection.execute(
      'SELECT * FROM agent_runs WHERE id = ?', (run_id,)
    ).fetchone()
    return dict(row) if row else None

  def list_agent_runs(self, agent_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    if agent_id:
      rows = self.connection.execute(
        'SELECT * FROM agent_runs WHERE agent_id = ? ORDER BY started_at DESC LIMIT ?',
        (agent_id, limit),
      ).fetchall()
    else:
      rows = self.connection.execute(
        'SELECT * FROM agent_runs ORDER BY started_at DESC LIMIT ?', (limit,)
      ).fetchall()
    return [dict(r) for r in rows]

  def list_action_logs(self, run_id: str) -> list[dict[str, Any]]:
    rows = self.connection.execute(
      'SELECT * FROM agent_action_log WHERE run_id = ? ORDER BY step_index', (run_id,)
    ).fetchall()
    return [dict(r) for r in rows]

  def upsert_project(self, project: dict[str, Any]) -> dict[str, Any]:
    with self.connection:
      self.connection.execute(
        '''
        INSERT INTO projects (id, user_id, name, description, repo_url, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          user_id = excluded.user_id,
          name = excluded.name,
          description = excluded.description,
          repo_url = excluded.repo_url,
          updated_at = excluded.updated_at
        ''',
        (
          project['id'],
          project['user_id'],
          project['name'],
          project.get('description', ''),
          project.get('repo_url', ''),
          project['created_at'],
          project['updated_at'],
        ),
      )
    row = self.connection.execute('SELECT * FROM projects WHERE id = ?', (project['id'],)).fetchone()
    return dict(row) if row else project

  def link_project_note(self, project_id: str, note_id: str) -> None:
    with self.connection:
      self.connection.execute(
        'INSERT OR IGNORE INTO project_notes (project_id, note_id) VALUES (?, ?)',
        (project_id, note_id),
      )

  def get_all_notes_content(self, user_id: str | None = None) -> list[dict[str, str]]:
    """Return id, title, content for all notes — used as agent context."""
    if user_id:
      rows = self.connection.execute(
        'SELECT id, title, content FROM notes WHERE user_id = ? ORDER BY updated_at DESC',
        (user_id,),
      ).fetchall()
    else:
      rows = self.connection.execute(
        'SELECT id, title, content FROM notes ORDER BY updated_at DESC'
      ).fetchall()
    return [{'id': r['id'], 'title': r['title'], 'content': r['content']} for r in rows]

  # ── Eval results ────────────────────────────────────────────────────────

  def insert_eval_result(self, result: dict[str, Any]) -> None:
    with self.connection:
      self.connection.execute(
        '''
        INSERT INTO eval_results (id, eval_case_id, agent_id, tool_trajectory_score,
          response_match_score, overall_pass, actual_trajectory, expected_trajectory,
          actual_response, expected_response, metadata, evaluated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
          result['id'], result['eval_case_id'], result['agent_id'],
          result.get('tool_trajectory_score'), result.get('response_match_score'),
          int(result.get('overall_pass', False)),
          result.get('actual_trajectory'), result.get('expected_trajectory'),
          result.get('actual_response'), result.get('expected_response'),
          result.get('metadata', '{}'), result['evaluated_at'],
        ),
      )

  def list_eval_results(self, agent_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    if agent_id:
      rows = self.connection.execute(
        'SELECT * FROM eval_results WHERE agent_id = ? ORDER BY evaluated_at DESC LIMIT ?',
        (agent_id, limit),
      ).fetchall()
    else:
      rows = self.connection.execute(
        'SELECT * FROM eval_results ORDER BY evaluated_at DESC LIMIT ?',
        (limit,),
      ).fetchall()
    return [dict(row) for row in rows]

  def _attach_tags(self, notes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not notes:
      return notes

    note_ids = [note['id'] for note in notes]
    tag_map = self._load_tags_for_note_ids(note_ids)
    for note in notes:
      note['tags'] = tag_map.get(note['id'], [])
    return notes

  def _load_tags_for_note_ids(self, note_ids: list[str]) -> dict[str, list[str]]:
    if not note_ids:
      return {}

    placeholders = ','.join('?' for _ in note_ids)
    rows = self.connection.execute(
      f'''
      SELECT nt.note_id, t.name
      FROM note_tags nt
      JOIN tags t ON t.id = nt.tag_id
      WHERE nt.note_id IN ({placeholders})
      ORDER BY t.name ASC
      ''',
      note_ids,
    ).fetchall()

    tag_map: dict[str, list[str]] = {note_id: [] for note_id in note_ids}
    for row in rows:
      tag_map[str(row['note_id'])].append(str(row['name']))
    return tag_map

  def _sync_note_tags(self, note_id: str, tags: list[str]) -> None:
    self.connection.execute('DELETE FROM note_tags WHERE note_id = ?', (note_id,))
    if not tags:
      return

    self.connection.executemany(
      'INSERT OR IGNORE INTO tags (name) VALUES (?)',
      [(tag,) for tag in tags],
    )
    placeholders = ','.join('?' for _ in tags)
    tag_rows = self.connection.execute(
      f'SELECT id, name FROM tags WHERE name IN ({placeholders})',
      tags,
    ).fetchall()
    tag_ids = {str(row['name']): int(row['id']) for row in tag_rows}
    self.connection.executemany(
      'INSERT OR IGNORE INTO note_tags (note_id, tag_id) VALUES (?, ?)',
      [(note_id, tag_ids[tag]) for tag in tags if tag in tag_ids],
    )

  @staticmethod
  def _normalize_tags(tags: list[str] | None) -> list[str]:
    normalized = sorted({str(tag).strip().lower() for tag in (tags or []) if str(tag).strip()})
    return normalized or ['general']

  @staticmethod
  def _row_to_note(row: sqlite3.Row) -> dict[str, Any]:
    return {
      'id': row['id'],
      'user_id': row['user_id'],
      'title': row['title'],
      'content': row['content'],
      'excerpt': row['excerpt'],
      'source_path': row['source_path'],
      'created_at': row['created_at'],
      'updated_at': row['updated_at'],
      'is_ai_generated': bool(row['is_ai_generated']),
      'tags': [],
    }


class SupabaseNoteStore:
  is_remote = True
  connection = None

  def __init__(self, supabase_client: Any, logger: logging.Logger | None = None) -> None:
    self.supabase = supabase_client
    self.logger = logger or logging.getLogger('graphite.note_store')

  def list_notes(self, user_id: str, limit: int = 100) -> list[dict[str, Any]]:
    rows = (
      self.supabase
      .table('notes')
      .select('*')
      .eq('user_id', user_id)
      .order('updated_at', desc=True)
      .limit(limit)
      .execute()
      .data
      or []
    )
    notes = [self._row_to_note(row) for row in rows]
    return self._attach_tags(notes)

  def get_note(self, note_id: str) -> dict[str, Any] | None:
    rows = (
      self.supabase
      .table('notes')
      .select('*')
      .eq('id', note_id)
      .limit(1)
      .execute()
      .data
      or []
    )
    if not rows:
      return None

    note = self._row_to_note(rows[0])
    self._attach_tags([note])
    return note

  def upsert_note(
    self,
    payload: dict[str, Any],
    embedding: list[float],
    *,
    tags: list[str] | None = None,
  ) -> dict[str, Any]:
    self.supabase.table('notes').upsert(payload, on_conflict='id').execute()
    self.supabase.table('note_embeddings').upsert(
      {
        'note_id': payload['id'],
        'embedding': _format_pgvector_literal(embedding),
        'updated_at': payload['updated_at'],
      },
      on_conflict='note_id',
    ).execute()
    self._sync_note_tags(payload['id'], self._normalize_tags(tags))

    stored_note = self.get_note(payload['id'])
    if stored_note is None:
      raise RuntimeError('Saved note could not be reloaded from Supabase.')
    return stored_note

  def list_notes_by_tag(self, user_id: str, tag: str, limit: int = 50) -> list[dict[str, Any]]:
    normalized_tag = tag.strip().lower()
    if not normalized_tag:
      return []

    tag_rows = (
      self.supabase
      .table('tags')
      .select('id')
      .eq('name', normalized_tag)
      .limit(1)
      .execute()
      .data
      or []
    )
    if not tag_rows:
      return []

    note_tag_rows = (
      self.supabase
      .table('note_tags')
      .select('note_id')
      .eq('tag_id', tag_rows[0]['id'])
      .execute()
      .data
      or []
    )
    note_ids = [str(row['note_id']) for row in note_tag_rows]
    if not note_ids:
      return []

    rows = (
      self.supabase
      .table('notes')
      .select('*')
      .eq('user_id', user_id)
      .in_('id', note_ids)
      .order('updated_at', desc=True)
      .limit(limit)
      .execute()
      .data
      or []
    )
    notes = [self._row_to_note(row) for row in rows]
    return self._attach_tags(notes)

  def list_tag_counts(self, user_id: str) -> dict[str, int]:
    note_rows = (
      self.supabase
      .table('notes')
      .select('id')
      .eq('user_id', user_id)
      .execute()
      .data
      or []
    )
    note_ids = [str(row['id']) for row in note_rows]
    if not note_ids:
      return {}

    tag_map = self._load_tags_for_note_ids(note_ids)
    counts = Counter(tag for tags in tag_map.values() for tag in tags)
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))

  def get_rankable_notes(self, user_id: str, limit: int = 250) -> list[dict[str, Any]]:
    notes = self.list_notes(user_id, limit=limit)
    if not notes:
      return []

    note_ids = [note['id'] for note in notes]
    embedding_rows = (
      self.supabase
      .table('note_embeddings')
      .select('note_id, embedding')
      .in_('note_id', note_ids)
      .execute()
      .data
      or []
    )
    embedding_map = {
      str(row['note_id']): _parse_pgvector_payload(row.get('embedding'))
      for row in embedding_rows
    }

    rankable_notes: list[dict[str, Any]] = []
    for note in notes:
      embedding = embedding_map.get(note['id'])
      if not embedding:
        continue
      rankable_notes.append({**note, 'embedding': embedding})
    return rankable_notes

  def close(self) -> None:
    return None

  def insert_agent_run(self, run: dict[str, Any]) -> None:
    self.supabase.table('agent_runs').upsert(run, on_conflict='id').execute()

  def update_agent_run(self, run_id: str, updates: dict[str, Any]) -> None:
    self.supabase.table('agent_runs').update(updates).eq('id', run_id).execute()

  def insert_action_log(self, entry: dict[str, Any]) -> None:
    self.supabase.table('agent_action_log').upsert(entry, on_conflict='id').execute()

  def get_agent_run(self, run_id: str) -> dict[str, Any] | None:
    rows = (
      self.supabase
      .table('agent_runs')
      .select('*')
      .eq('id', run_id)
      .limit(1)
      .execute()
      .data
      or []
    )
    return rows[0] if rows else None

  def list_agent_runs(self, agent_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    query = self.supabase.table('agent_runs').select('*').order('started_at', desc=True).limit(limit)
    if agent_id:
      query = query.eq('agent_id', agent_id)
    return query.execute().data or []

  def list_action_logs(self, run_id: str) -> list[dict[str, Any]]:
    return (
      self.supabase
      .table('agent_action_log')
      .select('*')
      .eq('run_id', run_id)
      .order('step_index')
      .execute()
      .data
      or []
    )

  def upsert_project(self, project: dict[str, Any]) -> dict[str, Any]:
    self.supabase.table('projects').upsert(project, on_conflict='id').execute()
    rows = (
      self.supabase
      .table('projects')
      .select('*')
      .eq('id', project['id'])
      .limit(1)
      .execute()
      .data
      or []
    )
    return rows[0] if rows else project

  def link_project_note(self, project_id: str, note_id: str) -> None:
    self.supabase.table('project_notes').upsert(
      {'project_id': project_id, 'note_id': note_id},
      on_conflict='project_id,note_id',
    ).execute()

  def get_all_notes_content(self, user_id: str | None = None) -> list[dict[str, str]]:
    query = self.supabase.table('notes').select('id, title, content').order('updated_at', desc=True)
    if user_id:
      query = query.eq('user_id', user_id)
    rows = query.execute().data or []
    return [
      {'id': str(row['id']), 'title': str(row.get('title', '')), 'content': str(row.get('content', ''))}
      for row in rows
    ]

  def insert_eval_result(self, result: dict[str, Any]) -> None:
    self.supabase.table('eval_results').upsert(result, on_conflict='id').execute()

  def list_eval_results(self, agent_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    query = self.supabase.table('eval_results').select('*').order('evaluated_at', desc=True).limit(limit)
    if agent_id:
      query = query.eq('agent_id', agent_id)
    return query.execute().data or []

  def _attach_tags(self, notes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not notes:
      return notes

    note_ids = [note['id'] for note in notes]
    tag_map = self._load_tags_for_note_ids(note_ids)
    for note in notes:
      note['tags'] = tag_map.get(note['id'], [])
    return notes

  def _load_tags_for_note_ids(self, note_ids: list[str]) -> dict[str, list[str]]:
    if not note_ids:
      return {}

    note_tag_rows = (
      self.supabase
      .table('note_tags')
      .select('note_id, tag_id')
      .in_('note_id', note_ids)
      .execute()
      .data
      or []
    )
    tag_ids = sorted({int(row['tag_id']) for row in note_tag_rows})
    tag_rows = []
    if tag_ids:
      tag_rows = (
        self.supabase
        .table('tags')
        .select('id, name')
        .in_('id', tag_ids)
        .execute()
        .data
        or []
      )
    tag_names = {int(row['id']): str(row['name']) for row in tag_rows}
    tag_map: dict[str, list[str]] = {note_id: [] for note_id in note_ids}
    for row in note_tag_rows:
      note_id = str(row['note_id'])
      tag_name = tag_names.get(int(row['tag_id']))
      if tag_name:
        tag_map[note_id].append(tag_name)

    for tags in tag_map.values():
      tags.sort()
    return tag_map

  def _sync_note_tags(self, note_id: str, tags: list[str]) -> None:
    self.supabase.table('note_tags').delete().eq('note_id', note_id).execute()
    if not tags:
      return

    self.supabase.table('tags').upsert(
      [{'name': tag} for tag in tags],
      on_conflict='name',
    ).execute()
    tag_rows = (
      self.supabase
      .table('tags')
      .select('id, name')
      .in_('name', tags)
      .execute()
      .data
      or []
    )
    note_tag_rows = [
      {'note_id': note_id, 'tag_id': int(row['id'])}
      for row in tag_rows
    ]
    if note_tag_rows:
      self.supabase.table('note_tags').upsert(
        note_tag_rows,
        on_conflict='note_id,tag_id',
      ).execute()

  @staticmethod
  def _normalize_tags(tags: list[str] | None) -> list[str]:
    normalized = sorted({str(tag).strip().lower() for tag in (tags or []) if str(tag).strip()})
    return normalized or ['general']

  @staticmethod
  def _row_to_note(row: dict[str, Any]) -> dict[str, Any]:
    return {
      'id': str(row['id']),
      'user_id': str(row['user_id']),
      'title': str(row.get('title', '')),
      'content': str(row.get('content', '')),
      'excerpt': str(row.get('excerpt', '')),
      'source_path': row.get('source_path'),
      'created_at': str(row.get('created_at', '')),
      'updated_at': str(row.get('updated_at', '')),
      'is_ai_generated': bool(row.get('is_ai_generated', False)),
      'tags': [],
    }


def build_note_store(database_path: Path, *, supabase: Any = None, logger: logging.Logger | None = None) -> Any:
  if supabase is not None:
    return SupabaseNoteStore(supabase, logger=logger)
  return LocalNoteStore(database_path)