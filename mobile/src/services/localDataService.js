import { DEFAULT_NOTE_TITLE } from '../config/constants';
import { previewNotes, previewWorkflow } from '../data/previewData';
import { createNote, listNotes, updateNote } from '../db/notesRepo';
import { listWorkflows } from '../db/workflowsRepo';
import { createUuid } from '../utils/id';
import { createIsoTimestamp } from '../utils/time';

const createFallbackNote = (draft = {}) => {
  const timestamp = createIsoTimestamp();

  return {
    id: draft.id ?? createUuid(),
    title: draft.title?.trim() || DEFAULT_NOTE_TITLE,
    content: draft.content ?? '',
    created_at: draft.created_at ?? timestamp,
    updated_at: timestamp,
    source_path: draft.source_path ?? 'preview://local-note',
  };
};

const sortByUpdatedAt = (items = []) => [...items].sort((left, right) => (
  new Date(right.updated_at).getTime() - new Date(left.updated_at).getTime()
));

export const loadNotesForApp = async (databaseEnabled) => {
  if (!databaseEnabled) {
    return sortByUpdatedAt(previewNotes);
  }

  try {
    const notes = await listNotes();
    return notes.length ? sortByUpdatedAt(notes) : sortByUpdatedAt(previewNotes);
  } catch (error) {
    console.warn('[notes] Falling back to preview notes:', error?.message ?? error);
    return sortByUpdatedAt(previewNotes);
  }
};

export const saveNoteForApp = async (databaseEnabled, draftNote) => {
  if (!databaseEnabled) {
    return createFallbackNote(draftNote);
  }

  try {
    if (draftNote.isDraft) {
      return await createNote({
        title: draftNote.title,
        content: draftNote.content,
        sourcePath: draftNote.source_path ?? 'local://editor',
      });
    }

    return await updateNote(draftNote.id, {
      title: draftNote.title,
      content: draftNote.content,
      sourcePath: draftNote.source_path,
    });
  } catch (error) {
    console.warn('[notes] Falling back to local save:', error?.message ?? error);
    return createFallbackNote(draftNote);
  }
};

export const createDraftNote = () => ({
  id: createUuid(),
  title: '',
  content: '',
  created_at: createIsoTimestamp(),
  updated_at: createIsoTimestamp(),
  source_path: 'draft://note',
  isDraft: true,
});

export const loadWorkflowForApp = async (databaseEnabled) => {
  if (!databaseEnabled) {
    return previewWorkflow;
  }

  try {
    const workflows = await listWorkflows();

    if (!workflows.length) {
      return previewWorkflow;
    }

    const [latest] = workflows;

    return {
      title: latest.title,
      prompt: latest.prompt,
      nodes: JSON.parse(latest.graph_json ?? '[]').nodes ?? previewWorkflow.nodes,
    };
  } catch (error) {
    console.warn('[workflow] Falling back to preview workflow:', error?.message ?? error);
    return previewWorkflow;
  }
};

export const buildWorkflowPreview = (prompt) => {
  const normalizedPrompt = prompt?.trim() || previewWorkflow.prompt;
  const focusLabel = normalizedPrompt.split(' ').slice(0, 5).join(' ') || 'the request';

  return {
    title: 'Workflow Agent Preview',
    prompt: normalizedPrompt,
    nodes: [
      {
        id: 'intake',
        label: 'Capture intent',
        caption: `Understand the goal around ${focusLabel}`,
      },
      {
        id: 'research',
        label: 'Research sources',
        caption: 'Pull structured references, notes, and supporting context',
      },
      {
        id: 'synthesis',
        label: 'Synthesize plan',
        caption: 'Convert research into a concise graph of actions',
      },
      {
        id: 'execution',
        label: 'Queue execution',
        caption: 'Turn the plan into next actions and reminders',
      },
    ],
  };
};

export const sortNotesDescending = sortByUpdatedAt;
