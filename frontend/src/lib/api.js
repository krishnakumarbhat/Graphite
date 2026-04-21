import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const client = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

export async function fetchHealth() {
  const { data } = await client.get('/health');
  return data;
}

export async function generateWorkflow(prompt) {
  const { data } = await client.post('/workflow/generate', { prompt });
  return data.graph;
}

export async function fetchAgentsStatus() {
  const { data } = await client.get('/agents/status');
  return data.agents;
}

export async function orchestrateAgent(agent, task) {
  const { data } = await client.post('/agents/orchestrate', { agent, task });
  return data;
}

export async function storeMemory(text, metadata = {}, namespace = 'default') {
  const { data } = await client.post('/memory/store', { text, metadata, namespace });
  return data;
}

export async function searchMemory(query, topK = 5, namespace = 'default') {
  const { data } = await client.post('/memory/search', { query, top_k: topK, namespace });
  return data.matches;
}

export default client;
