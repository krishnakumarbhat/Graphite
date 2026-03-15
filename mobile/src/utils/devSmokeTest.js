import { createNote, countNotes, listNotes } from '../db/notesRepo';
import {
  createWorkflow,
  countWorkflows,
  listWorkflows,
} from '../db/workflowsRepo';

export const runDevSmokeTest = async () => {
  const notesBefore = await countNotes();
  const workflowsBefore = await countWorkflows();

  let seeded = false;

  if (notesBefore === 0) {
    await createNote({
      title: 'Welcome to your offline-first brain',
      content: '- SQLite schema initialized\n- Notes table ready\n- Markdown import/export comes next',
      sourcePath: 'seed://phase-1',
    });
    seeded = true;
  }

  if (workflowsBefore === 0) {
    await createWorkflow({
      title: 'Seed workflow',
      prompt: 'Create a workflow to find VC funding',
      graphJson: JSON.stringify({
        nodes: [
          { id: 'research', label: 'Research target investors' },
          { id: 'outreach', label: 'Draft personalized outreach' },
        ],
        edges: [
          { id: 'edge-1', source: 'research', target: 'outreach' },
        ],
      }),
    });
    seeded = true;
  }

  const notes = await listNotes();
  const workflows = await listWorkflows();

  const summary = {
    seeded,
    notesCount: notes.length,
    workflowsCount: workflows.length,
    latestNoteTitle: notes[0]?.title ?? null,
    latestWorkflowTitle: workflows[0]?.title ?? null,
  };

  console.info('[dev-smoke-test] Database summary:', summary);

  return summary;
};
