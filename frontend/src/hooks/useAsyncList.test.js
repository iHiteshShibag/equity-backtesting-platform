import { act, renderHook, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { useAsyncList } from './useAsyncList'

describe('useAsyncList', () => {
  it('starts loading and resolves with the fetched data', async () => {
    const fetcher = vi.fn().mockResolvedValue([{ id: 1 }])
    const { result } = renderHook(() => useAsyncList(fetcher))

    expect(result.current.loading).toBe(true)

    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.data).toEqual([{ id: 1 }])
    expect(result.current.error).toBeNull()
  })

  it('surfaces the API error message on failure', async () => {
    const fetcher = vi.fn().mockRejectedValue({ response: { data: { detail: 'Boom' } } })
    const { result } = renderHook(() => useAsyncList(fetcher, { fallbackError: 'Failed to load' }))

    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.error).toBe('Boom')
    expect(result.current.data).toBeNull()
  })

  it('falls back to the provided fallback message when the error has no detail', async () => {
    const fetcher = vi.fn().mockRejectedValue(new Error())
    const { result } = renderHook(() => useAsyncList(fetcher, { fallbackError: 'Custom fallback' }))

    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.error).toBe('Custom fallback')
  })

  it('reload() re-invokes the fetcher and refreshes data', async () => {
    const fetcher = vi.fn().mockResolvedValueOnce([1]).mockResolvedValueOnce([1, 2])
    const { result } = renderHook(() => useAsyncList(fetcher))

    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.data).toEqual([1])

    await act(async () => {
      await result.current.reload()
    })

    expect(fetcher).toHaveBeenCalledTimes(2)
    expect(result.current.data).toEqual([1, 2])
  })
})
