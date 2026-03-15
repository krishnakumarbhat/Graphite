import { StatusBar } from 'expo-status-bar';
import { useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, SafeAreaView, StyleSheet, Text, View, useColorScheme } from 'react-native';
import { BottomTabBar } from './src/components/bottom-tab-bar';
import { getThemeTokens } from './src/config/theme';
import { previewSettings } from './src/data/previewData';
import { bootstrapApp } from './src/core/bootstrap';
import { NoteEditorScreen } from './src/screens/note-editor-screen';
import { NotesScreen } from './src/screens/notes-screen';
import { SettingsScreen } from './src/screens/settings-screen';
import { WorkflowScreen } from './src/screens/workflow-screen';
import {
  buildWorkflowPreview,
  createDraftNote,
  loadNotesForApp,
  loadWorkflowForApp,
  saveNoteForApp,
  sortNotesDescending,
} from './src/services/localDataService';

export default function App() {
  const colorScheme = useColorScheme();
  const [themeMode, setThemeMode] = useState('system');
  const [bootState, setBootState] = useState({
    status: 'loading',
    payload: null,
    error: null,
  });
  const [activeTab, setActiveTab] = useState('notes');
  const [searchQuery, setSearchQuery] = useState('');
  const [notes, setNotes] = useState([]);
  const [editorNote, setEditorNote] = useState(null);
  const [workflowPreview, setWorkflowPreview] = useState(buildWorkflowPreview('Create a workflow to find VC funding'));
  const [workflowPrompt, setWorkflowPrompt] = useState('Create a workflow to find VC funding');
  const [settings, setSettings] = useState(previewSettings);

  const resolvedThemeMode = themeMode === 'system'
    ? (colorScheme === 'dark' ? 'dark' : 'light')
    : themeMode;
  const theme = useMemo(() => getThemeTokens(resolvedThemeMode), [resolvedThemeMode]);
  const styles = useMemo(() => createStyles(theme), [theme]);

  useEffect(() => {
    let isMounted = true;

    const startApp = async () => {
      try {
        const payload = await bootstrapApp();
        const databaseEnabled = payload.status === 'ready';
        const [loadedNotes, loadedWorkflow] = await Promise.all([
          loadNotesForApp(databaseEnabled),
          loadWorkflowForApp(databaseEnabled),
        ]);

        if (!isMounted) {
          return;
        }

        setNotes(loadedNotes);
        setWorkflowPreview({
          title: loadedWorkflow.title,
          prompt: loadedWorkflow.prompt,
          nodes: loadedWorkflow.nodes,
        });
        setWorkflowPrompt(loadedWorkflow.prompt);
        setBootState({
          status: 'ready',
          payload,
          error: null,
        });
      } catch (error) {
        if (!isMounted) {
          return;
        }

        setBootState({
          status: 'error',
          payload: null,
          error: error?.message ?? 'Unknown boot error',
        });
      }
    };

    startApp();

    return () => {
      isMounted = false;
    };
  }, []);

  const filteredNotes = useMemo(() => {
    const normalizedQuery = searchQuery.trim().toLowerCase();

    if (!normalizedQuery) {
      return notes;
    }

    return notes.filter((note) => (
      note.title.toLowerCase().includes(normalizedQuery) ||
      note.content.toLowerCase().includes(normalizedQuery)
    ));
  }, [notes, searchQuery]);

  const isLoading = bootState.status === 'loading';
  const databaseEnabled = bootState.payload?.status === 'ready';
  const statusMessage = databaseEnabled ? 'Native SQLite connected' : 'Web preview uses seeded data';
  const runtimeStatus = bootState.payload?.warning ?? 'Native runtime will use SQLite-backed notes and workflows.';

  const handleCreateNote = () => {
    setEditorNote(createDraftNote());
  };

  const handleOpenNote = (note) => {
    setEditorNote({ ...note, isDraft: false });
  };

  const handleSaveNote = async () => {
    if (!editorNote) {
      return;
    }

    const savedNote = await saveNoteForApp(databaseEnabled, editorNote);

    setNotes((currentNotes) => {
      const nextNotes = currentNotes.filter((note) => note.id !== savedNote.id);
      return sortNotesDescending([savedNote, ...nextNotes]);
    });
    setEditorNote(null);
  };

  const handleGenerateWorkflow = () => {
    setWorkflowPreview(buildWorkflowPreview(workflowPrompt));
  };

  const handleToggleSetting = (key) => {
    setSettings((current) => ({
      ...current,
      [key]: !current[key],
    }));
  };

  const renderContent = () => {
    if (isLoading) {
      return (
        <View style={styles.loadingState} testID="mobile-app-loading-state" dataSet={{ testid: 'mobile-app-loading-state' }}>
          <ActivityIndicator color={theme.colors.primary} size="large" />
          <Text style={styles.loadingTitle}>Preparing your second brain</Text>
          <Text style={styles.loadingBody}>Loading notes, workflow previews, and local-first shell.</Text>
        </View>
      );
    }

    if (bootState.error) {
      return (
        <View style={styles.loadingState} testID="mobile-app-error-state" dataSet={{ testid: 'mobile-app-error-state' }}>
          <Text style={styles.errorTitle}>Something blocked the preview</Text>
          <Text style={styles.errorBody}>{bootState.error}</Text>
        </View>
      );
    }

    if (editorNote) {
      return (
        <NoteEditorScreen
          draftNote={editorNote}
          onBack={() => setEditorNote(null)}
          onChange={(field, value) => setEditorNote((current) => ({ ...current, [field]: value }))}
          onSave={handleSaveNote}
          theme={theme}
        />
      );
    }

    if (activeTab === 'workflow') {
      return (
        <WorkflowScreen
          onChangePrompt={setWorkflowPrompt}
          onGenerate={handleGenerateWorkflow}
          prompt={workflowPrompt}
          theme={theme}
          workflow={workflowPreview}
        />
      );
    }

    if (activeTab === 'settings') {
      return (
        <SettingsScreen
          modelDirectories={bootState.payload?.modelDirectories ?? []}
          onToggleSetting={handleToggleSetting}
          onToggleTheme={() => setThemeMode((current) => {
            if (current === 'system') return 'dark';
            if (current === 'dark') return 'light';
            return 'system';
          })}
          resolvedThemeMode={resolvedThemeMode}
          runtimeStatus={runtimeStatus}
          settings={settings}
          theme={theme}
        />
      );
    }

    return (
      <NotesScreen
        notes={filteredNotes}
        onCreateNote={handleCreateNote}
        onOpenNote={handleOpenNote}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        statusMessage={statusMessage}
        theme={theme}
      />
    );
  };

  return (
    <SafeAreaView style={styles.safeArea} testID="mobile-app-root" dataSet={{ testid: 'mobile-app-root' }}>
      <StatusBar style={resolvedThemeMode === 'dark' ? 'light' : 'dark'} />
      <View style={styles.header} testID="mobile-app-header" dataSet={{ testid: 'mobile-app-header' }}>
        <View style={styles.headerTextWrap}>
          <Text style={styles.headerEyebrow} testID="mobile-app-header-eyebrow" dataSet={{ testid: 'mobile-app-header-eyebrow' }}>
            Second Brain Mobile
          </Text>
          <Text style={styles.headerTitle} testID="mobile-app-header-title" dataSet={{ testid: 'mobile-app-header-title' }}>
            Autonomous executive assistant
          </Text>
        </View>
        <View style={styles.headerBadge} testID="mobile-app-header-badge" dataSet={{ testid: 'mobile-app-header-badge' }}>
          <Text style={styles.headerBadgeText}>Phase 2</Text>
        </View>
      </View>

      <View style={styles.contentWrap}>{renderContent()}</View>

      {!editorNote ? (
        <BottomTabBar activeTab={activeTab} onChange={setActiveTab} theme={theme} />
      ) : null}
    </SafeAreaView>
  );
}

