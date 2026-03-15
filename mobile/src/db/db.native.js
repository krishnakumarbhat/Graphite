import * as SQLite from 'expo-sqlite';
import { DB_NAME } from '../config/constants';
import { applyMigrations } from './migrations';

let databasePromise;

export const getDatabase = async () => {
  if (!databasePromise) {
    databasePromise = SQLite.openDatabaseAsync(DB_NAME, {
      enableChangeListener: true,
    });
  }

  return databasePromise;
};

export const initializeDatabase = async () => {
  try {
    const database = await getDatabase();
    const migration = await applyMigrations(database);

    return {
      database,
      migration,
      isSupported: true,
      warning: null,
    };
  } catch (error) {
    throw new Error(`Failed to initialize the local SQLite database. ${error?.message ?? error}`.trim());
  }
};

export const runQuery = async (source, params = []) => {
  const database = await getDatabase();
  return database.runAsync(source, params);
};

export const getFirst = async (source, params = []) => {
  const database = await getDatabase();
  return database.getFirstAsync(source, params);
};

export const getAll = async (source, params = []) => {
  const database = await getDatabase();
  return database.getAllAsync(source, params);
};
