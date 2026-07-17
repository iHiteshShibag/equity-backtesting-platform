from types import SimpleNamespace

import pandas as pd

from app.modules.backtest.engine.rankers import rank_stocks


def test_rank_stocks_orders_by_single_metric_descending():
    df = pd.DataFrame({"ticker": ["A", "B", "C"], "roe": [10, 30, 20]})
    ranked = rank_stocks(df, [SimpleNamespace(metric="roe", order="desc")])
    assert list(ranked["ticker"]) == ["B", "C", "A"]


def test_rank_stocks_returns_input_unchanged_when_no_metrics():
    df = pd.DataFrame({"ticker": ["A", "B"], "roe": [10, 30]})
    ranked = rank_stocks(df, [])
    assert list(ranked["ticker"]) == ["A", "B"]
