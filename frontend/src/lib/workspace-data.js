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
      label: 'Financial Intelligence',
      role: 'agent',
      description: 'Bookkeeping, budget optimization, forecasting.',
      agentKey: 'finance',
      color: '#10b981',
      capabilities: ['Automated Bookkeeping', 'Budget Optimization', 'Forecasting'],
    },
  },
  {
    id: 'vc-agent',
    type: 'agentNode',
    position: { x: 300, y: 380 },
    data: {
      label: 'VC & Fundraising',
      role: 'agent',
      description: 'Investor matching, outreach automation, due diligence prep.',
      agentKey: 'vc',
      color: '#f59e0b',
      capabilities: ['Investor Matching', 'Outreach Automation', 'Due Diligence Prep'],
    },
  },
  {
    id: 'career-agent',
    type: 'agentNode',
    position: { x: 550, y: 380 },
    data: {
      label: 'Career & Talent',
      role: 'agent',
      description: 'Job scanning, application management, interview prep.',
      agentKey: 'career',
      color: '#ec4899',
      capabilities: ['Job Market Scanning', 'Application Management', 'Interview Prep'],
    },
  },
  {
    id: 'scraper-agent',
    type: 'agentNode',
    position: { x: 800, y: 380 },
    data: {
      label: 'Autonomous Data Engine',
      role: 'agent',
      description: 'High-frequency monitoring every 30 min, info synthesis, trigger-based actions.',
      agentKey: 'scraper',
      color: '#ef4444',
      capabilities: ['High-Frequency Monitoring', 'Information Synthesis', 'Trigger-Based Actions'],
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
