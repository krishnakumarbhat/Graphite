import { useMemo, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { SectionCard, SectionHeader } from '../components/section-card';

export const ProfileSettingsScreen = ({
  currentUser,
  onClose,
  onSignIn,
  onSignUp,
  onSignOut,
  onToggleTheme,
  settings,
  onToggleSetting,
  resolvedThemeMode,
  theme,
  authEnabled,
}) => {
  const styles = createStyles(theme);
  const [mode, setMode] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState('');

  const actionLabel = mode === 'login' ? 'Login' : 'Register';
  const isSignedIn = Boolean(currentUser?.id);
  const profileLabel = useMemo(() => {
    if (!isSignedIn) {
      return 'Not signed in';
    }

    return currentUser.email || currentUser.id;
  }, [currentUser, isSignedIn]);

  const submitAuth = async () => {
    if (!authEnabled) {
      setFeedback('Supabase not configured. Set EXPO_PUBLIC_SUPABASE_URL and EXPO_PUBLIC_SUPABASE_ANON_KEY.');
      return;
    }

    setBusy(true);
    setFeedback('');

    try {
      if (mode === 'login') {
        await onSignIn({ email, password });
        setFeedback('Logged in successfully.');
      } else {
        await onSignUp({ email, password });
        setFeedback('Registration complete. Check your email if confirmation is enabled.');
      }
    } catch (error) {
      setFeedback(error?.message ?? 'Authentication failed.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
      <View style={styles.topRow}>
        <SectionHeader
          eyebrow="Profile & Settings"
          title="Account, theme, and local-first controls"
          description="Use Supabase Auth for sign-in and keep data scoped by user_id."
          theme={theme}
          testID="profile-settings-header"
        />
        <Pressable onPress={onClose} style={styles.closeButton}>
          <Feather color={theme.colors.text} name="x" size={18} />
        </Pressable>
      </View>

      <SectionCard theme={theme} testID="profile-account-card">
        <Text style={styles.itemTitle}>Account</Text>
        <Text style={styles.itemBody}>{profileLabel}</Text>

        {!isSignedIn ? (
          <>
            <View style={styles.modeRow}>
              <Pressable
                onPress={() => setMode('login')}
                style={[styles.modeButton, mode === 'login' ? styles.modeButtonActive : null]}
              >
                <Text style={[styles.modeButtonText, mode === 'login' ? styles.modeButtonTextActive : null]}>Login</Text>
              </Pressable>
              <Pressable
                onPress={() => setMode('register')}
                style={[styles.modeButton, mode === 'register' ? styles.modeButtonActive : null]}
              >
                <Text style={[styles.modeButtonText, mode === 'register' ? styles.modeButtonTextActive : null]}>Register</Text>
              </Pressable>
            </View>

            <TextInput
              autoCapitalize="none"
              keyboardType="email-address"
              onChangeText={setEmail}
              placeholder="Email"
              placeholderTextColor={theme.colors.textMuted}
              style={styles.input}
              value={email}
            />
            <TextInput
              onChangeText={setPassword}
              placeholder="Password"
              placeholderTextColor={theme.colors.textMuted}
              secureTextEntry
              style={styles.input}
              value={password}
            />

            <Pressable onPress={submitAuth} style={styles.primaryButton}>
              <Text style={styles.primaryButtonText}>{busy ? 'Please wait...' : actionLabel}</Text>
            </Pressable>
          </>
        ) : (
          <Pressable onPress={onSignOut} style={styles.secondaryButton}>
            <Text style={styles.secondaryButtonText}>Sign out</Text>
          </Pressable>
        )}

        {feedback ? <Text style={styles.feedbackText}>{feedback}</Text> : null}
      </SectionCard>

      <SectionCard theme={theme} testID="profile-preferences-card">
        <Text style={styles.itemTitle}>Preferences</Text>
        <View style={styles.preferenceRow}>
          <Text style={styles.itemBody}>Theme: {resolvedThemeMode}</Text>
          <Pressable onPress={onToggleTheme} style={styles.secondaryButtonCompact}>
            <Text style={styles.secondaryButtonText}>Toggle</Text>
          </Pressable>
        </View>

        <View style={styles.preferenceRow}>
          <Text style={styles.itemBody}>Speak reminders</Text>
          <Pressable onPress={() => onToggleSetting('speakReminders')} style={styles.secondaryButtonCompact}>
            <Text style={styles.secondaryButtonText}>{settings.speakReminders ? 'On' : 'Off'}</Text>
          </Pressable>
        </View>

        <View style={styles.preferenceRow}>
          <Text style={styles.itemBody}>Offline-first priority</Text>
          <Pressable onPress={() => onToggleSetting('offlinePriority')} style={styles.secondaryButtonCompact}>
            <Text style={styles.secondaryButtonText}>{settings.offlinePriority ? 'On' : 'Off'}</Text>
          </Pressable>
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
  topRow: {
    gap: theme.spacing.md,
  },
  closeButton: {
    alignItems: 'center',
    alignSelf: 'flex-end',
    backgroundColor: theme.colors.surface,
    borderColor: theme.colors.border,
    borderRadius: theme.radius.pill,
    borderWidth: 1,
    height: 36,
    justifyContent: 'center',
    width: 36,
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
  modeRow: {
    flexDirection: 'row',
    gap: theme.spacing.sm,
  },
  modeButton: {
    backgroundColor: theme.colors.surfaceMuted,
    borderColor: theme.colors.border,
    borderRadius: theme.radius.control,
    borderWidth: 1,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.sm,
  },
  modeButtonActive: {
    backgroundColor: theme.colors.primarySoft,
    borderColor: theme.colors.primary,
  },
  modeButtonText: {
    color: theme.colors.textMuted,
    fontSize: 13,
    fontWeight: '700',
  },
  modeButtonTextActive: {
    color: theme.colors.primaryDeep,
  },
  input: {
    backgroundColor: theme.colors.surfaceMuted,
    borderColor: theme.colors.border,
    borderRadius: theme.radius.control,
    borderWidth: 1,
    color: theme.colors.text,
    fontSize: 14,
    minHeight: 44,
    paddingHorizontal: theme.spacing.md,
  },
  primaryButton: {
    alignItems: 'center',
    backgroundColor: theme.colors.primary,
    borderRadius: theme.radius.control,
    justifyContent: 'center',
    minHeight: 44,
    paddingHorizontal: theme.spacing.lg,
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
  secondaryButton: {
    alignItems: 'center',
    alignSelf: 'flex-start',
    backgroundColor: theme.colors.surfaceMuted,
    borderColor: theme.colors.border,
    borderRadius: theme.radius.control,
    borderWidth: 1,
    justifyContent: 'center',
    minHeight: 42,
    paddingHorizontal: theme.spacing.lg,
  },
  secondaryButtonCompact: {
    alignItems: 'center',
    backgroundColor: theme.colors.surfaceMuted,
    borderColor: theme.colors.border,
    borderRadius: theme.radius.control,
    borderWidth: 1,
    justifyContent: 'center',
    minHeight: 34,
    minWidth: 72,
    paddingHorizontal: theme.spacing.md,
  },
  secondaryButtonText: {
    color: theme.colors.text,
    fontSize: 13,
    fontWeight: '700',
  },
  feedbackText: {
    color: theme.colors.textMuted,
    fontSize: 12,
    lineHeight: 18,
  },
  preferenceRow: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
});
