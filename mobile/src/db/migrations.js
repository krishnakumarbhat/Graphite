import { DB_SCHEMA_VERSION } from '../config/constants';
import { migrationStatements } from './schema';

const getPragmaVersion = async (database) => {
  const result = await database.getFirstAsync('PRAGMA user_version;');
  return Number(result?.user_version ?? 0);
};

const configureDatabase = async (database) => {
  try {
    await database.execAsync('PRAGMA journal_mode = WAL;');
  } catch (error) {
    console.warn('[db] Unable to enable WAL mode:', error?.message ?? error);
  }

  await database.execAsync('PRAGMA foreign_keys = ON;');
};

export const applyMigrations = async (database) => {
  await configureDatabase(database);

  const startingVersion = await getPragmaVersion(database);

  if (startingVersion >= DB_SCHEMA_VERSION) {
    return {
      fromVersion: startingVersion,
      toVersion: startingVersion,
      appliedVersions: [],
    };
  }

  const appliedVersions = [];

  for (let nextVersion = startingVersion + 1; nextVersion <= DB_SCHEMA_VERSION; nextVersion += 1) {
    const statements = migrationStatements[nextVersion] ?? [];

    for (const statement of statements) {
      await database.execAsync(statement);
    }

    await database.execAsync(`PRAGMA user_version = ${nextVersion};`);
    appliedVersions.push(nextVersion);
  }

  return {
    fromVersion: startingVersion,
    toVersion: DB_SCHEMA_VERSION,
    appliedVersions,
  };
};
