import pandas as pd


def apply_filters(df: pd.DataFrame, cfg) -> pd.DataFrame:
    result = df.copy()
    if cfg.market_cap_min is not None:
        result = result[result["market_cap"] >= cfg.market_cap_min]
    if cfg.market_cap_max is not None:
        result = result[result["market_cap"] <= cfg.market_cap_max]
    if cfg.roce_min is not None and result["roce"].notna().any():
        result = result[result["roce"] >= cfg.roce_min]
    if cfg.pat_positive and result["pat"].notna().any():
        result = result[result["pat"] > 0] 
    return result.reset_index(drop=True)

