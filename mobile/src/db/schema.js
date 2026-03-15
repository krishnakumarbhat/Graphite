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
};
