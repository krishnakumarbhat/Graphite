import { useMemo, useState } from 'react';
import '@/App.css';
import {
  ArrowLeft,
  BrainCircuit,
  CloudOff,
  Database,
  FileText,
  GitBranch,
  Moon,
  Settings2,
  Sparkles,
  SunMedium,
  Waves,
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

const formatScreenLabel = (screen) => {
  if (screen === 'notes') return 'Notes';
  if (screen === 'workflow') return 'Workflow Agent';
  return 'Settings';
};

const buildWorkflowPreview = (prompt) => {
  const normalizedPrompt = prompt.trim() || previewWorkflow.prompt;
  const focus = normalizedPrompt.split(' ').slice(0, 5).join(' ') || 'your request';

  return [
    {
      id: 'capture-intent',
      title: 'Capture intent',
      description: `Understand constraints, context, and success criteria for ${focus}.`,
    },
    {
      id: 'research-sources',
      title: 'Research sources',
      description: 'Pull notes, docs, calendar context, and relevant datasets into one lane.',
    },
    {
      id: 'compose-graph',
      title: 'Compose graph',
      description: 'Shape the workflow as nodes and edges ready for React Flow rendering.',
    },
    {
      id: 'queue-actions',
      title: 'Queue actions',
      description: 'Convert outputs into reminders, docs, and saved operational notes.',
    },
  ];
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
  const [activeTab, setActiveTab] = useState('notes');
  const [notes, setNotes] = useState(previewNotes);
  const [searchQuery, setSearchQuery] = useState('');
  const [editorNote, setEditorNote] = useState(previewNotes[0]);
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [workflowPrompt, setWorkflowPrompt] = useState(previewWorkflow.prompt);
  const [workflowNodes, setWorkflowNodes] = useState(previewWorkflow.nodes);
  const [settings, setSettings] = useState(previewSettings);

  const filteredNotes = useMemo(() => {
    const normalized = searchQuery.trim().toLowerCase();

    if (!normalized) {
      return notes;
    }

    return notes.filter((note) => (
      note.title.toLowerCase().includes(normalized) ||
      note.content.toLowerCase().includes(normalized)
    ));
  }, [notes, searchQuery]);

  const activeCountLabel = `${notes.length} local notes`;

  const handleCreateNote = () => {
    const draft = createDraftNote();
    setEditorNote(draft);
    setIsEditorOpen(true);
    toast('Draft ready', {
      description: 'A new note draft is open in the mirrored mobile preview.',
    });
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

    setNotes((currentNotes) => {
      const remainingNotes = currentNotes.filter((note) => note.id !== nextNote.id);
      return [nextNote, ...remainingNotes];
    });
    setEditorNote(nextNote);
    setIsEditorOpen(false);
    toast.success('Note saved', {
      description: 'The mirrored preview updated its local note state.',
    });
  };

  const handleGenerateWorkflow = () => {
    setWorkflowNodes(buildWorkflowPreview(workflowPrompt));
    toast.success('Workflow refreshed', {
      description: 'The canvas placeholder has been updated from your prompt.',
    });
  };

  const handleToggleTheme = () => {
    setTheme(resolvedTheme === 'dark' ? 'light' : 'dark');
  };

  const handleToggleSetting = (key) => {
    setSettings((current) => ({
      ...current,
      [key]: !current[key],
    }));
  };

  return (
    <div className="preview-shell min-h-screen overflow-hidden">
      <main className="relative mx-auto flex min-h-screen w-full max-w-7xl flex-col gap-8 px-4 py-6 sm:px-6 lg:px-8 lg:py-10">
        <div className="grid items-start gap-8 lg:grid-cols-[minmax(0,1fr)_440px]">
          <section className="relative space-y-6" data-testid="preview-sidebar">
            <div className="space-y-4 rounded-[28px] border border-border/70 bg-background/70 p-6 backdrop-blur-md sm:p-8">
              <div className="flex flex-wrap items-center gap-3" data-testid="preview-header-badges">
                <Badge className="bg-primary/12 text-primary hover:bg-primary/12" data-testid="mirror-preview-badge">
                  Mirrored mobile preview
                </Badge>
                <Badge className="bg-secondary text-secondary-foreground" data-testid="phase-two-badge">
                  Phase 2 live
                </Badge>
              </div>

              <div className="space-y-4">
                <p className="font-display text-sm font-semibold uppercase tracking-[0.24em] text-primary" data-testid="preview-eyebrow">
                  Autonomous secondary brain
                </p>
                <h1 className="font-display text-4xl font-semibold tracking-tight text-foreground sm:text-5xl" data-testid="preview-title">
                  Calm, local-first notes and workflows—now visible in the main preview.
                </h1>
                <p className="max-w-2xl text-base leading-7 text-muted-foreground" data-testid="preview-description">
                  Per design guidelines, this mirror uses ocean-teal and warm neutral surfaces to reflect a premium, operator-grade mobile assistant without using purple or heavy gradients.
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <Button
                  className="rounded-xl px-5"
                  data-testid="header-theme-toggle-button"
                  onClick={handleToggleTheme}
                >
                  {resolvedTheme === 'dark' ? <SunMedium /> : <Moon />}
                  {resolvedTheme === 'dark' ? 'Switch to light' : 'Switch to dark'}
                </Button>
                <Button
                  className="rounded-xl border-border bg-secondary text-secondary-foreground hover:bg-accent"
                  data-testid="header-open-editor-button"
                  onClick={() => {
                    setActiveTab('notes');
                    setIsEditorOpen(true);
                  }}
                  variant="outline"
                >
                  <FileText />
                  Open editor
                </Button>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <Card className="rounded-[24px] border-border/80 bg-card/90 shadow-[var(--shadow-soft)]" data-testid="insight-card-notes">
                <CardHeader className="space-y-3">
                  <CardDescription className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-muted-foreground">
                    <Database className="h-4 w-4" /> Local-first
                  </CardDescription>
                  <CardTitle className="font-display text-2xl">{activeCountLabel}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm leading-6 text-muted-foreground">SQLite-backed mobile core on native, with a faithful web mirror for this preview URL.</p>
                </CardContent>
              </Card>

              <Card className="rounded-[24px] border-border/80 bg-card/90 shadow-[var(--shadow-soft)]" data-testid="insight-card-workflow">
                <CardHeader className="space-y-3">
                  <CardDescription className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-muted-foreground">
                    <GitBranch className="h-4 w-4" /> Workflow agent
                  </CardDescription>
                  <CardTitle className="font-display text-2xl">{workflowNodes.length} staged nodes</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm leading-6 text-muted-foreground">Prompt-to-graph preview scaffolding is ready for Gemini and React Flow in later phases.</p>
                </CardContent>
              </Card>

              <Card className="rounded-[24px] border-border/80 bg-card/90 shadow-[var(--shadow-soft)]" data-testid="insight-card-models">
                <CardHeader className="space-y-3">
                  <CardDescription className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-muted-foreground">
                    <CloudOff className="h-4 w-4" /> Edge-ready
                  </CardDescription>
                  <CardTitle className="font-display text-2xl">3 local model folders</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm leading-6 text-muted-foreground">Reserved paths for TTS, STT, and Vision remain blank and ready for your on-device models.</p>
                </CardContent>
              </Card>
            </div>

            <Card className="rounded-[28px] border-border/80 bg-card/90 shadow-[var(--shadow-soft)]" data-testid="preview-roadmap-card">
              <CardHeader>
                <CardDescription className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-muted-foreground">
                  <Sparkles className="h-4 w-4" /> What is live right now
                </CardDescription>
                <CardTitle className="font-display text-3xl">Notes, editor, workflow agent, and settings</CardTitle>
              </CardHeader>
              <CardContent className="space-y-5">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="rounded-2xl border border-border/80 bg-secondary/55 p-4" data-testid="roadmap-card-notes">
                    <div className="mb-3 flex items-center gap-2 text-foreground">
                      <FileText className="h-4 w-4 text-primary" />
                      <span className="font-semibold">Note system</span>
                    </div>
                    <p className="text-sm leading-6 text-muted-foreground">Search, create, edit, and structure local notes in a phone-like shell.</p>
                  </div>
                  <div className="rounded-2xl border border-border/80 bg-secondary/55 p-4" data-testid="roadmap-card-workflow">
                    <div className="mb-3 flex items-center gap-2 text-foreground">
                      <BrainCircuit className="h-4 w-4 text-primary" />
                      <span className="font-semibold">Workflow agent</span>
                    </div>
                    <p className="text-sm leading-6 text-muted-foreground">Prompt box and graph placeholder prepare the path to Gemini-generated JSON workflows.</p>
                  </div>
                </div>
                <Separator />
                <div className="flex flex-wrap gap-3 text-sm text-muted-foreground" data-testid="preview-next-phases">
                  <span className="rounded-full border border-border bg-background px-3 py-1">Next: Supabase auth + sync mock</span>
                  <span className="rounded-full border border-border bg-background px-3 py-1">Then: markdown import/export</span>
                  <span className="rounded-full border border-border bg-background px-3 py-1">Later: Google + Gemini integrations</span>
                </div>
              </CardContent>
            </Card>
          </section>

          <section className="lg:sticky lg:top-6" data-testid="preview-phone-column">
            <div className="preview-phone rounded-[34px] border border-border/80 bg-card/85 p-3 shadow-[var(--shadow-float)]">
              <div className="rounded-[28px] border border-border/70 bg-background/95">
                <div className="flex items-center justify-between border-b border-border/70 px-5 py-4" data-testid="phone-header">
                  <div>
                    <p className="font-display text-sm font-semibold uppercase tracking-[0.2em] text-primary" data-testid="phone-header-eyebrow">
                      Mobile shell
                    </p>
                    <h2 className="font-display text-xl font-semibold text-foreground" data-testid="phone-header-title">
                      {isEditorOpen ? 'Note Editor' : formatScreenLabel(activeTab)}
                    </h2>
                  </div>
                  <Badge className="bg-accent text-accent-foreground hover:bg-accent" data-testid="phone-header-status-badge">
                    {resolvedTheme === 'dark' ? 'Dark' : 'Light'} preview
                  </Badge>
                </div>

                <Tabs className="flex min-h-[760px] flex-col" onValueChange={setActiveTab} value={activeTab}>
                  <div className="flex-1 px-5 py-5">
                    <TabsContent className="mt-0 h-full" value="notes">
                      {isEditorOpen ? (
                        <div className="flex h-full flex-col gap-4" data-testid="note-editor-screen">
                          <div className="flex items-center justify-between gap-3">
                            <Button
                              data-testid="editor-back-button"
                              onClick={() => setIsEditorOpen(false)}
                              variant="outline"
                            >
                              <ArrowLeft />
                              Back
                            </Button>
                            <Button data-testid="editor-save-button" onClick={handleSaveNote}>
                              Save note
                            </Button>
                          </div>
                          <Card className="rounded-[24px] border-border/80 bg-card/95 shadow-[var(--shadow-soft)]" data-testid="editor-card">
                            <CardContent className="space-y-4 p-5">
                              <p className="font-display text-xs font-semibold uppercase tracking-[0.2em] text-primary" data-testid="editor-eyebrow">
                                Block editor placeholder
                              </p>
                              <Input
                                className="h-12 rounded-xl border-input bg-background text-lg font-semibold"
                                data-testid="editor-title-input"
                                onChange={(event) => setEditorNote((current) => ({ ...current, title: event.target.value }))}
                                placeholder="Untitled note"
                                value={editorNote.title}
                              />
                              <div className="flex flex-wrap gap-2" data-testid="editor-block-chip-row">
                                {['Paragraph', 'Heading', 'Checklist', 'Quote', 'Code'].map((chip) => (
                                  <Badge key={chip} className="bg-secondary text-secondary-foreground hover:bg-secondary" data-testid={`editor-block-chip-${chip.toLowerCase()}`}>
                                    {chip}
                                  </Badge>
                                ))}
                              </div>
                              <Textarea
                                className="min-h-[260px] rounded-2xl border-input bg-secondary/35 px-4 py-3 text-sm leading-6"
                                data-testid="editor-content-input"
                                onChange={(event) => setEditorNote((current) => ({ ...current, content: event.target.value }))}
                                placeholder="Start writing. Markdown import/export and richer block actions arrive in later phases."
                                value={editorNote.content}
                              />
                              <p className="text-sm leading-6 text-muted-foreground" data-testid="editor-helper-text">
                                This mirrored editor is intentionally simple today while preserving the structure for a future block-based canvas.
                              </p>
                            </CardContent>
                          </Card>
                        </div>
                      ) : (
                        <div className="flex h-full flex-col gap-4" data-testid="notes-screen">
                          <div className="space-y-4">
                            <div className="flex items-center justify-between gap-3">
                              <Badge className="bg-primary/12 text-primary hover:bg-primary/12" data-testid="notes-status-badge">
                                Web mirror active
                              </Badge>
                              <Button data-testid="notes-create-button" onClick={handleCreateNote}>
                                <FileText />
                                New note
                              </Button>
                            </div>
                            <div className="space-y-2">
                              <label className="text-sm font-semibold text-foreground" data-testid="notes-search-label">Search</label>
                              <Input
                                className="h-11 rounded-xl border-input bg-secondary/35"
                                data-testid="notes-search-input"
                                onChange={(event) => setSearchQuery(event.target.value)}
                                placeholder="Search notes and imported markdown"
                                value={searchQuery}
                              />
                            </div>
                          </div>

                          {filteredNotes.length ? (
                            <ScrollArea className="h-[520px] pr-1" data-testid="notes-list-scroll-area">
                              <div className="space-y-3 pr-3">
                                {filteredNotes.map((note) => (
                                  <Card className="rounded-[22px] border-border/80 bg-card/95 shadow-[var(--shadow-soft)]" data-testid={`notes-list-item-${note.id}`} key={note.id}>
                                    <CardContent className="space-y-4 p-4">
                                      <div className="flex items-start justify-between gap-4">
                                        <div className="space-y-1">
                                          <h3 className="font-display text-lg font-semibold text-foreground" data-testid={`note-title-${note.id}`}>
                                            {note.title}
                                          </h3>
                                          <p className="text-sm leading-6 text-muted-foreground" data-testid={`note-excerpt-${note.id}`}>
                                            {note.excerpt}
                                          </p>
                                        </div>
                                        <Badge className="bg-secondary text-secondary-foreground hover:bg-secondary" data-testid={`note-tag-${note.id}`}>
                                          {note.tag}
                                        </Badge>
                                      </div>
                                      <div className="flex items-center justify-between gap-3 text-xs uppercase tracking-[0.2em] text-muted-foreground">
                                        <span data-testid={`note-updated-at-${note.id}`}>{note.updatedAt}</span>
                                        <Button
                                          className="rounded-xl"
                                          data-testid={`notes-open-button-${note.id}`}
                                          onClick={() => handleOpenNote(note)}
                                          size="sm"
                                          variant="outline"
                                        >
                                          Open
                                        </Button>
                                      </div>
                                    </CardContent>
                                  </Card>
                                ))}
                              </div>
                            </ScrollArea>
                          ) : (
                            <Card className="rounded-[24px] border-border/80 bg-card/95 shadow-[var(--shadow-soft)]" data-testid="notes-empty-state">
                              <CardContent className="space-y-3 p-5">
                                <h3 className="font-display text-lg font-semibold">No matching notes</h3>
                                <p className="text-sm leading-6 text-muted-foreground">Refine your search or create a fresh note for the next meeting, memo, or thought.</p>
                              </CardContent>
                            </Card>
                          )}
                        </div>
                      )}
                    </TabsContent>

                    <TabsContent className="mt-0 h-full" value="workflow">
                      <div className="flex h-full flex-col gap-4" data-testid="workflow-screen">
                        <Card className="rounded-[24px] border-border/80 bg-card/95 shadow-[var(--shadow-soft)]" data-testid="workflow-prompt-card">
                          <CardContent className="space-y-4 p-5">
                            <div className="space-y-1">
                              <p className="font-display text-xs font-semibold uppercase tracking-[0.2em] text-primary" data-testid="workflow-eyebrow">
                                Prompt-to-graph preview
                              </p>
                              <h3 className="font-display text-xl font-semibold" data-testid="workflow-title">Workflow Agent</h3>
                            </div>
                            <Textarea
                              className="min-h-[140px] rounded-2xl border-input bg-secondary/35 px-4 py-3 text-sm leading-6"
                              data-testid="workflow-prompt-input"
                              onChange={(event) => setWorkflowPrompt(event.target.value)}
                              placeholder="Create a workflow to find VC funding"
                              value={workflowPrompt}
                            />
                            <Button className="w-full rounded-xl" data-testid="workflow-generate-button" onClick={handleGenerateWorkflow}>
                              <GitBranch />
                              Generate preview graph
                            </Button>
                          </CardContent>
                        </Card>

                        <Card className="rounded-[24px] border-border/80 bg-card/95 shadow-[var(--shadow-soft)]" data-testid="workflow-canvas-webview">
                          <CardHeader>
                            <CardTitle className="font-display text-xl">Canvas placeholder</CardTitle>
                            <CardDescription>React Flow will be rendered inside a WebView in a later phase.</CardDescription>
                          </CardHeader>
                          <CardContent>
                            <div className="space-y-5">
                              {workflowNodes.map((node) => (
                                <div className="preview-node relative ml-6 rounded-2xl border border-border/80 bg-secondary/45 p-4" data-testid={`workflow-node-${node.id}`} key={node.id}>
                                  <h4 className="font-display text-base font-semibold text-foreground">{node.title}</h4>
                                  <p className="mt-2 text-sm leading-6 text-muted-foreground">{node.description}</p>
                                </div>
                              ))}
                            </div>
                          </CardContent>
                        </Card>
                      </div>
                    </TabsContent>

                    <TabsContent className="mt-0 h-full" value="settings">
                      <div className="flex h-full flex-col gap-4" data-testid="settings-screen">
                        <Card className="rounded-[24px] border-border/80 bg-card/95 shadow-[var(--shadow-soft)]" data-testid="settings-list">
                          <CardHeader>
                            <CardTitle className="font-display text-xl">Settings</CardTitle>
                            <CardDescription>Theme, reminders, and local-first behavior for the mobile preview shell.</CardDescription>
                          </CardHeader>
                          <CardContent className="space-y-5">
                            <div className="flex items-center justify-between gap-4">
                              <div>
                                <p className="font-medium text-foreground">Dark mode</p>
                                <p className="text-sm leading-6 text-muted-foreground">Matches the mirrored mobile shell and Sonner theme.</p>
                              </div>
                              <Switch
                                checked={resolvedTheme === 'dark'}
                                data-testid="settings-dark-mode-switch"
                                onCheckedChange={handleToggleTheme}
                              />
                            </div>
                            <Separator />
                            <div className="flex items-center justify-between gap-4">
                              <div>
                                <p className="font-medium text-foreground">Speak reminders</p>
                                <p className="text-sm leading-6 text-muted-foreground">Placeholder for local TTS reminder playback before meetings.</p>
                              </div>
                              <Switch
                                checked={settings.speakReminders}
                                data-testid="settings-speak-reminders-switch"
                                onCheckedChange={() => handleToggleSetting('speakReminders')}
                              />
                            </div>
                            <Separator />
                            <div className="flex items-center justify-between gap-4">
                              <div>
                                <p className="font-medium text-foreground">Offline-first priority</p>
                                <p className="text-sm leading-6 text-muted-foreground">Keep local capture as source of truth before cloud sync.</p>
                              </div>
                              <Switch
                                checked={settings.offlinePriority}
                                data-testid="settings-offline-priority-switch"
                                onCheckedChange={() => handleToggleSetting('offlinePriority')}
                              />
                            </div>
                          </CardContent>
                        </Card>

                        <Card className="rounded-[24px] border-border/80 bg-card/95 shadow-[var(--shadow-soft)]" data-testid="settings-storage-card">
                          <CardHeader>
                            <CardTitle className="font-display text-xl">Reserved local model folders</CardTitle>
                            <CardDescription>These stay blank until you add your edge AI assets.</CardDescription>
                          </CardHeader>
                          <CardContent className="space-y-3 font-mono text-sm text-primary">
                            <div data-testid="settings-model-tts">models/tts</div>
                            <div data-testid="settings-model-stt">models/stt</div>
                            <div data-testid="settings-model-vision">models/vision</div>
                          </CardContent>
                        </Card>
                      </div>
                    </TabsContent>
                  </div>

                  <div className="border-t border-border/70 px-3 pb-3 pt-2">
                    <TabsList className="grid h-auto grid-cols-3 rounded-[22px] bg-secondary/80 p-2" data-testid="preview-tab-list">
                      <TabsTrigger className="min-h-[52px] rounded-2xl data-[state=active]:bg-background" data-testid="tab-notes" value="notes">
                        <FileText className="mr-2 h-4 w-4" /> Notes
                      </TabsTrigger>
                      <TabsTrigger className="min-h-[52px] rounded-2xl data-[state=active]:bg-background" data-testid="tab-workflow" value="workflow">
                        <GitBranch className="mr-2 h-4 w-4" /> Workflow
                      </TabsTrigger>
                      <TabsTrigger className="min-h-[52px] rounded-2xl data-[state=active]:bg-background" data-testid="tab-settings" value="settings">
                        <Settings2 className="mr-2 h-4 w-4" /> Settings
                      </TabsTrigger>
                    </TabsList>
                  </div>
                </Tabs>
              </div>
            </div>

            <div className="mt-4 flex items-center justify-center gap-2 text-sm text-muted-foreground" data-testid="preview-phone-footer">
              <Waves className="h-4 w-4 text-primary" />
              Main preview now mirrors the mobile experience while native Expo remains the primary app source.
            </div>
          </section>
        </div>
      </main>
      <Toaster closeButton richColors position="bottom-right" />
    </div>
  );
};
