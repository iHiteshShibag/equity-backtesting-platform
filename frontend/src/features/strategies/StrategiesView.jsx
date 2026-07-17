import { listStrategies, setStrategyActive, deleteStrategy } from './api'
import { useAsyncList } from '@/hooks/useAsyncList'
import Skeleton from '@/components/Skeleton'

export default function StrategiesView() {
  const {
    data: strategies,
    loading,
    error,
    reload,
  } = useAsyncList(listStrategies, {
    fallbackError: 'Failed to load strategies',
  })

  const toggleActive = async (s) => {
    await setStrategyActive(s.id, !s.is_active)
    reload()
  }

  const remove = async (s) => {
    if (!window.confirm(`Delete saved strategy "${s.name}"?`)) return
    await deleteStrategy(s.id)
    reload()
  }

  if (loading) return <Skeleton className="h-32" />
  if (error) return <div className="card">{error}</div>

  if (!strategies || strategies.length === 0) {
    return (
      <div className="card text-center py-16">
        <div className="text-5xl mb-4">🔔</div>
        <h3 className="text-lg font-semibold mb-2 text-gray-900 dark:text-white">
          No saved strategies yet
        </h3>
        <p className="text-gray-600 dark:text-gray-300">
          Run a backtest and click "Save as Strategy" to get an email when it's due for rebalance.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {strategies.map((s) => (
        <div key={s.id} className="card flex items-center justify-between gap-4">
          <div className="min-w-0">
            <p className="font-semibold truncate">{s.name}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {s.rebalance_freq} · next rebalance {s.next_rebalance_date}
            </p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={() => toggleActive(s)}
              className={`text-xs font-semibold px-2.5 py-1 rounded-lg ${
                s.is_active ? 'bg-emerald-600/10 text-emerald-500' : 'bg-gray-500/10 text-gray-500'
              }`}
            >
              {s.is_active ? 'Active' : 'Paused'}
            </button>
            <button
              onClick={() => remove(s)}
              className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-red-500/10 text-red-500"
            >
              Delete
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}
