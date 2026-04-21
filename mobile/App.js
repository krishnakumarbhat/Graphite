import { StatusBar } from 'expo-status-bar';
import { useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Pressable, SafeAreaView, StyleSheet, Text, View, useColorScheme } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { LOCAL_DEFAULT_USER_ID } from './src/config/constants';
import { getThemeTokens } from './src/config/theme';
import { previewSettings } from './src/data/previewData';
import { bootstrapApp } from './src/core/bootstrap';
import { ensureLocalDefaultUser, ensureUserMirror } from './src/db/usersRepo';
import { NoteEditorScreen } from './src/screens/note-editor-screen';
import { NotesScreen } from './src/screens/notes-screen';
import { ProfileSettingsScreen } from './src/screens/profile-settings-screen';
import { WorkflowScreen } from './src/screens/workflow-screen';
import {
  getCurrentUser,
  isSupabaseConfigured,
  onAuthStateChange,
  signInWithEmail,
  signOutSession,
  signUpWithEmail,
} from './src/services/authService';
import {
  createDraftNote,
  generateWorkflowForApp,
  loadNotesForApp,
  loadWorkflowForApp,
  saveNoteForApp,
  sortNotesDescending,
} from './src/services/localDataService';

export default function App() {
  const colorScheme = useColorScheme();
  const [themeMode, setThemeMode] = useState('system');
  const [bootState, setBootState] = useState({ status: 'loading', payload: null, error: null });
  const [activeTab, setActiveTab] = useState('notes');
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [notes, setNotes] = useState([]);
  const [editorNote, setEditorNote] = useState(null);
  const [workflowPreview, setWorkflowPreview] = useState({ title: 'Workflow Agent Preview', prompt: '', nodes: [] });
  const [workflowPrompt, setWorkflowPrompt] = useState('Create a workflow to find VC funding');
  const [settings, setSettings] = useState(previewSettings);
  const [currentUser, setCurrentUser] = useState(null);
  const [activeUserId, setActiveUserId] = useState(LOCAL_DEFAULT_USER_ID);

  const resolvedThemeMode = themeMode === 'system' ? (colorScheme === 'dark' ? 'dark' : 'light') : themeMode;
  const theme = useMemo(() => getThemeTokens(resolvedThemeMode), [resolvedThemeMode]);
  const styles = useMemo(() => createStyles(theme), [theme]);

  useEffect(() => {
    let isMounted = true;

    const resolveUserContext = async (databaseEnabled, user) => {
      if (!databaseEnabled) {
        return LOCAL_DEFAULT_USER_ID;
      }

      if (user?.id) {
        await ensureUserMirror({
          userId: user.id,
          email: user.email,
          displayName: user.user_metadata?.full_name ?? user.email,
          provider: 'supabase',
        });
        return user.id;
      }

      const localUser = await ensureLocalDefaultUser();
      return localUser?.id ?? LOCAL_DEFAULT_USER_ID;
    };

    const hydrateForUser = async (databaseEnabled, userId) => {
      const [loadedNotes, loadedWorkflow] = await Promise.all([
        loadNotesForApp(databaseEnabled, userId),
        loadWorkflowForApp(databaseEnabled, userId),
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
    };

    const startApp = async () => {
      try {
        const payload = await bootstrapApp();
        const databaseEnabled = payload.status === 'ready';

        let user = null;
        try {
          user = await getCurrentUser();
        } catch (error) {
          console.warn('[auth] Unable to fetch current user:', error?.message ?? error);
        }

        const userId = await resolveUserContext(databaseEnabled, user);
        await hydrateForUser(databaseEnabled, userId);

        if (!isMounted) {
          return;
        }

        setCurrentUser(user);
        setActiveUserId(userId);
        setBootState({ status: 'ready', payload, error: null });
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

    const authListener = onAuthStateChange(async (user) => {
      if (!isMounted) {
        return;
      }

      const databaseEnabled = bootState.payload?.status === 'ready';
      const userId = await resolveUserContext(databaseEnabled, user);

      if (databaseEnabled) {
        await hydrateForUser(databaseEnabled, userId);
      }

      setCurrentUser(user);
      setActiveUserId(userId);
    });

    return () => {
      isMounted = false;
      authListener?.data?.subscription?.unsubscribe?.();
    };
  }, [bootState.payload?.status]);

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
  const runtimeStatus = bootState.payload?.warning ?? 'Native runtime uses expo-sqlite with user-scoped notes/workflows.';

  const handleCreateNote = () => {
    setEditorNote({ ...createDraftNote(), user_id: activeUserId });
  };

  const handleSaveNote = async () => {
    if (!editorNote) {
      return;
    }

    const savedNote = await saveNoteForApp(databaseEnabled, editorNote, activeUserId);
    setNotes((currentNotes) => {
      const nextNotes = currentNotes.filter((note) => note.id !== savedNote.id);
      return sortNotesDescending([savedNote, ...nextNotes]);
    });
    setEditorNote(null);
  };

  const handleGenerateWorkflow = async () => {
    const nextWorkflow = await generateWorkflowForApp(workflowPrompt);
    setWorkflowPreview(nextWorkflow);
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
        <View style={styles.loadingState}>
          <ActivityIndicator color={theme.colors.primary} size="large" />
          <Text style={styles.loadingTitle}>Preparing your local-first workspace</Text>
          <Text style={styles.loadingBody}>Loading user-scoped notes, workflows, and profile state.</Text>
        </View>
      );
    }

    if (bootState.error) {
      return (
        <View style={styles.loadingState}>
          <Text style={styles.errorTitle}>Startup blocked</Text>
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

    if (isProfileOpen) {
      return (
        <ProfileSettingsScreen
          authEnabled={isSupabaseConfigured()}
          currentUser={currentUser}
          onClose={() => setIsProfileOpen(false)}
          onSignIn={signInWithEmail}
          onSignOut={async () => {
            await signOutSession();
            setIsProfileOpen(false);
          }}
          onSignUp={signUpWithEmail}
          onToggleSetting={handleToggleSetting}
          onToggleTheme={() => setThemeMode((current) => {
            if (current === 'system') return 'dark';
            if (current === 'dark') return 'light';
            return 'system';
          })}
          resolvedThemeMode={resolvedThemeMode}
          settings={settings}
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

    return (
      <NotesScreen
        notes={filteredNotes}
        onCreateNote={handleCreateNote}
        onOpenNote={(note) => setEditorNote({ ...note, isDraft: false })}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        statusMessage={statusMessage}
        theme={theme}
      />
    );
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar style={resolvedThemeMode === 'dark' ? 'light' : 'dark'} />

      <View style={styles.header}>
        <View style={styles.headerTextWrap}>
          <Text style={styles.headerEyebrow}>Graphite local-first</Text>
          <Text style={styles.headerTitle}>Notes and workflows</Text>
        </View>

        <View style={styles.headerActions}>
          <Pressable
            onPress={() => {
              setIsProfileOpen(false);
              setActiveTab('notes');
            }}
            style={[styles.topTab, activeTab === 'notes' && !isProfileOpen ? styles.topTabActive : null]}
          >
            <Text style={[styles.topTabText, activeTab === 'notes' && !isProfileOpen ? styles.topTabTextActive : null]}>Notes</Text>
          </Pressable>
          <Pressable
            onPress={() => {
              setIsProfileOpen(false);
              setActiveTab('workflow');
            }}
            style={[styles.topTab, activeTab === 'workflow' && !isProfileOpen ? styles.topTabActive : null]}
          >
            <Text style={[styles.topTabText, activeTab === 'workflow' && !isProfileOpen ? styles.topTabTextActive : null]}>Workflows</Text>
          </Pressable>
          <Pressable
            onPress={() => setIsProfileOpen(true)}
            style={[styles.profileButton, isProfileOpen ? styles.profileButtonActive : null]}
          >
            <Feather color={theme.colors.text} name="user" size={16} />
          </Pressable>
        </View>
      </View>

      <View style={styles.contentWrap}>{renderContent()}</View>

      <View style={styles.footerStatus}>
        <Text style={styles.footerStatusText}>{runtimeStatus}</Text>
      </View>
    </SafeAreaView>
  );
}

const createStyles = (theme) => StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  header: {
    alignItems: 'center',
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
    fontSize: 24,
    fontWeight: '700',
    lineHeight: 30,
  },
  headerActions: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: theme.spacing.sm,
  },
  topTab: {
    backgroundColor: theme.colors.surfaceMuted,
    borderColor: theme.colors.border,
    borderRadius: theme.radius.control,
    borderWidth: 1,
    justifyContent: 'center',
    minHeight: 34,
    paddingHorizontal: theme.spacing.md,
  },
  topTabActive: {
    backgroundColor: theme.colors.primarySoft,
    borderColor: theme.colors.primary,
  },
  topTabText: {
    color: theme.colors.textMuted,
    fontSize: 12,
    fontWeight: '700',
  },
  topTabTextActive: {
    color: theme.colors.primaryDeep,
  },
  profileButton: {
    alignItems: 'center',
    backgroundColor: theme.colors.surfaceMuted,
    borderColor: theme.colors.border,
    borderRadius: theme.radius.pill,
    borderWidth: 1,
    height: 34,
    justifyContent: 'center',
    width: 34,
  },
  profileButtonActive: {
    backgroundColor: theme.colors.primarySoft,
    borderColor: theme.colors.primary,
  },
  contentWrap: {
    flex: 1,
  },
  footerStatus: {
    borderTopColor: theme.colors.border,
    borderTopWidth: 1,
    paddingHorizontal: theme.spacing.lg,
    paddingVertical: theme.spacing.sm,
  },
  footerStatusText: {
    color: theme.colors.textMuted,
    fontSize: 12,
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
