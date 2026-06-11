"""
Graphite Agent Evaluation Tests — pytest-based evaluation runner.

Uses the ADK-eval compatible eval set files to test agent behavior
with trajectory scoring and response matching.

Run with: cd backend && ../.venv/bin/python -m pytest ../tests/ -v
"""

import json
import os
import sys
from pathlib import Path

import pytest

# Add backend to path
BACKEND_DIR = Path(__file__).resolve().parent.parent / 'backend'
sys.path.insert(0, str(BACKEND_DIR))


@pytest.fixture(scope='module')
def services():
  """Create a test ServiceRegistry."""
  from src.settings import Settings
  from src.services import ServiceRegistry
  import logging

  test_db = BACKEND_DIR / 'data' / 'test_graphite.sqlite3'
  settings = Settings(notes_database_path=test_db)
  logger = logging.getLogger('graphite.test')
  svc = ServiceRegistry(settings, logger)
  yield svc
  svc.close()
  # Clean up test database
  if test_db.exists():
    test_db.unlink()


@pytest.fixture(scope='module')
def eval_set():
  """Load the evaluation set."""
  eval_path = Path(__file__).parent / 'eval' / 'graphite_react_agent.evalset.json'
  with open(eval_path) as f:
    return json.load(f)


@pytest.fixture(scope='module')
def eval_criteria():
  """Load evaluation criteria."""
  config_path = Path(__file__).parent / 'eval' / 'test_config.json'
  with open(config_path) as f:
    return json.load(f).get('criteria', {})


class TestEvalFramework:
  """Test the evaluation framework itself."""

  def test_trajectory_exact_match(self):
    from src.eval_framework import compute_trajectory_score

    actual = ['search_notes', 'get_note_by_id', 'update_note']
    expected = ['search_notes', 'get_note_by_id', 'update_note']
    score = compute_trajectory_score(actual, expected)
    assert score == 1.0

  def test_trajectory_partial_match(self):
    from src.eval_framework import compute_trajectory_score

    actual = ['search_notes', 'create_note']
    expected = ['search_notes', 'get_note_by_id', 'update_note']
    score = compute_trajectory_score(actual, expected)
    assert score == 0.0

  def test_trajectory_in_order_match(self):
    from src.eval_framework import compute_trajectory_score

    actual = ['search_notes', 'list_all_notes', 'get_note_by_id', 'update_note']
    expected = ['search_notes', 'get_note_by_id', 'update_note']
    score = compute_trajectory_score(actual, expected, match_type='IN_ORDER')
    assert score == 1.0

  def test_trajectory_any_order_match(self):
    from src.eval_framework import compute_trajectory_score

    actual = ['create_note', 'search_notes', 'update_note']
    expected = ['update_note', 'search_notes']
    score = compute_trajectory_score(actual, expected, match_type='ANY_ORDER')
    assert score == 1.0

  def test_trajectory_empty(self):
    from src.eval_framework import compute_trajectory_score

    assert compute_trajectory_score([], []) == 1.0
    assert compute_trajectory_score([], ['search_notes']) == 0.0

  def test_response_match_identical(self):
    from src.eval_framework import compute_response_match_score

    score = compute_response_match_score(
      'The capital of France is Paris.',
      'The capital of France is Paris.',
    )
    assert score >= 0.99

  def test_response_match_similar(self):
    from src.eval_framework import compute_response_match_score

    score = compute_response_match_score(
      'Paris is the capital city of France.',
      'The capital of France is Paris.',
    )
    assert score > 0.5

  def test_response_match_different(self):
    from src.eval_framework import compute_response_match_score

    score = compute_response_match_score(
      'The weather today is sunny.',
      'The capital of France is Paris.',
    )
    assert score < 0.5

  def test_evaluate_single_case(self):
    from src.eval_framework import evaluate_single_case

    case = {
      'eval_id': 'test_case',
      'conversation': [{
        'user_content': {'parts': [{'text': 'Search notes'}], 'role': 'user'},
        'final_response': {'parts': [{'text': 'Found notes.'}], 'role': 'model'},
        'intermediate_data': {
          'tool_uses': [{'name': 'search_notes', 'args': {'query': 'test'}}],
          'intermediate_responses': [],
        },
      }],
    }
    agent_result = {
      'agent': 'react',
      'trajectory': ['search_notes'],
      'result': {'summary': 'Found matching notes.'},
    }
    result = evaluate_single_case(case, agent_result)
    assert result['tool_trajectory_score'] > 0.5
    assert result['response_match_score'] > 0.3
    assert 'eval_case_id' in result

  def test_evaluate_single_case_with_structured_criteria(self):
    from src.eval_framework import evaluate_single_case

    case = {
      'eval_id': 'structured_case',
      'conversation': [{
        'user_content': {'parts': [{'text': 'Search notes'}], 'role': 'user'},
        'final_response': {'parts': [{'text': 'Found notes.'}], 'role': 'model'},
        'intermediate_data': {
          'tool_uses': [{'name': 'search_notes', 'args': {'query': 'test'}}],
          'intermediate_responses': [],
        },
      }],
    }
    agent_result = {
      'agent': 'react',
      'trajectory': ['search_notes', 'list_all_notes'],
      'result': {'summary': 'Found notes.'},
    }
    result = evaluate_single_case(case, agent_result, {
      'tool_trajectory_avg_score': {'threshold': 1.0, 'match_type': 'IN_ORDER'},
      'response_match_score': 0.8,
    })
    assert result['tool_trajectory_score'] == 1.0
    assert result['overall_pass'] is True


