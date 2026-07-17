import { Fragment, memo, useState } from 'react'
import { formatDate, formatINR } from '@/lib/format'

const DATA_STATUS_LABEL = {
  skipped_no_point_in_time_fundamentals: 'no PIT data',
  skipped_no_matches: 'no matches',
}

const DATA_STATUS_TITLE = {
  skipped_no_point_in_time_fundamentals:
    'No fundamentals recorded from before this date — held cash',
  skipped_no_matches: 'No stocks passed the filters this period — held cash',
}

function PortfolioLog({ logs }) {
  const [expandedIndex, setExpandedIndex] = useState(null)

  if (!logs || logs.length === 0) {
    return (
      <div className="card text-center py-12 text-gray-500 dark:text-gray-400">
        No rebalance data
      </div>
    )
  }

  return (
    <div className="card">
      <h3 className="section-title">Rebalance Log</h3>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 dark:border-gray-700">
              <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-200">
                Date
              </th>
              <th className="text-right py-3 px-4 font-semibold text-gray-700 dark:text-gray-200">
                Portfolio Value
              </th>
              <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-200">
                Stocks
              </th>
              <th className="text-center py-3 px-4 font-semibold text-gray-700 dark:text-gray-200">
                Details
              </th>
            </tr>
          </thead>

          <tbody>
            {logs.map((log, i) => (
              <Fragment key={`${log.date}-${i}`}>
                <tr className="border-b border-gray-100 hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-700 transition">
                  <td className="py-3 px-4">
                    {formatDate(log.date, 'dd MMM yyyy')}
                    {log.data_status && log.data_status !== 'ok' && (
                      <span
                        title={DATA_STATUS_TITLE[log.data_status] || undefined}
                        className="ml-2 inline-block px-1.5 py-0.5 rounded text-[10px] font-medium cursor-help bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300"
                      >
                        {DATA_STATUS_LABEL[log.data_status] || log.data_status}
                      </span>
                    )}
                  </td>

                  <td className="py-3 px-4 text-right font-semibold text-gray-900 dark:text-white">
                    {formatINR(log.portfolio_value)}
                  </td>

                  <td className="py-3 px-4 text-gray-600 dark:text-gray-300">
                    {log.num_stocks || log.holdings?.length || 0}
                  </td>

                  <td className="py-3 px-4 text-center">
                    <button
                      onClick={() => setExpandedIndex(expandedIndex === i ? null : i)}
                      aria-expanded={expandedIndex === i}
                      className="text-emerald-600 dark:text-emerald-400 hover:underline text-xs font-medium"
                    >
                      {expandedIndex === i ? 'Hide' : 'View'}
                    </button>
                  </td>
                </tr>

                {expandedIndex === i && (
                  <tr className="border-b bg-gray-50 border-gray-100 dark:bg-gray-700 dark:border-gray-600">
                    <td colSpan={4} className="py-4 px-4">
                      <div className="space-y-2">
                        <p className="font-semibold text-sm text-gray-700 dark:text-gray-200">
                          Holdings:
                        </p>

                        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                          {log.holdings?.map((h, j) => (
                            <div
                              key={j}
                              className="p-2 rounded border text-xs bg-white border-gray-200 dark:bg-gray-800 dark:border-gray-600"
                            >
                              <p className="font-semibold text-gray-900 dark:text-white">
                                {h.ticker}
                              </p>
                              <p className="text-gray-600 dark:text-gray-300">{h.weight}</p>
                              <p className="text-gray-500 dark:text-gray-400">
                                ₹{(h.buy_price || 0).toFixed(2)}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default memo(PortfolioLog)
