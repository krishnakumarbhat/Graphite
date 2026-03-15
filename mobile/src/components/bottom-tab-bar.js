import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';

const tabs = [
  { key: 'notes', label: 'Notes', icon: 'file-text' },
  { key: 'workflow', label: 'Workflow', icon: 'git-branch' },
  { key: 'settings', label: 'Settings', icon: 'sliders' },
];

export const BottomTabBar = ({ activeTab, onChange, theme }) => {
  const styles = createStyles(theme);

  return (
    <View style={styles.container} testID="mobile-tab-bar" dataSet={{ testid: 'mobile-tab-bar' }}>
      {tabs.map((tab) => {
        const isActive = activeTab === tab.key;

        return (
          <Pressable
            key={tab.key}
            onPress={() => onChange(tab.key)}
            style={[styles.tabButton, isActive ? styles.tabButtonActive : null]}
            testID={`tab-${tab.key}`}
            dataSet={{ testid: `tab-${tab.key}` }}
          >
            <Feather color={isActive ? theme.colors.primaryDeep : theme.colors.textMuted} name={tab.icon} size={18} />
            <Text style={[styles.tabLabel, isActive ? styles.tabLabelActive : null]}>{tab.label}</Text>
          </Pressable>
        );
      })}
    </View>
  );
};

const createStyles = (theme) => StyleSheet.create({
  container: {
    backgroundColor: theme.colors.surface,
    borderColor: theme.colors.border,
    borderTopWidth: 1,
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingBottom: theme.spacing.xl,
    paddingHorizontal: theme.spacing.lg,
    paddingTop: theme.spacing.md,
  },
  tabButton: {
    alignItems: 'center',
    borderRadius: theme.radius.control,
    gap: 6,
    minHeight: 48,
    justifyContent: 'center',
    minWidth: 88,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.sm,
  },
  tabButtonActive: {
    backgroundColor: theme.colors.primarySoft,
  },
  tabLabel: {
    color: theme.colors.textMuted,
    fontSize: 12,
    fontWeight: '600',
  },
  tabLabelActive: {
    color: theme.colors.primaryDeep,
  },
});
