import { useEffect, useState } from 'react'
import { runBacktest, getUniverseCount } from '@/features/backtest/api'
import { getErrorMessage } from '@/lib/errors'
import ErrorBanner from '@/components/ErrorBanner'

const FREQ_OPTIONS = ['monthly', 'quarterly', 'yearly']
const SIZER_OPTIONS = ['equal', 'market_cap', 'metric']
const METRICS = ['roe', 'roce', 'pe_ratio', 'pb_ratio', 'pat', 'market_cap']

function Section({ icon, title, collapsed, onToggle, right, children }) {
  return (
    <div className="rounded-xl border border-gray-100 dark:border-gray-700 bg-gray-50/70 dark:bg-gray-900/40 overflow-hidden">
      <button
        type="button"
        onClick={onToggle}
        className="w-full flex items-center justify-between gap-3 p-4 text-left"
      >
        <h3 className="subsection-label flex items-center gap-1.5 mb-0">
          <span>{icon}</span> {title}
        </h3>
        <div className="flex items-center gap-2 shrink-0">
          {right}
          <span
            className={`text-gray-400 dark:text-gray-500 transition-transform duration-200 ${collapsed ? '-rotate-90' : ''}`}
          >
            ▾
          </span>
        </div>
      </button>
      {!collapsed && <div className="px-4 pb-4">{children}</div>}
    </div>
  )
}

