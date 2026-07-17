from datetime import date

import pandas as pd

from app.modules.backtest.engine import backtest_engine as backtest_engine_module
from app.modules.backtest.engine.backtest_engine import BacktestConfig, BacktestEngine

PRICE_COLUMNS = ["ticker", "date", "open", "close", "adj_close"]
FUND_COLUMNS = [
    "ticker", "name", "sector", "report_date", "market_cap", "roce", "roe",
    "pe_ratio", "pb_ratio", "pat", "capital_employed", "total_debt", "total_equity",
]


def _prices(rows):
    return pd.DataFrame(rows, columns=PRICE_COLUMNS)


def _funds(rows):
    return pd.DataFrame(rows, columns=FUND_COLUMNS)


def _make_engine(cfg, prices_df, funds_df):
    engine = BacktestEngine(cfg, db=None)
    engine._load_all_prices = lambda: prices_df
    engine._load_all_fundamentals = lambda: funds_df
    engine._get_benchmark_metrics = lambda: None
    return engine


def _base_cfg(**overrides):
    defaults = dict(
        start_date=date(2020, 1, 1),
        end_date=date(2020, 7, 1),
        initial_capital=1_000_000,
        portfolio_size=20,
        rebalance_freq="quarterly",
        position_sizing="equal",
        sizing_metric=None,
        market_cap_min=1000,
        market_cap_max=10000,
        roce_min=None,
        pat_positive=False,
        rank_metrics=[],
        commission_bps=0,
        slippage_pct=0,
    )
    defaults.update(overrides)
    return BacktestConfig(**defaults)


def test_all_periods_skipped_when_fundamentals_never_predate_any_rebalance():
    # Reproduces the real bug: fundamentals.py stamps report_date at ingestion
    # time (e.g. "today"), which is always later than any historical rebalance
    # date -- so no historical rebalance should ever trade on it.
    prices = _prices([
        ("AAA", date(2020, 1, 1), 100, 100, 100),
        ("AAA", date(2020, 4, 1), 100, 100, 100),
        ("AAA", date(2020, 7, 1), 100, 100, 100),
    ])
    funds = _funds([
        ("AAA", "AAA", "Tech", date(2025, 1, 1), 5000, None, None, None, None, 10, 100, 50, 50),
    ])
    engine = _make_engine(_base_cfg(), prices, funds)

    result = engine.run()

    statuses = [log["data_status"] for log in result["rebalance_logs"]]
    assert statuses == ["skipped_no_point_in_time_fundamentals"] * 3
    assert result["data_quality"]["rebalances_skipped_no_data"] == 3
    assert result["data_quality"]["total_rebalances"] == 3
    assert "3 of 3" in result["data_quality"]["message"]
    assert result["metrics"]["final_value"] == 1_000_000
    assert result["metrics"]["total_return"] == 0.0


def test_periods_trade_normally_once_fundamentals_predate_rebalances():
    prices = _prices([
        ("AAA", date(2020, 1, 1), 100, 100, 100),
        ("AAA", date(2020, 4, 1), 100, 100, 100),
        ("AAA", date(2020, 7, 1), 100, 100, 100),
    ])
    funds = _funds([
        ("AAA", "AAA", "Tech", date(2019, 1, 1), 5000, None, None, None, None, 10, 100, 50, 50),
    ])
    engine = _make_engine(_base_cfg(), prices, funds)

    result = engine.run()

    statuses = [log["data_status"] for log in result["rebalance_logs"]]
    assert statuses == ["ok", "ok", "ok"]
    assert result["data_quality"]["rebalances_skipped_no_data"] == 0
    assert result["data_quality"]["message"] is None


def test_skipped_period_clears_stale_holdings_instead_of_double_liquidating():
    # Regression test: a period skipped for any reason (no point-in-time data,
    # no stocks pass filters) must clear out the prior period's positions
    # immediately, since they were already cashed out into `capital`. Before
    # the fix, the stale position dict survived the skip and got "sold" a
    # second time on the next rebalance -- corrupting capital with a phantom
    # trade.
    prices = _prices([
        ("AAA", date(2020, 1, 1), 100, 100, 100),
        ("AAA", date(2020, 4, 1), 200, 200, 200),
        ("AAA", date(2020, 7, 1), 150, 150, 150),
    ])
    funds = _funds([
        # Passes the market-cap filter as of rebalance 1 (2020-01-01)
        ("AAA", "AAA", "Tech", date(2019, 6, 1), 5000, None, None, None, None, 10, 100, 50, 50),
        # Latest-known-as-of rebalance 2 (2020-04-01): fails the filter
        ("AAA", "AAA", "Tech", date(2020, 2, 1), 50, None, None, None, None, 10, 100, 50, 50),
        # Latest-known-as-of rebalance 3 (2020-07-01): passes again
        ("AAA", "AAA", "Tech", date(2020, 5, 1), 5000, None, None, None, None, 10, 100, 50, 50),
    ])
    engine = _make_engine(_base_cfg(), prices, funds)

    result = engine.run()
    logs = result["rebalance_logs"]

    assert [log["data_status"] for log in logs] == ["ok", "skipped_no_stocks_passed_filters", "ok"]
    assert [log["num_stocks"] for log in logs] == [1, 0, 1]
    # Bought 10,000 shares at 100, sold at 200 on rebalance 2 -> capital = 2,000,000.
    assert logs[1]["portfolio_value"] == 2_000_000.0
    # No holdings survive the skip, so rebalance 3 must deploy that same
    # 2,000,000 -- not a phantom re-sale of the original position at the
    # rebalance-3 price (which would wrongly yield 1,500,000 instead).
    assert logs[2]["portfolio_value"] == 2_000_000.0
    # This skip is a filter miss, not a point-in-time data gap.
    assert result["data_quality"]["rebalances_skipped_no_data"] == 0


def test_ticker_excluded_from_universe_before_its_index_membership_start(monkeypatch):
    # Regression test for the survivorship-bias fix: a ticker not yet an
    # index member as of rb_date must be excluded even though it has
    # qualifying point-in-time fundamentals available.
    prices = _prices([
        ("NEWCO", date(2020, 1, 1), 100, 100, 100),
        ("NEWCO", date(2020, 4, 1), 100, 100, 100),
    ])
    funds = _funds([
        ("NEWCO", "NEWCO", "Tech", date(2019, 1, 1), 5000, None, None, None, None, 10, 100, 50, 50),
    ])
    engine = _make_engine(_base_cfg(end_date=date(2020, 4, 1)), prices, funds)

    # NEWCO only became an index member from 2020-03-01 onward. An empty set
    # from get_active_tickers means "no membership data, don't filter" (see
    # its docstring), so the pre-membership period must return some *other*
    # active ticker instead of an empty set to actually exercise exclusion.
    monkeypatch.setattr(
        backtest_engine_module,
        "get_active_tickers",
        lambda db, index_name, as_of: {"NEWCO"} if as_of >= date(2020, 3, 1) else {"SOMEOTHERTICKER"},
    )

    result = engine.run()
    logs = result["rebalance_logs"]

    assert logs[0]["data_status"] == "skipped_no_stocks_passed_filters"
    assert logs[0]["num_stocks"] == 0
    assert logs[1]["data_status"] == "ok"
    assert logs[1]["num_stocks"] == 1
