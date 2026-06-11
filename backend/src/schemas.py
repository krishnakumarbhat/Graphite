from typing import Any

from pydantic import BaseModel, Field


class WorkflowNode(BaseModel):
  id: str
  title: str
  description: str


class WorkflowEdge(BaseModel):
  id: str
  source: str
  target: str


class WorkflowGraph(BaseModel):
  nodes: list[WorkflowNode] = Field(default_factory=list)
  edges: list[WorkflowEdge] = Field(default_factory=list)


class WorkflowGenerateRequest(BaseModel):
  prompt: str = Field(min_length=1, max_length=4000)


class WorkflowGenerateResponse(BaseModel):
  graph: WorkflowGraph


class NoteSyncPayload(BaseModel):
  id: str
  user_id: str
  title: str = ''
  content: str = ''
  source_path: str | None = None
  created_at: str
  updated_at: str


class NoteRecord(BaseModel):
  id: str
  user_id: str
  title: str = ''
  content: str = ''
  excerpt: str = ''
  source_path: str | None = None
  created_at: str
  updated_at: str
  is_ai_generated: bool = False


class NoteSaveRequest(BaseModel):
  id: str | None = None
  user_id: str = 'web-local'
  title: str = Field(default='', max_length=240)
  content: str = Field(default='', max_length=50000)
  source_path: str | None = Field(default=None, max_length=1024)
  is_ai_generated: bool = False


class MarkdownImportRequest(BaseModel):
  user_id: str = 'web-local'
  filename: str = Field(min_length=1, max_length=1024)
  content: str = Field(min_length=1, max_length=100000)


class AINoteDraftRequest(BaseModel):
  user_id: str = 'web-local'
  prompt: str = Field(min_length=1, max_length=4000)
  title_hint: str = Field(default='', max_length=240)


class WorkflowSyncPayload(BaseModel):
  id: str
  user_id: str
  title: str = ''
  prompt: str = ''
  graph_json: str | None = None
  created_at: str
  updated_at: str


class MemoryStoreRequest(BaseModel):
  text: str = Field(min_length=1, max_length=10000)
  metadata: dict[str, Any] = Field(default_factory=dict)
  namespace: str = 'default'


class MemorySearchRequest(BaseModel):
  query: str = Field(min_length=1, max_length=4000)
  top_k: int = Field(default=5, ge=1, le=20)
  namespace: str = 'default'


class OrchestrateRequest(BaseModel):
  agent: str = Field(min_length=1)
  task: str = Field(min_length=1, max_length=4000)


class ProjectAnalyzeRequest(BaseModel):
  project_path: str = Field(min_length=1, max_length=4096)
  project_name: str = Field(default='', max_length=240)
  user_id: str = 'web-local'


class EvalRunRequest(BaseModel):
  eval_set_path: str = Field(default='', max_length=4096)
  config_path: str = Field(default='', max_length=4096)


class ResearchRequest(BaseModel):
  ticker: str = Field(min_length=1, max_length=10)
  algorithms: list[str] = Field(default_factory=lambda: ['ma', 'rsi', 'macd', 'bollinger'])


class DeepResearchRequest(BaseModel):
  query: str = Field(min_length=1, max_length=4000)
  source_text: str = Field(default='', max_length=120000)
  user_id: str = 'web-local'
  retrieval_mode: str = Field(default='fixed', pattern='^(fixed|gemini|hybrid)$')
  max_chunks: int = Field(default=6, ge=2, le=12)
  save_as_note: bool = True


class TTSRequest(BaseModel):
  text: str = Field(min_length=1, max_length=20000)
  provider: str = Field(default='kitten', pattern='^(kitten|espeak)$')
  voice: str = Field(default='Bruno', max_length=32)
  speed: float = Field(default=1.0, ge=0.7, le=1.4)


class TTSCompareRequest(BaseModel):
  text: str = Field(min_length=1, max_length=20000)
  voice: str = Field(default='Bruno', max_length=32)
  speed: float = Field(default=1.0, ge=0.7, le=1.4)