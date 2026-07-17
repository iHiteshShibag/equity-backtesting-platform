import { DatabaseIcon } from '@/components/icons'

const PREVIEW_ITEMS = [
  { icon: '📊', label: 'Performance metrics', desc: 'CAGR, Sharpe, max drawdown & more' },
  { icon: '📈', label: 'Equity curve & drawdown', desc: 'Visualize growth vs. the benchmark' },
  { icon: '🔁', label: 'Rebalance log', desc: 'Every buy/sell at each rebalance date' },
  { icon: '🏆', label: 'Winners & losers', desc: 'Top and bottom performing picks' },
]

export function ConfigurePromptEmptyState() {
  return (
    <div className="card text-center py-14">
      <div className="mx-auto mb-4 w-16 h-16 rounded-full flex items-center justify-center text-3xl bg-emerald-50 dark:bg-emerald-500/10">
        🎯
      </div>
      <h3 className="text-xl font-semibold mb-2 text-gray-900 dark:text-white">
        Configure and Run a Backtest
      </h3>
      <p className="mb-8 text-gray-600 dark:text-gray-300">
        Set your parameters on the left to begin testing your strategy
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-xl mx-auto text-left">
        {PREVIEW_ITEMS.map((item) => (
          <div
            key={item.label}
            className="flex items-start gap-3 rounded-xl border p-3 border-gray-100 bg-gray-50/70 dark:border-gray-700 dark:bg-gray-900/40"
          >
            <span className="text-xl shrink-0">{item.icon}</span>
            <div>
              <p className="text-sm font-semibold text-gray-900 dark:text-white">{item.label}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">{item.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export function DatabaseEmptyState({ onPopulate, loading }) {
  return (
    <div className="card text-center py-16 border-2 border-dashed border-gray-300 dark:border-gray-600">
      <div className="mx-auto mb-4 w-16 h-16 rounded-full flex items-center justify-center bg-amber-50 text-amber-600 dark:bg-amber-500/10 dark:text-amber-400">
        <DatabaseIcon width={32} height={32} />
      </div>
      <h3 className="text-xl font-semibold mb-2 text-gray-900 dark:text-white">
        Database is Empty
      </h3>
      <p className="mb-6 max-w-sm mx-auto text-gray-600 dark:text-gray-300">
        No historical price or fundamental data has been loaded yet. Populate the database before
        running a backtest.
      </p>
      <button onClick={onPopulate} disabled={loading} className="btn-primary px-6 py-3">
        {loading ? '⏳ Starting ingestion…' : 'Click here to populate historical market data'}
      </button>
    </div>
  )
}
