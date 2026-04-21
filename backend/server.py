from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pathlib import Path
import json
import os
import time
import hashlib
from urllib import request as url_request
from urllib.error import HTTPError, URLError
from supabase import create_client

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

app = FastAPI(title='Graphite API', version='2.0.0')
api_router = APIRouter(prefix='/api')

# --- Supabase ---
supabase_url = os.environ.get('SUPABASE_URL', '').strip()
supabase_service_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '').strip()
supabase = None
if supabase_url and supabase_service_key and 'your-project' not in supabase_url:
  try:
    supabase = create_client(supabase_url, supabase_service_key)
  except Exception as e:
    print(f'[WARN] Supabase init failed: {e}')

# --- Pinecone ---
PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY', '').strip()
PINECONE_INDEX_NAME = os.environ.get('PINECONE_INDEX', 'graphite-memory').strip()
PINECONE_CLOUD = os.environ.get('PINECONE_CLOUD', 'aws').strip()
PINECONE_REGION = os.environ.get('PINECONE_REGION', 'us-east-1').strip()

pc = None
pc_index = None
pinecone_error = None

if PINECONE_API_KEY:
  try:
    from pinecone import Pinecone, ServerlessSpec
    pc = Pinecone(api_key=PINECONE_API_KEY)
    existing_indexes = [idx.name for idx in pc.list_indexes()]
    if PINECONE_INDEX_NAME not in existing_indexes:
      pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=768,
        metric='cosine',
        spec=ServerlessSpec(cloud=PINECONE_CLOUD, region=PINECONE_REGION),
      )
      print(f'[INFO] Created Pinecone index: {PINECONE_INDEX_NAME}')
    pc_index = pc.Index(PINECONE_INDEX_NAME)
    print(f'[INFO] Pinecone connected to index: {PINECONE_INDEX_NAME}')
  except Exception as e:
    pinecone_error = str(e)
    print(f'[WARN] Pinecone init failed: {e}')

# --- Agent definitions (Manager-Worker architecture) ---
AGENT_DEFINITIONS = {
  'finance': {
    'name': 'Financial Intelligence Agent',
    'capabilities': ['automated_bookkeeping', 'budget_optimization', 'forecasting'],
    'description': 'Real-time expense/revenue tracking, AI-driven budget insights, predictive financial modeling.',
    'status': 'active',
  },
  'vc': {
    'name': 'VC & Fundraising Agent',
    'capabilities': ['investor_matching', 'outreach_automation', 'due_diligence_prep'],
    'description': 'Scans global DB for aligned VCs, drafts pitch emails, organizes data rooms.',
    'status': 'active',
  },
  'career': {
    'name': 'Career & Talent Acquisition Agent',
    'capabilities': ['job_market_scanning', 'application_management', 'interview_prep'],
    'description': 'Monitors job boards, tailors resumes, provides Gemini-powered mock interviews.',
    'status': 'active',
  },
  'scraper': {
    'name': 'Autonomous Data Engine',
    'capabilities': ['high_frequency_monitoring', 'information_synthesis', 'trigger_based_actions'],
    'description': 'Crawls target websites every 30 min, synthesizes data, triggers cross-agent alerts.',
    'status': 'active',
  },
}


class WorkflowGenerateRequest(BaseModel):
  prompt: str = Field(min_length=1, max_length=4000)


class WorkflowGenerateResponse(BaseModel):
  graph: dict


class NoteSyncPayload(BaseModel):
  id: str
  user_id: str
  title: str = ''
  content: str = ''
  source_path: str | None = None
  created_at: str
  updated_at: str


class WorkflowSyncPayload(BaseModel):
  id: str
  user_id: str
  title: str = ''
  prompt: str = ''
  graph_json: str | None = None
  created_at: str
  updated_at: str


def require_supabase():
  if not supabase:
    raise HTTPException(
      status_code=400,
      detail='Supabase is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in backend/.env.',
    )


def require_pinecone():
  if not pc_index:
    detail = f'Pinecone not configured. {pinecone_error or "Set PINECONE_API_KEY in backend/.env."}'
    raise HTTPException(status_code=400, detail=detail)


def _fallback_embedding(text: str, dim: int = 768) -> list:
  """Deterministic hash-based embedding fallback when Gemini is unavailable."""
  result = []
  for i in range(dim):
    h = hashlib.md5(f'{text}:{i}'.encode()).hexdigest()
    # Convert first 8 hex chars to a float in [-1, 1]
    val = (int(h[:8], 16) / 0xFFFFFFFF) * 2.0 - 1.0
    result.append(val)
  # L2 normalize
  norm = sum(v * v for v in result) ** 0.5
  if norm > 0:
    result = [v / norm for v in result]
  return result


