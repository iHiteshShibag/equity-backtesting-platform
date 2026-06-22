import { useState } from 'react'
import BacktestForm from './components/BacktestForm'
import EquityCurve from './components/Charts/EquityCurve'
import DrawdownChart from './components/Charts/DrawdownChart'
import MetricsPanel from './components/MetricsPanel'
import PortfolioLog from './components/PortfolioLog'
import ExportButton from './components/ExportButton'
import './index.css'

export default function App() {
  const [result, setResult] = useState(null)
  const [config, setConfig] = useState(null)
  const [darkMode, setDarkMode] = useState(false)

  const handleBacktestResult = (res) => {
    setResult(res)
  }

  // Store the config from the form for context

  return (
    <div
  className={`min-h-screen py-8 ${
    darkMode ? 'dark bg-gray-900 text-white' : 'bg-gray-50 text-gray-900'
  }`}
>
      <div className="max-w-7xl mx-auto px-4">
        {/* Header */}
        <div className="mb-8 flex justify-between items-start">
          <div>
            <h1
              className={`text-4xl font-bold mb-2 ${
                darkMode ? 'text-white' : 'text-gray-900'
              }`}
            >
              📈 Equity Backtesting Platform
            </h1>

            <p
              className={`text-lg ${
                darkMode ? 'text-gray-400' : 'text-gray-600'
              }`}
            >
              Test fundamental-based stock selection strategies
            </p>
          </div>

          <button
            onClick={() => setDarkMode(!darkMode)}
            className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700"
          >
            {darkMode ? '☀️ Light Mode' : '🌙 Dark Mode'}
          </button>
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Left: Form */}
          <div className="lg:col-span-1">
            <BacktestForm onResult={handleBacktestResult} />
          </div>

          {/* Right: Results */}
          <div className="lg:col-span-2">
            {!result ? (
              <div
                className={`card text-center py-16 ${
                  darkMode ? 'bg-gray-800 text-white' : ''
                }`}
              >
                <div className="text-6xl mb-4">🎯</div>
                <h3
                  className={`text-xl font-semibold mb-2 ${
                    darkMode ? 'text-white' : 'text-gray-900'
                  }`}
                >
                  Configure and Run a Backtest
                </h3>
                <p className={darkMode ? 'text-gray-300' : 'text-gray-600'}>
                  Set your parameters on the left to begin testing your strategy
                </p>
              </div>
            ) : (
              <div className="space-y-6">
                <MetricsPanel
                  metrics={result.metrics}
                  benchmark={result.benchmark}
                  darkMode={darkMode}
                />
                <EquityCurve
                  data={result.timeseries}
                  initialCapital={config?.initial_capital || 1000000}
                />
                <DrawdownChart data={result.timeseries} />
              </div>
            )}
          </div>
        </div>

        {/* Full Width: Portfolio Log */}
        {result && (
          <div className="grid grid-cols-1 gap-6 mb-8">
            <PortfolioLog
              logs={result.rebalance_logs}
              darkMode={darkMode}
            />
          </div>
        )}

        {/* Winners & Losers */}
        {result && (result.winners?.length > 0 || result.losers?.length > 0) && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            {/* Winners */}
            <div className={`card ${darkMode ? 'bg-gray-800 text-white' : ''}`}>
              <h3 className="section-title">🏆 Top Winners</h3>
              <div className="space-y-2">
                {result.winners?.map((w, i) => (
                  <div
                    key={i}
                    className={
                      'flex justify-between items-center p-2 rounded ' +
                      (darkMode ? 'bg-green-900/30' : 'bg-green-50')
                    }
                  >
                    <span
  className={`font-semibold ${
    darkMode ? 'text-white' : 'text-gray-900'
  }`}
>{w.ticker}</span>
                    <span className="text-green-600 font-bold">
                      +{w.return_pct?.toFixed(2)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Losers */}
            <div className={`card ${darkMode ? 'bg-gray-800 text-white' : ''}`}>
              <h3 className="section-title">⚠️ Bottom Losers</h3>
              <div className="space-y-2">
                {result.losers?.map((l, i) => (
                  <div
                    key={i}
                    className={
                      'flex justify-between items-center p-2 rounded ' +
                      (darkMode ? 'bg-green-900/30' : 'bg-green-50')
                    }
                  >
                    <span
  className={`font-semibold ${
    darkMode ? 'text-white' : 'text-gray-900'
  }`}
>{l.ticker}</span>
                    <span className="text-red-600 font-bold">
                      {l.return_pct?.toFixed(2)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Export Section */}
        {result && (
          <div className="card mb-8">
            <h3 className="section-title">Export Results</h3>
            <ExportButton
              timeseries={result.timeseries}
              rebalanceLogs={result.rebalance_logs}
              metrics={result.metrics}
            />
          </div>
        )}

        {/* Footer */}
        <footer
          className={`text-center text-sm mt-12 pt-8 border-t ${
            darkMode
              ? 'text-gray-400 border-gray-700'
              : 'text-gray-500 border-gray-200'
          }`}
        >
          <p>Equity Backtesting Platform v1.0 | Built for fundamental strategy testing</p>
        </footer>
      </div>
    </div>
  )
}
