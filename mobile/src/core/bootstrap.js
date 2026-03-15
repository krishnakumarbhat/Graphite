import { Platform } from 'react-native';
import { APP_NAME, ENABLE_DEV_SMOKE_TEST, MODEL_DIRECTORIES } from '../config/constants';
import { initializeDatabase } from '../db/db';
import { runDevSmokeTest } from '../utils/devSmokeTest';

export const bootstrapApp = async () => {
  const { migration, isSupported, warning } = await initializeDatabase();
  const smokeTest = isSupported && ENABLE_DEV_SMOKE_TEST ? await runDevSmokeTest() : null;

  return {
    appName: APP_NAME,
    platform: Platform.OS,
    status: isSupported ? 'ready' : 'scaffold-only-web',
    migration,
    smokeTest,
    modelDirectories: MODEL_DIRECTORIES,
    warning,
  };
};
