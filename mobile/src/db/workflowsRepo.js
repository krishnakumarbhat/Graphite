import { DEFAULT_WORKFLOW_TITLE } from '../config/constants';
import { getAll, getFirst, runQuery } from './db';
import { createUuid } from '../utils/id';
import { createIsoTimestamp } from '../utils/time';

export const createWorkflow = async ({ title = DEFAULT_WORKFLOW_TITLE, prompt = '', graphJson = null } = {}) => {
  const timestamp = createIsoTimestamp();
  const workflow = {
    id: createUuid(),
    title: title?.trim() || DEFAULT_WORKFLOW_TITLE,
    prompt,
    graph_json: graphJson,
    created_at: timestamp,
    updated_at: timestamp,
  };

  await runQuery(
    `INSERT INTO workflows (id, title, prompt, graph_json, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, ?);`,
    [
      workflow.id,
      workflow.title,
      workflow.prompt,
      workflow.graph_json,
      workflow.created_at,
      workflow.updated_at,
    ],
  );

  return workflow;
};

export const listWorkflows = async () => getAll(
  'SELECT id, title, prompt, graph_json, created_at, updated_at FROM workflows ORDER BY updated_at DESC;'
);

export const getWorkflowById = async (workflowId) => getFirst(
  'SELECT id, title, prompt, graph_json, created_at, updated_at FROM workflows WHERE id = ? LIMIT 1;',
  [workflowId],
);

export const updateWorkflow = async (workflowId, updates = {}) => {
  const existingWorkflow = await getWorkflowById(workflowId);

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
     WHERE id = ?;`,
    [
      nextWorkflow.title,
      nextWorkflow.prompt,
      nextWorkflow.graph_json,
      nextWorkflow.updated_at,
      workflowId,
    ],
  );

  return getWorkflowById(workflowId);
};

export const deleteWorkflow = async (workflowId) => {
  await runQuery('DELETE FROM workflows WHERE id = ?;', [workflowId]);
  return true;
};

export const countWorkflows = async () => {
  const result = await getFirst('SELECT COUNT(*) as count FROM workflows;');
  return Number(result?.count ?? 0);
};
