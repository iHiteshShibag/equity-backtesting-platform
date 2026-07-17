from types import SimpleNamespace

import pandas as pd
import pytest

from app.modules.backtest.engine.sizers import compute_weights


def test_equal_weighting_splits_evenly():
    selected = pd.DataFrame({"ticker": ["A", "B"], "market_cap": [100, 300]})
    weights = compute_weights(selected, SimpleNamespace(position_sizing="equal", sizing_metric=None))
    assert weights == {"A": 0.5, "B": 0.5}


def test_market_cap_weighting_is_proportional():
    selected = pd.DataFrame({"ticker": ["A", "B"], "market_cap": [100, 300]})
    weights = compute_weights(selected, SimpleNamespace(position_sizing="market_cap", sizing_metric=None))
    assert weights["A"] == pytest.approx(0.25)
    assert weights["B"] == pytest.approx(0.75)
