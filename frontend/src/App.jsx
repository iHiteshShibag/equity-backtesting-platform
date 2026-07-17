import { lazy, Suspense, useState } from 'react'
import { useAuth } from '@/context/AuthContext'
import { useTheme } from '@/context/ThemeContext'
import LoginScreen from '@/components/LoginScreen'
import Sidebar from '@/components/Sidebar'
import { ConfigurePromptEmptyState, DatabaseEmptyState } from '@/components/EmptyState'
import DisclaimerGate, { DisclaimerBanner } from '@/components/DisclaimerGate'
import BacktestForm from './features/backtest/BacktestForm'
import MetricsPanel from './features/backtest/MetricsPanel'
import PortfolioLog from './features/backtest/PortfolioLog'
import { triggerIngestion } from './features/dataManagement/api'
import { saveStrategy } from './features/strategies/api'
import { getErrorMessage } from '@/lib/errors'
import './index.css'

// Split out of the main bundle: recharts (EquityCurve/DrawdownChart) and
// xlsx/file-saver (ExportButton) are only needed once a backtest result
// exists, and DataManagementView/UserAdminView are separate views the user
// may never visit in a given session.
const EquityCurve = lazy(() => import('./features/backtest/Charts/EquityCurve'))
const DrawdownChart = lazy(() => import('./features/backtest/Charts/DrawdownChart'))
const ExportButton = lazy(() => import('./features/backtest/ExportButton'))
const DataManagementView = lazy(() => import('./features/dataManagement/DataManagementView'))
const StrategiesView = lazy(() => import('./features/strategies/StrategiesView'))
const UserAdminView = lazy(() => import('./features/userAdmin/UserAdminView'))
const ProfileView = lazy(() => import('./features/profile/ProfileView'))

function isDbEmptyError(message) {
  return typeof message === 'string' && /no price data|run data ingestion/i.test(message)
}

function PageHeader({ icon, title, subtitle }) {
  return (
    <div className="flex items-center gap-3 mb-6 pb-4 border-b border-gray-200 dark:border-gray-800">
      <span className="w-9 h-9 shrink-0 rounded-lg bg-gradient-to-br from-emerald-500 to-emerald-700 flex items-center justify-center text-base">
        {icon}
      </span>
      <div>
        <h1 className="text-lg font-bold leading-tight text-gray-900 dark:text-white">{title}</h1>
        <p className="text-xs text-gray-500 dark:text-gray-400">{subtitle}</p>
      </div>
    </div>
  )
}

