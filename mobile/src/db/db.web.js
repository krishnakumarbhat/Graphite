export const getDatabase = async () => null;

export const initializeDatabase = async () => ({
  database: null,
  migration: null,
  isSupported: false,
  warning: 'Expo web support is enabled for scaffold verification. The real SQLite runtime is configured for native iOS/Android and will be exercised there.',
});

export const runQuery = async () => {
  throw new Error('SQLite queries are unavailable in the Expo web scaffold adapter.');
};

export const getFirst = async () => null;

export const getAll = async () => [];
