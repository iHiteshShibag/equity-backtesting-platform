import { useEffect, useRef, useState } from 'react'
import { getIngestionStatus, triggerIngestion } from '@/features/dataManagement/api'
import { RefreshIcon, DatabaseIcon } from '@/components/icons'
import { getErrorMessage } from '@/lib/errors'
import { formatDateTime } from '@/lib/format'
import ErrorBanner from '@/components/ErrorBanner'

const POLL_MS = 3000

const STATUS_BADGE = {
  running: 'text-emerald-400 bg-emerald-500/10',
  success: 'text-emerald-400 bg-emerald-500/10',
  partial: 'text-amber-400 bg-amber-500/10',
  failure: 'text-red-400 bg-red-500/10',
}

function FailedTickers({ label, tickers }) {
  if (!tickers?.length) return null
  return (
    <details className="text-xs">
      <summary className="cursor-pointer text-amber-600 dark:text-amber-400">
        {label}: {tickers.length} failed
      </summary>
      <p className="mt-1 pl-3 text-gray-500 dark:text-gray-400">{tickers.join(', ')}</p>
    </details>
  )
}

export default function DataManagementView() {
  const [status, setStatus] = useState(null)
  const [starting, setStarting] = useState(false)
  const [error, setError] = useState(null)
  const pollRef = useRef(null)

  const refresh = async () => {
    try {
      const data = await getIngestionStatus()
      setStatus(data)
      return data
    } catch (err) {
      setError(getErrorMessage(err))
      return null
    }
  }

  useEffect(() => {
    refresh()
    return () => clearInterval(pollRef.current)
  }, [])

  useEffect(() => {
    if (status?.latest_run?.status === 'running') {
      pollRef.current = setInterval(refresh, POLL_MS)
    } else {
      clearInterval(pollRef.current)
    }
    return () => clearInterval(pollRef.current)
  }, [status?.latest_run?.status])

  const handlePopulate = async () => {
    setStarting(true)
    setError(null)
    try {
      await triggerIngestion()
      await refresh()
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setStarting(false)
    }
  }

  const latest = status?.latest_run
  const running = latest?.status === 'running'

  return (
    <div className="space-y-6">
      <ErrorBanner message={error} />

      {/* DB counts */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { label: 'Stocks', value: status?.counts?.stocks },
          { label: 'Daily Prices', value: status?.counts?.prices },
          { label: 'Fundamentals', value: status?.counts?.fundamentals },
        ].map((c) => (
          <div key={c.label} className="metric-card border-l-emerald-500">
            <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
              {c.label}
            </p>
            <p className="text-2xl font-bold mt-1">{c.value?.toLocaleString('en-IN') ?? '–'}</p>
          </div>
        ))}
      </div>

      {/* Ingestion control */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="section-title mb-0">
            <DatabaseIcon width={20} height={20} /> Ingestion
          </h3>
          <button
            onClick={refresh}
            aria-label="Refresh ingestion status"
            title="Refresh"
            className="p-1.5 rounded-lg transition text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-white/5"
          >
            <RefreshIcon width={16} height={16} />
          </button>
        </div>

        <p className="text-sm mb-4 text-gray-500 dark:text-gray-400">
          Runs automatically {status?.schedule || 'on a schedule'}, with per-ticker retries and
          backoff on transient failures. You can also trigger a run manually below.
        </p>

        {running ? (
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="font-medium">{latest.step || 'Running…'}</span>
            </div>
            <div className="h-2 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700">
              <div className="h-full w-1/2 bg-emerald-500 animate-pulse rounded-full" />
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {latest ? (
              <div className="space-y-1.5">
                <p className="text-gray-600 dark:text-gray-300">
                  Last run ({latest.trigger}) at {formatDateTime(latest.started_at)}:{' '}
                  <span
                    className={`inline-block text-[10px] font-bold uppercase tracking-wide px-1.5 py-0.5 rounded ${STATUS_BADGE[latest.status] || ''}`}
                  >
                    {latest.status}
                  </span>
                  {' — '}
                  prices {latest.prices_success}✓/{latest.prices_failed}✗, fundamentals{' '}
                  {latest.funds_success}✓/{latest.funds_failed}✗
                  {latest.error && <span className="text-red-500"> ({latest.error})</span>}
                </p>
                <FailedTickers label="Price tickers" tickers={latest.prices_failed_tickers} />
                <FailedTickers label="Fundamentals tickers" tickers={latest.funds_failed_tickers} />
              </div>
            ) : (
              <p className="text-gray-600 dark:text-gray-300">No ingestion has been run yet.</p>
            )}
            <button
              onClick={handlePopulate}
              disabled={starting}
              className="btn-primary px-5 py-2.5"
            >
              {starting ? '⏳ Queuing…' : '⬇ Run Ingestion Now'}
            </button>
          </div>
        )}
      </div>

      {/* Run history */}
      {status?.recent_runs?.length > 0 && (
        <div className="card">
          <h3 className="section-title">Recent Runs</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left border-b border-gray-200 text-gray-500 dark:border-white/10 dark:text-gray-400">
                  <th className="py-2 pr-4">Started</th>
                  <th className="py-2 pr-4">Trigger</th>
                  <th className="py-2 pr-4">Status</th>
                  <th className="py-2 pr-4">Prices</th>
                  <th className="py-2 pr-4">Fundamentals</th>
                </tr>
              </thead>
              <tbody>
                {status.recent_runs.map((r) => (
                  <tr key={r.id} className="border-b border-gray-100 dark:border-white/5">
                    <td className="py-2 pr-4 whitespace-nowrap">{formatDateTime(r.started_at)}</td>
                    <td className="py-2 pr-4 capitalize">{r.trigger}</td>
                    <td className="py-2 pr-4">
                      <span
                        className={`inline-block text-[10px] font-bold uppercase tracking-wide px-1.5 py-0.5 rounded ${STATUS_BADGE[r.status] || ''}`}
                      >
                        {r.status}
                      </span>
                    </td>
                    <td
                      className="py-2 pr-4"
                      title={r.prices_failed_tickers?.join(', ') || undefined}
                    >
                      {r.prices_success}✓ / {r.prices_failed}✗
                    </td>
                    <td
                      className="py-2 pr-4"
                      title={r.funds_failed_tickers?.join(', ') || undefined}
                    >
                      {r.funds_success}✓ / {r.funds_failed}✗
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
