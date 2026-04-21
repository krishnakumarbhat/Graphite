export const APP_NAME = 'Second Brain Mobile';
export const DB_NAME = 'second-brain-v1.db';
export const DB_SCHEMA_VERSION = 2;
export const ENABLE_DEV_SMOKE_TEST = true;
export const DEFAULT_NOTE_TITLE = 'Untitled note';
export const DEFAULT_WORKFLOW_TITLE = 'Untitled workflow';
export const LOCAL_DEFAULT_USER_ID = 'local-user';
export const LOCAL_DEFAULT_USER_EMAIL = 'local@graphite.app';

export const SUPABASE_URL = process.env.EXPO_PUBLIC_SUPABASE_URL ?? '';
export const SUPABASE_ANON_KEY = process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY ?? '';
export const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://127.0.0.1:8001';

export const MODEL_DIRECTORIES = [
  'models/tts',
  'models/stt',
  'models/vision',
];
