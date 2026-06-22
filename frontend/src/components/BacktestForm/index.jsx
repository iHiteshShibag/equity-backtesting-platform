import { useState } from 'react'
import { runBacktest } from '@/api/client'

const FREQ_OPTIONS = ['monthly', 'quarterly', 'yearly']
const SIZER_OPTIONS = ['equal', 'market_cap', 'metric']
const METRICS = ['roe', 'roce', 'pe_ratio', 'pb_ratio', 'pat', 'market_cap']

export default function BacktestForm({ onResult }) {
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
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const addRankMetric = () => {
    setForm(f => ({
      ...f,
      rank_metrics: [...f.rank_metrics, { metric: 'pe_ratio', order: 'asc' }],
    }))
  }

  const removeRankMetric = (i) => {
    setForm(f => ({
      ...f,
      rank_metrics: f.rank_metrics.filter((_, idx) => idx !== i),
    }))
  }

  const updateRankMetric = (i, field, value) => {
    setForm(f => {
      const r = [...f.rank_metrics]
      r[i] = { ...r[i], [field]: value }
      return { ...f, rank_metrics: r }
    })
  }

  const handleSubmit = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await runBacktest(form)
      onResult(result)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="w-full max-w-2xl mx-auto space-y-6">
      <div className="card">
        <h2 className="section-title">Configure Backtest</h2>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        {/* Date Range */}
        <div className="mb-6 pb-6 border-b border-gray-200">
          <h3 className="field-label">Date Range</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="field-label">Start Date</label>
              <input
                type="date"
                value={form.start_date}
                onChange={e => setForm(f => ({ ...f, start_date: e.target.value }))}
                className="input"
              />
            </div>
            <div>
              <label className="field-label">End Date</label>
              <input
                type="date"
                value={form.end_date}
                onChange={e => setForm(f => ({ ...f, end_date: e.target.value }))}
                className="input"
              />
            </div>
          </div>
        </div>

        {/* Capital & Portfolio */}
        <div className="mb-6 pb-6 border-b border-gray-200">
          <h3 className="field-label">Portfolio Settings</h3>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="field-label">Initial Capital (₹)</label>
              <input
                type="number"
                value={form.initial_capital}
                onChange={e => setForm(f => ({ ...f, initial_capital: +e.target.value }))}
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
                onChange={e => setForm(f => ({ ...f, portfolio_size: +e.target.value }))}
                className="input"
              />
            </div>
            <div>
              <label className="field-label">Rebalance Frequency</label>
              <select
                value={form.rebalance_freq}
                onChange={e => setForm(f => ({ ...f, rebalance_freq: e.target.value }))}
                className="input"
              >
                {FREQ_OPTIONS.map(o => (
                  <option key={o} value={o}>
                    {o.charAt(0).toUpperCase() + o.slice(1)}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="mb-6 pb-6 border-b border-gray-200">
          <h3 className="field-label">Filters</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="field-label">Market Cap Min (Cr)</label>
              <input
                type="number"
                value={form.market_cap_min || ''}
                onChange={e => setForm(f => ({ ...f, market_cap_min: e.target.value ? +e.target.value : null }))}
                className="input"
              />
            </div>
            <div>
              <label className="field-label">Market Cap Max (Cr)</label>
              <input
                type="number"
                value={form.market_cap_max || ''}
                onChange={e => setForm(f => ({ ...f, market_cap_max: e.target.value ? +e.target.value : null }))}
                className="input"
              />
            </div>
            <div>
              <label className="field-label">Min ROCE (%)</label>
              <input
                type="number"
                value={form.roce_min || ''}
                onChange={e => setForm(f => ({ ...f, roce_min: e.target.value ? +e.target.value : null }))}
                className="input"
              />
            </div>
            <div className="flex items-end">
              <label className="flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.pat_positive}
                  onChange={e => setForm(f => ({ ...f, pat_positive: e.target.checked }))}
                  className="w-4 h-4 rounded border-gray-300"
                />
                <span className="ml-2 text-sm text-gray-700">PAT &gt; 0</span>
              </label>
            </div>
          </div>
        </div>

        {/* Ranking */}
        <div className="mb-6 pb-6 border-b border-gray-200">
          <h3 className="field-label">Ranking Metrics</h3>
          <div className="space-y-3">
            {form.rank_metrics.map((rm, i) => (
              <div key={i} className="flex gap-3 items-end">
                <div className="flex-1">
                  <label className="field-label text-xs">Metric</label>
                  <select
                    value={rm.metric}
                    onChange={e => updateRankMetric(i, 'metric', e.target.value)}
                    className="input"
                  >
                    {METRICS.map(m => (
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
                    onChange={e => updateRankMetric(i, 'order', e.target.value)}
                    className="input"
                  >
                    <option value="desc">Descending ↓</option>
                    <option value="asc">Ascending ↑</option>
                  </select>
                </div>
                <button
                  onClick={() => removeRankMetric(i)}
                  className="px-3 py-2 text-red-500 hover:bg-red-50 rounded-lg transition"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
          <button
            onClick={addRankMetric}
            className="mt-3 text-sm text-blue-600 hover:underline"
          >
            + Add metric
          </button>
        </div>

        {/* Position Sizing */}
        <div className="mb-6">
          <h3 className="field-label">Position Sizing</h3>
          <div className="flex gap-3 mb-3 flex-wrap">
            {SIZER_OPTIONS.map(o => (
              <button
                key={o}
                onClick={() => setForm(f => ({ ...f, position_sizing: o }))}
                className={`px-4 py-2 rounded-lg text-sm font-medium border-2 transition ${
                  form.position_sizing === o
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:border-blue-400'
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
                onChange={e => setForm(f => ({ ...f, sizing_metric: e.target.value }))}
                className="input"
              >
                <option value="">Select metric</option>
                {METRICS.map(m => (
                  <option key={m} value={m}>
                    {m.toUpperCase()}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        <button
          onClick={handleSubmit}
          disabled={loading}
          className="w-full btn-primary py-3 text-base"
        >
          {loading ? '⏳ Running backtest...' : '▶ Run Backtest'}
        </button>
      </div>
    </div>
  )
}
