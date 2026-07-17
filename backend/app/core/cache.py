import functools
import json
import logging

import redis

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: redis.Redis | None = None


def get_redis_client() -> redis.Redis:
    """Lazily-created singleton -- module import shouldn't require a live
    Redis connection (e.g. plain unit tests that never touch a cached call)."""
    global _client
    if _client is None:
        _client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _client


def cached(prefix: str, ttl_seconds: int, key_fn):
    """Cache a JSON-serializable function result in Redis.

    `key_fn` receives the wrapped function's exact call arguments and must
    return a cache key suffix built only from the parts that determine the
    result (e.g. query params) -- callers routinely pass non-serializable
    dependencies too (a SQLAlchemy Session, the current user), so this
    intentionally does not try to auto-derive a key from every argument.

    Redis is already a hard runtime dependency elsewhere (Celery broker,
    rate limiting), but a cache is an optimization, not a correctness
    requirement -- reads/writes fail open on any Redis error so a blip there
    degrades to "slower", never "broken".
    """

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            key = f"cache:{prefix}:{key_fn(*args, **kwargs)}"
            try:
                raw = get_redis_client().get(key)
                if raw is not None:
                    return json.loads(raw)
            except Exception:
                logger.warning("Cache read failed for %s", prefix, exc_info=True)

            result = fn(*args, **kwargs)

            try:
                get_redis_client().set(key, json.dumps(result, default=str), ex=ttl_seconds)
            except Exception:
                logger.warning("Cache write failed for %s", prefix, exc_info=True)

            return result

        return wrapper

    return decorator