class TestEvalRunner:
  """Test config parsing and local eval runner behavior."""

  def test_load_eval_config_declares_all_metrics(self):
    from src.eval_runner import load_eval_config

    config = load_eval_config(str(Path(__file__).parent / 'eval' / 'test_config.json'))
    criteria = config['criteria']
    assert 'tool_trajectory_avg_score' in criteria
    assert 'response_match_score' in criteria
    assert 'final_response_match_v2' in criteria
    assert 'multi_turn_tool_use_quality_v1' in criteria

  def test_run_saved_eval_set_reports_supported_and_unsupported(self, services, eval_set):
    from src.eval_runner import run_saved_eval_set

    eval_path = Path(__file__).parent / 'eval' / 'graphite_react_agent.evalset.json'
    config_path = Path(__file__).parent / 'eval' / 'test_config.json'

    def fake_runner(_services, task, user_id='web-local'):
      query = task.lower()
      if 'search' in query:
        return {'agent': 'react', 'trajectory': ['search_notes'], 'result': {'summary': 'I found notes related to architecture in your workspace.'}}
      if 'create a note' in query:
        return {'agent': 'react', 'trajectory': ['create_note'], 'result': {'summary': "I've created a new note titled 'Meeting Notes' about the Q4 planning session."}}
      if 'show me all my notes' in query:
        return {'agent': 'react', 'trajectory': ['list_all_notes'], 'result': {'summary': 'Here are all your notes in the workspace.'}}
      if 'analyze the project' in query:
        return {'agent': 'react', 'trajectory': ['analyze_project', 'create_note'], 'result': {'summary': "I've analyzed the Graphite project and created detailed notes covering the architecture, tech stack, and setup instructions."}}
      if 'research aapl' in query:
        return {'agent': 'react', 'trajectory': ['run_financial_research'], 'result': {'summary': "Here's my analysis of AAPL including technical indicators."}}
      return {'agent': 'react', 'trajectory': [], 'result': {'summary': task}, 'duration_ms': 1}

    summary = run_saved_eval_set(
      services,
      eval_set_path=str(eval_path),
      config_path=str(config_path),
      run_agent_fn=fake_runner,
    )

    assert summary['total'] >= 1
    assert 'tool_trajectory_avg_score' in summary['supported_criteria']
    assert 'response_match_score' in summary['supported_criteria']
    assert 'final_response_match_v2' in summary['unsupported_criteria']
    assert 'rubric_based_tool_use_quality_v1' in summary['unsupported_criteria']


