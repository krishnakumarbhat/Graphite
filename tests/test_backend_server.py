from io import BytesIO
from pathlib import Path

from src.app_factory import create_app
from src.services import ServiceRegistry
from src.settings import FRONTEND_BUILD_DIR, Settings


def build_app(database_path: Path | None = None) -> object:
  settings = Settings(
    SUPABASE_URL='',
    SUPABASE_SERVICE_ROLE_KEY='',
    GEMINI_API_KEY='',
    CORS_ORIGINS='http://localhost:3000,http://127.0.0.1:8081',
    NOTES_DATABASE_PATH=str(database_path or (FRONTEND_BUILD_DIR.parent / 'test.sqlite3')),
    frontend_build_dir=FRONTEND_BUILD_DIR,
  )
  return create_app(settings)


def test_health_endpoint_reports_service_configuration() -> None:
  app = build_app()
  client = app.test_client()

  response = client.get('/api/health')

  assert response.status_code == 200
  payload = response.get_json()
  assert payload['status'] == 'ok'
  assert payload['cacheBackend'] == 'memory'
  assert payload['redisConfigured'] is False
  assert payload['supabaseConfigured'] is False
  assert 'finance' in payload['agents']


def test_workflow_generation_requires_gemini_key() -> None:
  app = build_app()
  client = app.test_client()

  response = client.post('/api/workflow/generate', json={'prompt': 'draft a workflow'})

  assert response.status_code == 400
  assert 'GEMINI_API_KEY' in response.get_json()['detail']


def test_workflow_generation_validates_payload() -> None:
  app = build_app()
  client = app.test_client()

  response = client.post('/api/workflow/generate', json={})

  assert response.status_code == 422
  payload = response.get_json()
  assert payload['detail'] == 'Invalid request payload.'


def test_agents_status_returns_registry() -> None:
  app = build_app()
  client = app.test_client()

  response = client.get('/api/agents/status')

  assert response.status_code == 200
  payload = response.get_json()
  assert payload['agents']['vc']['status'] == 'active'


def test_local_notes_round_trip_without_supabase(tmp_path: Path) -> None:
  app = build_app(tmp_path / 'graphite.sqlite3')
  client = app.test_client()

  create_response = client.post(
    '/api/notes',
    json={'user_id': 'web-local', 'title': 'Launch plan', 'content': 'Ship the /notes page.'},
  )

  assert create_response.status_code == 200
  created_note = create_response.get_json()['item']
  assert created_note['title'] == 'Launch plan'

  list_response = client.get('/api/notes?user_id=web-local')

  assert list_response.status_code == 200
  listed_notes = list_response.get_json()['items']
  assert len(listed_notes) == 1
  assert listed_notes[0]['id'] == created_note['id']
  assert 'general' in listed_notes[0]['tags']


def test_note_search_endpoint_returns_ranked_matches(tmp_path: Path) -> None:
  app = build_app(tmp_path / 'graphite.sqlite3')
  client = app.test_client()

  client.post(
    '/api/notes',
    json={
      'user_id': 'web-local',
      'title': 'Architecture decisions',
      'content': 'The architecture decisions cover data pipeline design, retrieval, and indexing.',
    },
  )
  client.post(
    '/api/notes',
    json={
      'user_id': 'web-local',
      'title': 'Groceries',
      'content': 'Buy milk, eggs, and bread on the way home.',
    },
  )

  response = client.get('/api/notes/search?q=architecture%20decisions&user_id=web-local')

  assert response.status_code == 200
  payload = response.get_json()
  assert payload['backend'] == 'sqlite-cosine'
  assert payload['count'] >= 1
  assert payload['matches'][0]['title'] == 'Architecture decisions'
  assert payload['matches'][0]['cross_encoder_score'] > 0
  assert payload['matches'][0]['semantic_score'] >= 0


def test_note_tags_are_persisted_and_filterable(tmp_path: Path) -> None:
  app = build_app(tmp_path / 'graphite.sqlite3')
  client = app.test_client()

  response = client.post(
    '/api/notes',
    json={
      'user_id': 'web-local',
      'title': 'NVDA buy setup',
      'content': 'Track NVDA earnings, options flow, and price target zones before buying shares.',
    },
  )

  assert response.status_code == 200
  created_note = response.get_json()['item']
  assert 'stocks' in created_note['tags']

  tag_response = client.post('/api/notes/tag?user_id=web-local')
  assert tag_response.status_code == 200
  assert tag_response.get_json()['tags']['stocks'] == 1

  filter_response = client.get('/api/notes/by-tag/stocks?user_id=web-local')
  assert filter_response.status_code == 200
  payload = filter_response.get_json()
  assert payload['count'] == 1
  assert payload['items'][0]['id'] == created_note['id']


