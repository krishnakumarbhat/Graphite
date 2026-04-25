from typing import TypeVar

from flask import Blueprint, jsonify, request
from pydantic import BaseModel

from src.agents import AGENT_DEFINITIONS
from src.schemas import (
  AINoteDraftRequest,
  MemorySearchRequest,
  MemoryStoreRequest,
  MarkdownImportRequest,
  NoteSyncPayload,
  NoteSaveRequest,
  OrchestrateRequest,
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
    return jsonify(services.orchestrate_agent(orchestrate_request.agent, orchestrate_request.task))

  return api