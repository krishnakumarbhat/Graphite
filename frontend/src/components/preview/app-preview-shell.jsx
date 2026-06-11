import { useCallback, useEffect, useMemo, useState } from 'react';
import '@/App.css';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Handle,
  Position,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import {
  ArrowLeft,
  BrainCircuit,
  CloudOff,
  Database,
  FileText,
  GitBranch,
  Loader2,
  Moon,
  Search,
  Settings2,
  Shield,
  Sparkles,
  SunMedium,
  Zap,
} from 'lucide-react';
import { useTheme } from 'next-themes';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { Toaster, toast } from '@/components/ui/sonner';
import { previewNotes, previewSettings, previewWorkflow } from './preview-data';
import { AGENT_NODES, AGENT_EDGES } from '@/lib/workspace-data';
import {
  fetchHealth,
  generateWorkflow,
  fetchAgentsStatus,
  orchestrateAgent,
  storeMemory,
  searchMemory,
} from '@/lib/api';

// --- Custom React Flow node ---
function AgentNode({ data }) {
  return (
    <div
      className="rounded-xl border-2 bg-card/95 px-4 py-3 shadow-lg backdrop-blur-sm"
      style={{ borderColor: data.color, minWidth: 180 }}
    >
      <Handle type="target" position={Position.Top} className="!bg-primary" />
      <div className="flex items-center gap-2 mb-1">
        <div className="h-3 w-3 rounded-full" style={{ backgroundColor: data.color }} />
        <span className="font-semibold text-sm text-foreground">{data.label}</span>
      </div>
      <p className="text-xs text-muted-foreground leading-4">{data.description}</p>
      {data.capabilities && (
        <div className="mt-2 flex flex-wrap gap-1">
          {data.capabilities.map((c) => (
            <Badge key={c} variant="secondary" className="text-[10px] px-1.5 py-0">
              {c}
            </Badge>
          ))}
        </div>
      )}
      <Handle type="source" position={Position.Bottom} className="!bg-primary" />
    </div>
  );
}

const nodeTypes = { agentNode: AgentNode };

const formatScreenLabel = (screen) => {
  if (screen === 'notes') return 'Notes';
  if (screen === 'agents') return 'Agent Orchestrator';
  if (screen === 'workflow') return 'Workflow Agent';
  if (screen === 'memory') return 'Memory Search';
  return 'Settings';
};

const createDraftNote = () => ({
  id: `draft-${Date.now()}`,
  title: '',
  excerpt: 'Fresh note draft',
  content: '',
  updatedAt: 'Now',
  tag: 'Draft',
  isDraft: true,
});

