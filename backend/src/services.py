import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx
from pydantic import ValidationError

from src.agents import AGENT_DEFINITIONS
from src.errors import ConfigurationError, UpstreamServiceError
from src.note_store import LocalNoteStore
from src.schemas import AINoteDraftRequest, NoteSaveRequest, WorkflowGraph
from src.settings import Settings


def _fallback_embedding(text: str, dim: int = 768) -> list[float]:
  result: list[float] = []
  for index in range(dim):
    digest = hashlib.md5(f'{text}:{index}'.encode()).hexdigest()
    value = (int(digest[:8], 16) / 0xFFFFFFFF) * 2.0 - 1.0
    result.append(value)

  norm = sum(value * value for value in result) ** 0.5
  if norm > 0:
    result = [value / norm for value in result]
  return result


def _parse_gemini_text(payload: dict[str, Any]) -> str:
  candidates = payload.get('candidates', [])
  if not candidates:
    return ''

  first_candidate = candidates[0] or {}
  content = first_candidate.get('content', {})
  parts = content.get('parts', [])
  if not parts:
    return ''

  first_part = parts[0] or {}
  return str(first_part.get('text', '')).strip()


def _parse_json_block(text: str) -> dict[str, Any]:
  cleaned = text.strip()
  if cleaned.startswith('```'):
    cleaned = cleaned.replace('```json', '').replace('```', '').strip()
  return json.loads(cleaned)


