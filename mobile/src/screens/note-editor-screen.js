import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { SectionCard } from '../components/section-card';

const blockTypes = ['Paragraph', 'Heading', 'Checklist', 'Quote', 'Code'];

export const NoteEditorScreen = ({ draftNote, onBack, onSave, onChange, theme }) => {
  const styles = createStyles(theme);

  return (
    <ScrollView
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
      testID="note-editor-screen"
      dataSet={{ testid: 'note-editor-screen' }}
    >
      <View style={styles.topBar}>
        <Pressable
          onPress={onBack}
          style={styles.ghostButton}
          testID="editor-back-button"
          dataSet={{ testid: 'editor-back-button' }}
        >
          <Feather color={theme.colors.text} name="arrow-left" size={18} />
          <Text style={styles.ghostButtonText}>Back</Text>
        </Pressable>
        <Pressable
          onPress={onSave}
          style={styles.primaryButton}
          testID="editor-save-button"
          dataSet={{ testid: 'editor-save-button' }}
        >
          <Text style={styles.primaryButtonText}>Save note</Text>
        </Pressable>
      </View>

      <Pressable
        onPress={() => {
          const voicePlaceholder = `\n\n[Voice note]\n(whisper-tiny placeholder) Transcribed text will appear here once local STT is connected.`;
          const nextContent = `${draftNote.content || ''}${voicePlaceholder}`.trim();
          onChange('content', nextContent);
        }}
        style={styles.voiceButton}
        testID="editor-voice-note-button"
        dataSet={{ testid: 'editor-voice-note-button' }}
      >
        <Feather color="#FFFFFF" name="mic" size={16} />
        <Text style={styles.voiceButtonText}>Voice note</Text>
      </Pressable>

      <SectionCard theme={theme} testID="note-editor-card">
        <Text style={styles.eyebrow}>Block-based editor placeholder</Text>
        <TextInput
          onChangeText={(value) => onChange('title', value)}
          placeholder="Untitled note"
          placeholderTextColor={theme.colors.textMuted}
          style={styles.titleInput}
          testID="editor-title-input"
          dataSet={{ testid: 'editor-title-input' }}
          value={draftNote.title}
        />
        <View style={styles.blockTypeRow}>
          {blockTypes.map((blockType) => (
            <View
              key={blockType}
              style={styles.blockChip}
              testID={`editor-block-type-${blockType.toLowerCase()}`}
              dataSet={{ testid: `editor-block-type-${blockType.toLowerCase()}` }}
            >
              <Text style={styles.blockChipText}>{blockType}</Text>
            </View>
          ))}
        </View>
        <TextInput
          multiline
          onChangeText={(value) => onChange('content', value)}
          placeholder="Write freely. This phase keeps the editor simple, while preserving a path to richer block editing."
          placeholderTextColor={theme.colors.textMuted}
          style={styles.contentInput}
          testID="editor-content-input"
          dataSet={{ testid: 'editor-content-input' }}
          textAlignVertical="top"
          value={draftNote.content}
        />
        <Text style={styles.helperText} testID="editor-helper-text" dataSet={{ testid: 'editor-helper-text' }}>
          Slash commands, drag handles, and markdown import/export utilities land in upcoming phases.
        </Text>
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
  topBar: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  ghostButton: {
    alignItems: 'center',
    backgroundColor: theme.colors.surface,
    borderColor: theme.colors.border,
    borderRadius: theme.radius.control,
    borderWidth: 1,
    flexDirection: 'row',
    gap: 8,
    minHeight: 44,
    paddingHorizontal: theme.spacing.lg,
    paddingVertical: theme.spacing.sm,
  },
  ghostButtonText: {
    color: theme.colors.text,
    fontSize: 14,
    fontWeight: '600',
  },
  primaryButton: {
    alignItems: 'center',
    backgroundColor: theme.colors.primary,
    borderRadius: theme.radius.control,
    justifyContent: 'center',
    minHeight: 44,
    paddingHorizontal: theme.spacing.lg,
    paddingVertical: theme.spacing.sm,
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
  voiceButton: {
    alignItems: 'center',
    alignSelf: 'flex-start',
    backgroundColor: theme.colors.primary,
    borderRadius: theme.radius.control,
    flexDirection: 'row',
    gap: 8,
    minHeight: 42,
    paddingHorizontal: theme.spacing.lg,
    paddingVertical: theme.spacing.sm,
  },
  voiceButtonText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '700',
  },
  eyebrow: {
    color: theme.colors.primaryDeep,
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
  },
  titleInput: {
    borderBottomColor: theme.colors.border,
    borderBottomWidth: 1,
    color: theme.colors.text,
    fontSize: 28,
    fontWeight: '700',
    minHeight: 56,
    paddingBottom: theme.spacing.sm,
  },
  blockTypeRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: theme.spacing.sm,
  },
  blockChip: {
    backgroundColor: theme.colors.surfaceMuted,
    borderColor: theme.colors.border,
    borderRadius: theme.radius.pill,
    borderWidth: 1,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.sm,
  },
  blockChipText: {
    color: theme.colors.textSoft,
    fontSize: 12,
    fontWeight: '600',
  },
  contentInput: {
    backgroundColor: theme.colors.surfaceMuted,
    borderColor: theme.colors.border,
    borderRadius: theme.radius.control,
    borderWidth: 1,
    color: theme.colors.text,
    fontSize: 15,
    lineHeight: 24,
    minHeight: 280,
    padding: theme.spacing.lg,
  },
  helperText: {
    color: theme.colors.textMuted,
    fontSize: 13,
    lineHeight: 20,
  },
});