function BacktestDashboard({ onNavigate }) {
  const [result, setResult] = useState(null)
  const [config, setConfig] = useState(null)
  const [errorDetail, setErrorDetail] = useState(null)
  const [populating, setPopulating] = useState(false)
  const [savingStrategy, setSavingStrategy] = useState(false)
  const [saveMessage, setSaveMessage] = useState(null)

  const handleBacktestResult = (res, form) => {
    setResult(res)
    setConfig(form)
    setErrorDetail(null)
  }

  const handleError = (detail) => {
    setResult(null)
    setErrorDetail(detail)
  }

  const handleSaveStrategy = async () => {
    const name = window.prompt('Name this strategy:')
    if (!name) return
    setSavingStrategy(true)
    try {
      await saveStrategy(name, config)
      setSaveMessage('Saved! You will get an email when it is due for rebalance.')
    } catch (err) {
      setSaveMessage(getErrorMessage(err, 'Failed to save strategy'))
    } finally {
      setSavingStrategy(false)
      setTimeout(() => setSaveMessage(null), 4000)
    }
  }

  const handlePopulate = async () => {
    setPopulating(true)
    try {
      await triggerIngestion()
      onNavigate('data')
    } finally {
      setPopulating(false)
    }
  }

  return (
    <>
      <DisclaimerBanner />
      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Left: Form */}
        <div className="lg:col-span-1">
          <BacktestForm onResult={handleBacktestResult} onError={handleError} />
        </div>

        {/* Right: Results */}
        <div className="lg:col-span-2">
          {isDbEmptyError(errorDetail) ? (
            <DatabaseEmptyState onPopulate={handlePopulate} loading={populating} />
          ) : errorDetail ? (
            <div className="card text-center py-16">
              <div className="text-5xl mb-4">⚠️</div>
              <h3 className="text-lg font-semibold mb-2 text-gray-900 dark:text-white">
                Backtest Failed
              </h3>
              <p className="text-gray-600 dark:text-gray-300">{errorDetail}</p>
            </div>
          ) : !result ? (
            <ConfigurePromptEmptyState />
          ) : (
            <div className="space-y-6">
              <MetricsPanel
                metrics={result.metrics}
                benchmark={result.benchmark}
                dataQuality={result.data_quality}
              />
              <Suspense fallback={<div className="card h-64 animate-pulse" />}>
                <EquityCurve
                  data={result.timeseries}
                  initialCapital={config?.initial_capital || 1000000}
                />
                <DrawdownChart data={result.timeseries} />
              </Suspense>
            </div>
          )}
        </div>
      </div>

      {/* Full Width: Portfolio Log */}
      {result && (
        <div className="grid grid-cols-1 gap-6 mb-8">
          <PortfolioLog logs={result.rebalance_logs} />
        </div>
      )}

      {/* Winners & Losers */}
      {result && (result.winners?.length > 0 || result.losers?.length > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="card">
            <h3 className="section-title">🏆 Top Winners</h3>
            <div className="space-y-2">
              {result.winners?.map((w, i) => (
                <div
                  key={i}
                  className="flex justify-between items-center p-2 rounded bg-green-50 dark:bg-green-900/30"
                >
                  <span className="font-semibold text-gray-900 dark:text-white">{w.ticker}</span>
                  <span className="text-green-600 dark:text-green-400 font-bold">
                    +{w.return_pct?.toFixed(2)}%
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <h3 className="section-title">⚠️ Bottom Losers</h3>
            <div className="space-y-2">
              {result.losers?.map((l, i) => (
                <div
                  key={i}
                  className="flex justify-between items-center p-2 rounded bg-red-50 dark:bg-red-900/30"
                >
                  <span className="font-semibold text-gray-900 dark:text-white">{l.ticker}</span>
                  <span className="text-red-600 dark:text-red-400 font-bold">
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
          <Suspense fallback={null}>
            <ExportButton
              timeseries={result.timeseries}
              rebalanceLogs={result.rebalance_logs}
              metrics={result.metrics}
            />
          </Suspense>
          <div className="mt-3 flex items-center gap-3">
            <button
              onClick={handleSaveStrategy}
              disabled={savingStrategy}
              className="text-sm font-semibold px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white"
            >
              {savingStrategy ? 'Saving…' : '🔔 Save as Strategy'}
            </button>
            {saveMessage && (
              <span className="text-xs text-gray-500 dark:text-gray-400">{saveMessage}</span>
            )}
          </div>
        </div>
      )}
    </>
  )
}

export default function App() {
  const { user, ready, isAdmin } = useAuth()
  const { darkMode } = useTheme()
  const [activeView, setActiveView] = useState('dashboard')

  if (!ready) return null
  if (!user) return <LoginScreen />

  const view = activeView === 'users' && !isAdmin ? 'dashboard' : activeView

  return (
    <div
      className={`flex min-h-screen ${darkMode ? 'bg-zinc-900 text-white' : 'bg-gray-50 text-gray-900'}`}
    >
      <DisclaimerGate />
      <Sidebar activeView={activeView} onNavigate={setActiveView} />

      <main className="flex-1 py-8 min-w-0">
        <div className="max-w-[1800px] mx-auto px-6">
          {view === 'dashboard' && (
            <>
              <PageHeader
                icon="📈"
                title="Equity Backtesting Platform"
                subtitle="Test fundamental-based stock selection strategies"
              />
              <BacktestDashboard onNavigate={setActiveView} />
            </>
          )}
          {view === 'strategies' && (
            <>
              <PageHeader
                icon="🔔"
                title="Saved Strategies"
                subtitle="Get emailed when a saved strategy is due for rebalance"
              />
              <Suspense fallback={null}>
                <StrategiesView />
              </Suspense>
            </>
          )}
          {view === 'data' && (
            <>
              <PageHeader
                icon="🗄"
                title="Data Management"
                subtitle="Ingest historical prices and fundamentals for the Nifty 100 universe"
              />
              <Suspense fallback={null}>
                <DataManagementView />
              </Suspense>
            </>
          )}
          {view === 'users' && isAdmin && (
            <>
              <PageHeader
                icon="👤"
                title="User Admin"
                subtitle="Manage accounts, roles, and access"
              />
              <Suspense fallback={null}>
                <UserAdminView />
              </Suspense>
            </>
          )}
          {view === 'profile' && (
            <>
              <PageHeader icon="🙍" title="Your Profile" subtitle="Manage your account details" />
              <Suspense fallback={null}>
                <ProfileView />
              </Suspense>
            </>
          )}

          <footer className="text-center text-sm mt-12 pt-8 border-t text-gray-500 border-gray-200 dark:text-gray-400 dark:border-gray-700">
            <p>Equity Backtesting Platform v1.0 | Built for fundamental strategy testing</p>
          </footer>
        </div>
      </main>
    </div>
  )
}
