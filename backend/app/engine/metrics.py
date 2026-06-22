import numpy as np
import pandas as pd


def compute_metrics(values: pd.Series, initial_capital: float) -> dict:
    values = values.dropna()
    if len(values) < 2:
        return {
            "cagr": 0, "total_return": 0, "sharpe": 0,
            "sortino": 0, "max_drawdown": 0, "calmar": 0,
            "final_value": float(values.iloc[-1]) if len(values) > 0 else initial_capital
        }

    n_years = max(len(values) / 252, 0.01)
    total_return = values.iloc[-1] / initial_capital
    cagr = (total_return ** (1 / n_years) - 1) * 100

    daily_ret = values.pct_change().dropna()
    rf_daily = 0.06 / 252
    excess = daily_ret - rf_daily

    sharpe = 0.0
    if excess.std() > 0:
        sharpe = (excess.mean() / excess.std()) * np.sqrt(252)

    downside = daily_ret[daily_ret < rf_daily]
    sortino = 0.0
    if len(downside) > 1 and downside.std() > 0:
        sortino = (excess.mean() / downside.std()) * np.sqrt(252)

    rolling_max = values.cummax()
    drawdown_series = (values - rolling_max) / rolling_max
    max_dd = float(drawdown_series.min()) * 100

    calmar = cagr / abs(max_dd) if max_dd != 0 else 0

    return {
        "cagr": round(cagr, 2),
        "total_return": round((total_return - 1) * 100, 2),
        "sharpe": round(float(sharpe), 2),
        "sortino": round(float(sortino), 2),
        "max_drawdown": round(max_dd, 2),
        "calmar": round(calmar, 2),
        "final_value": round(float(values.iloc[-1]), 2),
    }
