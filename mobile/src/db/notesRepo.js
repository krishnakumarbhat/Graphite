import { DEFAULT_NOTE_TITLE } from '../config/constants';
import { getAll, getFirst, runQuery } from './db';
import { createUuid } from '../utils/id';
import { createIsoTimestamp } from '../utils/time';

export const createNote = async ({ title = DEFAULT_NOTE_TITLE, content = '', sourcePath = null } = {}) => {
  const timestamp = createIsoTimestamp();
  const note = {
    id: createUuid(),
    title: title?.trim() || DEFAULT_NOTE_TITLE,
    content,
    created_at: timestamp,
    updated_at: timestamp,
    source_path: sourcePath,
  };

  await runQuery(
    `INSERT INTO notes (id, title, content, created_at, updated_at, source_path)
     VALUES (?, ?, ?, ?, ?, ?);`,
    [note.id, note.title, note.content, note.created_at, note.updated_at, note.source_path],
  );

  return note;
};

export const listNotes = async () => getAll(
  'SELECT id, title, content, created_at, updated_at, source_path FROM notes ORDER BY updated_at DESC;'
);

export const getNoteById = async (noteId) => getFirst(
  'SELECT id, title, content, created_at, updated_at, source_path FROM notes WHERE id = ? LIMIT 1;',
  [noteId],
);

export const updateNote = async (noteId, updates = {}) => {
  const existingNote = await getNoteById(noteId);

  if (!existingNote) {
    return null;
  }

  const nextNote = {
    ...existingNote,
    title: updates.title?.trim() || existingNote.title,
    content: updates.content ?? existingNote.content,
    source_path: updates.sourcePath ?? existingNote.source_path,
    updated_at: createIsoTimestamp(),
  };

  await runQuery(
    `UPDATE notes
     SET title = ?, content = ?, source_path = ?, updated_at = ?
     WHERE id = ?;`,
    [nextNote.title, nextNote.content, nextNote.source_path, nextNote.updated_at, noteId],
  );

  return getNoteById(noteId);
};

export const deleteNote = async (noteId) => {
  await runQuery('DELETE FROM notes WHERE id = ?;', [noteId]);
  return true;
};

export const countNotes = async () => {
  const result = await getFirst('SELECT COUNT(*) as count FROM notes;');
  return Number(result?.count ?? 0);
};
