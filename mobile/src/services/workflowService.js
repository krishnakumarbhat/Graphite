import { API_BASE_URL } from '../config/constants';

export const generateWorkflowFromApi = async (prompt) => {
  const response = await fetch(`${API_BASE_URL}/api/workflow/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ prompt }),
  });

  const payload = await response.json();

  if (!response.ok) {
    throw new Error(payload?.detail || 'Unable to generate workflow.');
  }

  const graph = payload?.graph ?? {};
  const nodes = Array.isArray(graph.nodes) ? graph.nodes : [];

  return {
    title: 'Workflow Agent Preview',
    prompt,
    nodes: nodes.map((node, index) => ({
      id: node.id || `node-${index + 1}`,
      label: node.title || `Step ${index + 1}`,
      caption: node.description || 'No description',
    })),
    edges: Array.isArray(graph.edges) ? graph.edges : [],
  };
};
