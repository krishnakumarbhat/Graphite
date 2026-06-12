import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || `${window.location.origin}/api`;
const API_URL = new URL(API_BASE, window.location.origin);

const client = axios.create({
  baseURL: API_BASE,
  timeout: 90000,
  headers: { 'Content-Type': 'application/json' },
});

export async function fetchHealth() {
  const { data } = await client.get('/health');
  return data;
}

export async function fetchNotes(userId = 'web-local') {
  const { data } = await client.get('/notes', { params: { user_id: userId } });
  return data.items;
}

export async function searchNotes(query, userId = 'web-local', limit = 20, tag = '') {
  const { data } = await client.get('/notes/search', {
    params: {
      q: query,
      user_id: userId,
      limit,
      ...(tag ? { tag } : {}),
    },
  });
  return data;
}

export async function filterNotesByTag(tag, userId = 'web-local') {
  const { data } = await client.get(`/notes/by-tag/${encodeURIComponent(tag)}`, {
    params: { user_id: userId },
  });
  return data.items;
}

function parseSseFrame(frame) {
  const lines = frame.split('\n');
  let event = 'message';
  const dataLines = [];

  for (const line of lines) {
    if (!line || line.startsWith(':')) {
      continue;
    }
    if (line.startsWith('event:')) {
      event = line.slice(6).trim();
      continue;
    }
    if (line.startsWith('data:')) {
      dataLines.push(line.slice(5).trim());
    }
  }

  if (!dataLines.length) {
    return null;
  }

  const rawData = dataLines.join('\n');
  let data;
  try {
    data = JSON.parse(rawData);
  } catch {
    data = rawData;
  }

  return { event, data };
}

export async function streamDeepResearch(payload, { onEvent, signal } = {}) {
  const response = await fetch(resolveApiUrl('/research/stream'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal,
  });

  if (!response.ok) {
    let detail = `Request failed with ${response.status}`;
    try {
      const errorPayload = await response.json();
      detail = errorPayload?.detail || detail;
    } catch {
      const errorText = await response.text();
      detail = errorText || detail;
    }
    throw new Error(detail);
  }

  if (!response.body) {
    throw new Error('Streaming is not supported in this browser.');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let finalPayload = null;

  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });

    let boundaryIndex = buffer.indexOf('\n\n');
    while (boundaryIndex !== -1) {
      const frame = buffer.slice(0, boundaryIndex);
      buffer = buffer.slice(boundaryIndex + 2);
      boundaryIndex = buffer.indexOf('\n\n');

      const parsed = parseSseFrame(frame);
      if (!parsed) {
        continue;
      }

      onEvent?.(parsed);

      if (parsed.event === 'error') {
        throw new Error(parsed.data?.msg || 'Deep research stream failed.');
      }

      if (parsed.event === 'result') {
        finalPayload = parsed.data;
      }
    }

    if (done) {
      break;
    }
  }

  return finalPayload;
}

export async function saveNote(note) {
  const { data } = await client.post('/notes', note);
  return data.item;
}

export async function importMarkdownNote(filename, content, userId = 'web-local') {
  const { data } = await client.post('/notes/import', {
    filename,
    content,
    user_id: userId,
  });
  return data.item;
}

export async function generateAiNote(prompt, titleHint = '', userId = 'web-local') {
  const { data } = await client.post('/notes/ai-draft', {
    prompt,
    title_hint: titleHint,
    user_id: userId,
  });
  return data.item;
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

export async function countNotes(userId = 'web-local') {
  const { data } = await client.get('/notes/count', { params: { user_id: userId } });
  return data.count;
}

export async function analyzeStock(ticker, algorithms = ['ma', 'rsi', 'macd', 'bollinger']) {
  const { data } = await client.post('/research/analyze', { ticker, algorithms });
  return data;
}

export async function runDeepResearch(payload) {
  const { data } = await client.post('/research/deep-dive', payload);
  return data;
}

export async function compareTtsProviders(payload) {
  const { data } = await client.post('/tts/compare', payload);
  return data;
}

export async function synthesizeSpeech(payload) {
  const { data } = await client.post('/tts/speak', payload);
  return data;
}

export async function transcribeSpeech(audioBlob, noteId = '') {
  const formData = new FormData();
  const inferredExtension = audioBlob.type.includes('ogg') ? 'ogg' : 'webm';
  formData.append('audio', audioBlob, `voice-input.${inferredExtension}`);
  if (noteId) {
    formData.append('note_id', noteId);
  }

  const { data } = await client.post('/stt/transcribe', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export function resolveApiUrl(path) {
  return new URL(path, API_URL).toString();
}

export default client;
