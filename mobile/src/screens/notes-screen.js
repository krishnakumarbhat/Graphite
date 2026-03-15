import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { SectionCard, SectionHeader } from '../components/section-card';

const formatRelativeDate = (timestamp) => new Date(timestamp).toLocaleDateString('en-US', {
  month: 'short',
  day: 'numeric',
});

export const NotesScreen = ({
  notes,
  onCreateNote,
  onOpenNote,
  searchQuery,
  setSearchQuery,
  theme,
  statusMessage,
}) => {
  const styles = createStyles(theme);
  const hasNotes = notes.length > 0;

  return (
    <ScrollView
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
      testID="notes-screen"
      dataSet={{ testid: 'notes-screen' }}
    >
      <SectionHeader
        eyebrow="Offline-first notes"
        title="Capture now, structure later"
        description="Notion-like capture with Obsidian-friendly portability."
        theme={theme}
        testID="notes-screen-header"
      />

      <SectionCard theme={theme} testID="notes-actions-card">
        <View style={styles.rowBetween}>
          <View style={styles.inlineBadge} testID="notes-preview-badge" dataSet={{ testid: 'notes-preview-badge' }}>
            <Text style={styles.inlineBadgeText}>{statusMessage}</Text>
          </View>
          <Pressable
            onPress={onCreateNote}
            style={styles.primaryButton}
            testID="notes-create-button"
            dataSet={{ testid: 'notes-create-button' }}
          >
            <Feather color="#FFFFFF" name="plus" size={16} />
            <Text style={styles.primaryButtonText}>New note</Text>
          </Pressable>
        </View>
        <View style={styles.searchWrap}>
          <Feather color={theme.colors.textMuted} name="search" size={16} />
          <TextInput
            onChangeText={setSearchQuery}
            placeholder="Search notes, workflows, or imported markdown"
            placeholderTextColor={theme.colors.textMuted}
            style={styles.searchInput}
            testID="notes-search-input"
            dataSet={{ testid: 'notes-search-input' }}
            value={searchQuery}
          />
        </View>
      </SectionCard>

      {hasNotes ? (
        <View style={styles.stack}>
          {notes.map((note) => (
            <Pressable
              key={note.id}
              onPress={() => onOpenNote(note)}
              style={styles.noteCard}
              testID={`notes-list-item-${note.id}`}
              dataSet={{ testid: `notes-list-item-${note.id}` }}
            >
              <View style={styles.rowBetween}>
                <Text style={styles.noteTitle}>{note.title}</Text>
                <Text style={styles.noteDate}>{formatRelativeDate(note.updated_at)}</Text>
              </View>
              <Text style={styles.noteBody} numberOfLines={3}>{note.content}</Text>
              <View style={styles.noteMetaRow}>
                <View style={styles.metaChip}>
                  <Text style={styles.metaChipText}>Markdown ready</Text>
                </View>
                <Text style={styles.noteSource}>{note.source_path ?? 'local note'}</Text>
              </View>
            </Pressable>
          ))}
        </View>
      ) : (
        <SectionCard theme={theme} testID="notes-empty-state">
          <Text style={styles.emptyTitle}>No notes yet</Text>
          <Text style={styles.emptyBody}>Start with a quick capture. Your block editor, markdown export, and sync flows will build on top of this list.</Text>
          <Pressable
            onPress={onCreateNote}
            style={styles.secondaryButton}
            testID="notes-empty-create-button"
            dataSet={{ testid: 'notes-empty-create-button' }}
          >
            <Text style={styles.secondaryButtonText}>Create your first note</Text>
          </Pressable>
        </SectionCard>
      )}
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
    gap: theme.spacing.sm,
    justifyContent: 'space-between',
  },
  inlineBadge: {
    alignSelf: 'flex-start',
    backgroundColor: theme.colors.primarySoft,
    borderRadius: theme.radius.pill,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.xs,
  },
  inlineBadgeText: {
    color: theme.colors.primaryDeep,
    fontSize: 12,
    fontWeight: '700',
  },
  primaryButton: {
    alignItems: 'center',
    backgroundColor: theme.colors.primary,
    borderRadius: theme.radius.control,
    flexDirection: 'row',
    gap: 8,
    minHeight: 44,
    paddingHorizontal: theme.spacing.lg,
    paddingVertical: theme.spacing.sm,
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
    minHeight: 44,
    justifyContent: 'center',
    paddingHorizontal: theme.spacing.lg,
    paddingVertical: theme.spacing.sm,
  },
  secondaryButtonText: {
    color: theme.colors.text,
    fontSize: 14,
    fontWeight: '700',
  },
  searchWrap: {
    alignItems: 'center',
    backgroundColor: theme.colors.surfaceMuted,
    borderColor: theme.colors.border,
    borderRadius: theme.radius.control,
    borderWidth: 1,
    flexDirection: 'row',
    gap: theme.spacing.sm,
    minHeight: 48,
    paddingHorizontal: theme.spacing.md,
  },
  searchInput: {
    color: theme.colors.text,
    flex: 1,
    fontSize: 15,
    minHeight: 44,
  },
  stack: {
    gap: theme.spacing.md,
  },
  noteCard: {
    backgroundColor: theme.colors.surface,
    borderColor: theme.colors.border,
    borderRadius: theme.radius.card,
    borderWidth: 1,
    gap: theme.spacing.sm,
    padding: theme.spacing.xl,
  },
  noteTitle: {
    color: theme.colors.text,
    flex: 1,
    fontSize: 18,
    fontWeight: '700',
    lineHeight: 24,
    paddingRight: theme.spacing.sm,
  },
  noteDate: {
    color: theme.colors.textMuted,
    fontSize: 12,
    fontWeight: '600',
  },
  noteBody: {
    color: theme.colors.textSoft,
    fontSize: 14,
    lineHeight: 22,
  },
  noteMetaRow: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: theme.spacing.sm,
    justifyContent: 'space-between',
  },
  metaChip: {
    backgroundColor: theme.colors.canvas,
    borderRadius: theme.radius.pill,
    paddingHorizontal: theme.spacing.sm,
    paddingVertical: 6,
  },
  metaChipText: {
    color: theme.colors.primaryDeep,
    fontSize: 11,
    fontWeight: '700',
  },
  noteSource: {
    color: theme.colors.textMuted,
    flex: 1,
    fontSize: 11,
    textAlign: 'right',
  },
  emptyTitle: {
    color: theme.colors.text,
    fontSize: 18,
    fontWeight: '700',
  },
  emptyBody: {
    color: theme.colors.textSoft,
    fontSize: 14,
    lineHeight: 22,
  },
});
