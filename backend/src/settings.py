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
  gemini_model: str = Field(default='gemini-3.1-flash-lite-preview', alias='GEMINI_MODEL')
  gemini_embedding_model: str = Field(default='text-embedding-004', alias='GEMINI_EMBEDDING_MODEL')
  gemini_thinking_level: str = Field(default='high', alias='GEMINI_THINKING_LEVEL')
  pinecone_api_key: str = Field(default='', alias='PINECONE_API_KEY')
  pinecone_index: str = Field(default='graphite-memory', alias='PINECONE_INDEX')
  pinecone_cloud: str = Field(default='aws', alias='PINECONE_CLOUD')
  pinecone_region: str = Field(default='us-east-1', alias='PINECONE_REGION')
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