export default function MetricsPanel({ metrics, benchmark, darkMode }) {
  if (!metrics || Object.keys(metrics).length === 0) {
    return <div className="text-center py-12 text-gray-500">No metrics available</div>
  }

  const benchmarkCagr = benchmark?.cagr ?? 0 
  const alpha = (metrics?.cagr ?? 0) - benchmarkCagr
  const cards = [
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
      label: 'Total Return',
      value: `${metrics.total_return?.toFixed(2)}%`,
      color: 'border-l-green-600',
      icon: '💰',
    },
    {
      label: 'Sharpe Ratio',
      value: metrics.sharpe?.toFixed(2),
      color: 'border-l-blue-500',
      icon: '📊',
    },
    {
      label: 'Sortino Ratio',
      value: metrics.sortino?.toFixed(2),
      color: 'border-l-blue-600',
      icon: '📉',
    },
    {
      label: 'Max Drawdown',
      value: `${metrics.max_drawdown?.toFixed(2)}%`,
      color: 'border-l-red-500',
      icon: '⬇️',
    },
    {
      label: 'Calmar Ratio',
      value: metrics.calmar?.toFixed(2),
      color: 'border-l-purple-500',
      icon: '⚡',
    },
    {
      label: 'Final Value',
      value: `₹${(metrics.final_value || 0).toLocaleString('en-IN')}`,
      color: 'border-l-amber-700',
      icon: '💵',
    },
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map(card => (
        <div
          key={card.label}
          className={`metric-card ${card.color} ${
            darkMode ? 'bg-gray-800 text-white' : ''
          }`}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                {card.label}
              </p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {card.value || '-'}
              </p>
            </div>
            <span className="text-4xl opacity-20">{card.icon}</span>
          </div>
        </div>
      ))}
    </div>
  )
}
