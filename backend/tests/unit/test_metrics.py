import pandas as pd

from app.modules.backtest.engine.metrics import compute_metrics


def test_flat_series_has_zero_drawdown_and_return():
    values = pd.Series([100_000] * 10)
    result = compute_metrics(values, initial_capital=100_000)
    assert result["max_drawdown"] == 0
    assert result["total_return"] == 0


def test_flat_series_has_zero_sharpe_and_sortino_not_float_noise():
    # A perfectly flat equity curve (e.g. a backtest that held cash the whole
    # time) has zero real variance, but pct_change()/std() can leave ~1e-20-scale
    # floating-point noise instead of an exact 0 -- which previously slipped past
    # `std() > 0` and blew up into a nonsensical ratio (e.g. -1.37e17).
    values = pd.Series([1_000_000.0] * 35)
    result = compute_metrics(values, initial_capital=1_000_000)
    assert result["sharpe"] == 0.0
    assert result["sortino"] == 0.0


def test_monotonically_increasing_series_has_positive_cagr():
    values = pd.Series([100_000 + i * 1000 for i in range(300)])
    result = compute_metrics(values, initial_capital=100_000)
    assert result["cagr"] > 0
    assert result["max_drawdown"] == 0