def test_note_search_endpoint_supports_tag_filter(tmp_path: Path) -> None:
  app = build_app(tmp_path / 'graphite.sqlite3')
  client = app.test_client()

  client.post(
    '/api/notes',
    json={
      'user_id': 'web-local',
      'title': 'NVDA watchlist',
      'content': 'Review NVDA earnings, options flow, and price target updates before buying shares.',
    },
  )
  client.post(
    '/api/notes',
    json={
      'user_id': 'web-local',
      'title': 'Career planning',
      'content': 'Prepare interview stories and update the resume for senior data roles.',
    },
  )

  response = client.get('/api/notes/search?q=buy&user_id=web-local&tag=stocks')

  assert response.status_code == 200
  payload = response.get_json()
  assert payload['count'] == 1
  assert payload['matches'][0]['title'] == 'NVDA watchlist'
  assert 'stocks' in payload['matches'][0]['tags']


def test_web_search_endpoint_reports_provider(monkeypatch, tmp_path: Path) -> None:
  app = build_app(tmp_path / 'graphite.sqlite3')
  client = app.test_client()

  monkeypatch.setattr(
    'src.web_search.search_web',
    lambda *args, **kwargs: {
      'provider': 'brave',
      'fallback_used': False,
      'results': [{'title': 'Brave result', 'url': 'https://example.com', 'snippet': 'Live data'}],
    },
  )

  response = client.get('/api/search/web?q=graphite')

  assert response.status_code == 200
  payload = response.get_json()
  assert payload['provider'] == 'brave'
  assert payload['results'][0]['title'] == 'Brave result'


def test_research_stream_endpoint_emits_web_plan_metrics_and_result(monkeypatch, tmp_path: Path) -> None:
  app = build_app(tmp_path / 'graphite.sqlite3')
  client = app.test_client()

  monkeypatch.setattr(
    'src.web_search.search_web',
    lambda *args, **kwargs: {
      'provider': 'duckduckgo',
      'fallback_used': True,
      'results': [{'title': 'Fallback result', 'url': 'https://example.com', 'snippet': 'Fallback snippet'}],
    },
  )

  def fake_run_deep_research(self, **kwargs):
    del kwargs
    return {
      'report_markdown': '# Report\n\nSection one.\n\nSection two.',
      'sources': [{'label': 'Workspace note', 'path': 'note://1', 'score': 0.9}],
      'plan': {'overview': 'Plan overview', 'subquestions': ['One'], 'sections': ['Summary']},
      'pipeline': {'query': 'Graphite', 'latency_ms': {'total': 123.4}},
      'cached': False,
      'note': None,
      'retrieval_mode': 'hybrid',
    }

  monkeypatch.setattr(ServiceRegistry, 'run_deep_research', fake_run_deep_research)

  response = client.post(
    '/api/research/stream',
    json={'query': 'Graphite', 'source_text': 'Seed context', 'retrieval_mode': 'hybrid'},
  )

  assert response.status_code == 200
  assert response.mimetype == 'text/event-stream'
  body = response.get_data(as_text=True)
  assert 'event: web' in body
  assert 'event: plan' in body
  assert 'event: metrics' in body
  assert 'event: result' in body


def test_presentation_route_serves_demo_page() -> None:
  app = build_app()
  client = app.test_client()

  response = client.get('/presentation')

  assert response.status_code == 200
  body = response.get_data(as_text=True)
  assert 'Graphite Demo Presentation' in body
  assert 'Altimate optimization lane' in body


def test_markdown_import_creates_a_note(tmp_path: Path) -> None:
  app = build_app(tmp_path / 'graphite.sqlite3')
  client = app.test_client()

  response = client.post(
    '/api/notes/import',
    json={
      'user_id': 'web-local',
      'filename': 'board-update.md',
      'content': '# Board Update\n\nRevenue is up 12% month over month.',
    },
  )

  assert response.status_code == 200
  note = response.get_json()['item']
  assert note['title'] == 'Board Update'
  assert note['source_path'] == 'board-update.md'


