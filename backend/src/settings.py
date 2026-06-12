from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BACKEND_DIR.parent
FRONTEND_BUILD_DIR = REPO_DIR / 'frontend' / 'build'


class Settings(BaseSettings):
  supabase_url: str = Field(
    default='',
    alias='SUPABASE_URL',
    validation_alias=AliasChoices('superbase_api', 'SUPABASE_API', 'SUPABASE_URL'),
  )
  supabase_service_role_key: str = Field(
    default='',
    alias='SUPABASE_SERVICE_ROLE_KEY',
    validation_alias=AliasChoices(
      'SUPABASE_SERVICE_ROLE_KEY',
      'SUPABASE_SECRET_KEY',
      'superbase_secret_key',
    ),
  )
  supabase_public_key: str = Field(
    default='',
    alias='SUPABASE_PUBLIC_KEY',
    validation_alias=AliasChoices(
      'superbase_pub_key',
      'SUPERBASE_PUB_KEY',
      'SUPABASE_PUBLIC_KEY',
      'SUPABASE_ANON_KEY',
    ),
  )
  cors_origins: str = Field(
    default='http://localhost:3000,http://127.0.0.1:3000,http://localhost:8081,http://127.0.0.1:8081',
    alias='CORS_ORIGINS',
  )
  gemini_api_key: str = Field(
    default='',
    alias='GEMINI_API_KEY',
    validation_alias=AliasChoices('gemini_api', 'GEMINI_API', 'GEMINI_API_KEY'),
  )
  gemini_model: str = Field(default='gemini-3.5-flash', alias='GEMINI_MODEL')
  gemini_fallback_model: str = Field(default='gemini-3.5-flash_preview', alias='GEMINI_FALLBACK_MODEL')
  gemini_retry_count: int = Field(default=3, alias='GEMINI_RETRY_COUNT')
  gemini_embedding_model: str = Field(default='text-embedding-004', alias='GEMINI_EMBEDDING_MODEL')
  gemini_thinking_level: str = Field(default='medium', alias='GEMINI_THINKING_LEVEL')
  brave_api_key: str = Field(
    default='',
    alias='BRAVE_API_KEY',
    validation_alias=AliasChoices('BRAVE_API_KEY', 'BRAVE_SEARCH_API_KEY'),
  )
  web_search_provider: str = Field(default='auto', alias='WEB_SEARCH_PROVIDER')
  web_search_max_results: int = Field(default=5, alias='WEB_SEARCH_MAX_RESULTS')
  redis_url: str = Field(default='', alias='REDIS_URL')
  cache_ttl_seconds: int = Field(default=300, alias='CACHE_TTL_SECONDS')
  research_chunk_size: int = Field(default=1400, alias='RESEARCH_CHUNK_SIZE')
  research_chunk_overlap: int = Field(default=180, alias='RESEARCH_CHUNK_OVERLAP')
  graphite_port: int = Field(default=8001, alias='GRAPHITE_PORT')
  flask_debug: bool = Field(default=False, alias='FLASK_DEBUG')
  payment_link_url: str = Field(
    default='',
    alias='PAYMENT_LINK_URL',
    validation_alias=AliasChoices('PAYMENT_LINK_URL', 'STRIPE_PAYMENT_LINK_URL'),
  )
  pricing_headline: str = Field(default='Graphite Pro', alias='PRICING_HEADLINE')
  notes_database_path: Path = Field(
    default=BACKEND_DIR / 'data' / 'graphite.sqlite3',
    alias='NOTES_DATABASE_PATH',
  )
  voice_input_model_path: Path = Field(
    default=BACKEND_DIR / 'data' / 'models' / 'stt' / 'voice-input-english-244.bin',
    alias='VOICE_INPUT_MODEL_PATH',
  )
  tts_output_dir: Path = Field(default=BACKEND_DIR / 'data' / 'audio', alias='TTS_OUTPUT_DIR')
  kitten_model_path: Path = Field(
    default=BACKEND_DIR / 'data' / 'models' / 'tts' / 'kitten_tts_mini_v0_8.onnx',
    alias='KITTEN_MODEL_PATH',
  )
  kitten_model_repo: str = Field(default='KittenML/kitten-tts-nano-0.8', alias='KITTEN_MODEL_REPO')
  model_cache_dir: Path = Field(default=BACKEND_DIR / 'data' / 'model-cache', alias='MODEL_CACHE_DIR')
  graphite_model_repo: str = Field(default='krishnah27/graphite', alias='GRAPHITE_MODEL_REPO')
  huggingface_token: str = Field(
    default='',
    alias='HUGGINGFACE_TOKEN',
    validation_alias=AliasChoices('HUGGINGFACE_TOKEN', 'HF_TOKEN'),
  )
  frontend_build_dir: Path = FRONTEND_BUILD_DIR

  model_config = SettingsConfigDict(
    env_file=(str(BACKEND_DIR / '.env'), str(REPO_DIR / '.env')),
    extra='ignore',
    populate_by_name=True,
  )

  @field_validator('supabase_url', mode='before')
  @classmethod
  def normalize_supabase_url(cls, value: str | None) -> str:
    if not value:
      return ''

    normalized = str(value).strip()
    if normalized.endswith('/rest/v1/'):
      return normalized[:-9]
    if normalized.endswith('/rest/v1'):
      return normalized[:-8]
    return normalized.rstrip('/')

  @property
  def supabase_key(self) -> str:
    return self.supabase_service_role_key or self.supabase_public_key

  @property
  def supabase_auth_enabled(self) -> bool:
    return bool(self.supabase_url and self.supabase_public_key)

  @property
  def payment_enabled(self) -> bool:
    return bool(self.payment_link_url)

  @property
  def cors_origin_list(self) -> list[str]:
    return [origin.strip() for origin in self.cors_origins.split(',') if origin.strip()]

  @property
  def allow_credentials(self) -> bool:
    return '*' not in self.cors_origin_list


@lru_cache(maxsize=1)
def get_settings() -> Settings:
  return Settings()