@dataclass(slots=True)
class ServiceRegistry:
  settings: Settings
  logger: logging.Logger
  http_client: httpx.Client = field(init=False)
  note_store: LocalNoteStore = field(init=False)
  supabase: Any = field(init=False, default=None)
  pinecone_index: Any = field(init=False, default=None)
  pinecone_error: str | None = field(init=False, default=None)

  def __post_init__(self) -> None:
    self.http_client = httpx.Client(timeout=30.0)
    self.note_store = LocalNoteStore(self.settings.notes_database_path)
    self.supabase = self._init_supabase()
    self.pinecone_index = self._init_pinecone_index()

  def _init_supabase(self) -> Any:
    if (
      not self.settings.supabase_url
      or not self.settings.supabase_service_role_key
      or 'your-project' in self.settings.supabase_url
    ):
      return None

    try:
      from supabase import create_client

      return create_client(self.settings.supabase_url, self.settings.supabase_service_role_key)
    except Exception as error:
      self.logger.warning('Supabase initialization failed: %s', error)
      return None

  def _init_pinecone_index(self) -> Any:
    if not self.settings.pinecone_api_key:
      return None

    try:
      from pinecone import Pinecone, ServerlessSpec

      pinecone = Pinecone(api_key=self.settings.pinecone_api_key)
      existing_indexes = [getattr(index, 'name', str(index)) for index in pinecone.list_indexes()]
      if self.settings.pinecone_index not in existing_indexes:
        pinecone.create_index(
          name=self.settings.pinecone_index,
          dimension=768,
          metric='cosine',
          spec=ServerlessSpec(
            cloud=self.settings.pinecone_cloud,
            region=self.settings.pinecone_region,
          ),
        )
      return pinecone.Index(self.settings.pinecone_index)
    except Exception as error:
      self.pinecone_error = str(error)
      self.logger.warning('Pinecone initialization failed: %s', error)
      return None

  def close(self) -> None:
    self.note_store.close()
    self.http_client.close()

  def require_supabase(self) -> Any:
    if not self.supabase:
      raise ConfigurationError(
        'Supabase is not configured. Set SUPABASE_URL and '
        'SUPABASE_SERVICE_ROLE_KEY in backend/.env.'
      )
    return self.supabase

  def require_pinecone(self) -> Any:
    if not self.pinecone_index:
      detail = (
        'Pinecone not configured. '
        f'{self.pinecone_error or "Set PINECONE_API_KEY in backend/.env."}'
      )
      raise ConfigurationError(detail)
    return self.pinecone_index

  def health_payload(self) -> dict[str, Any]:
    return {
      'status': 'ok',
      'supabaseConfigured': bool(self.supabase),
      'geminiConfigured': bool(self.settings.gemini_api_key),
      'pineconeConfigured': bool(self.pinecone_index),
      'notesDatabasePath': str(self.settings.notes_database_path),
      'pineconeIndex': self.settings.pinecone_index if self.pinecone_index else None,
      'pineconeError': self.pinecone_error,
      'agents': list(AGENT_DEFINITIONS.keys()),
    }

  def _generate_with_optional_thinking(
    self,
    *,
    action: str,
    body: dict[str, Any],
    timeout: float,
  ) -> dict[str, Any]:
    thinking_level = self.settings.gemini_thinking_level.strip()
    if not thinking_level:
      return self._post_gemini(action=action, body=body, timeout=timeout)

    thinking_body = {
      **body,
      'generationConfig': {
        'thinkingConfig': {
          'thinkingLevel': thinking_level,
        }
      },
    }
    try:
      return self._post_gemini(action=action, body=thinking_body, timeout=timeout)
    except UpstreamServiceError as error:
      self.logger.warning('Gemini thinking config failed, retrying without it: %s', error)
      return self._post_gemini(action=action, body=body, timeout=timeout)

  def _post_gemini(self, *, action: str, body: dict[str, Any], timeout: float) -> dict[str, Any]:
    if not self.settings.gemini_api_key:
      raise ConfigurationError(
        'GEMINI_API_KEY is missing. Add it to backend/.env '
        'before using this endpoint.'
      )

    endpoint = (
      f'https://generativelanguage.googleapis.com/v1beta/models/{self.settings.gemini_model}:{action}'
    )

    try:
      response = self.http_client.post(
        endpoint,
        params={'key': self.settings.gemini_api_key},
        json=body,
        timeout=timeout,
      )
      response.raise_for_status()
      return response.json()
    except httpx.HTTPStatusError as error:
      raise UpstreamServiceError(f'Gemini HTTP error: {error.response.text}') from error
    except httpx.RequestError as error:
      raise UpstreamServiceError(f'Gemini connection error: {error}') from error
    except json.JSONDecodeError as error:
      raise UpstreamServiceError('Gemini returned a non-JSON response.') from error

  def generate_embedding(self, text: str) -> list[float]:
    if not self.settings.gemini_api_key:
      self.logger.info('GEMINI_API_KEY is not configured; using deterministic fallback embeddings.')
      return _fallback_embedding(text)

    body = {'content': {'parts': [{'text': text[:2048]}]}}
    endpoint = (
      f'https://generativelanguage.googleapis.com/v1beta/models/'
      f'{self.settings.gemini_embedding_model}:embedContent'
    )

    try:
      response = self.http_client.post(
        endpoint,
        params={'key': self.settings.gemini_api_key},
        json=body,
        timeout=15.0,
      )
      response.raise_for_status()
      payload = response.json()
      values = payload.get('embedding', {}).get('values', [])
      if values:
        return values
    except httpx.HTTPError as error:
      self.logger.warning('Embedding request failed: %s', error)
    except json.JSONDecodeError as error:
      self.logger.warning('Embedding response was not JSON: %s', error)

    self.logger.info('Falling back to deterministic embeddings after Gemini embedding failure.')
    return _fallback_embedding(text)

  def generate_workflow_graph(self, prompt: str) -> WorkflowGraph:
    instruction = (
      'Return only JSON with keys nodes and edges. '
      'nodes must be an array of objects with id, title, description. '
      'edges must be an array of objects with id, source, target. '
      'No markdown and no additional text.'
    )
    payload = self._post_gemini(
      action='generateContent',
      body={
        'contents': [
          {
            'parts': [
              {'text': instruction},
              {'text': f'User prompt: {prompt.strip()}'},
            ]
          }
        ]
      },
      timeout=30.0,
    )

    raw_text = _parse_gemini_text(payload)
    if not raw_text:
      raise UpstreamServiceError('Gemini response had no text output.')

    try:
      graph_payload = _parse_json_block(raw_text)
      return WorkflowGraph.model_validate(graph_payload)
    except json.JSONDecodeError as error:
      raise UpstreamServiceError('Gemini returned non-JSON output.') from error
    except ValidationError as error:
      raise UpstreamServiceError('Gemini returned an invalid workflow graph.') from error

  def upsert_record(self, table_name: str, payload: dict[str, Any]) -> int:
    result = self.require_supabase().table(table_name).upsert(payload, on_conflict='id').execute()
    return len(result.data or [])

  def list_records(self, table_name: str, user_id: str) -> list[dict[str, Any]]:
    result = (
      self.require_supabase()
      .table(table_name)
      .select('*')
      .eq('user_id', user_id)
      .order('updated_at', desc=True)
      .execute()
    )
    return result.data or []

  def store_memory(self, text: str, metadata: dict[str, Any], namespace: str) -> str:
    index = self.require_pinecone()
    embedding = self.generate_embedding(text)
    memory_id = f'mem-{hashlib.sha256(text.encode()).hexdigest()[:12]}-{int(time.time())}'
    payload = {**metadata, 'text': text[:1000], 'stored_at': int(time.time())}
    index.upsert(
      vectors=[{'id': memory_id, 'values': embedding, 'metadata': payload}],
      namespace=namespace,
    )
    return memory_id

  def search_memory(self, query: str, top_k: int, namespace: str) -> list[dict[str, Any]]:
    index = self.require_pinecone()
    embedding = self.generate_embedding(query)
    results = index.query(vector=embedding, top_k=top_k, include_metadata=True, namespace=namespace)
    return [
      {'id': match.id, 'score': match.score, 'metadata': match.metadata}
      for match in getattr(results, 'matches', [])
    ]

  def orchestrate_agent(self, agent: str, task: str) -> dict[str, Any]:
    if agent not in AGENT_DEFINITIONS:
      raise ConfigurationError(f'Unknown agent: {agent}. Valid: {list(AGENT_DEFINITIONS.keys())}')

    agent_definition = AGENT_DEFINITIONS[agent]
    instruction = (
      f'You are the {agent_definition["name"]} in a Manager-Worker AI system. '
      f'Your capabilities: {", ".join(agent_definition["capabilities"])}. '
      'Respond with ONLY a JSON object containing: '
      '"action_plan" (array of step strings), "summary" (string), '
      '"next_actions" (array of strings). '
      'No markdown wrapping.'
    )
    payload = self._post_gemini(
      action='generateContent',
      body={'contents': [{'parts': [{'text': instruction}, {'text': f'Task: {task}'}]}]},
      timeout=30.0,
    )
    raw_text = _parse_gemini_text(payload)
    if not raw_text:
      raise UpstreamServiceError('Gemini response had no text output.')

    try:
      result = _parse_json_block(raw_text)
    except json.JSONDecodeError:
      result = {'summary': raw_text, 'action_plan': [], 'next_actions': []}

    return {
      'agent': agent,
      'agent_name': agent_definition['name'],
      'result': result,
    }

  def list_notes(self, user_id: str) -> list[dict[str, Any]]:
    return self.note_store.list_notes(user_id)

  def get_note(self, note_id: str) -> dict[str, Any] | None:
    return self.note_store.get_note(note_id)

  def save_note(self, note_request: NoteSaveRequest) -> dict[str, Any]:
    timestamp = datetime.now(timezone.utc).isoformat()
    existing_note = self.note_store.get_note(note_request.id) if note_request.id else None
    note_id = note_request.id or f'note-{uuid4().hex[:12]}'
    normalized_title = note_request.title.strip() or self._infer_note_title(note_request.content)
    normalized_content = note_request.content.strip()
    note_payload = {
      'id': note_id,
      'user_id': note_request.user_id,
      'title': normalized_title,
      'content': normalized_content,
      'excerpt': self._build_excerpt(normalized_content),
      'source_path': note_request.source_path,
      'created_at': existing_note['created_at'] if existing_note else timestamp,
      'updated_at': timestamp,
      'is_ai_generated': note_request.is_ai_generated,
    }
    embedding = self.generate_embedding(
      f"{note_payload['title']}\n\n{note_payload['content']}"
    )
    saved_note = self.note_store.upsert_note(note_payload, embedding)
    self._mirror_note_to_supabase(saved_note, embedding)
    return saved_note

  def import_markdown_note(
    self,
    *,
    filename: str,
    content: str,
    user_id: str,
  ) -> dict[str, Any]:
    inferred_title = Path(filename).stem.replace('-', ' ').replace('_', ' ').strip()
    return self.save_note(
      NoteSaveRequest(
        user_id=user_id,
        title=inferred_title.title(),
        content=content,
        source_path=filename,
      )
    )

  def generate_ai_note(self, note_request: AINoteDraftRequest) -> dict[str, Any]:
    instruction = (
      'Draft a concise but actionable markdown note. '
      'Return markdown only. Use a clear title, short sections, and flat bullet lists.'
    )
    payload = self._generate_with_optional_thinking(
      action='generateContent',
      body={
        'contents': [
          {
            'parts': [
              {'text': instruction},
              {'text': f'User request: {note_request.prompt.strip()}'},
            ]
          }
        ]
      },
      timeout=45.0,
    )
    draft_markdown = _parse_gemini_text(payload)
    if not draft_markdown:
      raise UpstreamServiceError('Gemini response had no text output.')

    return self.save_note(
      NoteSaveRequest(
        user_id=note_request.user_id,
        title=note_request.title_hint.strip() or self._infer_note_title(draft_markdown),
        content=draft_markdown,
        source_path='ai://gemini',
        is_ai_generated=True,
      )
    )

  @staticmethod
  def _build_excerpt(content: str) -> str:
    normalized = ' '.join(content.split()).strip()
    if not normalized:
      return 'Fresh note draft'
    return normalized[:157] + '...' if len(normalized) > 160 else normalized

  @staticmethod
  def _infer_note_title(content: str) -> str:
    for line in content.splitlines():
      candidate = line.strip().lstrip('#').strip()
      if candidate:
        return candidate[:240]
    return 'Untitled note'

  def _mirror_note_to_supabase(self, note_payload: dict[str, Any], embedding: list[float]) -> None:
    if not self.supabase:
      return

    try:
      self.require_supabase().table('notes').upsert(note_payload, on_conflict='id').execute()
    except Exception as error:
      self.logger.warning('Supabase note sync failed: %s', error)

    try:
      self.require_supabase().table('note_embeddings').upsert(
        {
          'note_id': note_payload['id'],
          'user_id': note_payload['user_id'],
          'embedding_json': json.dumps(embedding),
          'updated_at': note_payload['updated_at'],
        },
        on_conflict='note_id',
      ).execute()
    except Exception as error:
      self.logger.warning('Supabase note embedding sync failed: %s', error)