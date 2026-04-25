import { startTransition, useDeferredValue, useEffect, useMemo, useRef, useState } from 'react';
import {
  BookText,
  Bot,
  CloudOff,
  Database,
  FileText,
  FileUp,
  Loader2,
  Plus,
  Save,
  Search,
  Sparkles,
} from 'lucide-react';

import { useWorkspaceShell } from '@/components/workspace/app-workspace-shell';
import { previewNotes } from '@/components/preview/preview-data';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Textarea } from '@/components/ui/textarea';
import { toast } from '@/components/ui/sonner';
import { fetchNotes, generateAiNote, importMarkdownNote, saveNote } from '@/lib/api';

const USER_ID = 'web-local';
const LOCAL_STORAGE_KEY = 'graphite.notes.local';

const createDraftNote = (seed = {}) => {
  const timestamp = new Date().toISOString();
  return {
    id: seed.id || `draft-${Date.now()}`,
    user_id: seed.user_id || USER_ID,
    title: seed.title || '',
    content: seed.content || '',
    excerpt: seed.excerpt || 'Fresh note draft',
    source_path: seed.source_path || null,
    created_at: seed.created_at || timestamp,
    updated_at: seed.updated_at || timestamp,
    is_ai_generated: Boolean(seed.is_ai_generated),
  };
};

const buildExcerpt = (content) => {
  const normalized = content.trim().replace(/\s+/g, ' ');
  if (!normalized) {
    return 'Fresh note draft';
  }

  return normalized.length > 160 ? `${normalized.slice(0, 157)}...` : normalized;
};

