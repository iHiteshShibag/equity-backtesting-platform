import app.core.cache as cache_module
from app.core.cache import cached


class _FakeRedis:
    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value, ex=None):
        self.store[key] = value


def test_cached_returns_wrapped_result_and_reuses_it(monkeypatch):
    fake_redis = _FakeRedis()
    monkeypatch.setattr(cache_module, "get_redis_client", lambda: fake_redis)

    calls = {"n": 0}

    @cached("test-prefix", ttl_seconds=60, key_fn=lambda x: x)
    def compute(x):
        calls["n"] += 1
        return {"value": x * 2}

    assert compute(3) == {"value": 6}
    assert compute(3) == {"value": 6}
    assert calls["n"] == 1  # second call served from cache


def test_cached_distinguishes_keys(monkeypatch):
    fake_redis = _FakeRedis()
    monkeypatch.setattr(cache_module, "get_redis_client", lambda: fake_redis)

    @cached("test-prefix", ttl_seconds=60, key_fn=lambda x: x)
    def compute(x):
        return {"value": x}

    assert compute(1) == {"value": 1}
    assert compute(2) == {"value": 2}


def test_cached_fails_open_when_redis_is_unreachable(monkeypatch):
    class _BrokenRedis:
        def get(self, key):
            raise ConnectionError("redis down")

        def set(self, key, value, ex=None):
            raise ConnectionError("redis down")

    monkeypatch.setattr(cache_module, "get_redis_client", lambda: _BrokenRedis())

    @cached("test-prefix", ttl_seconds=60, key_fn=lambda x: x)
    def compute(x):
        return {"value": x}

    assert compute(1) == {"value": 1}