class TestNoteStore:
  """Test SQLite note store with new schema tables."""

  def test_schema_creation(self, services):
    """Verify all tables exist after initialization."""
    cursor = services.note_store.connection.execute(
      "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = [r[0] for r in cursor.fetchall()]
    assert 'notes' in tables
    assert 'note_embeddings' in tables
    assert 'tags' in tables
    assert 'note_tags' in tables
    assert 'agent_runs' in tables
    assert 'agent_action_log' in tables
    assert 'eval_results' in tables
    assert 'projects' in tables
    assert 'project_notes' in tables

  def test_agent_run_lifecycle(self, services):
    """Test insert and update of agent runs."""
    run_id = 'test-run-001'
    services.note_store.insert_agent_run({
      'id': run_id,
      'agent_id': 'react',
      'user_id': 'web-local',
      'task': 'Test task',
      'status': 'running',
      'started_at': '2024-01-01T00:00:00Z',
    })

    run = services.note_store.get_agent_run(run_id)
    assert run is not None
    assert run['status'] == 'running'

    services.note_store.update_agent_run(run_id, {
      'status': 'completed',
      'completed_at': '2024-01-01T00:01:00Z',
      'duration_ms': 60000,
    })

    run = services.note_store.get_agent_run(run_id)
    assert run['status'] == 'completed'

  def test_action_log_insert(self, services):
    """Test action log insertion and retrieval."""
    services.note_store.insert_action_log({
      'id': 'act-test-001',
      'run_id': 'test-run-001',
      'step_index': 1,
      'action_type': 'tool_call',
      'tool_name': 'search_notes',
      'tool_args': '{"query": "test"}',
      'timestamp': '2024-01-01T00:00:01Z',
    })

    logs = services.note_store.list_action_logs('test-run-001')
    assert len(logs) >= 1
    assert logs[0]['tool_name'] == 'search_notes'

  def test_eval_result_insert(self, services):
    """Test eval result storage."""
    services.note_store.insert_eval_result({
      'id': 'eval-test-001',
      'eval_case_id': 'test_case',
      'agent_id': 'react',
      'tool_trajectory_score': 0.85,
      'response_match_score': 0.92,
      'overall_pass': True,
      'actual_trajectory': '["search_notes"]',
      'expected_trajectory': '["search_notes"]',
      'actual_response': 'Found notes',
      'expected_response': 'Found notes',
      'metadata': '{}',
      'evaluated_at': '2024-01-01T00:00:00Z',
    })

  def test_list_eval_results(self, services):
    results = services.note_store.list_eval_results(limit=10)
    assert len(results) >= 1
    assert results[0]['agent_id'] == 'react'


class TestNoteCRUD:
  """Test note creation, reading, updating."""

  def test_create_and_read_note(self, services):
    from src.schemas import NoteSaveRequest

    saved = services.save_note(NoteSaveRequest(
      user_id='test-user',
      title='Test Note',
      content='This is a test note for evaluation.',
    ))
    assert saved['title'] == 'Test Note'
    assert saved['id'].startswith('note-')

    retrieved = services.get_note(saved['id'])
    assert retrieved is not None
    assert retrieved['content'] == 'This is a test note for evaluation.'

  def test_list_notes(self, services):
    notes = services.list_notes('test-user')
    assert len(notes) >= 1

  def test_count_notes(self, services):
    count = services.count_notes('test-user')
    assert count >= 1

  def test_guest_note_limit(self, services):
    from src.schemas import NoteSaveRequest
    from src.errors import ConfigurationError

    services.supabase = object()

    # Create up to the limit
    for i in range(5):
      try:
        services.save_note(NoteSaveRequest(
          user_id='web-local',
          title=f'Guest Note {i}',
          content=f'Content {i}',
        ))
      except ConfigurationError:
        break

    # The 6th should fail
    with pytest.raises(ConfigurationError, match='Guest mode is limited'):
      services.save_note(NoteSaveRequest(
        user_id='web-local',
        title='Over limit note',
        content='Should fail',
      ))


class TestGetAllNotesContext:
  """Test that agent can access full notes context."""

  def test_get_all_notes_content(self, services):
    notes = services.note_store.get_all_notes_content('test-user')
    assert len(notes) >= 1
    assert 'title' in notes[0]
    assert 'content' in notes[0]

  def test_get_all_notes_no_filter(self, services):
    notes = services.note_store.get_all_notes_content()
    assert len(notes) >= 1


class TestHealthEndpoint:
  """Test health check reports correctly."""

  def test_health_payload(self, services):
    health = services.health_payload()
    assert health['status'] == 'ok'
    assert 'agents' in health
    assert isinstance(health['agents'], list)


class TestResearch:
  """Test financial research (requires network)."""

  @pytest.mark.skipif(
    not os.environ.get('GRAPHITE_TEST_NETWORK'),
    reason='Skipping network-dependent test (set GRAPHITE_TEST_NETWORK=1)',
  )
  def test_run_research(self, services):
    result = services.run_research('AAPL', ['ma', 'rsi'])
    assert result['ticker'] == 'AAPL'
    assert 'algorithms' in result
    assert result['overall_signal'] in ('BUY', 'SELL', 'HOLD')
