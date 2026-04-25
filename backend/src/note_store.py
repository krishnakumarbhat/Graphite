import json
import sqlite3
from pathlib import Path
from typing import Any


class LocalNoteStore:
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

      CREATE INDEX IF NOT EXISTS idx_notes_user_updated_at
      ON notes(user_id, updated_at DESC);
      '''
    )
    self.connection.commit()

  def list_notes(self, user_id: str, limit: int = 100) -> list[dict[str, Any]]:
    cursor = self.connection.execute(
      '''
      SELECT id, user_id, title, content, excerpt, source_path, created_at, updated_at,
             is_ai_generated
      FROM notes
      WHERE user_id = ?
      ORDER BY updated_at DESC
      LIMIT ?
      ''',
      (user_id, limit),
    )
    return [self._row_to_note(row) for row in cursor.fetchall()]

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
    return self._row_to_note(row) if row else None

  def upsert_note(self, payload: dict[str, Any], embedding: list[float]) -> dict[str, Any]:
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

    stored_note = self.get_note(payload['id'])
    if stored_note is None:
      raise RuntimeError('Saved note could not be reloaded from SQLite.')
    return stored_note

  def close(self) -> None:
    self.connection.close()

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
    }