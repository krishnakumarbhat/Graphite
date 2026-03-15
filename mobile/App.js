import { StatusBar } from 'expo-status-bar';
import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { bootstrapApp } from './src/core/bootstrap';
import { theme } from './src/config/theme';

const scopeItems = [
  {
    id: 'scope-item-expo-scaffold',
    label: 'Expo app scaffold in /app/mobile',
  },
  {
    id: 'scope-item-blank-model-folders',
    label: 'Blank on-device model folders for tts, stt, and vision',
  },
  {
    id: 'scope-item-sqlite-schema',
    label: 'SQLite schema + migration runner for notes and workflows',
  },
  {
    id: 'scope-item-repositories',
    label: 'Repository helpers ready for future sync and editor layers',
  },
  {
    id: 'scope-item-stop-before-ui',
    label: 'Stop before UI screens/components pending approval',
  },
];

const createModelDirectoryTestId = (directory) => `model-directory-${directory.replace(/[^a-z0-9]+/gi, '-').toLowerCase()}`;

export default function App() {
  const [bootState, setBootState] = useState({
    status: 'loading',
    payload: null,
    error: null,
  });

  useEffect(() => {
    let isMounted = true;

    const startApp = async () => {
      try {
        const payload = await bootstrapApp();

        if (isMounted) {
          setBootState({
            status: payload.status,
            payload,
            error: null,
          });
        }
      } catch (error) {
        if (isMounted) {
          setBootState({
            status: 'error',
            payload: null,
            error: error?.message ?? 'Unknown bootstrap error',
          });
        }
      }
    };

    startApp();

    return () => {
      isMounted = false;
    };
  }, []);

  const isLoading = bootState.status === 'loading';
  const payload = bootState.payload;
  const smokeTest = payload?.smokeTest;
  const migration = payload?.migration;

  return (
    <SafeAreaView
      style={styles.safeArea}
      testID="app-bootstrap-screen"
      dataSet={{ testid: 'app-bootstrap-screen' }}
    >
      <StatusBar style="dark" />
      <ScrollView
        contentContainerStyle={styles.content}
        testID="app-bootstrap-scroll-view"
        dataSet={{ testid: 'app-bootstrap-scroll-view' }}
      >
        <View style={styles.hero} testID="app-bootstrap-hero" dataSet={{ testid: 'app-bootstrap-hero' }}>
          <Text style={styles.eyebrow} testID="app-bootstrap-phase-label" dataSet={{ testid: 'app-bootstrap-phase-label' }}>
            Phase 1 scaffold
          </Text>
          <Text style={styles.title} testID="app-bootstrap-title" dataSet={{ testid: 'app-bootstrap-title' }}>
            Second Brain mobile foundation
          </Text>
          <Text style={styles.body} testID="app-bootstrap-description" dataSet={{ testid: 'app-bootstrap-description' }}>
            Offline-first Expo scaffold initialized with a local SQLite data layer and future-ready mobile folder structure.
          </Text>
        </View>

        <View style={styles.card} testID="app-bootstrap-status-card" dataSet={{ testid: 'app-bootstrap-status-card' }}>
          <Text style={styles.sectionTitle} testID="app-bootstrap-status-heading" dataSet={{ testid: 'app-bootstrap-status-heading' }}>
            Boot status
          </Text>

          {isLoading ? (
            <View style={styles.loadingRow} testID="app-bootstrap-loading-state" dataSet={{ testid: 'app-bootstrap-loading-state' }}>
              <ActivityIndicator color={theme.colors.primary} />
              <Text style={styles.cardBody} testID="app-bootstrap-loading-copy" dataSet={{ testid: 'app-bootstrap-loading-copy' }}>
                Initializing local-first database…
              </Text>
            </View>
          ) : (
            <View style={styles.stack} testID="app-bootstrap-ready-state" dataSet={{ testid: 'app-bootstrap-ready-state' }}>
              <Text style={styles.statusPill} testID="app-bootstrap-status-pill" dataSet={{ testid: 'app-bootstrap-status-pill' }}>
                {bootState.status}
              </Text>
              <Text style={styles.cardBody} testID="app-bootstrap-platform-text" dataSet={{ testid: 'app-bootstrap-platform-text' }}>
                Platform: {payload?.platform ?? 'unknown'}
              </Text>
              <Text style={styles.cardBody} testID="app-bootstrap-migration-text" dataSet={{ testid: 'app-bootstrap-migration-text' }}>
                Migration: {migration ? `${migration.fromVersion} → ${migration.toVersion}` : 'native-ready scaffold'}
              </Text>
              <Text style={styles.cardBody} testID="app-bootstrap-note-count" dataSet={{ testid: 'app-bootstrap-note-count' }}>
                Notes in local store: {smokeTest?.notesCount ?? 0}
              </Text>
              <Text style={styles.cardBody} testID="app-bootstrap-workflow-count" dataSet={{ testid: 'app-bootstrap-workflow-count' }}>
                Workflows in local store: {smokeTest?.workflowsCount ?? 0}
              </Text>
              {payload?.warning ? (
                <Text style={styles.warningText} testID="app-bootstrap-warning" dataSet={{ testid: 'app-bootstrap-warning' }}>
                  {payload.warning}
                </Text>
              ) : null}
              {bootState.error ? (
                <Text style={styles.errorText} testID="app-bootstrap-error" dataSet={{ testid: 'app-bootstrap-error' }}>
                  {bootState.error}
                </Text>
              ) : null}
            </View>
          )}
        </View>

        <View style={styles.card} testID="app-bootstrap-scope-card" dataSet={{ testid: 'app-bootstrap-scope-card' }}>
          <Text style={styles.sectionTitle} testID="app-bootstrap-scope-heading" dataSet={{ testid: 'app-bootstrap-scope-heading' }}>
            Current scope
          </Text>
          {scopeItems.map((item) => (
            <Text
              key={item.id}
              style={styles.listItem}
              testID={item.id}
              dataSet={{ testid: item.id }}
            >
              • {item.label}
            </Text>
          ))}
        </View>

        <View style={styles.card} testID="app-bootstrap-model-card" dataSet={{ testid: 'app-bootstrap-model-card' }}>
          <Text style={styles.sectionTitle} testID="app-bootstrap-model-heading" dataSet={{ testid: 'app-bootstrap-model-heading' }}>
            Reserved local model folders
          </Text>
          {(payload?.modelDirectories ?? []).map((directory) => {
            const testId = createModelDirectoryTestId(directory);

            return (
              <Text
                key={directory}
                style={styles.codeLine}
                testID={testId}
                dataSet={{ testid: testId }}
              >
                {directory}
              </Text>
            );
          })}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  content: {
    paddingHorizontal: theme.spacing.lg,
    paddingVertical: theme.spacing.xxl,
    gap: theme.spacing.lg,
  },
  hero: {
    gap: theme.spacing.sm,
    paddingBottom: theme.spacing.md,
  },
  eyebrow: {
    color: theme.colors.primaryDeep,
    fontSize: 13,
    fontWeight: '700',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
  },
  title: {
    color: theme.colors.text,
    fontSize: 30,
    fontWeight: '700',
    lineHeight: 38,
  },
  body: {
    color: theme.colors.textSoft,
    fontSize: 16,
    lineHeight: 26,
  },
  card: {
    backgroundColor: theme.colors.surface,
    borderColor: theme.colors.border,
    borderRadius: theme.radius.card,
    borderWidth: 1,
    padding: theme.spacing.xl,
    gap: theme.spacing.sm,
    shadowColor: '#111418',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.08,
    shadowRadius: 20,
    elevation: 2,
  },
  sectionTitle: {
    color: theme.colors.text,
    fontSize: 15,
    fontWeight: '700',
    marginBottom: theme.spacing.xs,
  },
  loadingRow: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: theme.spacing.sm,
    minHeight: 32,
  },
  stack: {
    gap: theme.spacing.sm,
  },
  statusPill: {
    alignSelf: 'flex-start',
    backgroundColor: theme.colors.canvas,
    borderColor: theme.colors.border,
    borderRadius: 999,
    borderWidth: 1,
    color: theme.colors.primaryDeep,
    overflow: 'hidden',
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.xs,
    textTransform: 'capitalize',
  },
  cardBody: {
    color: theme.colors.textSoft,
    fontSize: 15,
    lineHeight: 24,
  },
  listItem: {
    color: theme.colors.textSoft,
    fontSize: 15,
    lineHeight: 24,
  },
  codeLine: {
    color: theme.colors.primaryDeep,
    fontFamily: 'monospace',
    fontSize: 14,
    lineHeight: 22,
  },
  warningText: {
    color: theme.colors.warning,
    fontSize: 14,
    lineHeight: 22,
  },
  errorText: {
    color: theme.colors.danger,
    fontSize: 14,
    lineHeight: 22,
  },
});