def get_gemini_embedding(text: str) -> list:
  """Get 768-dim embedding from Gemini text-embedding-004, with hash fallback."""
  api_key = os.environ.get('GEMINI_API_KEY', '').strip()
  if not api_key:
    print('[INFO] No Gemini key, using fallback embedding')
    return _fallback_embedding(text)
  endpoint = f'https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={api_key}'
  body = json.dumps({'content': {'parts': [{'text': text[:2048]}]}}).encode('utf-8')
  req = url_request.Request(endpoint, data=body, headers={'Content-Type': 'application/json'}, method='POST')
  try:
    with url_request.urlopen(req, timeout=15) as resp:
      data = json.loads(resp.read().decode('utf-8'))
      values = data.get('embedding', {}).get('values', [])
      if values:
        return values
  except Exception as e:
    print(f'[WARN] Embedding error: {e}')
  print('[INFO] Gemini embedding failed, using fallback')
  return _fallback_embedding(text)


def parse_gemini_json_response(payload: dict) -> str:
  candidates = payload.get('candidates', [])
  if not candidates:
    return ''

  first_candidate = candidates[0] or {}
  content = first_candidate.get('content', {})
  parts = content.get('parts', [])
  if not parts:
    return ''

  first_part = parts[0] or {}
  return first_part.get('text', '').strip()


def parse_json_block(text: str) -> dict:
  cleaned_text = text.strip()
  if cleaned_text.startswith('```'):
    cleaned_text = cleaned_text.replace('```json', '').replace('```', '').strip()
  return json.loads(cleaned_text)


@api_router.get('/')
async def root():
  return {'message': 'Graphite API is running'}


@api_router.get('/health')
async def health():
  return {
    'status': 'ok',
    'supabaseConfigured': bool(supabase),
    'geminiConfigured': bool(os.environ.get('GEMINI_API_KEY')),
    'pineconeConfigured': bool(pc_index),
    'pineconeIndex': PINECONE_INDEX_NAME if pc_index else None,
    'pineconeError': pinecone_error,
    'agents': list(AGENT_DEFINITIONS.keys()),
  }


@api_router.post('/workflow/generate', response_model=WorkflowGenerateResponse)
async def generate_workflow(input: WorkflowGenerateRequest):
  normalized_prompt = input.prompt.strip()
  gemini_api_key = os.environ.get('GEMINI_API_KEY')
  gemini_model = os.environ.get('GEMINI_MODEL', 'gemini-1.5-flash')

  if not gemini_api_key:
    raise HTTPException(
      status_code=400,
      detail='GEMINI_API_KEY is missing. Add it to backend/.env before using this endpoint.',
    )

  instruction = (
    'Return only JSON with keys nodes and edges. '
    'nodes must be an array of objects with id, title, description. '
    'edges must be an array of objects with id, source, target. '
    'No markdown and no additional text.'
  )

  body = {
    'contents': [
      {
        'parts': [
          {'text': instruction},
          {'text': f'User prompt: {normalized_prompt}'},
        ]
      }
    ]
  }

  endpoint = f'https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={gemini_api_key}'
  payload = json.dumps(body).encode('utf-8')
  request_headers = {'Content-Type': 'application/json'}
  http_request = url_request.Request(endpoint, data=payload, headers=request_headers, method='POST')

  try:
    with url_request.urlopen(http_request, timeout=30) as response:
      response_body = response.read().decode('utf-8')
      gemini_payload = json.loads(response_body)
  except HTTPError as error:
    error_body = error.read().decode('utf-8') if hasattr(error, 'read') else str(error)
    raise HTTPException(status_code=502, detail=f'Gemini HTTP error: {error_body}') from error
  except URLError as error:
    raise HTTPException(status_code=502, detail=f'Gemini connection error: {error.reason}') from error
  except Exception as error:
    raise HTTPException(status_code=500, detail=f'Unexpected Gemini error: {str(error)}') from error

  raw_text = parse_gemini_json_response(gemini_payload)
  if not raw_text:
    raise HTTPException(status_code=502, detail='Gemini response had no text output.')

  try:
    graph = parse_json_block(raw_text)
  except Exception as error:
    raise HTTPException(status_code=502, detail='Gemini returned non-JSON output.') from error

  return WorkflowGenerateResponse(graph=graph)


@api_router.post('/sync/notes')
async def sync_note(note: NoteSyncPayload):
  require_supabase()

  result = supabase.table('notes').upsert(note.model_dump(), on_conflict='id').execute()
  return {'status': 'ok', 'rows': len(result.data or [])}


@api_router.post('/sync/workflows')
async def sync_workflow(workflow: WorkflowSyncPayload):
  require_supabase()

  result = supabase.table('workflows').upsert(workflow.model_dump(), on_conflict='id').execute()
  return {'status': 'ok', 'rows': len(result.data or [])}


@api_router.get('/sync/notes/{user_id}')
async def list_user_notes(user_id: str):
  require_supabase()

  result = supabase.table('notes').select('*').eq('user_id', user_id).order('updated_at', desc=True).execute()
  return {'items': result.data or []}


