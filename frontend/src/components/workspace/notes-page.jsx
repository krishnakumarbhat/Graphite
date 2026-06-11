import { startTransition, useDeferredValue, useEffect, useMemo, useRef, useState } from 'react';
import {
  Bot,
  ChevronRight,
  FileUp,
  Loader2,
  LogIn,
  Mic,
  MoreHorizontal,
  Plus,
  Search,
  Square,
  Volume2,
} from 'lucide-react';
import { NavLink } from 'react-router-dom';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { toast } from '@/components/ui/sonner';
import {
  fetchNotes,
  filterNotesByTag,
  generateAiNote,
  importMarkdownNote,
  resolveApiUrl,
  saveNote,
  searchNotes,
  synthesizeSpeech,
  transcribeSpeech,
} from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import { Badge } from '@/components/ui/badge';

const GUEST_LIMIT = 5;
const LOCAL_STORAGE_KEY = 'graphite.notes.local';

const createDraftNote = (seed = {}) => {
  const timestamp = new Date().toISOString();
  return {
    id: seed.id || `draft-${Date.now()}`,
    user_id: seed.user_id || 'web-local',
    title: seed.title || '',
    content: seed.content || '',
    excerpt: seed.excerpt || '',
    tags: Array.isArray(seed.tags) ? seed.tags : [],
    source_path: seed.source_path || null,
    created_at: seed.created_at || timestamp,
    updated_at: seed.updated_at || timestamp,
    is_ai_generated: Boolean(seed.is_ai_generated),
  };
};

const buildExcerpt = (content) => {
  const normalized = content.trim().replace(/\s+/g, ' ');
  return normalized.length > 120 ? `${normalized.slice(0, 117)}...` : normalized;
};

