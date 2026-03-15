import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { SectionCard, SectionHeader } from '../components/section-card';

export const WorkflowScreen = ({ prompt, onChangePrompt, onGenerate, workflow, theme }) => {
  const styles = createStyles(theme);

  return (
    <ScrollView
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
      testID="workflow-screen"
      dataSet={{ testid: 'workflow-screen' }}
    >
      <SectionHeader
        eyebrow="Workflow agent"
        title="Shape agentic work as editable graph steps"
        description="Gemini and React Flow arrive next. This phase prepares the UI shell and prompt flow."
        theme={theme}
        testID="workflow-screen-header"
      />

      <SectionCard theme={theme} testID="workflow-prompt-card">
        <Text style={styles.label}>Prompt</Text>
        <TextInput
          multiline
          onChangeText={onChangePrompt}
          placeholder="Create a workflow to find VC funding"
          placeholderTextColor={theme.colors.textMuted}
          style={styles.promptInput}
          testID="workflow-prompt-input"
          dataSet={{ testid: 'workflow-prompt-input' }}
          textAlignVertical="top"
          value={prompt}
        />
        <Pressable
          onPress={onGenerate}
          style={styles.primaryButton}
          testID="workflow-generate-button"
          dataSet={{ testid: 'workflow-generate-button' }}
        >
          <Feather color="#FFFFFF" name="play" size={16} />
          <Text style={styles.primaryButtonText}>Generate preview graph</Text>
        </Pressable>
      </SectionCard>

      <SectionCard theme={theme} testID="workflow-canvas-placeholder">
        <Text style={styles.canvasLabel}>Graph canvas placeholder</Text>
        <Text style={styles.canvasBody}>
          React Flow will render inside a WebView in the next phase. For now, each step is shown as a draggable-ready node card.
        </Text>
        <View style={styles.nodeStack}>
          {workflow.nodes.map((node, index) => (
            <View
              key={node.id}
              style={[styles.nodeCard, index % 2 === 1 ? styles.nodeOffset : null]}
              testID={`workflow-node-${node.id}`}
              dataSet={{ testid: `workflow-node-${node.id}` }}
            >
              <Text style={styles.nodeTitle}>{node.label}</Text>
              <Text style={styles.nodeCaption}>{node.caption}</Text>
            </View>
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
  label: {
    color: theme.colors.text,
    fontSize: 14,
    fontWeight: '700',
  },
  promptInput: {
    backgroundColor: theme.colors.surfaceMuted,
    borderColor: theme.colors.border,
    borderRadius: theme.radius.control,
    borderWidth: 1,
    color: theme.colors.text,
    fontSize: 15,
    lineHeight: 24,
    minHeight: 140,
    padding: theme.spacing.lg,
  },
  primaryButton: {
    alignItems: 'center',
    backgroundColor: theme.colors.primary,
    borderRadius: theme.radius.control,
    flexDirection: 'row',
    gap: 8,
    justifyContent: 'center',
    minHeight: 48,
    paddingHorizontal: theme.spacing.lg,
    paddingVertical: theme.spacing.sm,
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
  canvasLabel: {
    color: theme.colors.text,
    fontSize: 16,
    fontWeight: '700',
  },
  canvasBody: {
    color: theme.colors.textSoft,
    fontSize: 14,
    lineHeight: 22,
  },
  nodeStack: {
    gap: theme.spacing.md,
    paddingTop: theme.spacing.sm,
  },
  nodeCard: {
    backgroundColor: theme.colors.surfaceMuted,
    borderColor: theme.colors.border,
    borderRadius: theme.radius.control,
    borderWidth: 1,
    gap: theme.spacing.xs,
    padding: theme.spacing.lg,
  },
  nodeOffset: {
    marginLeft: theme.spacing.xl,
  },
  nodeTitle: {
    color: theme.colors.text,
    fontSize: 15,
    fontWeight: '700',
  },
  nodeCaption: {
    color: theme.colors.textSoft,
    fontSize: 13,
    lineHeight: 20,
  },
});
