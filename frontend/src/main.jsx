import React from 'react'
import ReactDOM from 'react-dom/client'
import * as Sentry from '@sentry/react'
import App from './App'
import { AuthProvider } from './context/AuthContext'
import { ThemeProvider } from './context/ThemeContext'
import './index.css'

// Sentry.init with an empty/undefined dsn is a documented no-op, so this is
// safe to call unconditionally in local dev where VITE_SENTRY_DSN is unset.
Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  environment: import.meta.env.MODE,
  integrations: [Sentry.browserTracingIntegration()],
  tracesSampleRate: 0.1,
})

function ErrorFallback() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 text-gray-700 p-6 text-center">
      <div>
        <p className="text-lg font-semibold mb-2">Something went wrong.</p>
        <p className="text-sm text-gray-500 mb-4">
          The error has been reported. Try reloading the page.
        </p>
        <button onClick={() => window.location.reload()} className="btn-primary px-4 py-2">
          Reload
        </button>
      </div>
    </div>
  )
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <Sentry.ErrorBoundary fallback={<ErrorFallback />}>
      <ThemeProvider>
        <AuthProvider>
          <App />
        </AuthProvider>
      </ThemeProvider>
    </Sentry.ErrorBoundary>
  </React.StrictMode>,
)