export const AppPreviewShell = () => {
  const { resolvedTheme, setTheme } = useTheme();
  const [activeTab, setActiveTab] = useState('agents');
  const [notes, setNotes] = useState(previewNotes);
  const [searchQuery, setSearchQuery] = useState('');
  const [editorNote, setEditorNote] = useState(previewNotes[0]);
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [workflowPrompt, setWorkflowPrompt] = useState(previewWorkflow.prompt);
  const [workflowNodes, setWorkflowNodes] = useState(previewWorkflow.nodes);
  const [settings, setSettings] = useState(previewSettings);

  // React Flow state for Agent canvas
  const [rfNodes, setRfNodes, onNodesChange] = useNodesState(AGENT_NODES);
  const [rfEdges, setRfEdges, onEdgesChange] = useEdgesState(AGENT_EDGES);

  // Backend connectivity
  const [backendHealth, setBackendHealth] = useState(null);
  const [agentTask, setAgentTask] = useState('');
  const [selectedAgent, setSelectedAgent] = useState('finance');
  const [agentResult, setAgentResult] = useState(null);
  const [agentLoading, setAgentLoading] = useState(false);

  // Memory search
  const [memoryQuery, setMemoryQuery] = useState('');
  const [memoryResults, setMemoryResults] = useState([]);
  const [memoryStoreText, setMemoryStoreText] = useState('');
  const [memoryLoading, setMemoryLoading] = useState(false);

  // Workflow generation
  const [workflowLoading, setWorkflowLoading] = useState(false);

  // Check backend health on mount
  useEffect(() => {
    fetchHealth()
      .then(setBackendHealth)
      .catch(() => setBackendHealth({ status: 'unreachable' }));
  }, []);

  const filteredNotes = useMemo(() => {
    const normalized = searchQuery.trim().toLowerCase();
    if (!normalized) return notes;
    return notes.filter(
      (note) =>
        note.title.toLowerCase().includes(normalized) ||
        note.content.toLowerCase().includes(normalized),
    );
  }, [notes, searchQuery]);

  const activeCountLabel = `${notes.length} local notes`;

  const handleCreateNote = () => {
    const draft = createDraftNote();
    setEditorNote(draft);
    setIsEditorOpen(true);
    toast('Draft ready', { description: 'A new note draft is open.' });
  };

  const handleOpenNote = (note) => {
    setEditorNote(note);
    setIsEditorOpen(true);
  };

  const handleSaveNote = () => {
    const normalizedTitle = editorNote.title.trim() || 'Untitled note';
    const nextNote = {
      ...editorNote,
      title: normalizedTitle,
      excerpt: editorNote.content.slice(0, 72) || 'Fresh executive note',
      tag: editorNote.isDraft ? 'Draft saved' : editorNote.tag,
      updatedAt: 'Now',
      isDraft: false,
    };
    setNotes((current) => {
      const remaining = current.filter((n) => n.id !== nextNote.id);
      return [nextNote, ...remaining];
    });
    setEditorNote(nextNote);
    setIsEditorOpen(false);
    toast.success('Note saved');
  };

  const handleGenerateWorkflow = useCallback(async () => {
    const prompt = workflowPrompt.trim();
    if (!prompt) return;
    setWorkflowLoading(true);
    try {
      const graph = await generateWorkflow(prompt);
      if (graph && graph.nodes) {
        // Convert backend graph to React Flow nodes/edges in the workflow tab
        setWorkflowNodes(
          graph.nodes.map((n, i) => ({
            id: n.id,
            title: n.title || n.id,
            description: n.description || '',
          })),
        );
        toast.success('Workflow generated from Gemini');
      }
    } catch (err) {
      // Fallback to local preview
      const focus = prompt.split(' ').slice(0, 5).join(' ');
      setWorkflowNodes([
        { id: 'capture', title: 'Capture intent', description: `Understand: ${focus}` },
        { id: 'research', title: 'Research sources', description: 'Pull notes, docs, context.' },
        { id: 'compose', title: 'Compose graph', description: 'Shape as nodes and edges.' },
        { id: 'queue', title: 'Queue actions', description: 'Convert to reminders and docs.' },
      ]);
      toast.info('Using local preview (backend unreachable)');
    } finally {
      setWorkflowLoading(false);
    }
  }, [workflowPrompt]);

  const handleOrchestrateAgent = useCallback(async () => {
    if (!agentTask.trim()) return;
    setAgentLoading(true);
    setAgentResult(null);
    try {
      const resp = await orchestrateAgent(selectedAgent, agentTask.trim());
      setAgentResult(resp);
      toast.success(`${resp.agent_name} completed task`);
    } catch (err) {
      const msg = err?.response?.data?.detail || err.message || 'Failed';
      toast.error(`Agent error: ${msg}`);
    } finally {
      setAgentLoading(false);
    }
  }, [selectedAgent, agentTask]);

  const handleMemoryStore = useCallback(async () => {
    if (!memoryStoreText.trim()) return;
    setMemoryLoading(true);
    try {
      const resp = await storeMemory(memoryStoreText.trim());
      toast.success(`Stored in PGVECTOR: ${resp.id}`);
      setMemoryStoreText('');
    } catch (err) {
      const msg = err?.response?.data?.detail || err.message || 'Failed';
      toast.error(`Store error: ${msg}`);
    } finally {
      setMemoryLoading(false);
    }
  }, [memoryStoreText]);

  const handleMemorySearch = useCallback(async () => {
    if (!memoryQuery.trim()) return;
    setMemoryLoading(true);
    try {
      const matches = await searchMemory(memoryQuery.trim());
      setMemoryResults(matches);
      toast.success(`Found ${matches.length} results`);
    } catch (err) {
      const msg = err?.response?.data?.detail || err.message || 'Failed';
      toast.error(`Search error: ${msg}`);
      setMemoryResults([]);
    } finally {
      setMemoryLoading(false);
    }
  }, [memoryQuery]);

  const handleToggleTheme = () => setTheme(resolvedTheme === 'dark' ? 'light' : 'dark');
  const handleToggleSetting = (key) =>
    setSettings((current) => ({ ...current, [key]: !current[key] }));

  return (
    <div className="preview-shell min-h-screen overflow-hidden">
      <main className="relative mx-auto flex min-h-screen w-full max-w-7xl flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
        {/* Header */}
        <section className="space-y-4 rounded-[28px] border border-border/70 bg-background/70 p-6 backdrop-blur-md sm:p-8">
          <div className="flex flex-wrap items-center gap-3">
            <Badge className="bg-primary/12 text-primary hover:bg-primary/12">
              Multi-Agent Workspace
            </Badge>
            <Badge className="bg-secondary text-secondary-foreground">React Flow</Badge>
            {backendHealth && (
              <Badge
                className={
                  backendHealth.status === 'ok'
                    ? 'bg-green-500/15 text-green-600'
                    : 'bg-red-500/15 text-red-500'
                }
              >
                API: {backendHealth.status === 'ok' ? 'Connected' : 'Offline'}
              </Badge>
            )}
            {backendHealth?.PGVECTORConfigured && (
              <Badge className="bg-purple-500/15 text-purple-600">PGVECTOR: Active</Badge>
            )}
          </div>
          <div className="space-y-3">
            <p className="font-display text-sm font-semibold uppercase tracking-[0.24em] text-primary">
              Autonomous Multi-Agent System
            </p>
            <h1 className="font-display text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
              Manager-Worker AI Architecture with PGVECTOR Memory
            </h1>
            <p className="max-w-2xl text-base leading-7 text-muted-foreground">
              Finance, VC, Career, and Scraper agents orchestrated by Gemini AI Core.
              Vector memory backed by PGVECTOR. Workflows via React Flow.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Button className="rounded-xl px-5" onClick={handleToggleTheme}>
              {resolvedTheme === 'dark' ? <SunMedium /> : <Moon />}
              {resolvedTheme === 'dark' ? 'Light mode' : 'Dark mode'}
            </Button>
            <Button
              className="rounded-xl border-border bg-secondary text-secondary-foreground hover:bg-accent"
              onClick={() => { setActiveTab('notes'); setIsEditorOpen(true); }}
              variant="outline"
            >
              <FileText /> Open editor
            </Button>
          </div>
        </section>

        {/* Stats cards */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card className="rounded-[20px] border-border/80 bg-card/90">
            <CardHeader className="pb-2">
              <CardDescription className="flex items-center gap-2 text-xs uppercase tracking-widest">
                <Database className="h-4 w-4" /> Local-first
              </CardDescription>
              <CardTitle className="text-xl">{activeCountLabel}</CardTitle>
            </CardHeader>
          </Card>
          <Card className="rounded-[20px] border-border/80 bg-card/90">
            <CardHeader className="pb-2">
              <CardDescription className="flex items-center gap-2 text-xs uppercase tracking-widest">
                <Zap className="h-4 w-4" /> Agents
              </CardDescription>
              <CardTitle className="text-xl">4 active agents</CardTitle>
            </CardHeader>
          </Card>
          <Card className="rounded-[20px] border-border/80 bg-card/90">
            <CardHeader className="pb-2">
              <CardDescription className="flex items-center gap-2 text-xs uppercase tracking-widest">
                <GitBranch className="h-4 w-4" /> Workflow
              </CardDescription>
              <CardTitle className="text-xl">{workflowNodes.length} nodes</CardTitle>
            </CardHeader>
          </Card>
          <Card className="rounded-[20px] border-border/80 bg-card/90">
            <CardHeader className="pb-2">
              <CardDescription className="flex items-center gap-2 text-xs uppercase tracking-widest">
                <Shield className="h-4 w-4" /> Vault
              </CardDescription>
              <CardTitle className="text-xl">Encrypted</CardTitle>
            </CardHeader>
          </Card>
        </div>

        {/* Main workspace */}
        <Card className="rounded-[28px] border-border/80 bg-card/95 shadow-lg">
          <CardHeader className="border-b border-border/70 pb-4">
            <Badge className="w-fit bg-accent text-accent-foreground">
              {resolvedTheme === 'dark' ? 'Dark' : 'Light'} workspace
            </Badge>
            <CardTitle className="font-display text-2xl">
              {isEditorOpen ? 'Note Editor' : formatScreenLabel(activeTab)}
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4 sm:p-6">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="flex flex-col">
              <div className="mb-4 border-b border-border/70 pb-4">
                <TabsList className="grid h-auto grid-cols-5 rounded-[18px] bg-secondary/80 p-1.5">
                  <TabsTrigger className="min-h-[44px] rounded-xl text-xs data-[state=active]:bg-background" value="agents">
                    <BrainCircuit className="mr-1 h-4 w-4" /> Agents
                  </TabsTrigger>
                  <TabsTrigger className="min-h-[44px] rounded-xl text-xs data-[state=active]:bg-background" value="workflow">
                    <GitBranch className="mr-1 h-4 w-4" /> Workflow
                  </TabsTrigger>
                  <TabsTrigger className="min-h-[44px] rounded-xl text-xs data-[state=active]:bg-background" value="notes">
                    <FileText className="mr-1 h-4 w-4" /> Notes
                  </TabsTrigger>
                  <TabsTrigger className="min-h-[44px] rounded-xl text-xs data-[state=active]:bg-background" value="memory">
                    <Search className="mr-1 h-4 w-4" /> Memory
                  </TabsTrigger>
                  <TabsTrigger className="min-h-[44px] rounded-xl text-xs data-[state=active]:bg-background" value="settings">
                    <Settings2 className="mr-1 h-4 w-4" /> Settings
                  </TabsTrigger>
                </TabsList>
              </div>

              {/* ===== AGENTS TAB (React Flow) ===== */}
              <TabsContent className="mt-0" value="agents">
                <div className="space-y-4">
                  <Card className="rounded-2xl border-border/80 overflow-hidden">
                    <div className="h-[500px] w-full">
                      <ReactFlow
                        nodes={rfNodes}
                        edges={rfEdges}
                        onNodesChange={onNodesChange}
                        onEdgesChange={onEdgesChange}
                        nodeTypes={nodeTypes}
                        fitView
                        className="bg-background"
                      >
                        <Background gap={16} size={1} />
                        <Controls className="!bg-card !border-border !rounded-xl" />
                        <MiniMap
                          className="!bg-card !border-border !rounded-xl"
                          nodeColor={(n) => n.data?.color || '#888'}
                        />
                      </ReactFlow>
                    </div>
                  </Card>

                  {/* Agent task orchestration */}
                  <Card className="rounded-2xl border-border/80 bg-card/95">
                    <CardContent className="space-y-4 p-5">
                      <p className="font-display text-xs font-semibold uppercase tracking-[0.2em] text-primary">
                        Orchestrate an Agent
                      </p>
                      <div className="flex gap-2 flex-wrap">
                        {Object.entries({
                          finance: '💰 Finance',
                          vc: '🚀 VC',
                          career: '💼 Career',
                          scraper: '🕷️ Scraper',
                        }).map(([key, label]) => (
                          <Button
                            key={key}
                            variant={selectedAgent === key ? 'default' : 'outline'}
                            size="sm"
                            className="rounded-xl"
                            onClick={() => setSelectedAgent(key)}
                          >
                            {label}
                          </Button>
                        ))}
                      </div>
                      <Textarea
                        className="min-h-[80px] rounded-xl border-input bg-secondary/35 text-sm"
                        placeholder="Describe the task for this agent..."
                        value={agentTask}
                        onChange={(e) => setAgentTask(e.target.value)}
                      />
                      <Button
                        className="w-full rounded-xl"
                        onClick={handleOrchestrateAgent}
                        disabled={agentLoading || !agentTask.trim()}
                      >
                        {agentLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Sparkles className="mr-2 h-4 w-4" />}
                        {agentLoading ? 'Processing...' : 'Run Agent Task'}
                      </Button>
                      {agentResult && (
                        <Card className="rounded-xl bg-secondary/30 border-border/60">
                          <CardContent className="p-4 space-y-2">
                            <p className="font-semibold text-sm">{agentResult.agent_name} — Result</p>
                            {agentResult.result?.summary && (
                              <p className="text-sm text-muted-foreground">{agentResult.result.summary}</p>
                            )}
                            {agentResult.result?.action_plan?.length > 0 && (
                              <div>
                                <p className="text-xs font-semibold uppercase tracking-wider mb-1">Action Plan</p>
                                <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
                                  {agentResult.result.action_plan.map((step, i) => (
                                    <li key={i}>{step}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </CardContent>
                        </Card>
                      )}
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>

              {/* ===== WORKFLOW TAB ===== */}
              <TabsContent className="mt-0" value="workflow">
                <div className="space-y-4">
                  <Card className="rounded-2xl border-border/80 bg-card/95">
                    <CardContent className="space-y-4 p-5">
                      <p className="font-display text-xs font-semibold uppercase tracking-[0.2em] text-primary">
                        Gemini Workflow Generator
                      </p>
                      <Textarea
                        className="min-h-[100px] rounded-xl border-input bg-secondary/35 text-sm"
                        placeholder="Create a workflow to find VC funding"
                        value={workflowPrompt}
                        onChange={(e) => setWorkflowPrompt(e.target.value)}
                      />
                      <Button
                        className="w-full rounded-xl"
                        onClick={handleGenerateWorkflow}
                        disabled={workflowLoading}
                      >
                        {workflowLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <GitBranch className="mr-2 h-4 w-4" />}
                        {workflowLoading ? 'Generating...' : 'Generate Workflow'}
                      </Button>
                    </CardContent>
                  </Card>
                  <Card className="rounded-2xl border-border/80 bg-card/95">
                    <CardHeader>
                      <CardTitle className="text-lg">Generated Workflow</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {workflowNodes.map((node, idx) => (
                          <div
                            key={node.id}
                            className="relative ml-6 rounded-xl border border-border/80 bg-secondary/40 p-4"
                          >
                            <div className="absolute -left-4 top-4 flex h-6 w-6 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">
                              {idx + 1}
                            </div>
                            <h4 className="font-semibold text-sm">{node.title}</h4>
                            <p className="mt-1 text-xs text-muted-foreground">{node.description}</p>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>

              {/* ===== NOTES TAB ===== */}
              <TabsContent className="mt-0" value="notes">
                {isEditorOpen ? (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between gap-3">
                      <Button onClick={() => setIsEditorOpen(false)} variant="outline" className="rounded-xl">
                        <ArrowLeft /> Back
                      </Button>
                      <Button onClick={handleSaveNote} className="rounded-xl">Save note</Button>
                    </div>
                    <Card className="rounded-2xl border-border/80 bg-card/95">
                      <CardContent className="space-y-4 p-5">
                        <p className="font-display text-xs font-semibold uppercase tracking-[0.2em] text-primary">
                          Block editor
                        </p>
                        <Input
                          className="h-12 rounded-xl text-lg font-semibold"
                          placeholder="Untitled note"
                          value={editorNote.title}
                          onChange={(e) => setEditorNote((c) => ({ ...c, title: e.target.value }))}
                        />
                        <div className="flex flex-wrap gap-2">
                          {['Paragraph', 'Heading', 'Checklist', 'Quote', 'Code'].map((c) => (
                            <Badge key={c} variant="secondary">{c}</Badge>
                          ))}
                        </div>
                        <Textarea
                          className="min-h-[260px] rounded-xl border-input bg-secondary/35 text-sm"
                          placeholder="Start writing..."
                          value={editorNote.content}
                          onChange={(e) => setEditorNote((c) => ({ ...c, content: e.target.value }))}
                        />
                      </CardContent>
                    </Card>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between gap-3">
                      <Badge className="bg-primary/12 text-primary hover:bg-primary/12">
                        {activeCountLabel}
                      </Badge>
                      <Button onClick={handleCreateNote} className="rounded-xl">
                        <FileText className="mr-1 h-4 w-4" /> New note
                      </Button>
                    </div>
                    <Input
                      className="h-11 rounded-xl border-input bg-secondary/35"
                      placeholder="Search notes..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                    {filteredNotes.length ? (
                      <ScrollArea className="h-[420px] pr-1">
                        <div className="space-y-3 pr-3">
                          {filteredNotes.map((note) => (
                            <Card key={note.id} className="rounded-xl border-border/80 bg-card/95">
                              <CardContent className="p-4 space-y-2">
                                <div className="flex items-start justify-between gap-4">
                                  <div>
                                    <h3 className="font-semibold text-sm">{note.title}</h3>
                                    <p className="text-xs text-muted-foreground">{note.excerpt}</p>
                                  </div>
                                  <Badge variant="secondary">{note.tag}</Badge>
                                </div>
                                <div className="flex items-center justify-between text-xs text-muted-foreground">
                                  <span>{note.updatedAt}</span>
                                  <Button size="sm" variant="outline" className="rounded-lg" onClick={() => handleOpenNote(note)}>
                                    Open
                                  </Button>
                                </div>
                              </CardContent>
                            </Card>
                          ))}
                        </div>
                      </ScrollArea>
                    ) : (
                      <Card className="rounded-xl border-border/80 bg-card/95">
                        <CardContent className="p-5">
                          <p className="text-sm text-muted-foreground">No matching notes.</p>
                        </CardContent>
                      </Card>
                    )}
                  </div>
                )}
              </TabsContent>

              {/* ===== MEMORY TAB (PGVECTOR) ===== */}
              <TabsContent className="mt-0" value="memory">
                <div className="space-y-4">
                  <Card className="rounded-2xl border-border/80 bg-card/95">
                    <CardContent className="space-y-4 p-5">
                      <p className="font-display text-xs font-semibold uppercase tracking-[0.2em] text-primary">
                        Store Memory (PGVECTOR Vector DB)
                      </p>
                      <Textarea
                        className="min-h-[80px] rounded-xl border-input bg-secondary/35 text-sm"
                        placeholder="Enter text to store as vector memory..."
                        value={memoryStoreText}
                        onChange={(e) => setMemoryStoreText(e.target.value)}
                      />
                      <Button
                        className="w-full rounded-xl"
                        onClick={handleMemoryStore}
                        disabled={memoryLoading || !memoryStoreText.trim()}
                      >
                        {memoryLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Database className="mr-2 h-4 w-4" />}
                        Store in PGVECTOR
                      </Button>
                    </CardContent>
                  </Card>
                  <Card className="rounded-2xl border-border/80 bg-card/95">
                    <CardContent className="space-y-4 p-5">
                      <p className="font-display text-xs font-semibold uppercase tracking-[0.2em] text-primary">
                        Semantic Search
                      </p>
                      <div className="flex gap-2">
                        <Input
                          className="rounded-xl border-input bg-secondary/35"
                          placeholder="Search vector memory..."
                          value={memoryQuery}
                          onChange={(e) => setMemoryQuery(e.target.value)}
                          onKeyDown={(e) => e.key === 'Enter' && handleMemorySearch()}
                        />
                        <Button
                          className="rounded-xl"
                          onClick={handleMemorySearch}
                          disabled={memoryLoading || !memoryQuery.trim()}
                        >
                          <Search className="h-4 w-4" />
                        </Button>
                      </div>
                      {memoryResults.length > 0 && (
                        <ScrollArea className="h-[300px]">
                          <div className="space-y-2">
                            {memoryResults.map((match, idx) => (
                              <Card key={match.id} className="rounded-lg border-border/60 bg-secondary/30">
                                <CardContent className="p-3">
                                  <div className="flex items-center justify-between mb-1">
                                    <span className="text-xs font-mono text-muted-foreground">
                                      #{idx + 1} — Score: {match.score?.toFixed(4)}
                                    </span>
                                  </div>
                                  <p className="text-sm">{match.metadata?.text || 'No text metadata'}</p>
                                </CardContent>
                              </Card>
                            ))}
                          </div>
                        </ScrollArea>
                      )}
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>

              {/* ===== SETTINGS TAB ===== */}
              <TabsContent className="mt-0" value="settings">
                <div className="space-y-4">
                  <Card className="rounded-2xl border-border/80 bg-card/95">
                    <CardHeader>
                      <CardTitle className="text-lg">Settings</CardTitle>
                      <CardDescription>Theme, agents, and system configuration.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-5">
                      <div className="flex items-center justify-between gap-4">
                        <div>
                          <p className="font-medium text-foreground">Dark mode</p>
                          <p className="text-sm text-muted-foreground">Toggle dark/light theme.</p>
                        </div>
                        <Switch checked={resolvedTheme === 'dark'} onCheckedChange={handleToggleTheme} />
                      </div>
                      <Separator />
                      <div className="flex items-center justify-between gap-4">
                        <div>
                          <p className="font-medium text-foreground">Speak reminders</p>
                          <p className="text-sm text-muted-foreground">Local TTS reminder playback.</p>
                        </div>
                        <Switch checked={settings.speakReminders} onCheckedChange={() => handleToggleSetting('speakReminders')} />
                      </div>
                      <Separator />
                      <div className="flex items-center justify-between gap-4">
                        <div>
                          <p className="font-medium text-foreground">Offline-first priority</p>
                          <p className="text-sm text-muted-foreground">Keep local capture as source of truth.</p>
                        </div>
                        <Switch checked={settings.offlinePriority} onCheckedChange={() => handleToggleSetting('offlinePriority')} />
                      </div>
                    </CardContent>
                  </Card>
                  {/* Backend Status */}
                  <Card className="rounded-2xl border-border/80 bg-card/95">
                    <CardHeader>
                      <CardTitle className="text-lg">System Status</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3 font-mono text-sm">
                      <div className="flex justify-between">
                        <span>API</span>
                        <Badge variant={backendHealth?.status === 'ok' ? 'default' : 'destructive'}>
                          {backendHealth?.status === 'ok' ? 'Connected' : 'Offline'}
                        </Badge>
                      </div>
                      <div className="flex justify-between">
                        <span>Gemini</span>
                        <Badge variant={backendHealth?.geminiConfigured ? 'default' : 'secondary'}>
                          {backendHealth?.geminiConfigured ? 'Configured' : 'Missing key'}
                        </Badge>
                      </div>
                      <div className="flex justify-between">
                        <span>PGVECTOR</span>
                        <Badge variant={backendHealth?.PGVECTORConfigured ? 'default' : 'secondary'}>
                          {backendHealth?.PGVECTORConfigured ? 'Active' : 'Not connected'}
                        </Badge>
                      </div>
                      <div className="flex justify-between">
                        <span>Supabase</span>
                        <Badge variant={backendHealth?.supabaseConfigured ? 'default' : 'secondary'}>
                          {backendHealth?.supabaseConfigured ? 'Connected' : 'Not configured'}
                        </Badge>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </main>
      <Toaster closeButton richColors position="bottom-right" />
    </div>
  );
};
