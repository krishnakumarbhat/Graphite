import { useState } from 'react';
import {
  Background,
  Controls,
  Handle,
  MiniMap,
  Position,
  ReactFlow,
  useEdgesState,
  useNodesState,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import {
  BrainCircuit,
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
import { useNavigate } from 'react-router-dom';

import { useWorkspaceShell } from '@/components/workspace/app-workspace-shell';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { toast } from '@/components/ui/sonner';
import { previewSettings, previewWorkflow } from '@/components/preview/preview-data';
import {
  generateWorkflow,
  orchestrateAgent,
  searchMemory,
  storeMemory,
} from '@/lib/api';
import { AGENT_EDGES, AGENT_NODES } from '@/lib/workspace-data';

function AgentNode({ data }) {
  return (
    <div
      className="rounded-xl border-2 bg-card/95 px-4 py-3 shadow-lg backdrop-blur-sm"
      style={{ borderColor: data.color, minWidth: 190 }}
    >
      <Handle className="!bg-primary" position={Position.Top} type="target" />
      <div className="mb-1 flex items-center gap-2">
        <div className="h-3 w-3 rounded-full" style={{ backgroundColor: data.color }} />
        <span className="text-sm font-semibold text-foreground">{data.label}</span>
      </div>
      <p className="text-xs leading-4 text-muted-foreground">{data.description}</p>
      {data.capabilities && (
        <div className="mt-2 flex flex-wrap gap-1">
          {data.capabilities.map((capability) => (
            <Badge className="px-1.5 py-0 text-[10px]" key={capability} variant="secondary">
              {capability}
            </Badge>
          ))}
        </div>
      )}
      <Handle className="!bg-primary" position={Position.Bottom} type="source" />
    </div>
  );
}

const nodeTypes = { agentNode: AgentNode };

const AGENT_BUTTONS = {
  finance: 'Tradezy Finance',
  vc: 'VC Search',
  career: 'Job Search',
  scraper: 'Trend Scout',
};

const formatTabLabel = (screen) => {
  if (screen === 'agents') return 'Agent Orchestrator';
  if (screen === 'workflow') return 'Workflow Studio';
  if (screen === 'memory') return 'Memory Search';
  return 'Settings';
};

export function DashboardPage() {
  const navigate = useNavigate();
  const { backendHealth, onToggleTheme, resolvedTheme } = useWorkspaceShell();

  const [activeTab, setActiveTab] = useState('agents');
  const [workflowPrompt, setWorkflowPrompt] = useState(previewWorkflow.prompt);
  const [workflowNodes, setWorkflowNodes] = useState(previewWorkflow.nodes);
  const [settings, setSettings] = useState(previewSettings);
  const [rfNodes, , onNodesChange] = useNodesState(AGENT_NODES);
  const [rfEdges, , onEdgesChange] = useEdgesState(AGENT_EDGES);
  const [agentTask, setAgentTask] = useState('');
  const [selectedAgent, setSelectedAgent] = useState('finance');
  const [agentResult, setAgentResult] = useState(null);
  const [agentLoading, setAgentLoading] = useState(false);
  const [memoryQuery, setMemoryQuery] = useState('');
  const [memoryResults, setMemoryResults] = useState([]);
  const [memoryStoreText, setMemoryStoreText] = useState('');
  const [memoryLoading, setMemoryLoading] = useState(false);
  const [workflowLoading, setWorkflowLoading] = useState(false);

  const handleGenerateWorkflow = async () => {
    const prompt = workflowPrompt.trim();
    if (!prompt) {
      return;
    }

    setWorkflowLoading(true);
    try {
      const graph = await generateWorkflow(prompt);
      if (graph?.nodes) {
        setWorkflowNodes(
          graph.nodes.map((node) => ({
            id: node.id,
            title: node.title || node.id,
            description: node.description || '',
          })),
        );
        toast.success('Workflow generated from Gemini');
      }
    } catch (error) {
      const focus = prompt.split(' ').slice(0, 5).join(' ');
      setWorkflowNodes([
        { id: 'capture', title: 'Capture intent', description: `Understand: ${focus}` },
        { id: 'research', title: 'Research sources', description: 'Pull notes, docs, and context.' },
        { id: 'compose', title: 'Compose graph', description: 'Shape the work into clear nodes.' },
        { id: 'queue', title: 'Queue actions', description: 'Convert the plan into follow-ups.' },
      ]);
      toast.info('Using local workflow preview while the backend is unavailable');
    } finally {
      setWorkflowLoading(false);
    }
  };

  const handleOrchestrateAgent = async () => {
    if (!agentTask.trim()) {
      return;
    }

    setAgentLoading(true);
    setAgentResult(null);
    try {
      const response = await orchestrateAgent(selectedAgent, agentTask.trim());
      setAgentResult(response);
      toast.success(`${response.agent_name} completed the task`);
    } catch (error) {
      const message = error?.response?.data?.detail || error.message || 'Failed';
      toast.error(`Agent error: ${message}`);
    } finally {
      setAgentLoading(false);
    }
  };

  const handleMemoryStore = async () => {
    if (!memoryStoreText.trim()) {
      return;
    }

    setMemoryLoading(true);
    try {
      const response = await storeMemory(memoryStoreText.trim());
      toast.success(`Stored in vector memory: ${response.id}`);
      setMemoryStoreText('');
    } catch (error) {
      const message = error?.response?.data?.detail || error.message || 'Failed';
      toast.error(`Store error: ${message}`);
    } finally {
      setMemoryLoading(false);
    }
  };

  const handleMemorySearch = async () => {
    if (!memoryQuery.trim()) {
      return;
    }

    setMemoryLoading(true);
    try {
      const matches = await searchMemory(memoryQuery.trim());
      setMemoryResults(matches);
      toast.success(`Found ${matches.length} results`);
    } catch (error) {
      const message = error?.response?.data?.detail || error.message || 'Failed';
      setMemoryResults([]);
      toast.error(`Search error: ${message}`);
    } finally {
      setMemoryLoading(false);
    }
  };

  const handleToggleSetting = (key) => {
    setSettings((current) => ({ ...current, [key]: !current[key] }));
  };

  return (
    <main className="space-y-5">
      <section className="space-y-4 rounded-[28px] border border-border/70 bg-background/78 p-6 shadow-[var(--shadow-soft)] backdrop-blur-xl sm:p-8">
        <div className="flex flex-wrap items-center gap-3">
          <Badge className="bg-primary/12 text-primary hover:bg-primary/12">Routed web workspace</Badge>
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
          {backendHealth?.pineconeConfigured && (
            <Badge className="bg-purple-500/15 text-purple-600">Pinecone: Active</Badge>
          )}
          {backendHealth?.supabaseConfigured && (
            <Badge className="bg-blue-500/15 text-blue-600">Supabase: Mirroring</Badge>
          )}
        </div>

        <div className="space-y-3">
          <p className="font-display text-sm font-semibold uppercase tracking-[0.24em] text-primary">
            Autonomous multi-agent system
          </p>
          <h1 className="font-display text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Manager-worker dashboard with a dedicated notes workspace
          </h1>
          <p className="max-w-3xl text-base leading-7 text-muted-foreground">
            Tradezy finance, VC search, job search, and trend scouting agents stay on the
            main dashboard. Notes now live at `/notes` with local SQLite storage, markdown
            import, and optional AI drafting.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Button className="rounded-xl px-5" onClick={onToggleTheme}>
            {resolvedTheme === 'dark' ? <SunMedium /> : <Moon />}
            {resolvedTheme === 'dark' ? 'Light mode' : 'Dark mode'}
          </Button>
          <Button className="rounded-xl" onClick={() => navigate('/notes')}>
            <FileText className="mr-2 h-4 w-4" />
            Open notes
          </Button>
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-4">
        <Card className="rounded-[20px] border-border/80 bg-card/90">
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center gap-2 text-xs uppercase tracking-widest">
              <Database className="h-4 w-4" /> Local-first notes
            </CardDescription>
            <CardTitle className="text-xl">SQLite + optional Supabase mirror</CardTitle>
          </CardHeader>
        </Card>
        <Card className="rounded-[20px] border-border/80 bg-card/90">
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center gap-2 text-xs uppercase tracking-widest">
              <Zap className="h-4 w-4" /> Agents
            </CardDescription>
            <CardTitle className="text-xl">4 production lanes</CardTitle>
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
              <Shield className="h-4 w-4" /> Model & memory
            </CardDescription>
            <CardTitle className="text-xl">Gemini + Pinecone</CardTitle>
          </CardHeader>
        </Card>
      </div>

      <Card className="rounded-[28px] border-border/80 bg-card/95 shadow-lg">
        <CardHeader className="border-b border-border/70 pb-4">
          <Badge className="w-fit bg-accent text-accent-foreground">
            {resolvedTheme === 'dark' ? 'Dark' : 'Light'} workspace
          </Badge>
          <CardTitle className="font-display text-2xl">{formatTabLabel(activeTab)}</CardTitle>
        </CardHeader>
        <CardContent className="p-4 sm:p-6">
          <Tabs className="flex flex-col" onValueChange={setActiveTab} value={activeTab}>
            <div className="mb-4 border-b border-border/70 pb-4">
              <TabsList className="grid h-auto grid-cols-4 rounded-[18px] bg-secondary/80 p-1.5">
                <TabsTrigger className="min-h-[44px] rounded-xl text-xs data-[state=active]:bg-background" value="agents">
                  <BrainCircuit className="mr-1 h-4 w-4" /> Agents
                </TabsTrigger>
                <TabsTrigger className="min-h-[44px] rounded-xl text-xs data-[state=active]:bg-background" value="workflow">
                  <GitBranch className="mr-1 h-4 w-4" /> Workflow
                </TabsTrigger>
                <TabsTrigger className="min-h-[44px] rounded-xl text-xs data-[state=active]:bg-background" value="memory">
                  <Search className="mr-1 h-4 w-4" /> Memory
                </TabsTrigger>
                <TabsTrigger className="min-h-[44px] rounded-xl text-xs data-[state=active]:bg-background" value="settings">
                  <Settings2 className="mr-1 h-4 w-4" /> Settings
                </TabsTrigger>
              </TabsList>
            </div>

            <TabsContent className="mt-0" value="agents">
              <div className="space-y-4">
                <Card className="overflow-hidden rounded-2xl border-border/80">
                  <div className="h-[500px] w-full">
                    <ReactFlow
                      className="bg-background"
                      edges={rfEdges}
                      fitView
                      nodeTypes={nodeTypes}
                      nodes={rfNodes}
                      onEdgesChange={onEdgesChange}
                      onNodesChange={onNodesChange}
                    >
                      <Background gap={16} size={1} />
                      <Controls className="!rounded-xl !border-border !bg-card" />
                      <MiniMap
                        className="!rounded-xl !border-border !bg-card"
                        nodeColor={(node) => node.data?.color || '#888'}
                      />
                    </ReactFlow>
                  </div>
                </Card>

                <Card className="rounded-2xl border-border/80 bg-card/95">
                  <CardContent className="space-y-4 p-5">
                    <p className="font-display text-xs font-semibold uppercase tracking-[0.2em] text-primary">
                      Orchestrate an agent
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(AGENT_BUTTONS).map(([key, label]) => (
                        <Button
                          className="rounded-xl"
                          key={key}
                          onClick={() => setSelectedAgent(key)}
                          size="sm"
                          variant={selectedAgent === key ? 'default' : 'outline'}
                        >
                          {label}
                        </Button>
                      ))}
                    </div>
                    <Textarea
                      className="min-h-[88px] rounded-xl border-input bg-secondary/35 text-sm"
                      onChange={(event) => setAgentTask(event.target.value)}
                      placeholder="Describe the task for this agent..."
                      value={agentTask}
                    />
                    <Button
                      className="w-full rounded-xl"
                      disabled={agentLoading || !agentTask.trim()}
                      onClick={handleOrchestrateAgent}
                    >
                      {agentLoading ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      ) : (
                        <Sparkles className="mr-2 h-4 w-4" />
                      )}
                      {agentLoading ? 'Processing...' : 'Run agent task'}
                    </Button>
                    {agentResult && (
                      <Card className="rounded-xl border-border/60 bg-secondary/30">
                        <CardContent className="space-y-2 p-4">
                          <p className="text-sm font-semibold">{agentResult.agent_name} — Result</p>
                          {agentResult.result?.summary && (
                            <p className="text-sm text-muted-foreground">{agentResult.result.summary}</p>
                          )}
                          {agentResult.result?.action_plan?.length > 0 && (
                            <div>
                              <p className="mb-1 text-xs font-semibold uppercase tracking-wider">
                                Action plan
                              </p>
                              <ul className="list-inside list-disc space-y-1 text-sm text-muted-foreground">
                                {agentResult.result.action_plan.map((step, index) => (
                                  <li key={index}>{step}</li>
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

            <TabsContent className="mt-0" value="workflow">
              <div className="space-y-4">
                <Card className="rounded-2xl border-border/80 bg-card/95">
                  <CardContent className="space-y-4 p-5">
                    <p className="font-display text-xs font-semibold uppercase tracking-[0.2em] text-primary">
                      Gemini workflow generator
                    </p>
                    <Textarea
                      className="min-h-[100px] rounded-xl border-input bg-secondary/35 text-sm"
                      onChange={(event) => setWorkflowPrompt(event.target.value)}
                      placeholder="Create a workflow to find VC funding"
                      value={workflowPrompt}
                    />
                    <Button className="w-full rounded-xl" disabled={workflowLoading} onClick={handleGenerateWorkflow}>
                      {workflowLoading ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      ) : (
                        <GitBranch className="mr-2 h-4 w-4" />
                      )}
                      {workflowLoading ? 'Generating...' : 'Generate workflow'}
                    </Button>
                  </CardContent>
                </Card>

                <Card className="rounded-2xl border-border/80 bg-card/95">
                  <CardHeader>
                    <CardTitle className="text-lg">Generated workflow</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {workflowNodes.map((node, index) => (
                        <div
                          className="relative ml-6 rounded-xl border border-border/80 bg-secondary/40 p-4"
                          key={node.id}
                        >
                          <div className="absolute -left-4 top-4 flex h-6 w-6 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">
                            {index + 1}
                          </div>
                          <h4 className="text-sm font-semibold">{node.title}</h4>
                          <p className="mt-1 text-xs text-muted-foreground">{node.description}</p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <TabsContent className="mt-0" value="memory">
              <div className="space-y-4">
                <Card className="rounded-2xl border-border/80 bg-card/95">
                  <CardContent className="space-y-4 p-5">
                    <p className="font-display text-xs font-semibold uppercase tracking-[0.2em] text-primary">
                      Store memory
                    </p>
                    <Textarea
                      className="min-h-[80px] rounded-xl border-input bg-secondary/35 text-sm"
                      onChange={(event) => setMemoryStoreText(event.target.value)}
                      placeholder="Enter text to store as vector memory..."
                      value={memoryStoreText}
                    />
                    <Button
                      className="w-full rounded-xl"
                      disabled={memoryLoading || !memoryStoreText.trim()}
                      onClick={handleMemoryStore}
                    >
                      {memoryLoading ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      ) : (
                        <Database className="mr-2 h-4 w-4" />
                      )}
                      Store in Pinecone
                    </Button>
                  </CardContent>
                </Card>

                <Card className="rounded-2xl border-border/80 bg-card/95">
                  <CardContent className="space-y-4 p-5">
                    <p className="font-display text-xs font-semibold uppercase tracking-[0.2em] text-primary">
                      Semantic search
                    </p>
                    <div className="flex gap-2">
                      <Input
                        className="rounded-xl border-input bg-secondary/35"
                        onChange={(event) => setMemoryQuery(event.target.value)}
                        onKeyDown={(event) => event.key === 'Enter' && handleMemorySearch()}
                        placeholder="Search vector memory..."
                        value={memoryQuery}
                      />
                      <Button
                        className="rounded-xl"
                        disabled={memoryLoading || !memoryQuery.trim()}
                        onClick={handleMemorySearch}
                      >
                        <Search className="h-4 w-4" />
                      </Button>
                    </div>

                    {memoryResults.length > 0 && (
                      <ScrollArea className="h-[300px]">
                        <div className="space-y-2">
                          {memoryResults.map((match, index) => (
                            <Card className="rounded-lg border-border/60 bg-secondary/30" key={match.id}>
                              <CardContent className="p-3">
                                <div className="mb-1 flex items-center justify-between">
                                  <span className="font-mono text-xs text-muted-foreground">
                                    #{index + 1} — Score: {match.score?.toFixed(4)}
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
                        <p className="text-sm text-muted-foreground">Toggle dark and light theme.</p>
                      </div>
                      <Switch checked={resolvedTheme === 'dark'} onCheckedChange={onToggleTheme} />
                    </div>
                    <Separator />
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <p className="font-medium text-foreground">Speak reminders</p>
                        <p className="text-sm text-muted-foreground">Local TTS reminder playback.</p>
                      </div>
                      <Switch
                        checked={settings.speakReminders}
                        onCheckedChange={() => handleToggleSetting('speakReminders')}
                      />
                    </div>
                    <Separator />
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <p className="font-medium text-foreground">Offline-first priority</p>
                        <p className="text-sm text-muted-foreground">Keep local capture as the source of truth.</p>
                      </div>
                      <Switch
                        checked={settings.offlinePriority}
                        onCheckedChange={() => handleToggleSetting('offlinePriority')}
                      />
                    </div>
                  </CardContent>
                </Card>

                <Card className="rounded-2xl border-border/80 bg-card/95">
                  <CardHeader>
                    <CardTitle className="text-lg">System status</CardTitle>
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
                      <span>Pinecone</span>
                      <Badge variant={backendHealth?.pineconeConfigured ? 'default' : 'secondary'}>
                        {backendHealth?.pineconeConfigured ? 'Active' : 'Not connected'}
                      </Badge>
                    </div>
                    <div className="flex justify-between">
                      <span>Supabase</span>
                      <Badge variant={backendHealth?.supabaseConfigured ? 'default' : 'secondary'}>
                        {backendHealth?.supabaseConfigured ? 'Mirroring' : 'Not configured'}
                      </Badge>
                    </div>
                    <div className="flex justify-between">
                      <span>Notes DB</span>
                      <span className="truncate pl-4 text-right text-muted-foreground">
                        {backendHealth?.notesDatabasePath || 'backend/data/graphite.sqlite3'}
                      </span>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </main>
  );
}