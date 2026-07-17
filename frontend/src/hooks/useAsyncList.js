import { useCallback, useEffect, useState } from 'react'
import { getErrorMessage } from '@/lib/errors'

// Shared load/loading/error boilerplate for views that fetch a list/resource
// on mount and need a manual `reload` after mutations.
export function useAsyncList(fetcher, { fallbackError = 'Failed to load', deps = [] } = {}) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      setData(await fetcher())
      setError(null)
    } catch (err) {
      setError(getErrorMessage(err, fallbackError))
    } finally {
      setLoading(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  useEffect(() => {
    load()
  }, [load])

  return { data, setData, loading, error, setError, reload: load }
}
