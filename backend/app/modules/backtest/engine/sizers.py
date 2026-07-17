import pandas as pd


def compute_weights(selected: pd.DataFrame, cfg) -> dict:
    tickers = list(selected["ticker"])
    n = len(tickers)
    if n == 0:
        return {}

    if cfg.position_sizing == "equal":
        return {t: 1.0 / n for t in tickers}

    elif cfg.position_sizing == "market_cap":
        caps = selected.set_index("ticker")["market_cap"].fillna(0).clip(lower=0)
        total = caps.sum()
        if total > 0:
            return (caps / total).to_dict()
        return {t: 1.0 / n for t in tickers}

    elif cfg.position_sizing == "metric" and cfg.sizing_metric:
        col = cfg.sizing_metric
        if col in selected.columns:
            vals = selected.set_index("ticker")[col].fillna(0).clip(lower=0)
            total = vals.sum()
            if total > 0:
                return (vals / total).to_dict()
        return {t: 1.0 / n for t in tickers}

    return {t: 1.0 / n for t in tickers}