@api_router.get('/sync/workflows/{user_id}')
async def list_user_workflows(user_id: str):
  require_supabase()

  result = supabase.table('workflows').select('*').eq('user_id', user_id).order('updated_at', desc=True).execute()
  return {'items': result.data or []}


# --- Memory (Pinecone) endpoints ---

class MemoryStoreRequest(BaseModel):
  text: str = Field(min_length=1, max_length=10000)
  metadata: dict = {}
  namespace: str = 'default'


class MemorySearchRequest(BaseModel):
  query: str = Field(min_length=1, max_length=4000)
  top_k: int = Field(default=5, ge=1, le=20)
  namespace: str = 'default'


@api_router.post('/memory/store')
async def store_memory(req: MemoryStoreRequest):
  require_pinecone()
  embedding = get_gemini_embedding(req.text)
  if not embedding:
    raise HTTPException(status_code=502, detail='Failed to generate embedding via Gemini.')
  vec_id = f'mem-{hashlib.sha256(req.text.encode()).hexdigest()[:12]}-{int(time.time())}'
  metadata = {**req.metadata, 'text': req.text[:1000], 'stored_at': int(time.time())}
  pc_index.upsert(vectors=[{'id': vec_id, 'values': embedding, 'metadata': metadata}], namespace=req.namespace)
  return {'status': 'ok', 'id': vec_id}


@api_router.post('/memory/search')
async def search_memory(req: MemorySearchRequest):
  require_pinecone()
  embedding = get_gemini_embedding(req.query)
  if not embedding:
    raise HTTPException(status_code=502, detail='Failed to generate query embedding via Gemini.')
  results = pc_index.query(vector=embedding, top_k=req.top_k, include_metadata=True, namespace=req.namespace)
  matches = [{'id': m.id, 'score': m.score, 'metadata': m.metadata} for m in results.matches]
  return {'matches': matches}


# --- Agent endpoints ---

@api_router.get('/agents/status')
async def agents_status():
  return {'agents': AGENT_DEFINITIONS}


class OrchestrateRequest(BaseModel):
  agent: str = Field(min_length=1)
  task: str = Field(min_length=1, max_length=4000)


@api_router.post('/agents/orchestrate')
async def orchestrate_task(req: OrchestrateRequest):
  if req.agent not in AGENT_DEFINITIONS:
    raise HTTPException(status_code=400, detail=f'Unknown agent: {req.agent}. Valid: {list(AGENT_DEFINITIONS.keys())}')

  agent_def = AGENT_DEFINITIONS[req.agent]
  gemini_api_key = os.environ.get('GEMINI_API_KEY', '').strip()
  if not gemini_api_key:
    raise HTTPException(status_code=400, detail='GEMINI_API_KEY missing in backend/.env')

  instruction = (
    f'You are the {agent_def["name"]} in a Manager-Worker AI system. '
    f'Your capabilities: {", ".join(agent_def["capabilities"])}. '
    f'Respond with ONLY a JSON object containing: '
    f'"action_plan" (array of step strings), "summary" (string), "next_actions" (array of strings). '
    f'No markdown wrapping.'
  )

  body = {'contents': [{'parts': [{'text': instruction}, {'text': f'Task: {req.task}'}]}]}
  gemini_model = os.environ.get('GEMINI_MODEL', 'gemini-1.5-flash')
  endpoint = f'https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={gemini_api_key}'
  payload = json.dumps(body).encode('utf-8')
  http_request = url_request.Request(endpoint, data=payload, headers={'Content-Type': 'application/json'}, method='POST')

  try:
    with url_request.urlopen(http_request, timeout=30) as response:
      response_body = response.read().decode('utf-8')
      gemini_payload = json.loads(response_body)
  except HTTPError as error:
    error_body = error.read().decode('utf-8') if hasattr(error, 'read') else str(error)
    raise HTTPException(status_code=502, detail=f'Gemini HTTP error: {error_body}') from error
  except URLError as error:
    raise HTTPException(status_code=502, detail=f'Gemini connection error: {error.reason}') from error
  except Exception as error:
    raise HTTPException(status_code=500, detail=f'Unexpected error: {str(error)}') from error

  raw_text = parse_gemini_json_response(gemini_payload)
  if not raw_text:
    raise HTTPException(status_code=502, detail='Gemini response had no text output.')

  try:
    result = parse_json_block(raw_text)
  except Exception:
    result = {'summary': raw_text, 'action_plan': [], 'next_actions': []}

  return {'agent': req.agent, 'agent_name': agent_def['name'], 'result': result}


app.include_router(api_router)

cors_origins = [
  origin.strip()
  for origin in os.environ.get(
    'CORS_ORIGINS',
    'http://localhost:3000,http://127.0.0.1:3000,http://localhost:8081,http://127.0.0.1:8081',
  ).split(',')
  if origin.strip()
]
allow_credentials = '*' not in cors_origins

app.add_middleware(
  CORSMiddleware,
  allow_credentials=allow_credentials,
  allow_origins=cors_origins,
  allow_methods=['*'],
  allow_headers=['*'],
)
