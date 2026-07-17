from sqlalchemy import select

import app.modules.market_data.fetcher as mod


class _PgInsertShim:
    """Swaps the Postgres-only `INSERT ... ON CONFLICT` construct for a
    harmless no-op statement, so tests exercising the success path can run
    against the in-memory SQLite test DB (see conftest.py) without hitting
    either the dialect mismatch or SQLite's separate BigInteger-autoincrement
    quirk. on_conflict_do_nothing's actual insert behavior is Postgres-only
    and isn't under test here; only the surrounding retry/circuit-breaker
    bookkeeping is."""

    def __init__(self, table):
        self._table = table

    def values(self, rows):
        return self

    def on_conflict_do_nothing(self, constraint=None):
        return select(1)


def test_fetch_and_store_prices_trips_circuit_breaker_after_consecutive_failures(db_session, monkeypatch):
    """If Yahoo's chart endpoint itself is blocking/down, every ticker fails
    the same way -- the circuit breaker should abort well short of trying
    all ~100 tickers rather than spending minutes hammering a dead source."""
    monkeypatch.setattr(mod, "_fetch_chart", lambda *a, **k: None)

    result = mod.fetch_and_store_prices(db_session, start="2024-01-01", end="2024-01-02")

    assert result["aborted"] is True
    assert result["succeeded"] == 0
    assert result["failed"] == mod.CIRCUIT_BREAKER_CONSECUTIVE_FAILURES


def test_fetch_and_store_prices_does_not_abort_on_isolated_failures(db_session, monkeypatch):
    """A handful of scattered per-ticker failures (well under the circuit
    breaker threshold) shouldn't abort the whole run."""
    calls = {"n": 0}

    def fake_fetch_chart(ticker, period1, period2, max_retries=3):
        calls["n"] += 1
        if calls["n"] % 5 == 0:
            return None
        return {
            "timestamp": [1704067200],
            "indicators": {
                "quote": [{"open": [100], "high": [101], "low": [99], "close": [100.5], "volume": [1000]}],
                "adjclose": [{"adjclose": [100.5]}],
            },
        }

    monkeypatch.setattr(mod, "_fetch_chart", fake_fetch_chart)
    monkeypatch.setattr(mod.time, "sleep", lambda *a, **k: None)
    monkeypatch.setattr(mod, "pg_insert", _PgInsertShim)

    result = mod.fetch_and_store_prices(db_session, start="2024-01-01", end="2024-01-02")

    assert result["aborted"] is False
    assert result["succeeded"] > 0
