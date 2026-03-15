import { Platform } from 'react-native';

// Platform-specific database adapter
if (Platform.OS === 'web') {
  // Use the web scaffold adapter for Expo web compilation
  export * from './db.web';
} else {
  // Use the native SQLite implementation for iOS/Android
  export * from './db.native';
}