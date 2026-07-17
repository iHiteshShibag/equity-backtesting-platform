from types import SimpleNamespace

import pandas as pd

from app.modules.backtest.engine.filters import apply_filters


def _cfg(**overrides):
    defaults = dict(market_cap_min=None, market_cap_max=None, roce_min=None, pat_positive=False)
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_market_cap_filter_excludes_out_of_range_rows():
    df = pd.DataFrame({
        "ticker": ["A", "B", "C"],
        "market_cap": [100, 500, 2000],
        "roce": [10, 15, 20],
        "pat": [1, 1, 1],
    })
    result = apply_filters(df, _cfg(market_cap_min=200, market_cap_max=1000))
    assert list(result["ticker"]) == ["B"]


def test_pat_positive_filter_drops_non_positive_pat():
    df = pd.DataFrame({
        "ticker": ["A", "B"],
        "market_cap": [100, 100],
        "roce": [10, 10],
        "pat": [-5, 5],
    })
    result = apply_filters(df, _cfg(pat_positive=True))
    assert list(result["ticker"]) == ["B"]
