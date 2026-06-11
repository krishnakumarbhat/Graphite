import json
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class InMemoryCacheStore:
  default_ttl_seconds: int = 300
  _values: dict[str, tuple[float, str]] = field(default_factory=dict)

  @property
  def backend_name(self) -> str:
    return 'memory'

  @property
  def is_remote(self) -> bool:
    return False

  def get_json(self, key: str) -> dict[str, Any] | list[Any] | None:
    self._purge_expired()
    payload = self._values.get(key)
    if payload is None:
      return None

    expires_at, raw_value = payload
    if expires_at <= time.time():
      self._values.pop(key, None)
      return None
    return json.loads(raw_value)

  def set_json(self, key: str, value: dict[str, Any] | list[Any], ttl_seconds: int | None = None) -> None:
    ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
    expires_at = time.time() + max(ttl, 1)
    self._values[key] = (expires_at, json.dumps(value))

  def close(self) -> None:
    self._values.clear()

  def _purge_expired(self) -> None:
    now = time.time()
    expired_keys = [key for key, (expires_at, _raw_value) in self._values.items() if expires_at <= now]
    for key in expired_keys:
      self._values.pop(key, None)


@dataclass(slots=True)
class RedisCacheStore:
  client: Any
  default_ttl_seconds: int = 300

  @property
  def backend_name(self) -> str:
    return 'redis'

  @property
  def is_remote(self) -> bool:
    return True

  def get_json(self, key: str) -> dict[str, Any] | list[Any] | None:
    raw_value = self.client.get(key)
    if raw_value is None:
      return None
    if isinstance(raw_value, bytes):
      raw_value = raw_value.decode('utf-8')
    return json.loads(raw_value)

  def set_json(self, key: str, value: dict[str, Any] | list[Any], ttl_seconds: int | None = None) -> None:
    ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
    self.client.setex(key, max(ttl, 1), json.dumps(value))

  def close(self) -> None:
    try:
      self.client.close()
    except AttributeError:
      pass


def build_cache_store(redis_url: str, default_ttl_seconds: int):
  normalized_url = redis_url.strip()
  if not normalized_url:
    return InMemoryCacheStore(default_ttl_seconds=default_ttl_seconds)

  try:
    import redis

    client = redis.Redis.from_url(normalized_url, decode_responses=False)
    client.ping()
    return RedisCacheStore(client=client, default_ttl_seconds=default_ttl_seconds)
  except Exception:
    return InMemoryCacheStore(default_ttl_seconds=default_ttl_seconds)