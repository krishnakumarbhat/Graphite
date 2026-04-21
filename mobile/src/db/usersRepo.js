import { LOCAL_DEFAULT_USER_EMAIL, LOCAL_DEFAULT_USER_ID } from '../config/constants';
import { getAll, getFirst, runQuery } from './db';
import { createIsoTimestamp } from '../utils/time';

export const ensureUserMirror = async ({ userId, email, displayName, provider = 'supabase' } = {}) => {
  const safeUserId = userId || LOCAL_DEFAULT_USER_ID;
  const now = createIsoTimestamp();

  await runQuery(
    `INSERT OR IGNORE INTO users (id, email, display_name, auth_provider, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, ?);`,
    [
      safeUserId,
      email || LOCAL_DEFAULT_USER_EMAIL,
      displayName || 'User',
      provider,
      now,
      now,
    ],
  );

  await runQuery(
    `UPDATE users SET email = ?, display_name = ?, auth_provider = ?, updated_at = ? WHERE id = ?;`,
    [
      email || LOCAL_DEFAULT_USER_EMAIL,
      displayName || 'User',
      provider,
      now,
      safeUserId,
    ],
  );

  return getUserById(safeUserId);
};

export const ensureLocalDefaultUser = async () => ensureUserMirror({
  userId: LOCAL_DEFAULT_USER_ID,
  email: LOCAL_DEFAULT_USER_EMAIL,
  displayName: 'Local User',
  provider: 'local',
});

export const getUserById = async (userId) => getFirst(
  'SELECT id, email, display_name, auth_provider, created_at, updated_at FROM users WHERE id = ? LIMIT 1;',
  [userId],
);

export const listUsers = async () => getAll(
  'SELECT id, email, display_name, auth_provider, created_at, updated_at FROM users ORDER BY updated_at DESC;'
);
