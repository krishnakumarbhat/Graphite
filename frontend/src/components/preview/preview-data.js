export const previewNotes = [
  {
    id: 'fundraising-brief',
    title: 'Fundraising brief',
    excerpt: 'Warm path mapping, memo tightening, and fast investor prioritization.',
    content: '## Goal\nRaise a focused bridge from aligned sector investors.\n\n## Next actions\n- Map 20 funds by stage and thesis\n- Rank warm intros from founder network\n- Refresh traction memo with concise milestones\n\n## Executive note\nKeep narrative operator-first: proof of execution before expansion.',
    updatedAt: 'Mar 15',
    tag: 'Operator note',
  },
  {
    id: 'meeting-brief',
    title: 'Board meeting brief',
    excerpt: 'Agenda, risk framing, and speaking prompts for the upcoming sync.',
    content: '## Agenda\n1. Revenue health\n2. Product velocity\n3. Capital planning\n\n## Reminder\nIf a meeting is approaching, a local TTS reminder will speak aloud in a later phase.',
    updatedAt: 'Mar 14',
    tag: 'Calendar ready',
  },
  {
    id: 'travel-plan',
    title: 'Travel checklist',
    excerpt: 'Offline essentials before flying with edge models and notes archive.',
    content: 'Pack microphone, passport, adapter, and backup notebook.\n\nBefore leaving:\n- Export markdown\n- Cache workflows locally\n- Verify `models/tts`, `models/stt`, and `models/vision`',
    updatedAt: 'Mar 13',
    tag: 'Offline-first',
  },
];

export const previewWorkflow = {
  title: 'VC funding scout',
  prompt: 'Create a workflow to find VC funding',
  nodes: [
    {
      id: 'node-map',
      title: 'Map target funds',
      description: 'Identify stage-fit investors across geography, thesis, and check size.',
    },
    {
      id: 'node-warm-intros',
      title: 'Rank warm intros',
      description: 'Score paths through founders, angels, operators, and customers.',
    },
    {
      id: 'node-outreach',
      title: 'Draft outreach kit',
      description: 'Generate concise memo, traction bullets, and personal angle.',
    },
    {
      id: 'node-follow-up',
      title: 'Queue follow-up sequence',
      description: 'Push tasks into notes, reminders, and upcoming meeting prep.',
    },
  ],
};

export const previewSettings = {
  darkMode: false,
  speakReminders: true,
  offlinePriority: true,
  googleWorkspaceReady: false,
};