def test_project_analysis_creates_project_note(tmp_path: Path) -> None:
  project_dir = tmp_path / 'sample-project'
  source_dir = project_dir / 'src'
  source_dir.mkdir(parents=True)
  (project_dir / 'README.md').write_text(
    '# Sample Project\n\nA lightweight test fixture for project analysis.',
    encoding='utf-8',
  )
  (project_dir / 'package.json').write_text(
    '{"name": "sample-project", "version": "1.0.0"}',
    encoding='utf-8',
  )
  (source_dir / 'main.js').write_text('export const ready = true;\n', encoding='utf-8')

  app = build_app(tmp_path / 'graphite.sqlite3')
  client = app.test_client()

  response = client.post(
    '/api/agents/analyze-project',
    json={
      'project_path': str(project_dir),
      'project_name': 'Sample Project',
      'user_id': 'project-user',
    },
  )

  assert response.status_code == 200
  payload = response.get_json()
  assert payload['project']['name'] == 'Sample Project'
  assert payload['analysis']['project_name'] == 'Sample Project'
  assert '/README.md' in payload['analysis']['key_files']
  assert payload['note']['title'] == 'Sample Project Project Analysis'

  notes_response = client.get('/api/notes?user_id=project-user')
  assert notes_response.status_code == 200
  assert len(notes_response.get_json()['items']) == 1


def test_deep_research_endpoint_creates_cached_report_note(tmp_path: Path) -> None:
  app = build_app(tmp_path / 'graphite.sqlite3')
  client = app.test_client()
  request_payload = {
    'query': 'Explain the algorithmic speech and audio AI pipeline',
    'user_id': 'research-user',
    'retrieval_mode': 'fixed',
    'source_text': (
      'Phase 1 handles audio ingestion, analog-to-digital conversion, pre-emphasis, framing, '
      'and STFT or MFCC feature extraction. Phase 2 focuses on speech-to-text using CTC, '
      'Transformers, Conformers, and RNN-T. Phase 3 covers text-to-speech with FastSpeech, '
      'VITS, and HiFi-GAN. Phase 4 orchestrates VAD, STT, reasoning, and TTS into a '
      'full conversational loop.'
    ),
  }

  first_response = client.post('/api/research/deep-dive', json=request_payload)

  assert first_response.status_code == 200
  first_payload = first_response.get_json()
  assert first_payload['status'] == 'success'
  assert first_payload['retrieval_mode'] == 'fixed'
  assert first_payload['cached'] is False
  assert first_payload['note']['title'].startswith('Research Brief:')
  assert first_payload['report_markdown'].startswith('# Research Brief:')
  assert len(first_payload['sources']) >= 1

  second_response = client.post('/api/research/deep-dive', json=request_payload)

  assert second_response.status_code == 200
  second_payload = second_response.get_json()
  assert second_payload['cached'] is True
  assert second_payload['note']['id'] == first_payload['note']['id']

  notes_response = client.get('/api/notes?user_id=research-user')
  assert notes_response.status_code == 200
  assert len(notes_response.get_json()['items']) == 1


def test_deep_research_still_returns_report_when_guest_note_limit_is_hit(tmp_path: Path) -> None:
  app = build_app(tmp_path / 'graphite.sqlite3')
  client = app.test_client()
  app.extensions['graphite_services'].supabase = object()

  for index in range(5):
    save_response = client.post(
      '/api/notes',
      json={
        'user_id': 'web-local',
        'title': f'Guest note {index}',
        'content': 'Seed note content.',
      },
    )
    assert save_response.status_code == 200

  response = client.post(
    '/api/research/deep-dive',
    json={
      'query': 'Summarize the voice assistant pipeline',
      'source_text': 'A voice assistant chains ingestion, STT, reasoning, and TTS.',
      'user_id': 'web-local',
      'retrieval_mode': 'fixed',
      'save_as_note': True,
    },
  )

  assert response.status_code == 200
  payload = response.get_json()
  assert payload['status'] == 'success'
  assert payload['note'] is None
  assert 'Guest mode is limited' in payload['note_warning']
  assert payload['report_markdown'].startswith('# Research Brief:')


def test_eval_run_endpoint_delegates_to_runner(tmp_path: Path, monkeypatch) -> None:
  captured: dict[str, str | None] = {}

  def fake_run_saved_eval_set(services, *, eval_set_path=None, config_path=None, run_agent_fn=None):
    del services, run_agent_fn
    captured['eval_set_path'] = eval_set_path
    captured['config_path'] = config_path
    return {
      'eval_set_id': 'graphite_react_agent_eval_set',
      'total': 1,
      'passed': 1,
      'failed': 0,
      'supported_criteria': ['tool_trajectory_avg_score', 'response_match_score'],
      'unsupported_criteria': ['final_response_match_v2'],
      'results': [],
    }

  monkeypatch.setattr('src.eval_runner.run_saved_eval_set', fake_run_saved_eval_set)

  app = build_app(tmp_path / 'graphite.sqlite3')
  client = app.test_client()
  response = client.post('/api/eval/run', json={})

  assert response.status_code == 200
  payload = response.get_json()
  assert payload['passed'] == 1
  assert 'tool_trajectory_avg_score' in payload['supported_criteria']
  assert captured['eval_set_path'] is None
  assert captured['config_path'] is None


