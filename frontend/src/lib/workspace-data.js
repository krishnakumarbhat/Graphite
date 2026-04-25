// Multi-agent architecture node/edge definitions for React Flow

export const AGENT_NODES = [
  {
    id: 'gemini-core',
    type: 'agentNode',
    position: { x: 400, y: 50 },
    data: {
      label: 'Gemini AI Core',
      role: 'core',
      description: 'The "Brain" — reasoning, NLP, and decision-making.',
      color: '#8b5cf6',
    },
  },
  {
    id: 'orchestrator',
    type: 'agentNode',
    position: { x: 400, y: 200 },
    data: {
      label: 'Agent Orchestrator',
      role: 'orchestrator',
      description: 'Coordinates tasks between Finance, VC, Career, and Scraper agents.',
      color: '#3b82f6',
    },
  },
  {
    id: 'finance-agent',
    type: 'agentNode',
    position: { x: 50, y: 380 },
    data: {
      label: 'Tradezy Finance',
      role: 'agent',
      description: 'Bookkeeping, budget optimization, forecasting, and market signal tracking.',
      agentKey: 'finance',
      color: '#10b981',
      capabilities: [
        'Automated Bookkeeping',
        'Budget Optimization',
        'Forecasting',
        'Market Signals',
      ],
    },
  },
  {
    id: 'vc-agent',
    type: 'agentNode',
    position: { x: 300, y: 380 },
    data: {
      label: 'VC Search',
      role: 'agent',
      description: 'Investor matching, thesis search, outreach automation, and diligence prep.',
      agentKey: 'vc',
      color: '#f59e0b',
      capabilities: [
        'Investor Matching',
        'Thesis Search',
        'Outreach Automation',
        'Due Diligence Prep',
      ],
    },
  },
  {
    id: 'career-agent',
    type: 'agentNode',
    position: { x: 550, y: 380 },
    data: {
      label: 'Job Search',
      role: 'agent',
      description: 'Job scanning, application management, role fit scoring, and interview prep.',
      agentKey: 'career',
      color: '#ec4899',
      capabilities: [
        'Job Market Scanning',
        'Application Management',
        'Role Fit Scoring',
        'Interview Prep',
      ],
    },
  },
  {
    id: 'scraper-agent',
    type: 'agentNode',
    position: { x: 800, y: 380 },
    data: {
      label: 'Trend Scout',
      role: 'agent',
      description: 'High-frequency monitoring, info synthesis, and trend-triggered actions.',
      agentKey: 'scraper',
      color: '#ef4444',
      capabilities: [
        'High-Frequency Monitoring',
        'Information Synthesis',
        'Trend Detection',
        'Trigger-Based Actions',
      ],
    },
  },
  {
    id: 'task-scheduler',
    type: 'agentNode',
    position: { x: 100, y: 200 },
    data: {
      label: 'Task Scheduler',
      role: 'infra',
      description: 'Manages 30-minute scraping intervals and recurring cron jobs.',
      color: '#6366f1',
    },
  },
  {
    id: 'secure-vault',
    type: 'agentNode',
    position: { x: 700, y: 200 },
    data: {
      label: 'Secure Vault',
      role: 'infra',
      description: 'Stores API keys, financial credentials, and personal data with encryption.',
      color: '#64748b',
    },
  },
];

export const AGENT_EDGES = [
  { id: 'e-core-orch', source: 'gemini-core', target: 'orchestrator', animated: true, style: { stroke: '#8b5cf6' } },
  { id: 'e-orch-finance', source: 'orchestrator', target: 'finance-agent', animated: true, style: { stroke: '#10b981' } },
  { id: 'e-orch-vc', source: 'orchestrator', target: 'vc-agent', animated: true, style: { stroke: '#f59e0b' } },
  { id: 'e-orch-career', source: 'orchestrator', target: 'career-agent', animated: true, style: { stroke: '#ec4899' } },
  { id: 'e-orch-scraper', source: 'orchestrator', target: 'scraper-agent', animated: true, style: { stroke: '#ef4444' } },
  { id: 'e-sched-orch', source: 'task-scheduler', target: 'orchestrator', style: { stroke: '#6366f1', strokeDasharray: '5,5' } },
  { id: 'e-vault-orch', source: 'secure-vault', target: 'orchestrator', style: { stroke: '#64748b', strokeDasharray: '5,5' } },
  { id: 'e-scraper-sched', source: 'scraper-agent', target: 'task-scheduler', style: { stroke: '#ef4444', strokeDasharray: '5,5' } },
];

export const WORKFLOW_PROMPT_DEFAULT = 'Create a workflow to find VC funding';
