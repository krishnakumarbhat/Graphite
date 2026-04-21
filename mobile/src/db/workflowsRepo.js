import { DEFAULT_WORKFLOW_TITLE } from '../config/constants';
import { getAll, getFirst, runQuery } from './db';
import { createUuid } from '../utils/id';
import { createIsoTimestamp } from '../utils/time';

export const createWorkflow = async ({ userId, title = DEFAULT_WORKFLOW_TITLE, prompt = '', graphJson = null } = {}) => {
  if (!userId) {
    throw new Error('userId is required to create a workflow.');
  }

  const timestamp = createIsoTimestamp();
  const workflow = {
    id: createUuid(),
    user_id: userId,
    title: title?.trim() || DEFAULT_WORKFLOW_TITLE,
    prompt,
    graph_json: graphJson,
    created_at: timestamp,
    updated_at: timestamp,
  };

  await runQuery(
    `INSERT INTO workflows (id, user_id, title, prompt, graph_json, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, ?);`,
    [
      workflow.id,
      workflow.user_id,
      workflow.title,
      workflow.prompt,
      workflow.graph_json,
      workflow.created_at,
      workflow.updated_at,
    ],
  );

  return workflow;
};

export const listWorkflows = async (userId) => getAll(
  'SELECT id, user_id, title, prompt, graph_json, created_at, updated_at FROM workflows WHERE user_id = ? ORDER BY updated_at DESC;',
  [userId],
);

export const getWorkflowById = async (workflowId, userId) => getFirst(
  'SELECT id, user_id, title, prompt, graph_json, created_at, updated_at FROM workflows WHERE id = ? AND user_id = ? LIMIT 1;',
  [workflowId, userId],
);

export const updateWorkflow = async (workflowId, userId, updates = {}) => {
  const existingWorkflow = await getWorkflowById(workflowId, userId);

  if (!existingWorkflow) {
    return null;
  }

  const nextWorkflow = {
    ...existingWorkflow,
    title: updates.title?.trim() || existingWorkflow.title,
    prompt: updates.prompt ?? existingWorkflow.prompt,
    graph_json: updates.graphJson ?? existingWorkflow.graph_json,
    updated_at: createIsoTimestamp(),
  };

  await runQuery(
    `UPDATE workflows
     SET title = ?, prompt = ?, graph_json = ?, updated_at = ?
     WHERE id = ? AND user_id = ?;`,
    [
      nextWorkflow.title,
      nextWorkflow.prompt,
      nextWorkflow.graph_json,
      nextWorkflow.updated_at,
      workflowId,
      userId,
    ],
  );

  return getWorkflowById(workflowId, userId);
};

export const deleteWorkflow = async (workflowId, userId) => {
  await runQuery('DELETE FROM workflows WHERE id = ? AND user_id = ?;', [workflowId, userId]);
  return true;
};

export const countWorkflows = async (userId) => {
  const result = await getFirst('SELECT COUNT(*) as count FROM workflows WHERE user_id = ?;', [userId]);
  return Number(result?.count ?? 0);
};
