from datetime import date

from bs4 import BeautifulSoup

import app.modules.market_data.fundamentals_screener as mod
from app.modules.market_data.fundamentals_screener import (
    _is_recent_enough,
    _extract_periods,
    _section_table,
    fetch_company_page,
    parse_current_market_cap,
    parse_historical_fundamentals,
    parse_period_label,
)

SAMPLE_PAGE = """
<html><body>
<ul id="top-ratios">
  <li class="flex flex-space-between" data-source="default">
    <span class="name">Market Cap</span>
    <span class="nowrap value">₹ <span class="number">17,53,627</span> Cr.</span>
  </li>
  <li class="flex flex-space-between" data-source="default">
    <span class="name">Current Price</span>
    <span class="nowrap value">₹ <span class="number">1,297</span></span>
  </li>
</ul>

<section id="profit-loss">
  <table>
    <thead><tr><th></th><th>Mar 2023</th><th>Mar 2024</th><th>TTM</th></tr></thead>
    <tbody>
      <tr><td>Sales+</td><td>800,000</td><td>900,000</td><td>950,000</td></tr>
      <tr><td>Net Profit+</td><td>50,000</td><td>60,000</td><td>65,000</td></tr>
      <tr><td>EPS in Rs</td><td>10.5</td><td>12.0</td><td>13.0</td></tr>
    </tbody>
  </table>
</section>

<section id="balance-sheet">
  <table>
    <thead><tr><th></th><th>Mar 2023</th><th>Mar 2024</th><th>TTM</th></tr></thead>
    <tbody>
      <tr><td>Equity Capital</td><td>1,000</td><td>1,000</td><td>1,000</td></tr>
      <tr><td>Reserves</td><td>199,000</td><td>249,000</td><td>259,000</td></tr>
      <tr><td>Borrowings+</td><td>50,000</td><td>55,000</td><td>56,000</td></tr>
      <tr><td>Total Assets</td><td>300,000</td><td>350,000</td><td>360,000</td></tr>
    </tbody>
  </table>
</section>

<section id="ratios">
  <table>
    <thead><tr><th></th><th>Mar 2023</th><th>Mar 2024</th><th>TTM</th></tr></thead>
    <tbody>
      <tr><td>Debtor Days</td><td>10</td><td></td><td>-</td></tr>
      <tr><td>ROCE %</td><td>18%</td><td>20%</td><td>21%</td></tr>
    </tbody>
  </table>
</section>
</body></html>
"""


def _soup(html):
    return BeautifulSoup(html, "html.parser")


def test_parse_period_label_parses_fiscal_year_end():
    assert parse_period_label("Mar 2024") == date(2024, 3, 31)


def test_parse_period_label_rejects_ttm_and_garbage():
    assert parse_period_label("TTM") is None
    assert parse_period_label("") is None
    assert parse_period_label("Foo 2024") is None
    assert parse_period_label("Mar") is None


def test_parse_current_market_cap_reads_top_ratio_bar():
    assert parse_current_market_cap(_soup(SAMPLE_PAGE)) == 1753627.0


def test_parse_historical_fundamentals_excludes_ttm_column():
    rows = parse_historical_fundamentals(_soup(SAMPLE_PAGE))
    assert [r["report_date"] for r in rows] == [date(2023, 3, 31), date(2024, 3, 31)]


def test_parse_historical_fundamentals_computes_derived_fields():
    rows = parse_historical_fundamentals(_soup(SAMPLE_PAGE))
    fy2024 = rows[1]
    assert fy2024["revenue"] == 900000.0
    assert fy2024["pat"] == 60000.0
    assert fy2024["total_equity"] == 250000.0  # 1,000 + 249,000
    assert fy2024["total_debt"] == 55000.0
    assert fy2024["capital_employed"] == 305000.0
    assert fy2024["roe"] == 24.0  # 60,000 / 250,000 * 100
    assert fy2024["roce"] == 20.0  # real value straight from screener, not approximated
    assert fy2024["market_cap"] == 1753627.0  # current-only, same for every period


def test_parse_historical_fundamentals_handles_missing_sections_gracefully():
    html_no_balance_sheet = SAMPLE_PAGE.replace('id="balance-sheet"', 'id="balance-sheet-missing"')
    rows = parse_historical_fundamentals(_soup(html_no_balance_sheet))
    assert rows[0]["total_equity"] is None
    assert rows[0]["roce"] is not None  # ratios section is untouched
    assert rows[0]["revenue"] is not None  # P&L section is untouched


def test_parse_historical_fundamentals_returns_empty_when_no_periods_found():
    assert parse_historical_fundamentals(_soup("<html><body></body></html>")) == []
    assert parse_historical_fundamentals(None) == []


def test_is_recent_enough():
    periods_current = [(0, date(2024, 3, 31)), (1, date(2025, 3, 31))]
    periods_stale = [(0, date(2018, 3, 31)), (1, date(2019, 3, 31))]
    assert _is_recent_enough(periods_current, today=date(2026, 7, 13)) is True
    assert _is_recent_enough(periods_stale, today=date(2026, 7, 13)) is False
    assert _is_recent_enough([], today=date(2026, 7, 13)) is False


def test_fetch_company_page_keeps_consolidated_when_recent_enough(monkeypatch):
    calls = []

    def fake_fetch_page(http_session, ticker, view, max_retries=3):
        calls.append(view)
        return _soup(SAMPLE_PAGE)

    monkeypatch.setattr(mod, "_fetch_page", fake_fetch_page)
    fetch_company_page(http_session=None, screener_symbol="FAKE", today=date(2026, 7, 13))

    assert calls == ["consolidated/"]  # never fell back to standalone


def test_fetch_company_page_falls_back_to_standalone_when_consolidated_is_stale(monkeypatch):
    # Mirrors the real MOIL case: consolidated financials frozen years ago while
    # standalone stays current, since MOIL has no subsidiaries to consolidate.
    stale_html = SAMPLE_PAGE.replace("2023", "2015").replace("2024", "2016")

    def fake_fetch_page(http_session, ticker, view, max_retries=3):
        return _soup(stale_html) if view == "consolidated/" else _soup(SAMPLE_PAGE)

    monkeypatch.setattr(mod, "_fetch_page", fake_fetch_page)
    soup = fetch_company_page(http_session=None, screener_symbol="FAKE", today=date(2026, 7, 13))

    periods = _extract_periods(_section_table(soup, "profit-loss"))
    assert max(d.year for _, d in periods) == 2024