const inferTitle = (title, content) => {
  if (title.trim()) {
    return title.trim();
  }

  const firstLine = content
    .split('\n')
    .map((line) => line.replace(/^#+\s*/, '').trim())
    .find(Boolean);

  return firstLine || 'Untitled';
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

const upsertNotes = (currentNotes, note) =>
  [note, ...currentNotes.filter((item) => item.id !== note.id)].sort((left, right) =>
    right.updated_at.localeCompare(left.updated_at),
  );

const appendTranscript = (content, transcript) => {
  const normalizedTranscript = transcript.trim();
  if (!normalizedTranscript) {
    return content;
  }

  const normalizedContent = content.trim();
  if (!normalizedContent) {
    return normalizedTranscript;
  }

  return `${normalizedContent}\n\n${normalizedTranscript}`;
};

const buildTagCounts = (items) =>
  items.reduce((counts, note) => {
    (note.tags || []).forEach((tag) => {
      counts[tag] = (counts[tag] || 0) + 1;
    });
    return counts;
  }, {});

const getPreferredRecorderMimeType = () => {
  if (typeof window === 'undefined' || typeof window.MediaRecorder === 'undefined') {
    return '';
  }

  const candidates = [
    'audio/webm;codecs=opus',
    'audio/webm',
    'audio/ogg;codecs=opus',
    'audio/ogg',
  ];

  return candidates.find((mimeType) => window.MediaRecorder.isTypeSupported(mimeType)) || '';
};

export function NotesPage() {
  const fileInputRef = useRef(null);
  const audioRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const recordedChunksRef = useRef([]);
  const recordingNoteIdRef = useRef('');
  const { user } = useAuth();

  const userId = user?.id || 'web-local';
  const isGuest = !user;

  const [notes, setNotes] = useState([]);
  const [draft, setDraft] = useState(createDraftNote());
  const [selectedNoteId, setSelectedNoteId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTag, setSelectedTag] = useState('');
  const [aiPrompt, setAiPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isReading, setIsReading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [showAiBar, setShowAiBar] = useState(false);
  const [isRemoteSearching, setIsRemoteSearching] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const deferredSearch = useDeferredValue(searchQuery);

  const stopReading = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
    }
    setIsReading(false);
  };

  const stopRecordingStream = () => {
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }
  };

  useEffect(() => () => {
    stopReading();
    stopRecordingStream();
  }, []);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);

    fetchNotes(userId)
      .then((items) => {
        if (cancelled) {
          return;
        }

        const nextNotes = items.map(normalizeNote);
        startTransition(() => {
          setNotes(nextNotes);
          const first = nextNotes[0] || createDraftNote();
          setSelectedNoteId(first.id);
          setDraft(first);
        });
      })
      .catch(() => {
        if (cancelled) {
          return;
        }

        const localNotes = readLocalNotes();
        startTransition(() => {
          setNotes(localNotes);
          const first = localNotes[0] || createDraftNote();
          setSelectedNoteId(first.id);
          setDraft(first);
        });
        toast.info('Backend unavailable. Using browser storage.');
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [userId]);

  const filteredNotes = useMemo(() => {
    const sourceNotes = searchResults.length > 0 || deferredSearch.trim() ? searchResults : notes;
    const normalizedQuery = deferredSearch.trim().toLowerCase();
    if (!normalizedQuery && !selectedTag) {
      return sourceNotes;
    }

    return sourceNotes.filter(
      (note) =>
        (!selectedTag || (note.tags || []).includes(selectedTag)) && (
          !normalizedQuery ||
          note.title.toLowerCase().includes(normalizedQuery) ||
          note.content.toLowerCase().includes(normalizedQuery)
        ),
    );
  }, [deferredSearch, notes, searchResults, selectedTag]);

  const tagCounts = useMemo(() => buildTagCounts(notes), [notes]);

  const atGuestLimit = isGuest && notes.length >= GUEST_LIMIT;

  useEffect(() => {
    let cancelled = false;
    const normalizedQuery = deferredSearch.trim();

    if (!normalizedQuery) {
      if (!selectedTag) {
        setSearchResults([]);
        return undefined;
      }

      filterNotesByTag(selectedTag, userId)
        .then((items) => {
          if (!cancelled) {
            setSearchResults(items.map(normalizeNote));
          }
        })
        .catch(() => {
          if (!cancelled) {
            setSearchResults([]);
          }
        });
      return () => {
        cancelled = true;
      };
    }

    setIsRemoteSearching(true);
    searchNotes(normalizedQuery, userId, 40, selectedTag)
      .then((payload) => {
        if (cancelled) {
          return;
        }
        const matchedNotes = (payload.matches || []).map((match) => {
          const existing = notes.find((note) => note.id === match.id);
          return normalizeNote(existing || {
            id: match.id,
            user_id: userId,
            title: match.title,
            content: match.excerpt || '',
            excerpt: match.excerpt || '',
            tags: match.tags || [],
          });
        });
        setSearchResults(matchedNotes);
      })
      .catch(() => {
        if (!cancelled) {
          setSearchResults([]);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsRemoteSearching(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [deferredSearch, notes, selectedTag, userId]);

  const handleSelectNote = (note) => {
    setSelectedNoteId(note.id);
    setDraft(note);
    setShowAiBar(false);
  };

  const handleCreateNote = () => {
    if (atGuestLimit) {
      toast.error(`Guest limit reached (${GUEST_LIMIT} notes). Sign in for unlimited notes.`);
      return;
    }

    const nextDraft = createDraftNote();
    setSelectedNoteId(nextDraft.id);
    setDraft(nextDraft);
    setShowAiBar(false);
  };

  const handleSaveNote = async () => {
    const normalizedDraft = {
      ...draft,
      title: inferTitle(draft.title, draft.content),
      excerpt: buildExcerpt(draft.content),
      updated_at: new Date().toISOString(),
    };

    if (isGuest && notes.filter((note) => note.id !== draft.id).length >= GUEST_LIMIT) {
      toast.error(`Guest limit reached (${GUEST_LIMIT} notes). Sign in for unlimited notes.`);
      return;
    }

    setIsSaving(true);
    try {
      const saved = normalizeNote(
        await saveNote({
          id: normalizedDraft.id,
          user_id: userId,
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
      toast.success('Saved');
    } catch {
      const localSaved = normalizeNote(normalizedDraft);
      const nextNotes = upsertNotes(notes, localSaved);
      persistLocalNotes(nextNotes);
      startTransition(() => {
        setNotes(nextNotes);
        setSelectedNoteId(localSaved.id);
        setDraft(localSaved);
      });
      toast.info('Saved locally in the browser.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleImportFile = async (event) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    if (atGuestLimit) {
      toast.error(`Guest limit reached (${GUEST_LIMIT} notes). Sign in for unlimited notes.`);
      event.target.value = '';
      return;
    }

    const content = await file.text();

    try {
      const saved = normalizeNote(await importMarkdownNote(file.name, content, userId));
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
      toast.info(`Imported ${file.name} locally.`);
    } finally {
      event.target.value = '';
    }
  };

  const handleGenerateAiNote = async () => {
    if (!aiPrompt.trim()) {
      return;
    }

    if (atGuestLimit) {
      toast.error(`Guest limit reached (${GUEST_LIMIT} notes). Sign in for unlimited notes.`);
      return;
    }

    setIsGenerating(true);
    try {
      const saved = normalizeNote(await generateAiNote(aiPrompt.trim(), draft.title.trim(), userId));
      startTransition(() => {
        setNotes((current) => upsertNotes(current, saved));
        setSelectedNoteId(saved.id);
        setDraft(saved);
      });
      setAiPrompt('');
      setShowAiBar(false);
      toast.success('AI draft created');
    } catch (error) {
      toast.error(error?.response?.data?.detail || error.message || 'AI draft failed');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleReadNote = async () => {
    if (isReading) {
      stopReading();
      return;
    }

    const narration = [draft.title.trim(), draft.content.trim()].filter(Boolean).join('\n\n').trim();
    if (!narration) {
      toast.error('Add note content before reading it aloud.');
      return;
    }

    setIsReading(true);
    try {
      const response = await synthesizeSpeech({
        text: narration,
        provider: 'kitten',
        voice: 'Bruno',
        speed: 1.0,
      });
      const audio = new Audio(resolveApiUrl(response.file_url));
      audioRef.current = audio;
      audio.onended = () => {
        audioRef.current = null;
        setIsReading(false);
      };
      audio.onerror = () => {
        audioRef.current = null;
        setIsReading(false);
        toast.error('Audio playback failed.');
      };
      await audio.play();
    } catch (error) {
      setIsReading(false);
      toast.error(error?.response?.data?.detail || error.message || 'Read aloud failed');
    }
  };

  const handleWriteNote = async () => {
    if (isRecording) {
      mediaRecorderRef.current?.stop();
      return;
    }

    if (!navigator.mediaDevices?.getUserMedia || typeof window.MediaRecorder === 'undefined') {
      toast.error('This browser cannot record microphone audio.');
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = getPreferredRecorderMimeType();
      const recorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream);

      mediaStreamRef.current = stream;
      mediaRecorderRef.current = recorder;
      recordedChunksRef.current = [];
      recordingNoteIdRef.current = selectedNoteId || draft.id;

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          recordedChunksRef.current.push(event.data);
        }
      };

      recorder.onerror = () => {
        stopRecordingStream();
        mediaRecorderRef.current = null;
        recordedChunksRef.current = [];
        setIsRecording(false);
        toast.error('Microphone recording failed.');
      };

      recorder.onstop = async () => {
        const recordedChunks = [...recordedChunksRef.current];
        const recordedMimeType = recorder.mimeType || mimeType || 'audio/webm';

        stopRecordingStream();
        mediaRecorderRef.current = null;
        recordedChunksRef.current = [];
        setIsRecording(false);

        if (!recordedChunks.length) {
          toast.error('No audio was captured.');
          return;
        }

        setIsTranscribing(true);
        try {
          const blob = new Blob(recordedChunks, { type: recordedMimeType });
          const response = await transcribeSpeech(blob, recordingNoteIdRef.current);
          const transcript = response.text?.trim() || '';
          if (!transcript) {
            toast.error('No speech was detected.');
            return;
          }

          setDraft((current) => ({
            ...current,
            content: appendTranscript(current.content, transcript),
          }));
          toast.success('Transcribed into the current note. Click Save to persist it.');
        } catch (error) {
          toast.error(error?.response?.data?.detail || error.message || 'Voice transcription failed');
        } finally {
          setIsTranscribing(false);
        }
      };

      recorder.start();
      setIsRecording(true);
      toast.info('Recording started. Click Write again to stop.');
    } catch (error) {
      stopRecordingStream();
      setIsRecording(false);
      toast.error(error?.message || 'Microphone permission was denied.');
    }
  };

  return (
    <div
      className="flex h-[calc(100vh-3.5rem-2rem)] overflow-hidden rounded-xl border border-border/70 bg-background shadow-sm"
      style={{ minHeight: 520 }}
    >
      <aside className="flex w-64 shrink-0 flex-col border-r border-border/60 bg-card/80">
        <div className="flex items-center justify-between px-3 pb-2 pt-3">
          <span className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
            Pages
          </span>
          <button
            className="rounded p-1 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
            onClick={handleCreateNote}
            title="New page"
            type="button"
          >
            <Plus className="h-4 w-4" />
          </button>
        </div>

        <div className="relative px-2 pb-1">
          <Search className="pointer-events-none absolute left-4 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            className="h-7 rounded-md bg-secondary/50 pl-8 text-xs"
            onChange={(event) => setSearchQuery(event.target.value)}
            placeholder="Search..."
            value={searchQuery}
          />
        </div>

        {Object.keys(tagCounts).length > 0 ? (
          <div className="border-b border-border/60 px-2 pb-2 pt-1">
            <div className="mb-1 flex items-center justify-between text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
              <span>Facets</span>
              {selectedTag ? (
                <button className="text-[10px] normal-case text-primary" onClick={() => setSelectedTag('')} type="button">
                  Clear
                </button>
              ) : null}
            </div>
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(tagCounts).map(([tag, count]) => (
                <button key={tag} onClick={() => setSelectedTag((current) => current === tag ? '' : tag)} type="button">
                  <Badge variant={selectedTag === tag ? 'default' : 'secondary'} className="gap-1 capitalize">
                    {tag}
                    <span className="opacity-70">{count}</span>
                  </Badge>
                </button>
              ))}
            </div>
          </div>
        ) : null}

        {isGuest ? (
          <div className="mx-2 mb-1 mt-1 flex items-center justify-between rounded-md bg-amber-50 px-2.5 py-1.5 text-xs text-amber-700 dark:bg-amber-950/40 dark:text-amber-400">
            <span>
              {notes.length}/{GUEST_LIMIT} notes
            </span>
            <NavLink
              className="flex items-center gap-0.5 font-medium underline underline-offset-2"
              to="/login"
            >
              <LogIn className="h-3 w-3" />
              Sign in
            </NavLink>
          </div>
        ) : null}

        <div className="flex-1 overflow-y-auto py-1">
          {isLoading ? (
            <div className="flex items-center gap-2 px-3 py-4 text-xs text-muted-foreground">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              Loading...
            </div>
          ) : isRemoteSearching ? (
            <div className="flex items-center gap-2 px-3 py-4 text-xs text-muted-foreground">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              Searching notes...
            </div>
          ) : filteredNotes.length > 0 ? (
            filteredNotes.map((note) => (
              <div
                className={[
                  'group mx-1 flex cursor-pointer select-none items-center gap-1 rounded-md px-2 py-1.5 transition-colors',
                  selectedNoteId === note.id
                    ? 'bg-secondary text-foreground'
                    : 'text-muted-foreground hover:bg-secondary/60 hover:text-foreground',
                ].join(' ')}
                key={note.id}
                onClick={() => handleSelectNote(note)}
              >
                <ChevronRight className="h-3 w-3 shrink-0 opacity-40" />
                <div className="min-w-0 flex-1">
                  <span className="block truncate text-sm">{note.title || 'Untitled'}</span>
                  {note.tags?.length ? (
                    <div className="mt-1 flex flex-wrap gap-1">
                      {note.tags.slice(0, 3).map((tag) => (
                        <Badge key={tag} variant="outline" className="px-1.5 py-0 text-[10px] capitalize">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  ) : null}
                </div>
              </div>
            ))
          ) : (
            <p className="px-3 py-4 text-xs text-muted-foreground">
              {selectedTag || deferredSearch ? 'No notes match the current filters.' : 'No pages yet. Click + to create one.'}
            </p>
          )}
        </div>

        <div className="flex flex-col gap-1 border-t border-border/60 px-2 py-2">
          <button
            className="flex items-center gap-2 rounded px-2 py-1.5 text-xs text-muted-foreground transition-colors hover:bg-secondary/60 hover:text-foreground"
            onClick={() => fileInputRef.current?.click()}
            type="button"
          >
            <FileUp className="h-3.5 w-3.5" />
            Import .md
          </button>
          <button
            className="flex items-center gap-2 rounded px-2 py-1.5 text-xs text-muted-foreground transition-colors hover:bg-secondary/60 hover:text-foreground"
            onClick={() => setShowAiBar((value) => !value)}
            type="button"
          >
            <Bot className="h-3.5 w-3.5" />
            AI Draft
          </button>
          <input
            accept=".md,text/markdown"
            className="hidden"
            onChange={handleImportFile}
            ref={fileInputRef}
            type="file"
          />
        </div>
      </aside>

      <div className="flex flex-1 flex-col overflow-hidden">
        <div className="flex shrink-0 items-center justify-between border-b border-border/60 px-6 py-2">
          <span className="text-xs text-muted-foreground">
            {draft.updated_at ? `Edited ${new Date(draft.updated_at).toLocaleDateString()}` : ''}
            {draft.is_ai_generated ? ' • AI' : ''}
            {draft.source_path ? ` • ${draft.source_path}` : ''}
          </span>
          <div className="flex items-center gap-2">
            <Button
              className="h-7 text-xs text-muted-foreground"
              disabled={isRecording || isTranscribing}
              onClick={handleReadNote}
              size="sm"
              variant="ghost"
            >
              {isReading ? <Square className="mr-1 h-3.5 w-3.5" /> : <Volume2 className="mr-1 h-3.5 w-3.5" />}
              {isReading ? 'Stop' : 'Read'}
            </Button>
            <Button
              className="h-7 text-xs text-muted-foreground"
              disabled={isReading || isTranscribing}
              onClick={handleWriteNote}
              size="sm"
              variant="ghost"
            >
              {isRecording ? <Square className="mr-1 h-3.5 w-3.5" /> : isTranscribing ? <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" /> : <Mic className="mr-1 h-3.5 w-3.5" />}
              {isRecording ? 'Stop' : isTranscribing ? 'Writing...' : 'Write'}
            </Button>
            <Button
              className="h-7 text-xs text-muted-foreground"
              onClick={() => setShowAiBar((value) => !value)}
              size="sm"
              variant="ghost"
            >
              <Bot className="mr-1 h-3.5 w-3.5" />
              Ask AI
            </Button>
            <Button className="h-7 text-xs" disabled={isSaving} onClick={handleSaveNote} size="sm">
              {isSaving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : 'Save'}
            </Button>
          </div>
        </div>

        {showAiBar ? (
          <div className="flex shrink-0 items-center gap-2 border-b border-border/60 bg-secondary/30 px-6 py-2">
            <Bot className="h-4 w-4 shrink-0 text-muted-foreground" />
            <Input
              className="h-7 flex-1 border-0 bg-transparent px-1 text-sm shadow-none focus-visible:ring-0"
              onChange={(event) => setAiPrompt(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter') {
                  handleGenerateAiNote();
                }
              }}
              placeholder="Ask Gemini to draft meeting notes, summaries, or research briefs..."
              value={aiPrompt}
            />
            <Button
              className="h-7 shrink-0 text-xs"
              disabled={isGenerating || !aiPrompt.trim()}
              onClick={handleGenerateAiNote}
              size="sm"
            >
              {isGenerating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : 'Generate'}
            </Button>
            <button
              className="text-muted-foreground hover:text-foreground"
              onClick={() => setShowAiBar(false)}
              type="button"
            >
              <MoreHorizontal className="h-4 w-4" />
            </button>
          </div>
        ) : null}

        <div className="mx-auto flex w-full max-w-3xl flex-1 overflow-y-auto px-12 py-8">
          <div className="w-full">
            {draft.tags?.length ? (
              <div className="mb-4 flex flex-wrap gap-2">
                {draft.tags.map((tag) => (
                  <Badge key={tag} variant="secondary" className="capitalize">{tag}</Badge>
                ))}
              </div>
            ) : null}
            <input
              className="mb-4 w-full bg-transparent text-4xl font-bold text-foreground outline-none placeholder:text-muted-foreground/50"
              onChange={(event) => setDraft((current) => ({ ...current, title: event.target.value }))}
              placeholder="Untitled"
              value={draft.title}
            />
            <Textarea
              className="min-h-[60vh] w-full resize-none border-0 bg-transparent p-0 text-base leading-7 text-foreground shadow-none placeholder:text-muted-foreground/40 focus-visible:ring-0"
              onChange={(event) => setDraft((current) => ({ ...current, content: event.target.value }))}
              placeholder="Start writing, or ask AI above..."
              value={draft.content}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
