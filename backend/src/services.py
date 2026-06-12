import hashlib
import json
import logging
import os
import shutil
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx
from pydantic import ValidationError

from src.agents import AGENT_DEFINITIONS
from src.altimate_pipeline import PipelineRun, build_lineage_graph, estimate_cost
from src.auto_tagger import tag_note
from src.cache_store import build_cache_store
from src.errors import ConfigurationError, UpstreamServiceError
from src.note_store import build_note_store
from src.research_pipeline import (
  build_chunks,
  cosine_similarity,
  cross_encoder_rerank,
  document_lexical_score,
  rank_chunks,
  render_chunks_for_prompt,
)
from src.schemas import AINoteDraftRequest, NoteSaveRequest, WorkflowGraph
from src.settings import Settings
from src.stt_engine import transcribe_audio_file
from src.tts_engine import (
  ensure_tts_output_dir,
  inspect_audio_file,
  synthesize_with_espeak,
  synthesize_with_kitten,
)

GUEST_NOTE_LIMIT = 5


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


def _format_pgvector_literal(values: list[float]) -> str:
  return '[' + ','.join(f'{float(value):.10f}' for value in values) + ']'


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


def _extract_project_description(key_files: dict[str, str]) -> str:
  for path, content in key_files.items():
    normalized_path = path.lower()
    if 'readme' not in normalized_path:
      continue
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    for line in lines:
      if line.startswith('#'):
        continue
      return line[:280]
  return ''


def _build_project_note_markdown(analysis: dict[str, Any]) -> str:
  lines = [
    f"# {analysis['project_name']} Project Analysis",
    '',
    '## Overview',
    f"- Path: {analysis['project_path']}",
    f"- Total files scanned: {analysis['total_files']}",
  ]

  description = analysis.get('description', '').strip()
  if description:
    lines.extend(['', '## Summary', description])

  lines.extend(['', '## File Tree', '```text', analysis['file_tree'], '```'])

  key_files = analysis.get('key_files', {})
  if key_files:
    lines.extend(['', '## Key Files'])
    for path, content in key_files.items():
      snippet = content[:1200].rstrip()
      lines.extend([
        '',
        f"### {path or '/'}",
        '```text',
        snippet,
        '```',
      ])

  return '\n'.join(lines).strip()


def _build_fallback_research_report(query: str, selected_chunks: list[dict[str, Any]]) -> str:
  lines = [
    f'# Research Brief: {query}',
    '',
    '## Executive Summary',
    'Gemini is unavailable, so this report uses the highest-ranked local chunks from the workspace and pasted source material.',
    '',
    '## Key Findings',
  ]

  for index, chunk in enumerate(selected_chunks, start=1):
    snippet = ' '.join(chunk['content'].split())[:360]
    lines.extend([
      '',
      f'### Finding {index}',
      f'- Source: {chunk["source_label"]}',
      f'- Relevance score: {chunk["score"]}',
      snippet,
    ])

  lines.extend(['', '## References'])
  for index, chunk in enumerate(selected_chunks, start=1):
    lines.append(f'- [S{index}] {chunk["source_label"]} ({chunk["source_path"] or "inline://source"})')

  return '\n'.join(lines).strip()


def _build_fallback_research_plan(query: str) -> dict[str, Any]:
  return {
    'overview': 'Local fixed-size chunking plan',
    'subquestions': [
      f'What are the most important mechanisms behind: {query}?',
      'Which implementation tradeoffs or bottlenecks appear in the supplied material?',
      'What operational recommendations follow from the supplied material?',
    ],
    'sections': [
      'Executive Summary',
      'Technical Breakdown',
      'Implementation Guidance',
      'Open Questions',
      'References',
    ],
  }


