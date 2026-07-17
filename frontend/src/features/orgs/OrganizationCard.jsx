import { useState } from 'react'
import { getMyOrg, updateMyOrg } from './api'
import { useAsyncList } from '@/hooks/useAsyncList'
import { getErrorMessage } from '@/lib/errors'
import ErrorBanner from '@/components/ErrorBanner'
import Skeleton from '@/components/Skeleton'

const TIERS = ['free', 'pro', 'enterprise']

const TIER_RATE_LIMITS = {
  free: '5/minute',
  pro: '30/minute',
  enterprise: '120/minute',
}

export default function OrganizationCard() {
  const {
    data: org,
    setData: setOrg,
    loading,
    error,
    setError,
  } = useAsyncList(
    async () => {
      try {
        return await getMyOrg()
      } catch (err) {
        if (err?.response?.status === 404) return null
        throw err
      }
    },
    { fallbackError: 'Failed to load organization' },
  )
  const [saving, setSaving] = useState(false)

  const handleTierChange = async (tier) => {
    setSaving(true)
    try {
      setOrg(await updateMyOrg({ tier }))
      setError(null)
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to update tier'))
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <Skeleton className="h-24" />

  if (!org) {
    return (
      <div className="card">
        <h3 className="section-title">Organization</h3>
        <p className="text-sm text-gray-500 dark:text-gray-400">No organization assigned.</p>
      </div>
    )
  }

  return (
    <div className="card">
      <h3 className="section-title">Organization</h3>
      <ErrorBanner message={error} />
      <div className="flex items-center justify-between gap-4 flex-wrap mt-3">
        <div>
          <p className="font-semibold">{org.name}</p>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Rate limit: {TIER_RATE_LIMITS[org.tier] || TIER_RATE_LIMITS.free} on backtest runs
          </p>
        </div>
        <select
          value={org.tier}
          disabled={saving}
          onChange={(e) => handleTierChange(e.target.value)}
          className="px-3 py-2 rounded-lg border text-sm capitalize border-gray-300 dark:bg-zinc-900 dark:border-white/10 dark:text-white"
        >
          {TIERS.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </div>
    </div>
  )
}
