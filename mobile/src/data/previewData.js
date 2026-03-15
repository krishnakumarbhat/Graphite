export const previewNotes = [
  {
    id: 'note-1',
    title: 'Fundraising brief',
    content: '## Goal\nClose a focused list of warm VC introductions this month.\n\n## Next moves\n- Finalize target fund list\n- Pull partner overlap from CRM\n- Draft concise narrative for seed extension\n\n## Signals to track\nLook for operators with fintech and AI workflow exposure.',
    created_at: '2026-03-10T09:30:00.000Z',
    updated_at: '2026-03-15T08:45:00.000Z',
    source_path: 'preview://fundraising-brief',
  },
  {
    id: 'note-2',
    title: 'Operator daily review',
    content: 'Morning priorities:\n1. Clear meeting prep\n2. Review agent outputs\n3. Export decisions to markdown archive\n\nEvening review:\n- Capture blockers\n- Queue tomorrow\'s deep work',
    created_at: '2026-03-11T07:10:00.000Z',
    updated_at: '2026-03-14T19:20:00.000Z',
    source_path: 'preview://operator-review',
  },
  {
    id: 'note-3',
    title: 'Travel checklist',
    content: 'Pack passport, adapter, microphone, and paper backup notebook.\n\nBefore leaving:\n- Export active notes to markdown\n- Download local workflow graphs\n- Verify offline models are present',
    created_at: '2026-03-09T18:15:00.000Z',
    updated_at: '2026-03-13T15:00:00.000Z',
    source_path: 'preview://travel-checklist',
  },
];

export const previewWorkflow = {
  title: 'VC funding scout',
  prompt: 'Create a workflow to find VC funding',
  nodes: [
    { id: 'node-1', label: 'Map sector-fit funds', caption: 'Focus on stage, thesis, and geography' },
    { id: 'node-2', label: 'Rank warm paths', caption: 'Score intros from founders, angels, and operators' },
    { id: 'node-3', label: 'Draft outreach kit', caption: 'Prepare memo, traction snapshot, and ask' },
    { id: 'node-4', label: 'Schedule follow-ups', caption: 'Route reminders into calendar and notes' },
  ],
};

export const previewSettings = {
  speakReminders: true,
  webMirrorMode: true,
  offlinePriority: true,
};