@dataclass(slots=True)
class ServiceRegistry:
  settings: Settings
  logger: logging.Logger
  http_client: httpx.Client = field(init=False)
  note_store: Any = field(init=False)
  cache_store: Any = field(init=False)
  supabase: Any = field(init=False, default=None)
  PGVECTOR_index: Any = field(init=False, default=None)

  def __post_init__(self) -> None:
    self.http_client = httpx.Client(timeout=90.0)
    self.supabase = self._init_supabase()
    self.note_store = build_note_store(
      self.settings.notes_database_path,
      supabase=self.supabase,
      logger=self.logger,
    )
    self.cache_store = build_cache_store(
      self.settings.redis_url,
      self.settings.cache_ttl_seconds,
    )

  def _init_supabase(self) -> Any:
    if (
      not self.settings.supabase_url
      or 'your-project' in self.settings.supabase_url
    ):
      return None

    service_role_key = self.settings.supabase_service_role_key.strip()
    public_key = self.settings.supabase_public_key.strip()
    key = service_role_key or public_key
    if not key:
      return None

    try:
      from supabase import create_client

      return create_client(self.settings.supabase_url, key)
    except Exception as error:
      self.logger.warning('Supabase initialization failed: %s', error)
      return None

  def close(self) -> None:
    self.cache_store.close()
    self.note_store.close()
    self.http_client.close()

  def require_supabase(self) -> Any:
    if not self.supabase:
      raise ConfigurationError(
        'Supabase is not configured. Set SUPABASE_URL and '
        'SUPABASE_PUBLIC_KEY or SUPABASE_SERVICE_ROLE_KEY in backend/.env.'
      )
    return self.supabase

  def health_payload(self) -> dict[str, Any]:
    vector_backend = 'pgvector' if self.supabase else 'sqlite-cosine'
    return {
      'status': 'ok',
      'cacheBackend': self.cache_store.backend_name,
      'redisConfigured': self.cache_store.is_remote,
      'ttsFallbackAvailable': bool(shutil.which('espeak')),
      'voiceInputModelPath': str(self.settings.voice_input_model_path),
      'kittenModelPath': str(self.settings.kitten_model_path),
      'supabaseConfigured': bool(self.supabase),
      'geminiConfigured': bool(self.settings.gemini_api_key),
      'braveConfigured': bool(self.settings.brave_api_key),
      'vectorBackend': vector_backend,
      'webSearchProvider': self.settings.web_search_provider,
      'notesDatabasePath': str(self.settings.notes_database_path),
      'notesBackend': 'supabase' if self.supabase else 'sqlite',
      'agents': list(AGENT_DEFINITIONS.keys()),
    }

  def _generate_with_optional_thinking(
    self,
    *,
    action: str,
    body: dict[str, Any],
    timeout: float,
    model_name: str | None = None,
  ) -> dict[str, Any]:
    thinking_level = self.settings.gemini_thinking_level.strip()
    if not thinking_level:
      return self._generate_with_model_fallback(
        action=action,
        body=body,
        timeout=timeout,
        model_name=model_name,
      )

    thinking_body = {
      **body,
      'generationConfig': {
        **body.get('generationConfig', {}),
        'thinkingConfig': {
          'thinkingLevel': thinking_level,
        },
      },
    }
    try:
      return self._generate_with_model_fallback(
        action=action,
        body=thinking_body,
        timeout=timeout,
        model_name=model_name,
      )
    except UpstreamServiceError as error:
      self.logger.warning('Gemini thinking config failed, retrying without it: %s', error)
      return self._generate_with_model_fallback(
        action=action,
        body=body,
        timeout=timeout,
        model_name=model_name,
      )

  def _generate_with_model_fallback(
    self,
    *,
    action: str,
    body: dict[str, Any],
    timeout: float,
    model_name: str | None = None,
  ) -> dict[str, Any]:
    primary_model = model_name or self.settings.gemini_model
    fallback_model = self.settings.gemini_fallback_model.strip()
    retry_count = max(1, self.settings.gemini_retry_count)
    plan = [(primary_model, retry_count)]
    if fallback_model and fallback_model != primary_model:
      plan.append((fallback_model, 1))

    last_error: UpstreamServiceError | None = None
    for current_model, attempts in plan:
      for attempt in range(1, attempts + 1):
        try:
          return self._post_gemini(
            action=action,
            body=body,
            timeout=timeout,
            model_name=current_model,
          )
        except UpstreamServiceError as error:
          last_error = error
          self.logger.warning(
            'Gemini request failed for %s on attempt %s/%s: %s',
            current_model,
            attempt,
            attempts,
            error,
          )

    raise last_error or UpstreamServiceError('Gemini request failed before a response was returned.')

  def _post_gemini(
    self,
    *,
    action: str,
    body: dict[str, Any],
    timeout: float,
    model_name: str | None = None,
  ) -> dict[str, Any]:
    if not self.settings.gemini_api_key:
      raise ConfigurationError(
        'GEMINI_API_KEY is missing. Add it to backend/.env '
        'before using this endpoint.'
      )

    endpoint = (
      f'https://generativelanguage.googleapis.com/v1beta/models/{model_name or self.settings.gemini_model}:{action}'
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
    cache_key = f'embedding:{self.settings.gemini_embedding_model}:{hashlib.sha256(text.encode()).hexdigest()}'
    cached_embedding = self.cache_store.get_json(cache_key)
    if isinstance(cached_embedding, dict):
      cached_values = cached_embedding.get('values', [])
      if isinstance(cached_values, list) and cached_values:
        return [float(value) for value in cached_values]

    if not self.settings.gemini_api_key:
      self.logger.info('GEMINI_API_KEY is not configured; using deterministic fallback embeddings.')
      values = _fallback_embedding(text)
      self.cache_store.set_json(cache_key, {'values': values}, ttl_seconds=max(self.settings.cache_ttl_seconds, 300))
      return values

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
        self.cache_store.set_json(cache_key, {'values': values}, ttl_seconds=max(self.settings.cache_ttl_seconds, 300))
        return values
    except httpx.HTTPError as error:
      self.logger.warning('Embedding request failed: %s', error)
    except json.JSONDecodeError as error:
      self.logger.warning('Embedding response was not JSON: %s', error)

    self.logger.info('Falling back to deterministic embeddings after Gemini embedding failure.')
    values = _fallback_embedding(text)
    self.cache_store.set_json(cache_key, {'values': values}, ttl_seconds=max(self.settings.cache_ttl_seconds, 300))
    return values

  def synthesize_speech(
    self,
    *,
    text: str,
    provider: str,
    voice: str,
    speed: float,
  ) -> dict[str, Any]:
    normalized_text = text.strip()
    if not normalized_text:
      raise ConfigurationError('TTS requires non-empty text input.')

    output_dir = ensure_tts_output_dir(self.settings.tts_output_dir)
    digest = hashlib.sha256(f'{provider}:{voice}:{speed}:{normalized_text}'.encode()).hexdigest()[:16]
    output_path = output_dir / f'{provider}-{digest}.wav'

    if not output_path.exists():
      if provider == 'kitten':
        synthesize_with_kitten(
          text=normalized_text,
          output_path=output_path,
          voice=voice,
          speed=speed,
          model_name=self.settings.kitten_model_repo,
          local_model_path=self.settings.kitten_model_path,
          cache_dir=self.settings.model_cache_dir,
          artifact_repo_id=self.settings.graphite_model_repo,
          token=self.settings.huggingface_token,
        )
      elif provider == 'espeak':
        synthesize_with_espeak(
          text=normalized_text,
          output_path=output_path,
          voice=voice,
          speed=speed,
        )
      else:
        raise ConfigurationError(f'Unsupported TTS provider: {provider}')

    metadata = inspect_audio_file(output_path)
    return {
      'status': 'success',
      'provider': provider,
      'voice': voice,
      'speed': speed,
      'file_name': output_path.name,
      'file_url': f'/api/tts/files/{output_path.name}',
      **metadata,
    }

  def compare_tts_providers(self, *, text: str, voice: str, speed: float) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    kitten_result: dict[str, Any] | None = None
    espeak_result: dict[str, Any] | None = None

    for provider in ('kitten', 'espeak'):
      try:
        result = self.synthesize_speech(
          text=text,
          provider=provider,
          voice=voice,
          speed=speed,
        )
        results.append(result)
        if provider == 'kitten':
          kitten_result = result
        else:
          espeak_result = result
      except Exception as error:
        results.append({'provider': provider, 'status': 'error', 'detail': str(error)})

    preferred_provider = 'kitten' if kitten_result else 'espeak'
    rationale = (
      'KittenTTS is preferred because it generates neural 24 kHz speech with stronger text normalization for numeric-heavy technical content.'
      if kitten_result
      else 'espeak is the active fallback because KittenTTS is unavailable in the current environment.'
    )

    return {
      'status': 'success',
      'preferred_provider': preferred_provider,
      'comparison_reason': rationale,
      'results': results,
      'fallback_provider': 'espeak' if espeak_result else None,
    }

  def transcribe_audio_upload(
    self,
    *,
    audio_file: Any,
    note_id: str | None = None,
  ) -> dict[str, Any]:
    filename = Path(getattr(audio_file, 'filename', '')).name or 'voice-input.webm'

    with tempfile.TemporaryDirectory(prefix='graphite-audio-upload-') as temp_dir:
      source_path = Path(temp_dir) / filename
      audio_file.save(source_path)
      transcript = transcribe_audio_file(
        source_path,
        model_path=self.settings.voice_input_model_path,
        artifact_repo_id=self.settings.graphite_model_repo,
        cache_dir=self.settings.model_cache_dir,
        token=self.settings.huggingface_token,
      )

    return {
      'status': 'success',
      'text': transcript,
      'note_id': note_id,
      'model': Path(self.settings.voice_input_model_path).name,
    }

  def run_deep_research(
    self,
    *,
    query: str,
    source_text: str,
    user_id: str,
    retrieval_mode: str,
    max_chunks: int,
    save_as_note: bool,
  ) -> dict[str, Any]:
    normalized_query = query.strip()
    normalized_source_text = source_text.strip()
    requested_retrieval = retrieval_mode.strip().lower() or 'fixed'
    supports_embedding_rerank = requested_retrieval in {'gemini', 'hybrid'} and bool(self.settings.gemini_api_key)
    effective_retrieval = requested_retrieval if requested_retrieval == 'fixed' or supports_embedding_rerank else 'fixed'
    pipeline_run = PipelineRun(query=normalized_query)

    documents: list[dict[str, str]] = []
    if normalized_source_text:
      documents.append(
        {
          'title': 'Pasted source context',
          'source_label': 'Pasted source context',
          'source_path': 'inline://pasted-source',
          'content': normalized_source_text,
        }
      )

    related_notes: list[dict[str, Any]] = []
    if self.supabase:
      try:
        related_payload = self.search_notes(
          normalized_query,
          user_id=user_id,
          top_k=max(max_chunks * 2, 6),
        )
        related_notes = related_payload.get('matches', [])
      except Exception as error:
        self.logger.warning('Supabase retrieval failed for deep research, falling back to local notes: %s', error)

    note_candidates = related_notes or self.list_notes(user_id)[:25]
    for note in note_candidates:
      if (note.get('source_path') or '').strip() == 'research://deep-dive':
        continue
      documents.append(
        {
          'title': note.get('title', 'Workspace note') or 'Workspace note',
          'source_label': note.get('title', 'Workspace note') or 'Workspace note',
          'source_path': note.get('source_path') or f"note://{note['id']}",
          'content': note.get('content', ''),
        }
      )

    documents = [document for document in documents if document['content'].strip()]
    if not documents:
      raise ConfigurationError('Deep research needs pasted source text or existing notes to analyze.')

    corpus_fingerprint = hashlib.sha256(
      '\n'.join(
        f"{document['source_label']}::{document['content'][:2000]}"
        for document in documents
      ).encode()
    ).hexdigest()
    cache_key = f'deep-research:{effective_retrieval}:{user_id}:{hashlib.sha256((normalized_query + corpus_fingerprint).encode()).hexdigest()}'
    cached_result = self.cache_store.get_json(cache_key)
    if isinstance(cached_result, dict):
      return {**cached_result, 'cached': True}

    embedding_ms = 0.0

    def timed_embedding_provider(text: str) -> list[float]:
      nonlocal embedding_ms
      started_at = time.perf_counter()
      values = self.generate_embedding(text)
      embedding_ms += (time.perf_counter() - started_at) * 1000
      return values

    retrieval_started_at = time.perf_counter()
    chunks = build_chunks(
      documents,
      chunk_size=self.settings.research_chunk_size,
      overlap=self.settings.research_chunk_overlap,
    )
    selected_chunks = rank_chunks(
      normalized_query,
      chunks,
      max_chunks=max_chunks,
      embedding_provider=timed_embedding_provider if supports_embedding_rerank else None,
    )
    retrieval_elapsed_ms = (time.perf_counter() - retrieval_started_at) * 1000
    if not selected_chunks:
      raise UpstreamServiceError('No research chunks were available for the requested query.')

    pipeline_run.chunks_retrieved = len(selected_chunks)
    pipeline_run.embedding_ms = round(embedding_ms, 1)
    pipeline_run.ranking_ms = round(max(retrieval_elapsed_ms - embedding_ms, 0.0), 1)

    prompt_sources = render_chunks_for_prompt(selected_chunks)
    llm_started_at = time.perf_counter()
    try:
      plan = self._build_research_plan(normalized_query, prompt_sources)
      report_markdown = self._write_research_report(normalized_query, plan, prompt_sources)
    except (ConfigurationError, UpstreamServiceError) as error:
      self.logger.warning('Deep research generation failed, falling back to local report: %s', error)
      plan = _build_fallback_research_plan(normalized_query)
      report_markdown = _build_fallback_research_report(normalized_query, selected_chunks)
    pipeline_run.llm_ms = round((time.perf_counter() - llm_started_at) * 1000, 1)
    pipeline_run.cost = estimate_cost(normalized_query, selected_chunks, report_markdown)
    pipeline_run.lineage = build_lineage_graph(
      note_id=f'query-{hashlib.md5(normalized_query.encode()).hexdigest()[:12]}',
      note_title=normalized_query,
      chunks=selected_chunks,
      ranked_results=selected_chunks,
    )
    pipeline_run.finish()

    result: dict[str, Any] = {
      'status': 'success',
      'query': normalized_query,
      'retrieval_mode': effective_retrieval,
      'cached': False,
      'plan': plan,
      'sources': [
        {
          'label': chunk['source_label'],
          'path': chunk['source_path'],
          'score': chunk['score'],
        }
        for chunk in selected_chunks
      ],
      'report_markdown': report_markdown,
      'pipeline': pipeline_run.to_dict(),
      'note': None,
      'note_warning': None,
    }

    if save_as_note:
      try:
        note = self.save_note(
          NoteSaveRequest(
            user_id=user_id,
            title=f'Research Brief: {normalized_query[:180]}',
            content=report_markdown,
            source_path='research://deep-dive',
            is_ai_generated=bool(self.settings.gemini_api_key),
          )
        )
        result['note'] = note
      except ConfigurationError as error:
        self.logger.warning('Deep research note persistence skipped: %s', error)
        result['note_warning'] = str(error)

    self.cache_store.set_json(cache_key, result, ttl_seconds=max(self.settings.cache_ttl_seconds, 300))
    return result

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
    embedding = self.generate_embedding(text)
    memory_id = f'mem-{hashlib.sha256(text.encode()).hexdigest()[:12]}-{int(time.time())}'
    self.require_supabase().table('memory_vectors').upsert(
      {
        'id': memory_id,
        'user_id': str(metadata.get('user_id') or 'web-local'),
        'namespace': namespace,
        'text': text[:1000],
        'embedding': _format_pgvector_literal(embedding),
        'metadata': metadata,
      },
      on_conflict='id',
    ).execute()
    return memory_id

  def search_memory(self, query: str, top_k: int, namespace: str) -> list[dict[str, Any]]:
    embedding = self.generate_embedding(query)

    results = self.require_supabase().rpc(
      'match_memory',
      {
        'query_embedding': _format_pgvector_literal(embedding),
        'match_threshold': 0.0,
        'match_count': top_k,
        'filter_namespace': namespace,
        'filter_user_id': 'web-local',
      },
    ).execute()
    return [
      {'id': row['memory_id'], 'score': row['similarity'], 'metadata': row['metadata']}
      for row in (results.data or [])
    ]

  def orchestrate_agent(self, agent: str, task: str, user_id: str = 'web-local') -> dict[str, Any]:
    # Use ReAct agent for all orchestration when ADK is available
    try:
      from src.react_agent import run_react_agent_sync
      self.logger.info('Running ReAct agent for %s: %s', agent, task[:100])
      result = run_react_agent_sync(self, task, user_id=user_id, agent_id=agent)
      return result
    except ImportError:
      self.logger.warning('google-adk not available, falling back to simple Gemini orchestration')
    except Exception as err:
      self.logger.warning('ReAct agent failed, falling back to simple Gemini: %s', err)

    # Fallback: simple Gemini-based orchestration
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
    payload = self._generate_with_optional_thinking(
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

  def list_notes_by_tag(self, user_id: str, tag: str, limit: int = 50) -> list[dict[str, Any]]:
    return self.note_store.list_notes_by_tag(user_id, tag, limit)

  def list_note_tag_counts(self, user_id: str) -> dict[str, int]:
    return self.note_store.list_tag_counts(user_id)

  def search_notes(
    self,
    query: str,
    *,
    user_id: str = 'web-local',
    top_k: int = 10,
    tag: str | None = None,
  ) -> dict[str, Any]:
    normalized_query = query.strip()
    if not normalized_query:
      raise ConfigurationError('Search query cannot be empty.', status_code=400)

    normalized_tag = (tag or '').strip().lower()
    limited_top_k = max(1, min(top_k, 20))
    cache_key = (
      'note-search:'
      f'{user_id}:{normalized_tag}:{limited_top_k}:'
      f'{hashlib.sha256(normalized_query.encode()).hexdigest()}'
    )
    cached_result = self.cache_store.get_json(cache_key)
    if isinstance(cached_result, dict):
      return {**cached_result, 'cached': True}

    backend = 'sqlite-cosine'
    candidates: list[dict[str, Any]] = []
    query_embedding = self.generate_embedding(normalized_query)

    if self.supabase:
      try:
        result = self.require_supabase().rpc(
          'match_notes',
          {
            'query_embedding': _format_pgvector_literal(query_embedding),
            'match_threshold': 0.0,
            'match_count': max(limited_top_k * 3, 15),
            'filter_user_id': user_id,
          },
        ).execute()
        backend = 'pgvector-hnsw'
        for row in (result.data or []):
          note = self.note_store.get_note(str(row['note_id']))
          enriched_note = note or {
            'id': row['note_id'],
            'title': row.get('title', ''),
            'excerpt': row.get('excerpt', ''),
            'content': row.get('excerpt', ''),
            'source_path': None,
            'updated_at': '',
            'tags': [],
          }
          if normalized_tag and normalized_tag not in enriched_note.get('tags', []):
            continue

          lexical_rank = document_lexical_score(
            normalized_query,
            str(enriched_note.get('title', '')),
            str(enriched_note.get('content', '')),
          )
          semantic_rank = float(row.get('similarity', 0.0))
          candidates.append(
            {
              'id': enriched_note['id'],
              'title': enriched_note.get('title', ''),
              'excerpt': enriched_note.get('excerpt', ''),
              'content': enriched_note.get('content', ''),
              'source_path': enriched_note.get('source_path'),
              'updated_at': enriched_note.get('updated_at', ''),
              'tags': enriched_note.get('tags', []),
              'score': round((semantic_rank * 0.72) + (lexical_rank * 0.28), 6),
              'semantic_score': round(semantic_rank, 6),
              'lexical_score': round(lexical_rank, 6),
            }
          )
      except Exception as error:
        backend = 'sqlite-cosine'
        self.logger.warning('Supabase pgvector note search failed, falling back to local ranking: %s', error)

    if not candidates:
      local_notes = self.note_store.get_rankable_notes(user_id, limit=500)
      for note in local_notes:
        if normalized_tag and normalized_tag not in note.get('tags', []):
          continue

        lexical_rank = document_lexical_score(
          normalized_query,
          str(note.get('title', '')),
          str(note.get('content', '')),
        )
        semantic_rank = cosine_similarity(query_embedding, note.get('embedding', []))
        candidates.append(
          {
            'id': note['id'],
            'title': note.get('title', ''),
            'excerpt': note.get('excerpt', ''),
            'content': note.get('content', ''),
            'source_path': note.get('source_path'),
            'updated_at': note.get('updated_at', ''),
            'tags': note.get('tags', []),
            'score': round((semantic_rank * 0.72) + (lexical_rank * 0.28), 6),
            'semantic_score': round(semantic_rank, 6),
            'lexical_score': round(lexical_rank, 6),
          }
        )

    reranked = cross_encoder_rerank(
      normalized_query,
      candidates,
      max_items=limited_top_k,
    )
    matches = [
      {
        'id': item['id'],
        'title': item['title'],
        'excerpt': item['excerpt'],
        'source_path': item.get('source_path'),
        'tags': item.get('tags', []),
        'score': item['score'],
        'semantic_score': item.get('semantic_score', 0.0),
        'lexical_score': item.get('lexical_score', 0.0),
        'cross_encoder_score': item.get('cross_encoder_score', 0.0),
      }
      for item in reranked
    ]
    payload = {
      'query': normalized_query,
      'tag_filter': normalized_tag or None,
      'count': len(matches),
      'matches': matches,
      'backend': backend,
      'cached': False,
    }
    self.cache_store.set_json(cache_key, payload, ttl_seconds=max(self.settings.cache_ttl_seconds, 120))
    return payload

  def count_notes(self, user_id: str) -> int:
    return len(self.note_store.list_notes(user_id))

  def get_note(self, note_id: str) -> dict[str, Any] | None:
    return self.note_store.get_note(note_id)

  def analyze_project_directory(self, project_path: str, project_name: str | None = None) -> dict[str, Any]:
    project_root = Path(project_path).expanduser().resolve()
    if not project_root.is_dir():
      raise ConfigurationError(f'Project directory not found: {project_root}')

    resolved_name = (project_name or project_root.name).strip() or project_root.name
    file_tree: list[str] = []
    key_files: dict[str, str] = {}
    important_names = {
      'readme',
      'readme.md',
      'package.json',
      'requirements.txt',
      'pyproject.toml',
      'setup.py',
      'cargo.toml',
      'go.mod',
      'makefile',
      'dockerfile',
      '.env.example',
    }
    ignored_dirs = {'.git', '.venv', 'node_modules', '__pycache__', 'build', 'dist'}
    total_files = 0

    for root, dirs, files in os.walk(project_root):
      dirs[:] = [current for current in dirs if current not in ignored_dirs and not current.startswith('.')]
      total_files += len(files)
      root_path = Path(root)
      level = len(root_path.relative_to(project_root).parts)
      if level > 3:
        continue

      indent = '  ' * level
      folder_name = root_path.name if level else resolved_name
      file_tree.append(f'{indent}{folder_name}/')
      for filename in sorted(files)[:30]:
        file_path = root_path / filename
        file_tree.append(f'{indent}  {filename}')
        if filename.lower() not in important_names:
          continue
        try:
          key_files[f'/{file_path.relative_to(project_root).as_posix()}'] = file_path.read_text(
            encoding='utf-8',
            errors='ignore',
          )[:3000]
        except OSError:
          continue

    description = _extract_project_description(key_files)
    return {
      'status': 'success',
      'project_name': resolved_name,
      'project_path': str(project_root),
      'file_tree': '\n'.join(file_tree[:200]),
      'key_files': key_files,
      'total_files': total_files,
      'description': description,
    }

  def analyze_project_to_note(
    self,
    *,
    project_path: str,
    project_name: str | None = None,
    user_id: str = 'web-local',
  ) -> dict[str, Any]:
    analysis = self.analyze_project_directory(project_path, project_name)
    timestamp = datetime.now(timezone.utc).isoformat()
    project_id = f"project-{hashlib.md5(analysis['project_path'].encode()).hexdigest()[:12]}"
    project_payload = {
      'id': project_id,
      'user_id': user_id,
      'name': analysis['project_name'],
      'description': analysis.get('description', ''),
      'repo_url': '',
      'created_at': timestamp,
      'updated_at': timestamp,
    }
    project_record = self.note_store.upsert_project(project_payload)
    note = self.save_note(
      NoteSaveRequest(
        user_id=user_id,
        title=f"{analysis['project_name']} Project Analysis",
        content=_build_project_note_markdown(analysis),
        source_path=analysis['project_path'],
        is_ai_generated=True,
      )
    )
    self.note_store.link_project_note(project_record['id'], note['id'])
    return {
      'project': project_record,
      'analysis': analysis,
      'note': note,
    }

  def save_note(self, note_request: NoteSaveRequest) -> dict[str, Any]:
    timestamp = datetime.now(timezone.utc).isoformat()
    existing_note = self.note_store.get_note(note_request.id) if note_request.id else None

    if not existing_note and note_request.user_id == 'web-local' and self.supabase:
      # Only enforce guest limit when Supabase auth is configured (production)
      guest_note_count = self.count_notes('web-local')
      if guest_note_count >= GUEST_NOTE_LIMIT:
        raise ConfigurationError(
          f'Guest mode is limited to {GUEST_NOTE_LIMIT} notes. Sign in for unlimited notes.',
          status_code=403,
        )

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
    tags = tag_note(note_payload['title'], note_payload['content'])
    saved_note = self.note_store.upsert_note(note_payload, embedding, tags=tags)
    if not getattr(self.note_store, 'is_remote', False):
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

  def run_research(self, ticker: str, algorithms: list[str]) -> dict[str, Any]:
    """Run financial analysis algorithms on a ticker using yfinance."""
    try:
      import yfinance as yf
    except ImportError as err:
      raise ConfigurationError('yfinance not installed. Run: pip install yfinance') from err

    symbol = ticker.strip().upper()
    stock = yf.Ticker(symbol)
    hist = stock.history(period='6mo')

    if hist.empty:
      raise UpstreamServiceError(f'No price data found for ticker: {symbol}')

    info: dict[str, Any] = {}
    try:
      info = stock.info or {}
    except Exception:
      pass

    closes = hist['Close']
    current_price = float(closes.iloc[-1])

    result: dict[str, Any] = {
      'ticker': symbol,
      'company_name': info.get('longName', symbol),
      'current_price': round(current_price, 2),
      'currency': info.get('currency', 'USD'),
      'sector': info.get('sector', 'Unknown'),
      'market_cap': info.get('marketCap'),
      'algorithms': {},
      'overall_signal': 'HOLD',
    }

    signals: list[str] = []

    if 'ma' in algorithms:
      ma20 = float(closes.rolling(20).mean().iloc[-1]) if len(closes) >= 20 else None
      ma50 = float(closes.rolling(50).mean().iloc[-1]) if len(closes) >= 50 else None
      ma200 = float(closes.rolling(200).mean().iloc[-1]) if len(closes) >= 200 else None
      signal = 'BUY' if (ma20 and current_price > ma20) else ('SELL' if (ma20 and current_price < ma20) else 'HOLD')
      result['algorithms']['ma'] = {
        'signal': signal,
        'current_price': round(current_price, 2),
        'ma20': round(ma20, 2) if ma20 else None,
        'ma50': round(ma50, 2) if ma50 else None,
        'ma200': round(ma200, 2) if ma200 else None,
        'price_data': [
          {'date': str(d.date()), 'close': round(float(v), 2),
           'ma20': round(float(closes.rolling(20).mean().loc[d]), 2) if len(closes) >= 20 else None}
          for d, v in closes.tail(60).items()
        ],
      }
      signals.append(signal)

    if 'rsi' in algorithms:
      delta = closes.diff()
      gain = delta.clip(lower=0).rolling(14).mean()
      loss = (-delta.clip(upper=0)).rolling(14).mean()
      rs = gain / loss.replace(0.0, float('nan'))
      rsi = (100 - (100 / (1 + rs))).dropna()
      rsi_val = round(float(rsi.iloc[-1]), 2)
      signal = 'BUY' if rsi_val < 30 else ('SELL' if rsi_val > 70 else 'HOLD')
      result['algorithms']['rsi'] = {
        'signal': signal,
        'value': rsi_val,
        'oversold_level': 30,
        'overbought_level': 70,
        'rsi_data': [{'date': str(d.date()), 'rsi': round(float(v), 2)} for d, v in rsi.tail(60).items()],
      }
      signals.append(signal)

    if 'macd' in algorithms:
      ema12 = closes.ewm(span=12, adjust=False).mean()
      ema26 = closes.ewm(span=26, adjust=False).mean()
      macd_line = ema12 - ema26
      sig_line = macd_line.ewm(span=9, adjust=False).mean()
      histogram = macd_line - sig_line
      cur_hist = float(histogram.iloc[-1])
      prev_hist = float(histogram.iloc[-2]) if len(histogram) > 1 else 0.0
      if cur_hist > 0 and prev_hist <= 0:
        signal = 'BUY'
      elif cur_hist < 0 and prev_hist >= 0:
        signal = 'SELL'
      elif float(macd_line.iloc[-1]) > float(sig_line.iloc[-1]):
        signal = 'BUY'
      else:
        signal = 'SELL'
      result['algorithms']['macd'] = {
        'signal': signal,
        'macd': round(float(macd_line.iloc[-1]), 4),
        'signal_line': round(float(sig_line.iloc[-1]), 4),
        'histogram': round(cur_hist, 4),
        'macd_data': [
          {'date': str(d.date()), 'macd': round(float(m), 4), 'signal': round(float(s), 4), 'histogram': round(float(h), 4)}
          for d, m, s, h in zip(macd_line.tail(60).index, macd_line.tail(60), sig_line.tail(60), histogram.tail(60))
        ],
      }
      signals.append(signal)

    if 'bollinger' in algorithms:
      ma20_s = closes.rolling(20).mean()
      std20 = closes.rolling(20).std()
      upper = ma20_s + (std20 * 2)
      lower = ma20_s - (std20 * 2)
      cur_upper = float(upper.iloc[-1])
      cur_lower = float(lower.iloc[-1])
      cur_ma = float(ma20_s.iloc[-1])
      band_width = cur_upper - cur_lower
      if band_width > 0:
        pos = (current_price - cur_lower) / band_width
        signal = 'BUY' if pos < 0.2 else ('SELL' if pos > 0.8 else 'HOLD')
      else:
        signal = 'HOLD'
      clean_band = [
        {'date': str(d.date()), 'price': round(float(p), 2), 'upper': round(float(u), 2),
         'middle': round(float(m), 2), 'lower': round(float(lo), 2)}
        for d, p, u, m, lo in zip(closes.tail(60).index, closes.tail(60), upper.tail(60), ma20_s.tail(60), lower.tail(60))
        if all(v == v for v in [float(u), float(m), float(lo)])
      ]
      result['algorithms']['bollinger'] = {
        'signal': signal,
        'current_price': round(current_price, 2),
        'upper_band': round(cur_upper, 2),
        'middle_band': round(cur_ma, 2),
        'lower_band': round(cur_lower, 2),
        'band_data': clean_band,
      }
      signals.append(signal)

    if signals:
      buy_count = signals.count('BUY')
      sell_count = signals.count('SELL')
      result['overall_signal'] = 'BUY' if buy_count > sell_count else ('SELL' if sell_count > buy_count else 'HOLD')

    return result

  def _build_research_plan(self, query: str, prompt_sources: str) -> dict[str, Any]:
    if not self.settings.gemini_api_key:
      return _build_fallback_research_plan(query)

    instruction = (
      'You are a research planner inspired by GPT Researcher. '
      'Return only JSON with keys overview (string), subquestions (array of strings), '
      'and sections (array of strings). Keep the plan grounded in the provided source excerpts.'
    )
    payload = self._generate_with_optional_thinking(
      action='generateContent',
      body={
        'contents': [
          {
            'parts': [
              {'text': instruction},
              {'text': f'Research question: {query}'},
              {'text': f'Available source excerpts:\n{prompt_sources}'},
            ]
          }
        ]
      },
      timeout=45.0,
    )
    raw_text = _parse_gemini_text(payload)
    if not raw_text:
      raise UpstreamServiceError('Gemini returned no research plan.')

    try:
      plan = _parse_json_block(raw_text)
    except json.JSONDecodeError as error:
      raise UpstreamServiceError('Gemini returned a non-JSON research plan.') from error

    return {
      'overview': str(plan.get('overview', '')).strip() or 'Gemini research plan',
      'subquestions': [str(item).strip() for item in plan.get('subquestions', []) if str(item).strip()],
      'sections': [str(item).strip() for item in plan.get('sections', []) if str(item).strip()],
    }

  def _write_research_report(self, query: str, plan: dict[str, Any], prompt_sources: str) -> str:
    if not self.settings.gemini_api_key:
      ranked_sources = []
      for block in prompt_sources.split('\n\n'):
        block = block.strip()
        if not block.startswith('[S'):
          continue
        lines = block.splitlines()
        if len(lines) < 4:
          continue
        ranked_sources.append(
          {
            'source_label': lines[0].split('] ', 1)[-1].strip(),
            'source_path': lines[2].split(': ', 1)[-1].strip(),
            'content': '\n'.join(lines[3:]).strip(),
            'score': 1.0,
          }
        )
      return _build_fallback_research_report(query, ranked_sources)

    section_list = ', '.join(plan.get('sections', []) or ['Executive Summary', 'Findings', 'References'])
    subquestions = '\n'.join(f'- {item}' for item in plan.get('subquestions', [])) or '- Answer the main question directly.'
    instruction = (
      'Write a detailed markdown research report using only the supplied source excerpts. '
      'Cite factual statements inline as [S1], [S2], etc. '
      'If the supplied evidence is incomplete, say so explicitly instead of inventing facts. '
      f'Use these sections where appropriate: {section_list}.'
    )
    payload = self._generate_with_optional_thinking(
      action='generateContent',
      body={
        'contents': [
          {
            'parts': [
              {'text': instruction},
              {'text': f'Research question: {query}'},
              {'text': f'Plan overview: {plan.get("overview", "")}'},
              {'text': f'Subquestions:\n{subquestions}'},
              {'text': f'Source excerpts:\n{prompt_sources}'},
            ]
          }
        ]
      },
      timeout=60.0,
    )
    report_markdown = _parse_gemini_text(payload)
    if not report_markdown:
      raise UpstreamServiceError('Gemini returned no research report.')
    return report_markdown

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
    if not self.supabase or getattr(self.note_store, 'is_remote', False):
      return

    try:
      self.require_supabase().table('notes').upsert(note_payload, on_conflict='id').execute()
    except Exception as error:
      self.logger.warning('Supabase note sync failed: %s', error)

    try:
      self.require_supabase().table('note_embeddings').upsert(
        {
          'note_id': note_payload['id'],
          'embedding': _format_pgvector_literal(embedding),
          'model': self.settings.gemini_embedding_model,
          'updated_at': note_payload['updated_at'],
        },
        on_conflict='note_id',
      ).execute()
    except Exception as error:
      self.logger.warning('Supabase pgvector note embedding sync failed: %s', error)