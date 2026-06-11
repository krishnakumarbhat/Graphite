import json
import time
from typing import TypeVar

from flask import Blueprint, Response, jsonify, request, send_from_directory, stream_with_context
from pydantic import BaseModel

from src.agents import AGENT_DEFINITIONS
from src.schemas import (
  AINoteDraftRequest,
  DeepResearchRequest,
  EvalRunRequest,
  MarkdownImportRequest,
  MemorySearchRequest,
  MemoryStoreRequest,
  NoteSaveRequest,
  NoteSyncPayload,
  OrchestrateRequest,
  ProjectAnalyzeRequest,
  ResearchRequest,
  TTSCompareRequest,
  TTSRequest,
  WorkflowGenerateRequest,
  WorkflowGenerateResponse,
  WorkflowSyncPayload,
)
from src.services import ServiceRegistry

ModelType = TypeVar('ModelType', bound=BaseModel)


def _validate_json(model_class: type[ModelType]) -> ModelType:
  payload = request.get_json(silent=True)
  if payload is None:
    payload = {}
  return model_class.model_validate(payload)


def build_api_blueprint(services: ServiceRegistry) -> Blueprint:
  api = Blueprint('api', __name__, url_prefix='/api')

  def count_remote_rows(table_name: str, column_name: str = 'id') -> int:
    result = (
      services.require_supabase()
      .table(table_name)
      .select(column_name, count='exact')
      .limit(1)
      .execute()
    )
    return int(getattr(result, 'count', 0) or 0)

  @api.route('/', defaults={'path': ''}, methods=['OPTIONS'])
  @api.route('/<path:path>', methods=['OPTIONS'])
  def options_handler(path: str) -> tuple[str, int]:
    return ('', 204)

  @api.get('/')
  def root() -> tuple[dict[str, str], int]:
    return ({'message': 'Graphite API is running'}, 200)

  @api.get('/health')
  def health():
    return jsonify(services.health_payload())

  @api.post('/workflow/generate')
  def generate_workflow():
    workflow_request = _validate_json(WorkflowGenerateRequest)
    response = WorkflowGenerateResponse(
      graph=services.generate_workflow_graph(workflow_request.prompt)
    )
    return jsonify(response.model_dump(mode='json'))

  @api.get('/notes')
  def list_notes():
    user_id = request.args.get('user_id', 'web-local').strip() or 'web-local'
    return jsonify({'items': services.list_notes(user_id)})

  @api.get('/notes/search')
  def search_notes():
    query = request.args.get('q', '').strip()
    user_id = request.args.get('user_id', 'web-local').strip() or 'web-local'
    top_k = int(request.args.get('limit', 10))
    tag = request.args.get('tag', '').strip() or None
    return jsonify(services.search_notes(query, user_id=user_id, top_k=top_k, tag=tag))

  @api.get('/notes/<string:note_id>')
  def get_note(note_id: str):
    note = services.get_note(note_id)
    if note is None:
      return jsonify({'detail': 'Note not found.'}), 404
    return jsonify({'item': note})

  @api.post('/notes')
  def save_note():
    note_request = _validate_json(NoteSaveRequest)
    return jsonify({'item': services.save_note(note_request)})

  @api.post('/notes/import')
  def import_markdown_note():
    note_request = _validate_json(MarkdownImportRequest)
    return jsonify(
      {
        'item': services.import_markdown_note(
          filename=note_request.filename,
          content=note_request.content,
          user_id=note_request.user_id,
        )
      }
    )

  @api.post('/notes/ai-draft')
  def generate_ai_note():
    note_request = _validate_json(AINoteDraftRequest)
    return jsonify({'item': services.generate_ai_note(note_request)})

  @api.post('/sync/notes')
  def sync_note():
    note = _validate_json(NoteSyncPayload)
    row_count = services.upsert_record('notes', note.model_dump(mode='json'))
    return jsonify({'status': 'ok', 'rows': row_count})

  @api.post('/sync/workflows')
  def sync_workflow():
    workflow = _validate_json(WorkflowSyncPayload)
    row_count = services.upsert_record('workflows', workflow.model_dump(mode='json'))
    return jsonify({'status': 'ok', 'rows': row_count})

  @api.get('/sync/notes/<string:user_id>')
  def list_user_notes(user_id: str):
    return jsonify({'items': services.list_records('notes', user_id)})

  @api.get('/sync/workflows/<string:user_id>')
  def list_user_workflows(user_id: str):
    return jsonify({'items': services.list_records('workflows', user_id)})

  @api.post('/memory/store')
  def store_memory():
    memory_request = _validate_json(MemoryStoreRequest)
    memory_id = services.store_memory(
      memory_request.text,
      memory_request.metadata,
      memory_request.namespace,
    )
    return jsonify({'status': 'ok', 'id': memory_id})

  @api.post('/memory/search')
  def search_memory():
    memory_request = _validate_json(MemorySearchRequest)
    return jsonify(
      {
        'matches': services.search_memory(
          memory_request.query,
          memory_request.top_k,
          memory_request.namespace,
        )
      }
    )

  @api.get('/agents/status')
  def agents_status():
    return jsonify({'agents': AGENT_DEFINITIONS})

  @api.post('/agents/orchestrate')
  def orchestrate_task():
    orchestrate_request = _validate_json(OrchestrateRequest)
    user_id = request.args.get('user_id', 'web-local').strip() or 'web-local'
    return jsonify(services.orchestrate_agent(
      orchestrate_request.agent, orchestrate_request.task, user_id=user_id
    ))

  @api.post('/agents/analyze-project')
  def analyze_project():
    analysis_request = _validate_json(ProjectAnalyzeRequest)
    result = services.analyze_project_to_note(
      project_path=analysis_request.project_path,
      project_name=analysis_request.project_name,
      user_id=analysis_request.user_id,
    )
    return jsonify(result)

  @api.post('/eval/run')
  def run_eval_suite():
    eval_request = _validate_json(EvalRunRequest)
    from src.eval_runner import run_saved_eval_set

    return jsonify(
      run_saved_eval_set(
        services,
        eval_set_path=eval_request.eval_set_path or None,
        config_path=eval_request.config_path or None,
      )
    )

  @api.get('/eval/results')
  def list_eval_results():
    agent_id = request.args.get('agent_id')
    limit = min(int(request.args.get('limit', 50)), 200)
    return jsonify({'results': services.note_store.list_eval_results(agent_id, limit)})

  @api.get('/notes/count')
  def count_notes():
    user_id = request.args.get('user_id', 'web-local').strip() or 'web-local'
    return jsonify({'count': services.count_notes(user_id)})

  @api.post('/research/analyze')
  def research_analyze():
    req = _validate_json(ResearchRequest)
    return jsonify(services.run_research(req.ticker, req.algorithms))

  @api.post('/research/deep-dive')
  def deep_research():
    req = _validate_json(DeepResearchRequest)
    return jsonify(
      services.run_deep_research(
        query=req.query,
        source_text=req.source_text,
        user_id=req.user_id,
        retrieval_mode=req.retrieval_mode,
        max_chunks=req.max_chunks,
        save_as_note=req.save_as_note,
      )
    )

  @api.post('/tts/speak')
  def tts_speak():
    req = _validate_json(TTSRequest)
    return jsonify(
      services.synthesize_speech(
        text=req.text,
        provider=req.provider,
        voice=req.voice,
        speed=req.speed,
      )
    )

  @api.post('/tts/compare')
  def tts_compare():
    req = _validate_json(TTSCompareRequest)
    return jsonify(
      services.compare_tts_providers(
        text=req.text,
        voice=req.voice,
        speed=req.speed,
      )
    )

  @api.post('/stt/transcribe')
  def stt_transcribe():
    audio_file = request.files.get('audio')
    if audio_file is None or not audio_file.filename:
      return jsonify({'detail': 'Attach an audio file in the "audio" form field.'}), 400

    note_id = request.form.get('note_id', '').strip() or None
    return jsonify(services.transcribe_audio_upload(audio_file=audio_file, note_id=note_id))

  @api.get('/tts/files/<path:filename>')
  def tts_file(filename: str):
    return send_from_directory(services.settings.tts_output_dir, filename)

  @api.get('/config')
  def public_config():
    supabase_url = services.settings.supabase_url
    return jsonify(
      {
        'supabaseUrl': supabase_url if 'your-project' not in supabase_url else '',
        'supabasePublicKey': services.settings.supabase_public_key,
        'paymentLinkUrl': services.settings.payment_link_url,
        'pricingHeadline': services.settings.pricing_headline,
      }
    )

  @api.get('/agents/runs')
  def list_agent_runs():
    agent_id = request.args.get('agent_id')
    limit = min(int(request.args.get('limit', 50)), 200)
    return jsonify({'runs': services.note_store.list_agent_runs(agent_id, limit)})

  @api.get('/agents/runs/<string:run_id>')
  def get_agent_run(run_id: str):
    run = services.note_store.get_agent_run(run_id)
    if not run:
      return jsonify({'detail': 'Run not found'}), 404
    actions = services.note_store.list_action_logs(run_id)
    return jsonify({'run': run, 'actions': actions})

  @api.get('/agents/runs/<string:run_id>/trajectory')
  def get_run_trajectory(run_id: str):
    actions = services.note_store.list_action_logs(run_id)
    trajectory = [a.get('tool_name') or a['action_type'] for a in actions]
    return jsonify({'run_id': run_id, 'trajectory': trajectory, 'steps': actions})

  # ── Auto-tagging ────────────────────────────────────────────────────────
  @api.post('/notes/tag')
  def tag_notes():
    """Auto-tag all notes for a user and return tag→count map."""
    user_id = request.args.get('user_id', 'web-local')
    notes = services.list_notes(user_id)
    tag_map = services.list_note_tag_counts(user_id)
    return jsonify({'tags': tag_map, 'tagged_count': len(notes), 'sample': notes[:5]})

  @api.get('/notes/by-tag/<string:tag>')
  def notes_by_tag(tag: str):
    user_id = request.args.get('user_id', 'web-local')
    matched = services.list_notes_by_tag(user_id, tag)
    return jsonify({'tag': tag, 'count': len(matched), 'items': matched[:50]})

  # ── Free Web Search ─────────────────────────────────────────────────────
  @api.get('/search/web')
  def web_search_endpoint():
    from src.web_search import search_web
    q = request.args.get('q', '').strip()
    if not q:
      return jsonify({'detail': 'Provide ?q=<query>'}), 400
    provider = request.args.get('provider', services.settings.web_search_provider)
    payload = search_web(
      q,
      max_results=int(request.args.get('n', services.settings.web_search_max_results)),
      api_key=services.settings.brave_api_key,
      provider=provider,
    )
    return jsonify({'query': q, **payload})

  @api.post('/research/deep-dive-web')
  def deep_research_with_web():
    """Deep research enriched with live web search results."""
    from src.web_search import format_results_for_prompt, search_web
    req = _validate_json(DeepResearchRequest)
    search_payload = search_web(
      req.query,
      max_results=min(4, services.settings.web_search_max_results),
      api_key=services.settings.brave_api_key,
      provider=services.settings.web_search_provider,
    )
    web_results = search_payload['results']
    web_text = format_results_for_prompt(web_results)
    combined_source = (req.source_text or '') + '\n\n--- Live Web Context ---\n' + web_text
    result = services.run_deep_research(
      query=req.query,
      source_text=combined_source,
      user_id=req.user_id,
      retrieval_mode=req.retrieval_mode,
      max_chunks=req.max_chunks,
      save_as_note=req.save_as_note,
    )
    result['web_sources'] = web_results
    result['web_provider'] = search_payload['provider']
    result['web_fallback_used'] = search_payload['fallback_used']
    return jsonify(result)

  # ── Streaming SSE Deep Research ─────────────────────────────────────────
  @api.route('/research/stream', methods=['GET', 'POST'])
  def deep_research_stream():
    """Server-Sent Events streaming endpoint for deep research.
    Usage: GET /api/research/stream?q=<query>&user_id=web-local
    """
    if request.method == 'POST':
      payload = request.get_json(silent=True) or {}
      query = str(payload.get('query', '')).strip()
      user_id = str(payload.get('user_id', 'web-local')).strip() or 'web-local'
      source_text = str(payload.get('source_text', ''))
      retrieval_mode = str(payload.get('retrieval_mode', 'fixed')).strip().lower() or 'fixed'
      max_chunks = int(payload.get('max_chunks', 6))
      save_as_note = bool(payload.get('save_as_note', False))
    else:
      query = request.args.get('q', '').strip()
      user_id = request.args.get('user_id', 'web-local').strip() or 'web-local'
      source_text = request.args.get('source_text', '')
      retrieval_mode = request.args.get('retrieval_mode', 'fixed').strip().lower() or 'fixed'
      max_chunks = int(request.args.get('max_chunks', 6))
      save_as_note = request.args.get('save_as_note', 'false').lower() == 'true'

    if not query:
      return jsonify({'detail': 'Provide ?q=<query>'}), 400

    normalized_mode = retrieval_mode if retrieval_mode in {'fixed', 'gemini', 'hybrid'} else 'fixed'
    limited_chunks = max(2, min(max_chunks, 12))

    def generate():
      def send(event: str, data: dict) -> str:
        return f'event: {event}\ndata: {json.dumps(data)}\n\n'

      yield send('status', {'step': 'start', 'msg': f'Searching notes for: {query}'})

      try:
        from src.web_search import format_results_for_prompt, search_web

        search_payload = search_web(
          query,
          max_results=min(4, services.settings.web_search_max_results),
          api_key=services.settings.brave_api_key,
          provider=services.settings.web_search_provider,
        )
        web_results = search_payload['results']
        yield send('web', {
          'provider': search_payload['provider'],
          'fallback_used': search_payload['fallback_used'],
          'count': len(web_results),
          'results': web_results,
        })
        yield send('status', {'step': 'web', 'msg': f'Got {len(web_results)} live web results'})

        combined_source = source_text.strip()
        web_text = format_results_for_prompt(web_results)
        if web_text and web_text != '(No live web results found.)':
          combined_source = ((combined_source + '\n\n') if combined_source else '') + '--- Live Web Context ---\n' + web_text

        yield send('status', {'step': 'llm', 'msg': 'Building research plan and report'})
        result = services.run_deep_research(
          query=query,
          source_text=combined_source,
          user_id=user_id,
          retrieval_mode=normalized_mode,
          max_chunks=limited_chunks,
          save_as_note=save_as_note,
        )

        if result.get('plan'):
          yield send('plan', result['plan'])

        report_blocks = [block.strip() for block in result.get('report_markdown', '').split('\n\n') if block.strip()]
        for index, block in enumerate(report_blocks, start=1):
          yield send('chunk', {'index': index, 'markdown': block + '\n\n'})

        yield send('metrics', result.get('pipeline', {}))
        yield send('sources', {
          'sources': result.get('sources', []),
          'web_sources': web_results,
        })
        yield send('status', {'step': 'done', 'msg': 'Research complete'})
        yield send('result', {
          'report': result.get('report_markdown', ''),
          'sources': result.get('sources', []),
          'web_sources': web_results,
          'web_provider': search_payload['provider'],
          'pipeline': result.get('pipeline', {}),
          'cached': result.get('cached', False),
          'note': result.get('note'),
          'retrieval_mode': result.get('retrieval_mode', normalized_mode),
        })
      except Exception as exc:
        yield send('error', {'msg': str(exc)})

    return Response(
      stream_with_context(generate()),
      mimetype='text/event-stream',
      headers={
        'Cache-Control': 'no-cache',
        'X-Accel-Buffering': 'no',
        'Access-Control-Allow-Origin': '*',
      },
    )

  # ── Altimate Pipeline Integration ────────────────────────────────────────
  @api.get('/altimate/schema')
  def altimate_schema_health():
    """Altimate-style schema validation tool for notes DB."""
    from src.altimate_pipeline import validate_schema
    if services.supabase:
      try:
        note_count = count_remote_rows('notes')
        embedding_count = count_remote_rows('note_embeddings', 'note_id')
        run_count = count_remote_rows('agent_runs')
        issues = []
        if embedding_count < note_count:
          issues.append(f'{note_count - embedding_count} notes missing embeddings (search gap)')
        return jsonify({
          'status': 'healthy' if not issues else 'warning',
          'issues': issues,
          'stats': {
            'notes_count': note_count,
            'note_embeddings_count': embedding_count,
            'agent_runs_count': run_count,
            'backend': 'supabase-pgvector',
          },
        })
      except Exception as exc:
        return jsonify({
          'status': 'warning',
          'issues': [f'Supabase inspection error: {exc}'],
          'stats': {'backend': 'supabase-pgvector'},
        })

    db_path = services.settings.notes_database_path
    return jsonify(validate_schema(db_path))

  @api.post('/altimate/lineage')
  def altimate_lineage():
    """Return data lineage graph for a research query (Altimate lineage tool)."""
    from src.altimate_pipeline import build_lineage_graph
    data = request.get_json(silent=True) or {}
    note_id = data.get('note_id', 'demo-note')
    note_title = data.get('title', 'Sample Note')
    chunks = data.get('chunks', [{'id': 'c1', 'content': 'sample', 'score': 0.8}])
    results = data.get('results', [])
    return jsonify(build_lineage_graph(note_id, note_title, chunks, results))

  @api.get('/altimate/finops')
  def altimate_finops():
    """FinOps cost estimate for last N queries."""
    from src.altimate_pipeline import estimate_cost
    query = request.args.get('q', 'NVDA stock analysis')
    report_len = int(request.args.get('report_len', 2000))
    chunks = [{'content': 'x' * 400} for _ in range(6)]
    report = 'r' * report_len
    return jsonify(estimate_cost(query, chunks, report))

  @api.get('/altimate/metrics')
  def altimate_metrics():
    """Pipeline health metrics dashboard data."""
    if services.supabase:
      try:
        total_notes = count_remote_rows('notes')
        total_emb = count_remote_rows('note_embeddings', 'note_id')
        runs = count_remote_rows('agent_runs')
      except Exception:
        total_notes = total_emb = runs = 0
    else:
      import sqlite3
      db_path = services.settings.notes_database_path
      try:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        total_notes = conn.execute('SELECT COUNT(*) FROM notes').fetchone()[0]
        total_emb = conn.execute('SELECT COUNT(*) FROM note_embeddings').fetchone()[0]
        runs = conn.execute('SELECT COUNT(*) FROM agent_runs').fetchone()[0]
        conn.close()
      except Exception:
        total_notes = total_emb = runs = 0

    return jsonify({
      'notes': total_notes,
      'embeddings': total_emb,
      'coverage_pct': round(total_emb / max(total_notes, 1) * 100, 1),
      'agent_runs': runs,
      'vector_backend': services.health_payload().get('vectorBackend', 'sqlite-cosine'),
      'gemini_configured': services.health_payload().get('geminiConfigured', False),
      'estimated_monthly_cost_usd': round(runs * 0.0008, 4),
    })

  return api