const inferTitle = (title, content) => {
  if (title.trim()) {
    return title.trim();
  }

  const firstLine = content
    .split('\n')
    .map((line) => line.replace(/^#+\s*/, '').trim())
    .find(Boolean);

  return firstLine || 'Untitled note';
};

const normalizeNote = (note) =>
  createDraftNote({
    ...note,
    excerpt: note.excerpt || buildExcerpt(note.content || ''),
  });

const readLocalNotes = () => {
  try {
    const raw = window.localStorage.getItem(LOCAL_STORAGE_KEY);
    if (!raw) {
      return [];
    }

    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.map(normalizeNote) : [];
  } catch {
    return [];
  }
};

const persistLocalNotes = (notes) => {
  window.localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(notes));
};

const upsertNotes = (currentNotes, note) => {
  const nextNotes = [note, ...currentNotes.filter((item) => item.id !== note.id)];
  return nextNotes.sort((left, right) => right.updated_at.localeCompare(left.updated_at));
};

const BLOCK_TEMPLATES = {
  heading: '\n## Section\n',
  checklist: '\n- [ ] First task\n- [ ] Second task\n',
  meeting: '\n## Meeting Notes\n\n### Context\n\n### Decisions\n\n### Next steps\n- [ ] \n',
};

export function NotesPage() {
  const fileInputRef = useRef(null);
  const { backendHealth } = useWorkspaceShell();

  const [notes, setNotes] = useState([]);
  const [draft, setDraft] = useState(createDraftNote());
  const [selectedNoteId, setSelectedNoteId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [aiPrompt, setAiPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const deferredSearchQuery = useDeferredValue(searchQuery);

  useEffect(() => {
    let cancelled = false;

    const loadNotes = async () => {
      setIsLoading(true);
      try {
        const backendNotes = await fetchNotes(USER_ID);
        if (cancelled) {
          return;
        }

        const nextNotes = backendNotes.map(normalizeNote);
        startTransition(() => {
          setNotes(nextNotes);
          if (nextNotes[0]) {
            setSelectedNoteId(nextNotes[0].id);
            setDraft(nextNotes[0]);
          } else {
            const fallbackDraft = createDraftNote();
            setSelectedNoteId(fallbackDraft.id);
            setDraft(fallbackDraft);
          }
        });
      } catch {
        if (cancelled) {
          return;
        }

        const localNotes = readLocalNotes();
        startTransition(() => {
          setNotes(localNotes);
          if (localNotes[0]) {
            setSelectedNoteId(localNotes[0].id);
            setDraft(localNotes[0]);
          } else {
            const fallbackDraft = createDraftNote();
            setSelectedNoteId(fallbackDraft.id);
            setDraft(fallbackDraft);
          }
        });

        toast.info('Notes API unavailable. Falling back to browser-local drafts.');
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    loadNotes();

    return () => {
      cancelled = true;
    };
  }, []);

  const filteredNotes = useMemo(() => {
    const normalizedQuery = deferredSearchQuery.trim().toLowerCase();
    if (!normalizedQuery) {
      return notes;
    }

    return notes.filter(
      (note) =>
        note.title.toLowerCase().includes(normalizedQuery) ||
        note.content.toLowerCase().includes(normalizedQuery),
    );
  }, [deferredSearchQuery, notes]);

  const handleSelectNote = (note) => {
    setSelectedNoteId(note.id);
    setDraft(note);
  };

  const handleCreateNote = () => {
    const nextDraft = createDraftNote();
    setSelectedNoteId(nextDraft.id);
    setDraft(nextDraft);
  };

  const handleSaveNote = async () => {
    const normalizedDraft = {
      ...draft,
      title: inferTitle(draft.title, draft.content),
      content: draft.content,
      excerpt: buildExcerpt(draft.content),
      updated_at: new Date().toISOString(),
    };

    setIsSaving(true);
    try {
      const saved = normalizeNote(
        await saveNote({
          id: normalizedDraft.id,
          user_id: USER_ID,
          title: normalizedDraft.title,
          content: normalizedDraft.content,
          source_path: normalizedDraft.source_path,
          is_ai_generated: normalizedDraft.is_ai_generated,
        }),
      );
      startTransition(() => {
        setNotes((current) => upsertNotes(current, saved));
        setSelectedNoteId(saved.id);
        setDraft(saved);
      });
      toast.success('Note saved to SQLite');
    } catch {
      const localSaved = normalizeNote(normalizedDraft);
      const nextNotes = upsertNotes(notes, localSaved);
      persistLocalNotes(nextNotes);
      startTransition(() => {
        setNotes(nextNotes);
        setSelectedNoteId(localSaved.id);
        setDraft(localSaved);
      });
      toast.info('Backend unavailable. Saved locally in the browser.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleImportFile = async (event) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    const content = await file.text();

    try {
      const saved = normalizeNote(await importMarkdownNote(file.name, content, USER_ID));
      startTransition(() => {
        setNotes((current) => upsertNotes(current, saved));
        setSelectedNoteId(saved.id);
        setDraft(saved);
      });
      toast.success(`Imported ${file.name}`);
    } catch {
      const localSaved = normalizeNote(
        createDraftNote({
          title: file.name.replace(/\.md$/i, '').replace(/[-_]/g, ' '),
          content,
          excerpt: buildExcerpt(content),
          source_path: file.name,
        }),
      );
      const nextNotes = upsertNotes(notes, localSaved);
      persistLocalNotes(nextNotes);
      startTransition(() => {
        setNotes(nextNotes);
        setSelectedNoteId(localSaved.id);
        setDraft(localSaved);
      });
      toast.info(`Imported ${file.name} locally in the browser`);
    } finally {
      event.target.value = '';
    }
  };

  const handleGenerateAiNote = async () => {
    if (!aiPrompt.trim()) {
      return;
    }

    setIsGenerating(true);
    try {
      const saved = normalizeNote(await generateAiNote(aiPrompt.trim(), draft.title.trim(), USER_ID));
      startTransition(() => {
        setNotes((current) => upsertNotes(current, saved));
        setSelectedNoteId(saved.id);
        setDraft(saved);
      });
      setAiPrompt('');
      toast.success('AI draft created from Gemini');
    } catch (error) {
      const message = error?.response?.data?.detail || error.message || 'Failed to create AI draft';
      toast.error(message);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleInsertTemplate = (templateKey) => {
    setDraft((current) => ({
      ...current,
      content: `${current.content}${BLOCK_TEMPLATES[templateKey]}`,
    }));
  };

  const noteCountLabel = `${notes.length} note${notes.length === 1 ? '' : 's'}`;

  return (
    <main className="space-y-5">
      <section className="space-y-4 rounded-[28px] border border-border/70 bg-background/78 p-6 shadow-[var(--shadow-soft)] backdrop-blur-xl sm:p-8">
        <div className="flex flex-wrap items-center gap-3">
          <Badge className="bg-primary/12 text-primary hover:bg-primary/12">/notes</Badge>
          <Badge className="bg-secondary text-secondary-foreground">Notion-style editor</Badge>
          <Badge className="bg-secondary text-secondary-foreground">Markdown import</Badge>
          <Badge className="bg-secondary text-secondary-foreground">AI draft</Badge>
        </div>

        <div className="space-y-3">
          <p className="font-display text-sm font-semibold uppercase tracking-[0.24em] text-primary">
            Notes workspace
          </p>
          <h1 className="font-display text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            A local-first page editor with optional Supabase mirroring
          </h1>
          <p className="max-w-3xl text-base leading-7 text-muted-foreground">
            Notes save to SQLite first, can import markdown files, and can ask Gemini for a
            structured first draft. If the backend is unavailable, the page falls back to
            browser-local drafts so editing still works.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
          <div className="flex items-center gap-2 rounded-full border border-border/80 bg-card/90 px-3 py-1.5">
            <Database className="h-4 w-4 text-primary" />
            <span>{backendHealth?.notesDatabasePath || 'SQLite local store'}</span>
          </div>
          <div className="flex items-center gap-2 rounded-full border border-border/80 bg-card/90 px-3 py-1.5">
            {backendHealth?.status === 'ok' ? (
              <FileText className="h-4 w-4 text-primary" />
            ) : (
              <CloudOff className="h-4 w-4 text-destructive" />
            )}
            <span>{backendHealth?.status === 'ok' ? 'Backend connected' : 'Browser-local fallback'}</span>
          </div>
        </div>
      </section>

      <div className="grid gap-4 xl:grid-cols-[320px_minmax(0,1fr)]">
        <Card className="rounded-[28px] border-border/80 bg-card/95 shadow-lg">
          <CardHeader className="space-y-4 border-b border-border/70 pb-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <CardTitle className="font-display text-xl">Pages</CardTitle>
                <CardDescription>{noteCountLabel}</CardDescription>
              </div>
              <Badge className="bg-accent text-accent-foreground">Guest mode</Badge>
            </div>
            <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-1">
              <Button className="rounded-xl" onClick={handleCreateNote}>
                <Plus className="mr-2 h-4 w-4" />
                New page
              </Button>
              <Button className="rounded-xl" onClick={() => fileInputRef.current?.click()} variant="outline">
                <FileUp className="mr-2 h-4 w-4" />
                Import .md
              </Button>
            </div>
            <input
              accept=".md,text/markdown"
              className="hidden"
              onChange={handleImportFile}
              ref={fileInputRef}
              type="file"
            />
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                className="h-11 rounded-xl border-input bg-secondary/35 pl-9"
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder="Search pages..."
                value={searchQuery}
              />
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="h-[620px]">
              <div className="space-y-2 p-3">
                {isLoading ? (
                  <div className="space-y-3 p-3 text-sm text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <p>Loading notes…</p>
                  </div>
                ) : filteredNotes.length > 0 ? (
                  filteredNotes.map((note) => (
                    <button
                      className={[
                        'w-full rounded-2xl border px-4 py-3 text-left transition-colors',
                        selectedNoteId === note.id
                          ? 'border-primary/30 bg-primary/10'
                          : 'border-border/70 bg-background/60 hover:bg-secondary/60',
                      ].join(' ')}
                      key={note.id}
                      onClick={() => handleSelectNote(note)}
                      type="button"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="text-sm font-semibold text-foreground">{note.title || 'Untitled note'}</p>
                          <p className="mt-1 text-xs leading-5 text-muted-foreground">{note.excerpt}</p>
                        </div>
                        {note.is_ai_generated ? (
                          <Badge className="bg-primary/12 text-primary hover:bg-primary/12">AI</Badge>
                        ) : null}
                      </div>
                      <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
                        <span>{note.source_path || 'Manual page'}</span>
                        <span>{new Date(note.updated_at).toLocaleDateString()}</span>
                      </div>
                    </button>
                  ))
                ) : (
                  <div className="space-y-3 p-5 text-sm text-muted-foreground">
                    <BookText className="h-5 w-5 text-primary" />
                    <p>No pages yet. Create a new page, import a markdown file, or ask Gemini for a draft.</p>
                  </div>
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        <Card className="rounded-[28px] border-border/80 bg-card/97 shadow-lg">
          <CardHeader className="space-y-4 border-b border-border/70 pb-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <CardTitle className="font-display text-2xl">{draft.title || 'Untitled page'}</CardTitle>
                <CardDescription>
                  {draft.source_path || 'Local-first page'}
                  {draft.is_ai_generated ? ' • AI generated' : ''}
                </CardDescription>
              </div>
              <Button className="rounded-xl" disabled={isSaving} onClick={handleSaveNote}>
                {isSaving ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Save className="mr-2 h-4 w-4" />
                )}
                {isSaving ? 'Saving...' : 'Save page'}
              </Button>
            </div>

            <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_auto]">
              <Input
                className="h-11 rounded-xl border-input bg-secondary/35"
                onChange={(event) => setAiPrompt(event.target.value)}
                placeholder="Ask Gemini to draft meeting notes, research briefs, or summaries..."
                value={aiPrompt}
              />
              <Button
                className="rounded-xl"
                disabled={isGenerating || !aiPrompt.trim()}
                onClick={handleGenerateAiNote}
              >
                {isGenerating ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Bot className="mr-2 h-4 w-4" />
                )}
                {isGenerating ? 'Drafting...' : 'Generate AI note'}
              </Button>
            </div>

            <div className="flex flex-wrap gap-2">
              <Button className="rounded-xl" onClick={() => handleInsertTemplate('heading')} size="sm" variant="outline">
                Heading
              </Button>
              <Button className="rounded-xl" onClick={() => handleInsertTemplate('checklist')} size="sm" variant="outline">
                Checklist
              </Button>
              <Button className="rounded-xl" onClick={() => handleInsertTemplate('meeting')} size="sm" variant="outline">
                Meeting template
              </Button>
              <Badge className="bg-secondary text-secondary-foreground">
                Slash-style blocks via quick inserts
              </Badge>
            </div>
          </CardHeader>

          <CardContent className="space-y-5 p-5">
            <Input
              className="h-14 rounded-2xl border-none bg-transparent px-0 text-3xl font-semibold shadow-none focus-visible:ring-0"
              onChange={(event) => setDraft((current) => ({ ...current, title: event.target.value }))}
              placeholder="Untitled"
              value={draft.title}
            />

            <Textarea
              className="notes-editor min-h-[560px] rounded-[24px] border border-border/70 bg-secondary/20 p-5 text-[15px] leading-7"
              onChange={(event) => setDraft((current) => ({ ...current, content: event.target.value }))}
              placeholder="Type '/' for your own shortcuts, write in markdown, or import an existing .md page."
              value={draft.content}
            />

            <div className="grid gap-3 rounded-[24px] border border-border/70 bg-secondary/30 p-4 text-sm text-muted-foreground sm:grid-cols-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-primary">Source</p>
                <p className="mt-1 break-all">{draft.source_path || 'Manual page'}</p>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-primary">Updated</p>
                <p className="mt-1">{new Date(draft.updated_at).toLocaleString()}</p>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-primary">Access</p>
                <p className="mt-1">No login required until you choose to add auth.</p>
              </div>
            </div>

            <div className="rounded-[24px] border border-border/70 bg-background/70 p-4">
              <div className="mb-2 flex items-center gap-2 text-sm font-medium text-foreground">
                <Sparkles className="h-4 w-4 text-primary" />
                AI note help
              </div>
              <p className="text-sm leading-6 text-muted-foreground">
                Ask for research summaries, meeting briefs, architecture notes, or action-item
                lists. If Gemini is unavailable, the editor still works locally and you can save
                drafts without leaving the page.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}