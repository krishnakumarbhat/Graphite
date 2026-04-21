import { DEFAULT_NOTE_TITLE } from '../config/constants';
import { getAll, getFirst, runQuery } from './db';
import { createUuid } from '../utils/id';
import { createIsoTimestamp } from '../utils/time';

export const createNote = async ({ userId, title = DEFAULT_NOTE_TITLE, content = '', sourcePath = null } = {}) => {
  if (!userId) {
    throw new Error('userId is required to create a note.');
  }

  const timestamp = createIsoTimestamp();
  const note = {
    id: createUuid(),
    user_id: userId,
    title: title?.trim() || DEFAULT_NOTE_TITLE,
    content,
    created_at: timestamp,
    updated_at: timestamp,
    source_path: sourcePath,
  };

  await runQuery(
    `INSERT INTO notes (id, user_id, title, content, created_at, updated_at, source_path)
     VALUES (?, ?, ?, ?, ?, ?, ?);`,
    [note.id, note.user_id, note.title, note.content, note.created_at, note.updated_at, note.source_path],
  );

  return note;
};

export const listNotes = async (userId) => getAll(
  'SELECT id, user_id, title, content, created_at, updated_at, source_path FROM notes WHERE user_id = ? ORDER BY updated_at DESC;',
  [userId],
);

export const getNoteById = async (noteId, userId) => getFirst(
  'SELECT id, user_id, title, content, created_at, updated_at, source_path FROM notes WHERE id = ? AND user_id = ? LIMIT 1;',
  [noteId, userId],
);

export const updateNote = async (noteId, userId, updates = {}) => {
  const existingNote = await getNoteById(noteId, userId);

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
     WHERE id = ? AND user_id = ?;`,
    [nextNote.title, nextNote.content, nextNote.source_path, nextNote.updated_at, noteId, userId],
  );

  return getNoteById(noteId, userId);
};

export const deleteNote = async (noteId, userId) => {
  await runQuery('DELETE FROM notes WHERE id = ? AND user_id = ?;', [noteId, userId]);
  return true;
};

export const countNotes = async (userId) => {
  const result = await getFirst('SELECT COUNT(*) as count FROM notes WHERE user_id = ?;', [userId]);
  return Number(result?.count ?? 0);
};
