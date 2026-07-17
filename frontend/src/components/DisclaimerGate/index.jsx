import { useState } from 'react'
import { useAuth } from '@/context/AuthContext'

export function DisclaimerBanner() {
  return (
    <div className="text-xs rounded-lg px-4 py-2 mb-6 border bg-amber-50 border-amber-200 text-amber-800 dark:bg-amber-900/20 dark:border-amber-800 dark:text-amber-200">
      ⚠️ Backtested results are hypothetical and do not represent actual trading. Past performance
      does not guarantee future results. This platform does not provide investment advice.
    </div>
  )
}

export default function DisclaimerGate() {
  const { user, acceptTos } = useAuth()
  const [accepting, setAccepting] = useState(false)

  if (!user || user.tosAcceptedAt) return null

  const handleAccept = async () => {
    setAccepting(true)
    try {
      await acceptTos()
    } finally {
      setAccepting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4">
      <div className="max-w-lg w-full rounded-xl p-6 bg-white text-gray-900 dark:bg-zinc-800 dark:text-white">
        <h2 className="text-lg font-bold mb-3">Before you continue</h2>
        <p className="text-sm mb-3 leading-relaxed">
          This platform is a research and education tool for testing fundamental-based equity
          strategies historically. It does <strong>not</strong> provide investment advice, and
          backtested performance is hypothetical — it does not represent real trading and does not
          guarantee future results.
        </p>
        <p className="text-sm mb-5 leading-relaxed">
          By continuing, you acknowledge you understand this and will not treat any output as a
          recommendation to buy or sell securities.
        </p>
        <button
          onClick={handleAccept}
          disabled={accepting}
          className="w-full py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white font-semibold"
        >
          {accepting ? 'Saving…' : 'I Understand, Continue'}
        </button>
      </div>
    </div>
  )
}
