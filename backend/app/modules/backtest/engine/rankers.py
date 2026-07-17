import pandas as pd


def rank_stocks(df: pd.DataFrame, rank_metrics: list) -> pd.DataFrame:
    if not rank_metrics or df.empty:
        return df

    rank_cols = []
    for rm in rank_metrics:
        col = rm.metric
        ascending = rm.order == "asc"
        if col in df.columns:
            rank_col = f"_rank_{col}"
            df[rank_col] = df[col].rank(ascending=ascending, na_option="bottom")
            rank_cols.append(rank_col)

    if rank_cols:
        df["_composite_rank"] = df[rank_cols].mean(axis=1)
        df = df.sort_values("_composite_rank")
        df = df.drop(columns=rank_cols + ["_composite_rank"])

    return df.reset_index(drop=True)
