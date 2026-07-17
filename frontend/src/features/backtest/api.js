import api from '@/api/client'

export const queueBacktest = (params) => {
  return api.post('/api/backtest/run', params).then((r) => r.data)
}

export const getBacktestJob = (jobId) => {
  return api.get(`/api/backtest/jobs/${jobId}`).then((r) => r.data)
}

export const healthCheck = () => {
  return api.get('/api/backtest/health').then((r) => r.data)
}

export const getUniverseCount = (params) => {
  return api.get('/api/backtest/universe-count', { params }).then((r) => r.data)
}

const POLL_INTERVAL_MS = 1500

export async function runBacktest(params, { onStatusChange } = {}) {
  const job = await queueBacktest(params)
  onStatusChange?.(job.status)

  let current = job
  while (current.status === 'pending' || current.status === 'running') {
    await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS))
    current = await getBacktestJob(job.id)
    onStatusChange?.(current.status)
  }

  if (current.status === 'failure') {
    throw new Error(current.error || 'Backtest failed')
  }

  return current.result
}
