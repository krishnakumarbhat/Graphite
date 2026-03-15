import { View, Text, StyleSheet } from 'react-native';

export const SectionCard = ({ children, theme, testID }) => {
  const styles = createStyles(theme);

  return (
    <View style={styles.card} testID={testID} dataSet={{ testid: testID }}>
      {children}
    </View>
  );
};

const createStyles = (theme) => StyleSheet.create({
  card: {
    backgroundColor: theme.colors.surface,
    borderColor: theme.colors.border,
    borderRadius: theme.radius.card,
    borderWidth: 1,
    gap: theme.spacing.md,
    padding: theme.spacing.xl,
    shadowColor: '#111418',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.08,
    shadowRadius: 20,
    elevation: 3,
  },
});

export const SectionHeader = ({ eyebrow, title, description, theme, testID }) => {
  const styles = createHeaderStyles(theme);

  return (
    <View style={styles.container} testID={testID} dataSet={{ testid: testID }}>
      {eyebrow ? (
        <Text style={styles.eyebrow} testID={`${testID}-eyebrow`} dataSet={{ testid: `${testID}-eyebrow` }}>
          {eyebrow}
        </Text>
      ) : null}
      <Text style={styles.title} testID={`${testID}-title`} dataSet={{ testid: `${testID}-title` }}>
        {title}
      </Text>
      {description ? (
        <Text style={styles.description} testID={`${testID}-description`} dataSet={{ testid: `${testID}-description` }}>
          {description}
        </Text>
      ) : null}
    </View>
  );
};

const createHeaderStyles = (theme) => StyleSheet.create({
  container: {
    gap: theme.spacing.xs,
  },
  eyebrow: {
    color: theme.colors.primaryDeep,
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
  },
  title: {
    color: theme.colors.text,
    fontSize: 28,
    fontWeight: '700',
    lineHeight: 34,
  },
  description: {
    color: theme.colors.textSoft,
    fontSize: 15,
    lineHeight: 24,
  },
});
