from pathlib import Path

from src import settings as settings_module
from src.app_factory import create_app
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