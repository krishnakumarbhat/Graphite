export const migrationStatements = {
  1: [
    `CREATE TABLE IF NOT EXISTS notes (
      id TEXT PRIMARY KEY NOT NULL,
      title TEXT NOT NULL DEFAULT '',
      content TEXT NOT NULL DEFAULT '',
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL,
      source_path TEXT
    );`,
    'CREATE INDEX IF NOT EXISTS idx_notes_updated_at ON notes (updated_at DESC);',
    `CREATE TABLE IF NOT EXISTS workflows (
      id TEXT PRIMARY KEY NOT NULL,
      title TEXT NOT NULL DEFAULT '',
      prompt TEXT NOT NULL DEFAULT '',
      graph_json TEXT,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL
    );`,
    'CREATE INDEX IF NOT EXISTS idx_workflows_updated_at ON workflows (updated_at DESC);',
  ],
  2: [
    `CREATE TABLE IF NOT EXISTS users (
      id TEXT PRIMARY KEY NOT NULL,
      email TEXT,
      display_name TEXT,
      auth_provider TEXT NOT NULL DEFAULT 'local',
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL
    );`,
    `INSERT OR IGNORE INTO users (id, email, display_name, auth_provider, created_at, updated_at)
     VALUES ('local-user', 'local@graphite.app', 'Local User', 'local', datetime('now'), datetime('now'));`,

    `CREATE TABLE IF NOT EXISTS notes_v2 (
      id TEXT PRIMARY KEY NOT NULL,
      user_id TEXT NOT NULL,
      title TEXT NOT NULL DEFAULT '',
      content TEXT NOT NULL DEFAULT '',
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL,
      source_path TEXT,
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );`,
    `INSERT OR REPLACE INTO notes_v2 (id, user_id, title, content, created_at, updated_at, source_path)
     SELECT id, 'local-user', title, content, created_at, updated_at, source_path FROM notes;`,
    'DROP TABLE IF EXISTS notes;',
    'ALTER TABLE notes_v2 RENAME TO notes;',
    'CREATE INDEX IF NOT EXISTS idx_notes_user_updated_at ON notes (user_id, updated_at DESC);',

    `CREATE TABLE IF NOT EXISTS workflows_v2 (
      id TEXT PRIMARY KEY NOT NULL,
      user_id TEXT NOT NULL,
      title TEXT NOT NULL DEFAULT '',
      prompt TEXT NOT NULL DEFAULT '',
      graph_json TEXT,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL,
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );`,
    `INSERT OR REPLACE INTO workflows_v2 (id, user_id, title, prompt, graph_json, created_at, updated_at)
     SELECT id, 'local-user', title, prompt, graph_json, created_at, updated_at FROM workflows;`,
    'DROP TABLE IF EXISTS workflows;',
    'ALTER TABLE workflows_v2 RENAME TO workflows;',
    'CREATE INDEX IF NOT EXISTS idx_workflows_user_updated_at ON workflows (user_id, updated_at DESC);',
  ],
};
