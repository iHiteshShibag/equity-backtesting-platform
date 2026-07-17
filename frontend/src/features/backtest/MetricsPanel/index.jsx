import { memo, useMemo } from 'react'
import { formatINR } from '@/lib/format'

const TONE_CLASSES = {
  positive:
    'bg-green-50 border-green-200 text-green-700 dark:bg-green-500/10 dark:border-green-500/30 dark:text-green-400',
  negative:
    'bg-red-50 border-red-200 text-red-700 dark:bg-red-500/10 dark:border-red-500/30 dark:text-red-400',
  neutral:
    'bg-blue-50 border-blue-200 text-blue-700 dark:bg-blue-500/10 dark:border-blue-500/30 dark:text-blue-400',
}

function MetricsPanel({ metrics, benchmark, dataQuality }) {
  const benchmarkCagr = benchmark?.cagr ?? 0
  const alpha = (metrics?.cagr ?? 0) - benchmarkCagr

  const hero = useMemo(() => {
    if (!metrics) return []
    return [
      {
        label: 'Total Return',
        value: `${metrics.total_return >= 0 ? '+' : ''}${metrics.total_return?.toFixed(2)}%`,
        tone: metrics.total_return >= 0 ? 'positive' : 'negative',
        icon: '💰',
      },
      {
        label: 'Sharpe Ratio',
        value: metrics.sharpe?.toFixed(2),
        tone: metrics.sharpe >= 1 ? 'positive' : 'neutral',
        icon: '📊',
      },
      {
        label: 'Max Drawdown',
        value: `${metrics.max_drawdown?.toFixed(2)}%`,
        tone: 'negative',
        icon: '⬇️',
      },
      {
        label: 'Win Rate',
        value: `${metrics.win_rate?.toFixed(1)}%`,
        tone: metrics.win_rate >= 50 ? 'positive' : 'neutral',
        icon: '🎯',
      },
    ]
  }, [metrics])

  const cards = useMemo(() => {
    if (!metrics) return []
    return [
      {
        label: 'CAGR',
        value: `${metrics.cagr?.toFixed(2)}%`,
        color: 'border-l-green-500',
        icon: '📈',
      },
      {
        label: 'Benchmark CAGR',
        value: `${benchmarkCagr.toFixed(2)}%`,
        color: 'border-l-indigo-500',
        icon: '📊',
      },
      {
        label: 'Alpha',
        value: `${alpha.toFixed(2)}%`,
        color: alpha >= 0 ? 'border-l-green-500' : 'border-l-red-500',
        icon: '🚀',
      },
      {
        label: 'Sortino Ratio',
        value: metrics.sortino?.toFixed(2),
        color: 'border-l-blue-600',
        icon: '📉',
      },
      {
        label: 'Calmar Ratio',
        value: metrics.calmar?.toFixed(2),
        color: 'border-l-purple-500',
        icon: '⚡',
      },
      {
        label: 'Trading Costs',
        value: formatINR(metrics.total_costs),
        color: 'border-l-orange-500',
        icon: '🧾',
      },
      {
        label: 'Final Value',
        value: formatINR(metrics.final_value),
        color: 'border-l-amber-700',
        icon: '💵',
      },
    ]
  }, [metrics, benchmarkCagr, alpha])

  if (!metrics || Object.keys(metrics).length === 0) {
    return (
      <div className="text-center py-12 text-gray-500 dark:text-gray-400">No metrics available</div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Methodology disclaimer */}
      <div className="text-xs rounded-lg border p-3 leading-relaxed bg-amber-50 border-amber-200 text-amber-800 dark:bg-amber-500/10 dark:border-amber-500/30 dark:text-amber-300">
        <strong>Methodology note:</strong> the stock universe reflects today's Nifty 100
        constituents applied across the whole date range — stocks that fell out of the index
        historically aren't included (survivorship bias). Market Cap filters use today's market cap
        for every historical period, since point-in-time market cap isn't available from our data
        source.
        {dataQuality?.rebalances_skipped_no_data > 0 && <> {dataQuality.message}</>}
      </div>

      {/* Hero: Performance Dashboard */}
      <div>
        <h3 className="section-title">Performance Dashboard</h3>
        <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {hero.map((h) => (
            <div
              key={h.label}
              className={`rounded-xl border-2 p-5 flex flex-col gap-1 ${TONE_CLASSES[h.tone]}`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wide opacity-80">
                  {h.label}
                </span>
                <span className="text-xl opacity-60">{h.icon}</span>
              </div>
              <span className="text-3xl font-extrabold">{h.value ?? '-'}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Secondary metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map((card) => (
          <div key={card.label} className={`metric-card ${card.color}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
                  {card.label}
                </p>
                <p className="text-2xl font-bold mt-1">{card.value || '-'}</p>
              </div>
              <span className="text-4xl opacity-20">{card.icon}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default memo(MetricsPanel)