const createStyles = (theme) => StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  header: {
    alignItems: 'flex-start',
    borderBottomColor: theme.colors.border,
    borderBottomWidth: 1,
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: theme.spacing.lg,
    paddingVertical: theme.spacing.md,
  },
  headerTextWrap: {
    flex: 1,
    gap: 2,
    paddingRight: theme.spacing.md,
  },
  headerEyebrow: {
    color: theme.colors.primaryDeep,
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
  },
  headerTitle: {
    color: theme.colors.text,
    fontSize: 18,
    fontWeight: '700',
    lineHeight: 24,
  },
  headerBadge: {
    backgroundColor: theme.colors.primarySoft,
    borderRadius: theme.radius.pill,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.xs,
  },
  headerBadgeText: {
    color: theme.colors.primaryDeep,
    fontSize: 12,
    fontWeight: '700',
  },
  contentWrap: {
    flex: 1,
  },
  loadingState: {
    alignItems: 'flex-start',
    flex: 1,
    gap: theme.spacing.sm,
    justifyContent: 'center',
    paddingHorizontal: theme.spacing.xxl,
  },
  loadingTitle: {
    color: theme.colors.text,
    fontSize: 22,
    fontWeight: '700',
  },
  loadingBody: {
    color: theme.colors.textSoft,
    fontSize: 15,
    lineHeight: 24,
  },
  errorTitle: {
    color: theme.colors.danger,
    fontSize: 20,
    fontWeight: '700',
  },
  errorBody: {
    color: theme.colors.textSoft,
    fontSize: 15,
    lineHeight: 24,
  },
});