export default function BacktestForm({ onResult, onError }) {
  const [form, setForm] = useState({
    start_date: '2018-01-01',
    end_date: new Date().toISOString().split('T')[0],
    initial_capital: 1000000,
    portfolio_size: 20,
    rebalance_freq: 'quarterly',
    position_sizing: 'equal',
    sizing_metric: null,
    market_cap_min: 1000,
    market_cap_max: 100000,
    roce_min: null,
    pat_positive: false,
    rank_metrics: [{ metric: 'roe', order: 'desc' }],
    commission_bps: 5,
    slippage_pct: 0.1,
  })
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState(null)
  const [error, setError] = useState(null)
  const [collapsed, setCollapsed] = useState({})
  const toggleSection = (key) => setCollapsed((c) => ({ ...c, [key]: !c[key] }))

  const [universeCount, setUniverseCount] = useState(null)
  const [countLoading, setCountLoading] = useState(false)

  useEffect(() => {
    setCountLoading(true)
    const handle = setTimeout(() => {
      getUniverseCount({
        market_cap_min: form.market_cap_min ?? undefined,
        market_cap_max: form.market_cap_max ?? undefined,
        roce_min: form.roce_min ?? undefined,
        pat_positive: form.pat_positive,
      })
        .then(setUniverseCount)
        .catch(() => setUniverseCount(null))
        .finally(() => setCountLoading(false))
    }, 400)
    return () => clearTimeout(handle)
  }, [form.market_cap_min, form.market_cap_max, form.roce_min, form.pat_positive])

  const addRankMetric = () => {
    setForm((f) => ({
      ...f,
      rank_metrics: [...f.rank_metrics, { metric: 'pe_ratio', order: 'asc' }],
    }))
  }

  const removeRankMetric = (i) => {
    setForm((f) => ({
      ...f,
      rank_metrics: f.rank_metrics.filter((_, idx) => idx !== i),
    }))
  }

  const updateRankMetric = (i, field, value) => {
    setForm((f) => {
      const r = [...f.rank_metrics]
      r[i] = { ...r[i], [field]: value }
      return { ...f, rank_metrics: r }
    })
  }

  const handleSubmit = async () => {
    setLoading(true)
    setError(null)
    setStatus('pending')
    try {
      const result = await runBacktest(form, { onStatusChange: setStatus })
      onResult(result, form)
    } catch (err) {
      const detail = getErrorMessage(err)
      setError(detail)
      onError?.(detail)
    } finally {
      setLoading(false)
      setStatus(null)
    }
  }

  const STATUS_LABEL = {
    pending: '⏳ Queued…',
    running: '⚙️ Running backtest…',
  }

  return (
    <div className="w-full max-w-2xl mx-auto space-y-6">
      <div className="card">
        <h2 className="section-title">
          <span>⚙️</span> Configure Backtest
        </h2>

        {error && (
          <div className="mb-4">
            <ErrorBanner message={error} />
          </div>
        )}

        <div className="space-y-4">
          {/* Date Range */}
          <Section
            icon="📅"
            title="Date Range"
            collapsed={!!collapsed.dates}
            onToggle={() => toggleSection('dates')}
          >
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="field-label">Start Date</label>
                <input
                  type="date"
                  value={form.start_date}
                  onChange={(e) => setForm((f) => ({ ...f, start_date: e.target.value }))}
                  className="input"
                />
              </div>
              <div>
                <label className="field-label">End Date</label>
                <input
                  type="date"
                  value={form.end_date}
                  onChange={(e) => setForm((f) => ({ ...f, end_date: e.target.value }))}
                  className="input"
                />
              </div>
            </div>
          </Section>

          {/* Capital & Portfolio */}
          <Section
            icon="💰"
            title="Portfolio Settings"
            collapsed={!!collapsed.portfolio}
            onToggle={() => toggleSection('portfolio')}
          >
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="field-label">Initial Capital (₹)</label>
                <input
                  type="number"
                  value={form.initial_capital}
                  onChange={(e) => setForm((f) => ({ ...f, initial_capital: +e.target.value }))}
                  className="input"
                />
              </div>
              <div>
                <label className="field-label">Portfolio Size</label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={form.portfolio_size}
                  onChange={(e) => setForm((f) => ({ ...f, portfolio_size: +e.target.value }))}
                  className="input"
                />
              </div>
              <div>
                <label className="field-label">Rebalance Frequency</label>
                <select
                  value={form.rebalance_freq}
                  onChange={(e) => setForm((f) => ({ ...f, rebalance_freq: e.target.value }))}
                  className="input"
                >
                  {FREQ_OPTIONS.map((o) => (
                    <option key={o} value={o}>
                      {o.charAt(0).toUpperCase() + o.slice(1)}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </Section>

          {/* Filters */}
          <Section
            icon="🔍"
            title="Filters"
            collapsed={!!collapsed.filters}
            onToggle={() => toggleSection('filters')}
            right={
              universeCount && universeCount.universe > 0 ? (
                <span
                  className={`text-xs font-semibold px-2 py-1 rounded-full whitespace-nowrap ${
                    countLoading
                      ? 'bg-gray-100 dark:bg-gray-800 text-gray-400'
                      : 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400'
                  }`}
                >
                  {countLoading
                    ? '…'
                    : `${universeCount.matched} / ${universeCount.universe} stocks match`}
                </span>
              ) : null
            }
          >
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="field-label">Market Cap Min (Cr)</label>
                <input
                  type="number"
                  value={form.market_cap_min || ''}
                  onChange={(e) =>
                    setForm((f) => ({
                      ...f,
                      market_cap_min: e.target.value ? +e.target.value : null,
                    }))
                  }
                  className="input"
                />
              </div>
              <div>
                <label className="field-label">Market Cap Max (Cr)</label>
                <input
                  type="number"
                  value={form.market_cap_max || ''}
                  onChange={(e) =>
                    setForm((f) => ({
                      ...f,
                      market_cap_max: e.target.value ? +e.target.value : null,
                    }))
                  }
                  className="input"
                />
              </div>
              <div>
                <label className="field-label">Min ROCE (%)</label>
                <input
                  type="number"
                  value={form.roce_min || ''}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, roce_min: e.target.value ? +e.target.value : null }))
                  }
                  className="input"
                />
              </div>
              <div className="flex items-end">
                <label className="flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={form.pat_positive}
                    onChange={(e) => setForm((f) => ({ ...f, pat_positive: e.target.checked }))}
                    aria-label="Filter to only profit-after-tax positive stocks"
                    className="w-4 h-4 rounded border-gray-300 dark:border-gray-600"
                  />
                  <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">PAT &gt; 0</span>
                </label>
              </div>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
              Market Cap filters use today's market cap for every historical period — point-in-time
              market cap isn't available from our data source.
            </p>
          </Section>

          {/* Ranking */}
          <Section
            icon="📊"
            title="Ranking Metrics"
            collapsed={!!collapsed.ranking}
            onToggle={() => toggleSection('ranking')}
          >
            <div className="space-y-3">
              {form.rank_metrics.map((rm, i) => (
                <div key={i} className="flex flex-col sm:flex-row gap-3 sm:items-end">
                  <div className="flex-1">
                    <label className="field-label text-xs">Metric</label>
                    <select
                      value={rm.metric}
                      onChange={(e) => updateRankMetric(i, 'metric', e.target.value)}
                      className="input"
                    >
                      {METRICS.map((m) => (
                        <option key={m} value={m}>
                          {m.replace('_', ' ').toUpperCase()}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="flex-1">
                    <label className="field-label text-xs">Order</label>
                    <select
                      value={rm.order}
                      onChange={(e) => updateRankMetric(i, 'order', e.target.value)}
                      className="input"
                    >
                      <option value="desc">Descending ↓</option>
                      <option value="asc">Ascending ↑</option>
                    </select>
                  </div>
                  <button
                    onClick={() => removeRankMetric(i)}
                    aria-label={`Remove ranking metric ${rm.metric.replace('_', ' ')}`}
                    className="self-start sm:self-auto px-3 py-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg transition"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
            <button
              onClick={addRankMetric}
              className="mt-3 text-sm font-medium text-emerald-600 dark:text-emerald-400 hover:underline"
            >
              + Add metric
            </button>
          </Section>

          {/* Trading Costs */}
          <Section
            icon="💸"
            title="Trading Costs"
            collapsed={!!collapsed.costs}
            onToggle={() => toggleSection('costs')}
          >
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="field-label">Brokerage Commission (bps)</label>
                <input
                  type="number"
                  min="0"
                  step="0.1"
                  value={form.commission_bps}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, commission_bps: e.target.value ? +e.target.value : 0 }))
                  }
                  className="input"
                />
              </div>
              <div>
                <label className="field-label">Execution Slippage (%)</label>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={form.slippage_pct}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, slippage_pct: e.target.value ? +e.target.value : 0 }))
                  }
                  className="input"
                />
              </div>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
              Applied on every simulated buy and sell — deducted from portfolio value at each
              rebalance.
            </p>
          </Section>

          {/* Position Sizing */}
          <Section
            icon="⚖️"
            title="Position Sizing"
            collapsed={!!collapsed.sizing}
            onToggle={() => toggleSection('sizing')}
          >
            <div className="flex gap-3 mb-3 flex-wrap">
              {SIZER_OPTIONS.map((o) => (
                <button
                  key={o}
                  onClick={() => setForm((f) => ({ ...f, position_sizing: o }))}
                  className={`px-4 py-2 rounded-lg text-sm font-medium border-2 transition ${
                    form.position_sizing === o
                      ? 'bg-emerald-600 text-white border-emerald-600'
                      : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-200 border-gray-300 dark:border-gray-600 hover:border-emerald-400'
                  }`}
                >
                  {o.replace('_', ' ').charAt(0).toUpperCase() + o.replace('_', ' ').slice(1)}
                </button>
              ))}
            </div>
            {form.position_sizing === 'metric' && (
              <div>
                <label className="field-label text-sm">Sizing Metric</label>
                <select
                  value={form.sizing_metric || ''}
                  onChange={(e) => setForm((f) => ({ ...f, sizing_metric: e.target.value }))}
                  className="input"
                >
                  <option value="">Select metric</option>
                  {METRICS.map((m) => (
                    <option key={m} value={m}>
                      {m.toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </Section>
        </div>

        <button
          onClick={handleSubmit}
          disabled={loading}
          className="w-full btn-primary py-3 text-base mt-6 shadow-lg shadow-emerald-900/10"
        >
          {loading ? STATUS_LABEL[status] || '⏳ Running backtest…' : '▶ Run Backtest'}
        </button>
      </div>
    </div>
  )
}