def test_eval_results_endpoint_returns_saved_results(tmp_path: Path) -> None:
  app = build_app(tmp_path / 'graphite.sqlite3')
  client = app.test_client()

  services = app.extensions['graphite_services']
  services.note_store.insert_eval_result({
    'id': 'eval-http-001',
    'eval_case_id': 'endpoint-case',
    'agent_id': 'react',
    'tool_trajectory_score': 1.0,
    'response_match_score': 0.95,
    'overall_pass': True,
    'actual_trajectory': '["search_notes"]',
    'expected_trajectory': '["search_notes"]',
    'actual_response': 'Found notes',
    'expected_response': 'Found notes',
    'metadata': '{}',
    'evaluated_at': '2024-01-01T00:00:00Z',
  })

  response = client.get('/api/eval/results?agent_id=react')

  assert response.status_code == 200
  payload = response.get_json()
  assert len(payload['results']) == 1
  assert payload['results'][0]['eval_case_id'] == 'endpoint-case'


def test_tts_compare_endpoint_delegates_to_service(tmp_path: Path, monkeypatch) -> None:
  app = build_app(tmp_path / 'graphite.sqlite3')

  def fake_compare_tts_providers(self, *, text: str, voice: str, speed: float):
    del self
    assert text == 'Narrate this report.'
    assert voice == 'Bruno'
    assert speed == 1.0
    return {
      'status': 'success',
      'preferred_provider': 'kitten',
      'comparison_reason': 'Neural output is preferred.',
      'results': [
        {'provider': 'kitten', 'status': 'success', 'file_url': '/api/tts/files/kitten.wav'},
        {'provider': 'espeak', 'status': 'success', 'file_url': '/api/tts/files/espeak.wav'},
      ],
    }

  monkeypatch.setattr(ServiceRegistry, 'compare_tts_providers', fake_compare_tts_providers)
  client = app.test_client()

  response = client.post(
    '/api/tts/compare',
    json={'text': 'Narrate this report.', 'voice': 'Bruno', 'speed': 1.0},
  )

  assert response.status_code == 200
  payload = response.get_json()
  assert payload['preferred_provider'] == 'kitten'
  assert len(payload['results']) == 2


def test_stt_transcribe_endpoint_delegates_to_service(tmp_path: Path, monkeypatch) -> None:
  app = build_app(tmp_path / 'graphite.sqlite3')

  def fake_transcribe_audio_upload(self, *, audio_file, note_id=None):
    del self
    assert audio_file.filename == 'sample.webm'
    assert note_id == 'note-123'
    return {
      'status': 'success',
      'text': 'Transcribed note text.',
      'note_id': note_id,
      'model': 'voice-input-english-244.bin',
    }

  monkeypatch.setattr(ServiceRegistry, 'transcribe_audio_upload', fake_transcribe_audio_upload)
  client = app.test_client()

  response = client.post(
    '/api/stt/transcribe',
    data={
      'note_id': 'note-123',
      'audio': (BytesIO(b'fake-audio-bytes'), 'sample.webm'),
    },
    content_type='multipart/form-data',
  )

  assert response.status_code == 200
  payload = response.get_json()
  assert payload['status'] == 'success'
  assert payload['text'] == 'Transcribed note text.'
  assert payload['note_id'] == 'note-123'


def test_memory_store_prefers_supabase_pgvector(tmp_path: Path, monkeypatch) -> None:
  app = build_app(tmp_path / 'graphite.sqlite3')
  services = app.extensions['graphite_services']

  captured: dict[str, object] = {}

  class FakeTable:
    def __init__(self, name: str) -> None:
      self.name = name

    def upsert(self, payload, on_conflict='id'):
      captured['table'] = self.name
      captured['payload'] = payload
      captured['on_conflict'] = on_conflict
      return self

    def execute(self):
      return type('Result', (), {'data': [{'id': 'ok'}]})()

  class FakeSupabase:
    def table(self, name: str):
      return FakeTable(name)

  monkeypatch.setattr(ServiceRegistry, 'generate_embedding', lambda self, text: [0.1, -0.2])
  services.supabase = FakeSupabase()
  services.PGVECTOR_index = None

  memory_id = services.store_memory(
    'Remember this note',
    {'user_id': 'web-local', 'topic': 'notes'},
    'default',
  )

  assert memory_id.startswith('mem-')
  assert captured['table'] == 'memory_vectors'
  assert captured['payload']['embedding'] == '[0.1000000000,-0.2000000000]'
  assert captured['payload']['user_id'] == 'web-local'


