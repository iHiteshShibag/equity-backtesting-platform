import React, { useState } from 'react'
import { format, parseISO } from 'date-fns'

export default function PortfolioLog({ logs, darkMode }) {
const [expandedIndex, setExpandedIndex] = useState(null)

if (!logs || logs.length === 0) {
return ( <div className="card text-center py-12 text-gray-500">
No rebalance data </div>
)
}

const formatDate = (dateStr) => {
try {
return format(parseISO(dateStr), 'dd MMM yyyy')
} catch {
return dateStr
}
}

return (
<div className={`card ${darkMode ? 'bg-gray-800 text-white' : ''}`}> <h3 className="section-title">Rebalance Log</h3>


  <div className="overflow-x-auto">
    <table className="w-full text-sm">
      <thead>
        <tr
          className={`border-b ${
            darkMode ? 'border-gray-700' : 'border-gray-200'
          }`}
        >
          <th
            className={`text-left py-3 px-4 font-semibold ${
              darkMode ? 'text-gray-200' : 'text-gray-700'
            }`}
          >
            Date
          </th>

          <th
            className={`text-right py-3 px-4 font-semibold ${
              darkMode ? 'text-gray-200' : 'text-gray-700'
            }`}
          >
            Portfolio Value
          </th>

          <th
            className={`text-left py-3 px-4 font-semibold ${
              darkMode ? 'text-gray-200' : 'text-gray-700'
            }`}
          >
            Stocks
          </th>

          <th
            className={`text-center py-3 px-4 font-semibold ${
              darkMode ? 'text-gray-200' : 'text-gray-700'
            }`}
          >
            Details
          </th>
        </tr>
      </thead>

      <tbody>
        {logs.map((log, i) => (
          <React.Fragment key={`${log.date}-${i}`}>
            <tr
              className={`border-b transition ${
                  darkMode
                    ? 'border-gray-700 hover:bg-gray-700'
                    : 'border-gray-100 hover:bg-gray-50'
                }`}
              >
              <td className="py-3 px-4">
                {formatDate(log.date)}
              </td>

              <td
                className={`py-3 px-4 text-right font-semibold ${
                    darkMode ? 'text-white' : 'text-gray-900'
                  }`}
                >
                ₹{(log.portfolio_value || 0).toLocaleString('en-IN')}
              </td>

              <td
                className={`py-3 px-4 ${
                    darkMode ? 'text-gray-300' : 'text-gray-600'
                  }`}
                >
                {log.num_stocks || log.holdings?.length || 0}
              </td>

              <td className="py-3 px-4 text-center">
                <button
                  onClick={() =>
                    setExpandedIndex(
                      expandedIndex === i ? null : i
                    )
                  }
                  className="text-blue-500 hover:underline text-xs font-medium"
                >
                  {expandedIndex === i ? 'Hide' : 'View'}
                </button>
              </td>
            </tr>

            {expandedIndex === i && (
              <tr
                  className={`border-b ${
                    darkMode
                      ? 'bg-gray-700 border-gray-600'
                      : 'bg-gray-50 border-gray-100'
                  }`}
                >
                <td colSpan={4} className="py-4 px-4">
                  <div className="space-y-2">
                    <p
                      className={`font-semibold text-sm ${
                        darkMode
                          ? 'text-gray-200'
                          : 'text-gray-700'
                      }`}
                    >
                      Holdings:
                    </p>

                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                      {log.holdings?.map((h, j) => (
                        <div
                          key={j}
                          className={`p-2 rounded border text-xs ${
                            darkMode
                              ? 'bg-gray-800 border-gray-600'
                              : 'bg-white border-gray-200'
                          }`}
                        >
                          <p
                            className={`font-semibold ${
                              darkMode
                                ? 'text-white'
                                : 'text-gray-900'
                            }`}
                          >
                            {h.ticker}
                          </p>

                          <p
                            className={
                              darkMode
                                ? 'text-gray-300'
                                : 'text-gray-600'
                            }
                          >
                            {h.weight}
                          </p>

                          <p
                            className={
                              darkMode
                                ? 'text-gray-400'
                                : 'text-gray-500'
                            }
                          >
                            ₹{(h.buy_price || 0).toFixed(2)}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                </td>
              </tr>
            )}
          </React.Fragment>
        ))}
      </tbody>
    </table>
  </div>
</div>
)
}
