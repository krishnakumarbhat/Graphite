import { Pressable, ScrollView, StyleSheet, Switch, Text, View } from 'react-native';
import { SectionCard, SectionHeader } from '../components/section-card';

export const SettingsScreen = ({
  theme,
  resolvedThemeMode,
  onToggleTheme,
  settings,
  onToggleSetting,
  modelDirectories,
  runtimeStatus,
}) => {
  const styles = createStyles(theme);

  return (
    <ScrollView
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
      testID="settings-screen"
      dataSet={{ testid: 'settings-screen' }}
    >
      <SectionHeader
        eyebrow="Settings"
        title="Keep your assistant local-first"
        description="This view surfaces theme, reminders, sync placeholders, and model storage visibility."
        theme={theme}
        testID="settings-screen-header"
      />

      <SectionCard theme={theme} testID="settings-list">
        <View style={styles.rowBetween}>
          <View style={styles.copyWrap}>
            <Text style={styles.itemTitle}>Appearance</Text>
            <Text style={styles.itemBody}>Current theme: {resolvedThemeMode}</Text>
          </View>
          <Pressable
            onPress={onToggleTheme}
            style={styles.themeButton}
            testID="settings-theme-toggle-button"
            dataSet={{ testid: 'settings-theme-toggle-button' }}
          >
            <Text style={styles.themeButtonText}>Toggle</Text>
          </Pressable>
        </View>

        <View style={styles.separator} />

        <View style={styles.rowBetween}>
          <View style={styles.copyWrap}>
            <Text style={styles.itemTitle}>Speak meeting reminders</Text>
            <Text style={styles.itemBody}>Placeholder for local TTS reminder playback.</Text>
          </View>
          <Switch
            onValueChange={() => onToggleSetting('speakReminders')}
            testID="settings-speak-reminders-switch"
            thumbColor="#FFFFFF"
            trackColor={{ false: theme.colors.border, true: theme.colors.primary }}
            value={settings.speakReminders}
          />
        </View>

        <View style={styles.separator} />

        <View style={styles.rowBetween}>
          <View style={styles.copyWrap}>
            <Text style={styles.itemTitle}>Offline-first priority</Text>
            <Text style={styles.itemBody}>Keep local storage as source of truth before sync.</Text>
          </View>
          <Switch
            onValueChange={() => onToggleSetting('offlinePriority')}
            testID="settings-offline-priority-switch"
            thumbColor="#FFFFFF"
            trackColor={{ false: theme.colors.border, true: theme.colors.primary }}
            value={settings.offlinePriority}
          />
        </View>
      </SectionCard>

      <SectionCard theme={theme} testID="settings-runtime-card">
        <Text style={styles.itemTitle}>Runtime status</Text>
        <Text style={styles.itemBody}>{runtimeStatus}</Text>
        <Text style={styles.itemBody}>Supabase auth, sync engine, and Google integrations are intentionally staged for upcoming phases.</Text>
      </SectionCard>

      <SectionCard theme={theme} testID="settings-storage-card">
        <Text style={styles.itemTitle}>Reserved on-device model directories</Text>
        <View style={styles.modelStack}>
          {modelDirectories.map((directory) => (
            <Text
              key={directory}
              style={styles.modelLine}
              testID={`settings-model-directory-${directory.replace(/[^a-z0-9]+/gi, '-').toLowerCase()}`}
              dataSet={{ testid: `settings-model-directory-${directory.replace(/[^a-z0-9]+/gi, '-').toLowerCase()}` }}
            >
              {directory}
            </Text>
          ))}
        </View>
      </SectionCard>
    </ScrollView>
  );
};

const createStyles = (theme) => StyleSheet.create({
  content: {
    gap: theme.spacing.lg,
    paddingBottom: theme.spacing.xxxl,
    paddingHorizontal: theme.spacing.lg,
    paddingTop: theme.spacing.xl,
  },
  rowBetween: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: theme.spacing.lg,
    justifyContent: 'space-between',
  },
  copyWrap: {
    flex: 1,
    gap: theme.spacing.xs,
  },
  itemTitle: {
    color: theme.colors.text,
    fontSize: 16,
    fontWeight: '700',
  },
  itemBody: {
    color: theme.colors.textSoft,
    fontSize: 14,
    lineHeight: 22,
  },
  themeButton: {
    alignItems: 'center',
    backgroundColor: theme.colors.primarySoft,
    borderRadius: theme.radius.control,
    justifyContent: 'center',
    minHeight: 44,
    minWidth: 88,
    paddingHorizontal: theme.spacing.md,
  },
  themeButtonText: {
    color: theme.colors.primaryDeep,
    fontSize: 13,
    fontWeight: '700',
  },
  separator: {
    backgroundColor: theme.colors.border,
    height: 1,
    width: '100%',
  },
  modelStack: {
    gap: theme.spacing.sm,
  },
  modelLine: {
    color: theme.colors.primaryDeep,
    fontFamily: 'monospace',
    fontSize: 13,
  },
});