def test_memory_search_prefers_supabase_pgvector(tmp_path: Path, monkeypatch) -> None:
  app = build_app(tmp_path / 'graphite.sqlite3')
  services = app.extensions['graphite_services']

  captured: dict[str, object] = {}

  class FakeRpc:
    def execute(self):
      return type(
        'Result',
        (),
        {'data': [{'memory_id': 'mem-123', 'metadata': {'topic': 'notes'}, 'similarity': 0.88}]},
      )()

  class FakeSupabase:
    def rpc(self, name: str, payload: dict[str, object]):
      captured['name'] = name
      captured['payload'] = payload
      return FakeRpc()

  monkeypatch.setattr(ServiceRegistry, 'generate_embedding', lambda self, text: [0.25, 0.75])
  services.supabase = FakeSupabase()
  services.PGVECTOR_index = None

  matches = services.search_memory('Find the note', 3, 'default')

  assert captured['name'] == 'match_memory'
  assert captured['payload']['query_embedding'] == '[0.2500000000,0.7500000000]'
  assert matches == [{'id': 'mem-123', 'score': 0.88, 'metadata': {'topic': 'notes'}}]


def test_note_embedding_mirror_prefers_pgvector_payload(tmp_path: Path) -> None:
  app = build_app(tmp_path / 'graphite.sqlite3')
  services = app.extensions['graphite_services']

  captured: dict[str, object] = {}

  class FakeTable:
    def __init__(self, name: str) -> None:
      self.name = name

    def upsert(self, payload, on_conflict='id'):
      if self.name == 'note_embeddings':
        captured['payload'] = payload
      return self

    def execute(self):
      return type('Result', (), {'data': [{'id': 'ok'}]})()

  class FakeSupabase:
    def table(self, name: str):
      return FakeTable(name)

  services.supabase = FakeSupabase()
  services._mirror_note_to_supabase(
    {
      'id': 'note-123',
      'user_id': 'web-local',
      'title': 'Hello',
      'content': 'World',
      'excerpt': 'World',
      'source_path': None,
      'created_at': '2026-01-01T00:00:00Z',
      'updated_at': '2026-01-01T00:00:00Z',
      'is_ai_generated': False,
    },
    [0.3, 0.4],
  )

  assert captured['payload']['embedding'] == '[0.3000000000,0.4000000000]'
  assert captured['payload']['model'] == 'text-embedding-004'


def test_ai_note_requires_gemini_key(tmp_path: Path) -> None:
  app = build_app(tmp_path / 'graphite.sqlite3')
  client = app.test_client()

  response = client.post('/api/notes/ai-draft', json={'prompt': 'Draft a hiring note'})

  assert response.status_code == 400
  assert 'GEMINI_API_KEY' in response.get_json()['detail']


def test_flask_serves_built_web_index_and_spa_fallback() -> None:
  assert Path(FRONTEND_BUILD_DIR).exists()

  app = build_app()
  client = app.test_client()

  index_response = client.get('/')
  fallback_response = client.get('/workspace/notes')

  assert index_response.status_code == 200
  assert fallback_response.status_code == 200
  assert b'<html' in index_response.data.lower()
  assert b'<html' in fallback_response.data.lower()


def test_settings_support_root_env_alias_names(tmp_path: Path, monkeypatch) -> None:
  backend_env = tmp_path / 'backend.env'
  root_env = tmp_path / 'root.env'
  backend_env.write_text(
    'GEMINI_API_KEY=backend-key\nSUPABASE_URL=https://your-project.supabase.co\n',
    encoding='utf-8',
  )
  root_env.write_text(
    'gemini_api=root-key\nsuperbase_api=https://example.supabase.co/rest/v1/\n'
    'superbase_pub_key=public-key\n',
    encoding='utf-8',
  )

  settings = Settings(_env_file=(str(backend_env), str(root_env)))

  assert settings.gemini_api_key == 'root-key'
  assert settings.supabase_url == 'https://example.supabase.co'
  assert settings.supabase_public_key == 'public-key'